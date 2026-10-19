#!/usr/bin/env python3
"""Long local-stack memory/queue soak for the Conversation Lens Mac app.

Uses synthetic macOS speech and the production server Handler, Whisper model,
speaker worker and capture lease. No microphone is opened and transcript/audio
content is never written to the report. All generated media lives in a temporary
directory. Default duration is 45 minutes; use --duration-seconds for a shorter
smoke. The JSONL report contains only timing, counts, memory and queue metadata.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave
from http.server import ThreadingHTTPServer


ROOT = pathlib.Path(__file__).parent / "Conversation_Lens_Intelligent_Speaker_v6"
SPEC = importlib.util.spec_from_file_location("lens_soak_server", ROOT / "server.py")
SERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVER)
SYNTHETIC_WORDS = (
    "This is a local Conversation Lens resource check. The current sample is "
    "generated speech for checking recognition turnaround and bounded session memory."
)


def request(url: str, body: bytes = None, headers: dict = None,
            timeout: float = 65) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=body, headers=headers or {},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {"error": "HTTP error without JSON body"}
        return error.code, payload


def process_tree_rss_kib(root_pid: int) -> int:
    """Sum RSS for this harness/server and its active subprocess descendants."""
    output = subprocess.check_output(
        ["/bin/ps", "-axo", "pid=,ppid=,rss="], text=True, timeout=5
    )
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        pid, ppid, size = map(int, parts)
        children.setdefault(ppid, []).append(pid)
        rss[pid] = size
    pending = [root_pid]
    seen: set[int] = set()
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        pending.extend(children.get(pid, ()))
    return sum(rss.get(pid, 0) for pid in seen)


def make_media(directory: pathlib.Path) -> bytes:
    aiff = directory / "synthetic.aiff"
    webm = directory / "synthetic.webm"
    subprocess.run(
        ["/usr/bin/say", "-v", "Alex", "-r", "178", SYNTHETIC_WORDS,
         "-o", str(aiff)], check=True, timeout=25,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [str(SERVER.FFMPEG_BIN), "-nostdin", "-loglevel", "error", "-y",
         "-i", str(aiff), "-t", "9", "-c:a", "libopus", "-b:a", "32k",
         str(webm)], check=True, timeout=25,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    payload = webm.read_bytes()
    if len(payload) < 500:
        raise RuntimeError("Generated test audio is below the production upload minimum")
    return payload


def transcribe(base: str, headers: dict, capture: str, payload: bytes,
               window_id: str) -> tuple[int, float, str]:
    started = time.monotonic()
    code, body = request(
        base + "/api/transcribe", payload,
        {**headers, "Content-Type": "audio/webm",
         "X-Lens-Capture-Session": capture,
         "X-Lens-Window-ID": window_id,
         "X-Lens-Language": "en"},
    )
    elapsed = time.monotonic() - started
    if code == 200:
        if body.get("engine") != "whisper-cpp" or len(body.get("text", "")) < 18:
            raise RuntimeError("Local ASR returned no usable synthetic speech passage")
        if body.get("discarded"):
            raise RuntimeError("A live-window result was unexpectedly discarded")
    elif code != 429:
        raise RuntimeError("Local transcription HTTP %d: %s" % (code, body.get("error", "unknown error")))
    return code, elapsed, body.get("error", "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-seconds", type=int, default=45 * 60)
    parser.add_argument("--transcribe-interval-seconds", type=int, default=60)
    parser.add_argument("--sample-interval-seconds", type=int, default=10)
    parser.add_argument("--report", type=pathlib.Path,
                        default=pathlib.Path(tempfile.gettempdir()) /
                        ("conversation-lens-soak-%d.jsonl" % int(time.time())))
    parser.add_argument("--burst-every", type=int, default=5,
                        help="Every Nth cycle tests concurrent 429 retention and retry; 0 disables bursts")
    args = parser.parse_args()
    if min(args.duration_seconds, args.transcribe_interval_seconds,
           args.sample_interval_seconds) < 1:
        parser.error("durations and intervals must be positive")
    if args.burst_every < 0:
        parser.error("--burst-every cannot be negative")
    return args


def main() -> int:
    args = parse_args()
    if sys.platform != "darwin":
        print("BLOCKED: this resource soak is scoped to the MacBook macOS runtime")
        return 2
    if not SERVER.whisper_status().get("ready") or not SERVER.speaker_status().get("ready"):
        print("BLOCKED: local Whisper and speaker models must both be ready")
        return 2

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lens-resource-soak-") as temp:
        payload = make_media(pathlib.Path(temp))
        app = ThreadingHTTPServer(("127.0.0.1", 0), SERVER.Handler)
        app.daemon_threads = True
        threading.Thread(target=app.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:%d" % app.server_address[1]
        capture = None
        sample_rows: list[dict] = []
        latencies: list[float] = []
        rss_samples: list[tuple[float, int]] = []
        report_lock = threading.Lock()
        transcribe_ok = 0
        rate_limited = 0
        retry_ok = 0
        window_counter = 0
        report = open(args.report, "x", encoding="utf-8")
        try:
            _, status = request(base + "/api/status")
            if not status.get("stt", {}).get("ready") or not status.get("speakers", {}).get("ready"):
                raise RuntimeError("Production status does not report local models ready")
            headers = {"X-Lens-Token": status["token"], "Origin": base,
                       "X-Lens-Protocol": str(SERVER.PROTOCOL_VERSION),
                       "Content-Type": "application/json"}
            code, opened = request(base + "/api/capture/open", b'{"consent":true}', headers)
            if code != 200 or not opened.get("capture"):
                raise RuntimeError("Could not acquire an isolated production capture lease")
            capture = opened["capture"]

            # Warm the same production route before starting the measured interval.
            window_counter += 1
            code, elapsed, _ = transcribe(base, headers, capture, payload,
                                           "soak_%06d" % window_counter)
            if code != 200:
                raise RuntimeError("The warm-up request was unexpectedly rate limited")
            transcribe_ok += 1
            latencies.append(elapsed)
            start = time.monotonic()
            next_sample = start
            next_transcribe = start
            deadline = start + args.duration_seconds
            monitor_stop = threading.Event()

            def monitor_rss() -> None:
                while not monitor_stop.is_set():
                    elapsed = time.monotonic() - start
                    rss = process_tree_rss_kib(os.getpid())
                    rss_samples.append((elapsed, rss))
                    row = {"type": "rss_sample", "elapsedSeconds": round(elapsed, 3),
                           "aggregateRssKiB": rss}
                    with report_lock:
                        report.write(json.dumps(row, separators=(",", ":")) + "\n")
                        report.flush()
                    monitor_stop.wait(1.0)

            monitor = threading.Thread(target=monitor_rss, daemon=True)
            monitor.start()
            print("SOAK_STARTED duration_seconds=%d interval_seconds=%d report=%s" %
                  (args.duration_seconds, args.transcribe_interval_seconds, args.report),
                  flush=True)

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as burst_pool:
                while time.monotonic() < deadline:
                    now = time.monotonic()
                    if now >= next_transcribe:
                        window_counter += 1
                        if args.burst_every and window_counter % args.burst_every == 0:
                            ids = ["soak_%06d" % window_counter,
                                   "soak_%06d_retry" % window_counter]
                            futures = {burst_pool.submit(transcribe, base, headers, capture,
                                                         payload, window_id): window_id
                                       for window_id in ids}
                            for future in concurrent.futures.as_completed(futures):
                                code, elapsed, _ = future.result()
                                latencies.append(elapsed)
                                if code == 200:
                                    transcribe_ok += 1
                                else:
                                    rate_limited += 1
                                    time.sleep(2)
                                    retry_code, retry_elapsed, _ = transcribe(
                                        base, headers, capture, payload, futures[future])
                                    latencies.append(retry_elapsed)
                                    if retry_code != 200:
                                        raise RuntimeError("Rate-limited clip did not succeed on retry")
                                    retry_ok += 1
                                    transcribe_ok += 1
                        else:
                            code, elapsed, _ = transcribe(
                                base, headers, capture, payload,
                                "soak_%06d" % window_counter)
                            latencies.append(elapsed)
                            if code == 429:
                                rate_limited += 1
                                time.sleep(2)
                                retry_code, retry_elapsed, _ = transcribe(
                                    base, headers, capture, payload,
                                    "soak_%06d_retry" % window_counter)
                                latencies.append(retry_elapsed)
                                if retry_code != 200:
                                    raise RuntimeError("Rate-limited clip did not succeed on retry")
                                retry_ok += 1
                            transcribe_ok += 1
                        now = time.monotonic()
                        next_transcribe = now + args.transcribe_interval_seconds

                    if now >= next_sample:
                        code, health = request(base + "/api/health")
                        _, diagnostics = request(base + "/api/diagnostics")
                        if code != 200 or health.get("ok") is not True:
                            raise RuntimeError("Health check failed during soak")
                        events = diagnostics.get("events", [])
                        drain = health.get("captureDrain", {})
                        if len(events) > 120:
                            raise RuntimeError("Diagnostic event ring exceeded its 120-entry cap")
                        if int(drain.get("queuedDrain", 0)) > 4:
                            raise RuntimeError("Drain queue exceeded four-window bound")
                        row = {
                            "elapsedSeconds": round(now - start, 3),
                            "aggregateRssKiB": process_tree_rss_kib(os.getpid()),
                            "healthOk": True,
                            "captureActive": health.get("captureActive"),
                            "sttBusy": health.get("sttBusy"),
                            "queuedDrain": drain.get("queuedDrain", 0),
                            "inflightDrain": drain.get("inflightDrain", 0),
                            "diagnosticEvents": len(events),
                            "transcribeOk": transcribe_ok,
                            "rateLimited": rate_limited,
                            "retryOk": retry_ok,
                        }
                        with report_lock:
                            report.write(json.dumps(row, separators=(",", ":")) + "\n")
                            report.flush()
                        sample_rows.append(row)
                        print("SOAK_SAMPLE " + json.dumps(row, separators=(",", ":")), flush=True)
                        next_sample = now + args.sample_interval_seconds

                    sleep_until = min(deadline, next_sample, next_transcribe)
                    time.sleep(max(0.1, min(1.0, sleep_until - time.monotonic())))

            monitor_stop.set()
            monitor.join(timeout=3)
            _, closed = request(base + "/api/capture/close",
                                json.dumps({"capture": capture}).encode(), headers)
            capture = None
            if closed.get("closed") is not True:
                raise RuntimeError("Capture lease did not close cleanly")
            _, erased = request(base + "/api/session/erase", b'{"confirm":true}', headers)
            if erased.get("erased") is not True or SERVER.SPEAKERS or SERVER.SPEAKER_META:
                raise RuntimeError("Test-only session state did not erase cleanly")
            rss = [value for _, value in rss_samples]
            summary = {
                "result": "PASS",
                "durationSeconds": round(time.monotonic() - start, 3),
                "samples": len(sample_rows),
                "transcribeSuccessesIncludingWarmup": transcribe_ok,
                "rateLimited": rate_limited,
                "successfulRetries": retry_ok,
                "aggregateRssKiBFirst": rss_samples[0][1] if rss_samples else None,
                "aggregateRssKiBLast": rss_samples[-1][1] if rss_samples else None,
                "aggregateRssKiBPeak": max(rss) if rss else None,
                "aggregateRssSamples": len(rss_samples),
                "latencySecondsMin": round(min(latencies), 3),
                "latencySecondsMedian": round(sorted(latencies)[len(latencies) // 2], 3),
                "latencySecondsMax": round(max(latencies), 3),
                "report": str(args.report),
                "syntheticContentSaved": False,
            }
            report.write(json.dumps({"summary": summary}, separators=(",", ":")) + "\n")
            report.flush()
            print("SOAK_SUMMARY " + json.dumps(summary, separators=(",", ":")), flush=True)
            return 0
        finally:
            if capture:
                request(base + "/api/session/erase", b'{"confirm":true}',
                        {"X-Lens-Token": status["token"], "Origin": base,
                         "X-Lens-Protocol": str(SERVER.PROTOCOL_VERSION),
                         "Content-Type": "application/json"})
            if 'monitor_stop' in locals():
                monitor_stop.set()
                if 'monitor' in locals():
                    monitor.join(timeout=3)
            report.close()
            app.shutdown()
            app.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
