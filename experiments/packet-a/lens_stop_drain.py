"""Isolated, in-memory stop/freeze/drain state machine for Conversation Lens.

This module is NOT silently installed into server.py. Integrate endpoints against
its explicit transition methods only after the current MacBook worktree is read.
No clips, tokens, fingerprints, transcripts or names are written to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import re
import secrets
import threading
import time
from typing import Callable, Dict, Optional, Sequence

HEX_SHA = re.compile(r"^[a-f0-9]{64}$")
WINDOW_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


class LeaseConflict(Exception):
    """A second capture exists or a provided lease is stale."""


class InvalidWindow(ValueError):
    """The audio is not an authorized one-use recording window."""


@dataclass(frozen=True)
class Admission:
    capture: str
    epoch: int
    window_id: str
    nonce: str
    force_mixed: bool
    draining: bool


@dataclass
class ApprovedWindow:
    digest: str
    force_mixed: bool
    state: str = "ready"
    nonce: str = ""


@dataclass
class Lease:
    capture: str
    epoch: int
    mode: str
    deadline: Optional[float] = None
    windows: Dict[str, ApprovedWindow] = field(default_factory=dict)
    active_uploads: set[str] = field(default_factory=set)
    nonces: Dict[str, str] = field(default_factory=dict)
    consumed: set[str] = field(default_factory=set)


class CaptureDrainCoordinator:
    """Thread-safe capture generation and narrow audio-drain grants.

    All decisions are held under one RLock. The application must check `permitted`
    *immediately before speaker learning and immediately before returning a result*.
    `admit` alone is not a commit grant. STOP calls `freeze` first, so earlier
    admissions are invalidated before their later learning check.
    """

    MAX_DRAIN_WINDOWS = 4
    FROZEN_TTL_SECONDS = 90
    DRAIN_TTL_SECONDS = 120

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = threading.RLock()
        self._lease: Optional[Lease] = None
        self._epoch = 0

    def _time(self) -> float:
        return float(self._clock())

    def _expire_locked(self) -> None:
        if self._lease and self._lease.deadline is not None and self._time() >= self._lease.deadline:
            self._epoch += 1
            self._lease = None

    def _new_token(self) -> str:
        return secrets.token_urlsafe(24)

    def open_capture(self, takeover: bool = False) -> str:
        with self._lock:
            self._expire_locked()
            if self._lease is not None and not takeover:
                raise LeaseConflict("Capture exists; explicit takeover required")
            self._epoch += 1
            self._lease = Lease(self._new_token(), self._epoch, "live")
            return self._lease.capture

    def state(self) -> dict:
        """Redacted status: no tokens, file hashes, names, text or raw mic audio."""
        with self._lock:
            self._expire_locked()
            lease = self._lease
            return {"occupied": bool(lease), "mode": lease.mode if lease else "idle",
                    "queuedDrain": sum(x.state == "ready" for x in lease.windows.values()) if lease else 0,
                    "inflightDrain": sum(x.state == "processing" for x in lease.windows.values()) if lease else 0,
                    "deadlineSeconds": max(0, int(lease.deadline - self._time()))
                    if lease and lease.deadline is not None else None}

    def freeze(self, capture: str) -> dict:
        """Stop intake immediately and veto ALL old in-flight learning/results."""
        with self._lock:
            self._expire_locked()
            lease = self._lease
            if lease is None or lease.capture != capture or lease.mode != "live":
                raise LeaseConflict("Active capture is missing or stale")
            lease.mode = "frozen"
            lease.deadline = self._time() + self.FROZEN_TTL_SECONDS
            lease.active_uploads.clear()
            lease.nonces.clear()
            return {"frozen": True, "deadlineSeconds": self.FROZEN_TTL_SECONDS}

    def start_drain(self, frozen_capture: str, selected: Sequence[dict]) -> str:
        """Mint a NEW lease authorized only for hashes explicitly marked Keep.

        Drains reuse no prior live admission. A clip is resubmitted once as WAV,
        with a SHA-256 match. `forceMixed` remains a one-way veto on name learning.
        """
        if not isinstance(selected, (list, tuple)) or not (1 <= len(selected) <= self.MAX_DRAIN_WINDOWS):
            raise InvalidWindow("Select one to four buffered clips")
        allowed = {}
        for item in selected:
            if not isinstance(item, dict):
                raise InvalidWindow("Invalid window descriptor")
            name, digest = item.get("window_id"), item.get("sha256")
            if not isinstance(name, str) or not WINDOW_ID.fullmatch(name):
                raise InvalidWindow("Invalid window ID")
            if not isinstance(digest, str) or not HEX_SHA.fullmatch(digest):
                raise InvalidWindow("Invalid SHA-256 clip hash")
            if type(item.get("force_mixed")) is not bool:
                raise InvalidWindow("Mixed/edit state must be an explicit boolean")
            if name in allowed:
                raise InvalidWindow("Duplicate window ID")
            allowed[name] = ApprovedWindow(digest=digest, force_mixed=item["force_mixed"])
        with self._lock:
            self._expire_locked()
            lease = self._lease
            if not lease or lease.capture != frozen_capture or lease.mode != "frozen":
                raise LeaseConflict("Frozen capture expired or was superseded")
            self._epoch += 1
            self._lease = Lease(self._new_token(), self._epoch, "draining",
                                self._time() + self.DRAIN_TTL_SECONDS, windows=allowed)
            return self._lease.capture

    def admit(self, capture: str, window_id: str, wav_data: bytes,
              force_mixed: bool = False) -> Admission:
        if not isinstance(window_id, str) or not WINDOW_ID.fullmatch(window_id):
            raise InvalidWindow("Invalid window ID")
        if not isinstance(wav_data, bytes) or not (500 <= len(wav_data) <= 2_500_000):
            raise InvalidWindow("Invalid WAV upload size")
        if type(force_mixed) is not bool:
            raise InvalidWindow("Invalid overlap flag")
        digest = sha256(wav_data).hexdigest()
        with self._lock:
            self._expire_locked()
            lease = self._lease
            if not lease or lease.capture != capture or lease.mode not in ("live", "draining"):
                raise LeaseConflict("Capture unavailable or frozen")
            if window_id in lease.active_uploads or window_id in lease.consumed:
                raise InvalidWindow("Duplicate or already completed upload")
            if lease.mode == "draining":
                allowed = lease.windows.get(window_id)
                if not allowed or allowed.state != "ready" or digest != allowed.digest:
                    raise InvalidWindow("This exact clip was not selected for Keep or was already processed")
                if force_mixed != allowed.force_mixed:
                    raise InvalidWindow("Client edited/overlap flag disagrees with authorized clip")
                allowed.state = "processing"
                allowed.nonce = self._new_token()
                nonce = allowed.nonce
            else:
                nonce = self._new_token()
            lease.active_uploads.add(window_id)
            lease.nonces[window_id] = nonce
            return Admission(lease.capture, lease.epoch, window_id, nonce, force_mixed,
                             draining=lease.mode == "draining")

    def permitted(self, ticket: Admission) -> bool:
        with self._lock:
            self._expire_locked()
            lease = self._lease
            if not lease or not isinstance(ticket, Admission):
                return False
            if lease.capture != ticket.capture or lease.epoch != ticket.epoch or \
               (ticket.window_id not in lease.active_uploads or lease.nonces.get(ticket.window_id) != ticket.nonce) or lease.mode not in ("live", "draining"):
                return False
            if lease.mode == "draining":
                window = lease.windows.get(ticket.window_id)
                return bool(window and window.nonce == ticket.nonce and
                            window.state == "processing" and ticket.draining)
            return not ticket.draining

    def atomic_commit(self, ticket: Admission, apply=None) -> bool:
        """Perform the final in-memory speaker update atomically with STOP.

        Callbacks must be short, synchronous and must not block on STT or network.
        Errors propagate without marking the clip complete; caller should reject.
        """
        with self._lock:
            if not self.permitted(ticket):
                return False
            if apply is not None:
                apply()
            return self.complete(ticket)

    def complete(self, ticket: Admission) -> bool:
        with self._lock:
            if not self.permitted(ticket):
                return False
            lease = self._lease
            lease.active_uploads.discard(ticket.window_id)
            lease.nonces.pop(ticket.window_id, None)
            lease.consumed.add(ticket.window_id)
            if ticket.draining:
                lease.windows[ticket.window_id].state = "done"
            return True

    def reject(self, ticket: Admission) -> bool:
        """Mark a failed exact drain as dropped; it cannot be replayed silently."""
        with self._lock:
            if not self.permitted(ticket):
                return False
            lease = self._lease
            lease.active_uploads.discard(ticket.window_id)
            lease.nonces.pop(ticket.window_id, None)
            lease.consumed.add(ticket.window_id)
            if ticket.draining:
                lease.windows[ticket.window_id].state = "dropped"
            return True

    def close(self, capture: str) -> bool:
        with self._lock:
            self._expire_locked()
            if not self._lease or self._lease.capture != capture:
                return False
            self._epoch += 1
            self._lease = None
            return True

    def drop_all(self) -> None:
        with self._lock:
            self._epoch += 1
            self._lease = None
