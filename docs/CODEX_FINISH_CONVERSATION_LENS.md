# CODEX IMPLEMENTATION HANDOFF — Finish Conversation Lens

**Executor:** OpenAI Codex in the user's authorized MacBook checkout; full working-tree and browser access when available.  
**Repository:** `westkitty/Conversation_Lens`; MacBook path `/Users/andrew/Conversation_Lens`; main app `Conversation_Lens_Intelligent_Speaker_v6/`; Brave + loopback Python HTTP + Whisper.cpp + sherpa-onnx speaker worker + optional localhost Ollama.  
**Owner intent:** Personal, local-first real-time conversation observation and coaching, with the lowest practical latency and deliberate direct controls. No Docker, no cloud speech, no unnecessary enterprise/policy overlays. Preserve privacy by default and do not commit transcripts, recordings, embeddings, private notes, tokens or personal conversation examples.

## Mission

**Integrate the tested Packet A audio-window/Stop protocol into the full existing app, complete and independently verify every remaining item in the 60-feature backlog, and deliver a usable tested Brave-first release.** Treat prior `Done`/`Partial` labels as *claims requiring fresh tests*, not proof of completion. If the work exceeds one context window, checkpoint each coherent phase in an explicit state ledger, preserving regressions and continuation instructions. Never declare all 60 complete merely because the UI contains controls.

## Mandatory beginning: preserve the user's actual checkout

1. Confirm `hostname`, OS, cwd, repo remote `git@github.com:westkitty/Conversation_Lens.git`, current branch, HEAD, upstream, `git status --porcelain=v1 -uall`, `git diff --stat`, staged diff, and untracked files before any changes. Confirm the target really is the user's MacBook, not Big Mac or a scratch clone.
2. The October 18 ChatGPT implementation left **substantial uncommitted local work** in the MacBook checkout: `Conversation_Lens_Intelligent_Speaker_v6/server.py`, `Conversation_Lens_Intelligent_Speaker_v6/Conversation_Lens_Live.html`, `test_frontend.py`, plus new `test_live_upgrade.py`. This state was last seen on `main` at `a74e2b0`. Remote execution disconnected before final reconciliation. **DO NOT run `git reset`, `git clean`, forced checkout, automatic stash, `git pull --rebase` over dirty files, or replace these files with the older GitHub main version.** Distinguish owner work from prior ChatGPT changes; preserve both.
3. Obtain a reversible, **local-only** diff and untracked-file inventory checkpoint without storing sensitive conversation content in public GitHub. Verify the snapshot before any risky merge. Inspect repo instructions/project Bible/operational state; add to the established ledger, not overwrite it.
4. GitHub branch `feat/conversation-lens-packet-a-handoff` contains **isolated, tested** code under `experiments/packet-a/` plus these documents. Fetch the branch without changing the checkout; inspect the remote tree. Integrate selectively, preserving local changes. In an alternate handoff without remote access, ask the owner for `Conversation_Lens_Packet_A_Connected_Stop_v1.zip` in Downloads. Do not assume a ChatGPT sandbox path is accessible in Codex.
5. Establish actual device/browser/service/model capabilities. Where something is unavailable, record `BLOCKED`/`NOT TESTED` and continue independent work. Do not fabricate test passes, Git status, pushed commits, natural-speaker accuracy, or installed models.

## Verified handoff facts, with limits

- Previous ChatGPT v6 local changes added pinned right-rail coaching, layout modes, keyboard shortcuts, speaker corrections/evidence drawer with full/half cosine and margin, speaker boost, configurable coaching/grounding, in-memory queues, RMS cut visualization and diagnostics. Reports said existing Python/Playwright/real-model synthetic tests passed **before** the DEX//REACH connection failed; the final local diff was NOT verified or pushed. Re-test rather than trusting reports.
- Independently runnable Packet A is an **experimental component, not a drop-in app replacement**. Its `lens_pcm_core.js`, `lens_pcm_capture.js`, `lens_stop_client.js`, `lens_stop_drain.py`, `lens_packet_a_transport.js`, `packet_a_server.py`, `packet_a_lab.html` and tests implement 16 kHz PCM bounded ring, sample-accurate split/merge/boundary/roll controls, canonical WAV, per-clip SHA-256, selective Stop freeze/drain authorization, one-use lease, stale prevention, Drop All, 429 retry, and honest validation-only results when Whisper is missing. A 45-second memory ring, 10-second max WAV, max four kept clips, 90 s freeze lease and 120 s drain lease are the *Packet A prototype limits*, not immutable production choices.
- Packet A isolated QA previously: **29 Node tests, 12 Python tests, 6 Chromium checks passed** (browser checked through a test bridge to actual localhost server; real Mac microphone path still unverified). The current session separately re-ran 29 Node plus 12 Python tests and they passed; Chromium not rerun this session.
- `packet_a_server.py` **must not replace** v6 `server.py`; it does not implement speaker enrollment, transcript storage rules, all capture leases, existing coaching logic or full UI. Preserve original v6 tab lease, revocation, transcript and speaker fallback paths. Feature-gate any PCM transport migration until MacBook acceptance tests prove it.
- This GitHub repository was reported **public**. Read actual visibility and never push any user speech, session data, secret, embedding or relationship case notes to it. The desired **app** is private/local-first irrespective of repository visibility.

## Atomic 60-feature contract

The table below is the user's original upgrade inventory with **prior claimed status, not guaranteed current status**. Build/repair every row; for each keep a requirement ID, actual code location, independent reproducible check, and final observed PASS/PARTIAL/BLOCKED status. `Partial` means crucial behavior still missing, not permission to defer it.

| # | Requested feature | Prior reported status | Missing/verification note |
|---:|---|---|---|
| 1 | Persistent pinned coaching rail | Done | Desktop sticky rail and latest cue |
| 2 | Energy/silence graph; drag split/merge | Partial | RMS/cut times shown; drag split/merge requires PCM editing |
| 3 | In-place speaker reassignment | Done | Manual relabel and coaching refresh |
| 4 | Grounded evidence drawer | Done | Highlight, full/half cosine and margin |
| 5 | Keyboard controls | Done | Space, E, C, N/P, 1–9, M |
| 6 | Layout modes with memory | Done | Four modes stored in local layout preference |
| 7 | Skipped-window reasons and reprocess | Done | Buffered recent skips under active lease only |
| 8 | Flick-up mobile coaching sheet | Partial | Expand/collapse button works; gesture not added |
| 9 | Per-window Stop keep/drop dialog | Planned | Current Stop revokes and drops |
| 10 | Speaker chips, last-seen, boost | Done | Two-minute score-threshold boost, no forced name learning |
| 11 | Sticky optional context | Partial | Note updates next AI call, not visually sticky |
| 12 | Custom prompt fragment presets | Done | Preset or editable fragment |
| 13 | Transcript filters | Done | Speaker, keyword, coaching-attached |
| 14 | Reduced motion/contrast/mono | Done | Remembered settings |
| 15 | Precise empty coaching ingredients | Done | Transcript, samples, Ollama availability |
| 16 | Sliding plus priority AI context | Done | Recent + limited signal-heavy older turns |
| 17 | Exact/Fuzzy/Free grounding dial | Done | Controls prompt and evidence status |
| 18 | Offline linguistic cards | Partial | Existing questions/repeats/commitments, not full interruption and topic-shift classification |
| 19 | In-place copyable next-step cards | Partial | Editable/copyable current line, not each historical card |
| 20 | Mid-session coaching presets | Done | Model requests use current selection |
| 21 | Full/half speaker confidence strip | Partial | Numeric panels; strip graphic missing |
| 22 | Speaker lock N windows/unpin | Planned | Manual per-passage override exists |
| 23 | One-click Markdown/plain exports | Done | Browser downloads |
| 24 | Bookmarks/highlights in export | Done | Per-passage markers |
| 25 | Coaching pause, hot ASR | Done | Existing behavior retained |
| 26 | Smart debounce/manual immediate cue | Done | Automatic ~5.5 s, immediate manual attempt |
| 27 | Coaching timeline and per-card regenerate | Partial | Source-linked history; regenerate current cue only |
| 28 | Grounding badge/retry looser | Done | Exact/approximate/ungrounded/rejected |
| 29 | Private note/goal for next AI call | Done | Separate from transcript |
| 30 | Live VAD tunables and preview | Done | RMS, silence, min voiced, hard cap |
| 31 | Adaptive noise floor | Done | Original running estimate retained |
| 32 | Half-window overlap heat | Partial | Divergence and Mixed flag, no heat visualization |
| 33 | Enrollment quality meter | Partial | Acoustic rejection present, pre-activation gauge missing |
| 34 | Instant speaker drop | Partial | Individual removal still has confirmation |
| 35 | Longer follow-up enrollment sample | Partial | Guidance text, no separate guided flow |
| 36 | Raw cosine/margin available | Done | Evidence drawer |
| 37 | Soft cap/merge suggestion | Partial | Existing eight-profile hard cap only |
| 38 | Window-length distribution | Partial | Rolling median/range, no histogram |
| 39 | Whisper model switcher | Planned | Requires verified model inventory and reload |
| 40 | Adjustable pre-roll/post-roll | Planned | Requires bounded PCM ring |
| 41 | Overlap Mixed + no name learning | Done | Enforced before introduction learning |
| 42 | Speaker embedding RAM/compact | Partial | RAM estimate exposed; compact action absent |
| 43 | Structured performance and lease logs | Partial | Audio+AI timings exist, per-stage/lease details incomplete |
| 44 | Health endpoint and UI status | Done | `/api/health` and local UI diagnostic health indicator |
| 45 | Fallback when speaker worker times out | Done | Transcript retained, voice unknown |
| 46 | Live Ollama endpoint/model/timeout/temp | Done | Localhost-only setting and model check |
| 47 | Capture lease rotation and stale notice | Done | Fresh lease per Start; stale server results dropped |
| 48 | Queue dashboard and pause intake | Partial | Queue/status/skip buffers, no full worker graph |
| 49 | Explicit disk speaker-profile save/load | Planned | Default remains in-memory |
| 50 | Rate limit and backpressure | Done | STT lock/429 and bounded retries |
| 51 | Finish/drop in-flight shutdown | Partial | Drop/revoke exists; finish chosen windows absent |
| 52 | Versioned server-client messages | Partial | Version field advertised; no negotiation enforced |
| 53 | Recent-window replay/debug | Partial | Buffered skipped audio can reprocess; processed clips discarded |
| 54 | Snapshot/restore | Planned | Full session restore unavailable |
| 55 | Multi-tab lease visibility/transfer | Partial | Explicit takeover exists; owner/age display absent |
| 56 | Custom local cue rules | Planned | Existing built-in rules only |
| 57 | Running action-item/decision extraction | Partial | Local detection, no durable in-session list |
| 58 | Hotkey voice-note annotation | Planned | Private typed note exists |
| 59 | Speaker comparison/talk-time stats | Planned | No time accounting grounded to acoustic segments |
| 60 | Continue last coaching thought | Planned | Requires thread-aware follow-up AI call |

## Execution phases and dependency gates

**Phase 0 — recovery and baseline.** Establish source of truth, preserve dirty Mac checkout, inspect README, launch script, `server.py`, HTML, `speaker_worker.py`, all existing tests, Packet A tests and project state. Run `python3 test_backend.py`, `python3 test_regressions.py`, `python3 test_live_upgrade.py`, `python3 test_frontend.py`, `python3 test_e2e.py`, and `python3 test_real_local_stack.py` where dependencies/runtime allow. Record baseline failures as baseline. Do not build a parallel replacement app.

**Phase 1 — audio and Stop correctness (IDs 2, 7, 9, 30, 31, 38, 40, 43, 47, 48, 50, 51, 52, 53).** Embed Packet A PCM capture behind toggle, with MediaRecorder fallback during rollout. Integrate with existing transcription/speaker/cue queues and session-token/tab leases. Enforce exact monotonic sample boundaries, no gaps/duplicates in merge/split, crop pre/post-roll without violating ring capacity, real playback and visual cut points, bounded memory, max duration, deterministic speaker-learning veto for edited/mixed audio. Stop must freeze intake, show pending/in-flight windows, Keep/Drop per clip, finish only authorized clips with transactional retry and revocation, and never call stale cues authoritative. Confirm preserving all selected clips on 429 and network timeout, and no successful ghost transcripts in validation-only mode. Implement explicit message version negotiation and fail-closed handling of mismatches. Tests for high activity, silence, restarts, changed sample rates, revoke races and wrong-tab takeover.

**Phase 2 — speaker and model controls (IDs 3, 4, 10, 21, 22, 32–37, 39, 41–42, 45, 49, 55, 59).** Distinguish human manual labels/lock pins from learned embeddings; lock to N windows or unpin without training from mixed voices. Show true full/half cosine and margin as measurements (not calibrated probabilities), overlap heat and veto, quality gauge before named enrollment, longer optional intro recording, last-seen/boost/RAM metrics, remove and merge suggestions, real compact action. Gate live Whisper model switching on an inventory of actually installed models and voice-worker warm-up/rollback. Profile save/load is **opt-in** only; in-memory by default. Speaker talk time counts only actual eligible voice spans, accounts for Mixed/overlap/unknown and explains denominator. Preserve v6 fallback when worker errors.

**Phase 3 — UI and coaching (IDs 1, 5, 6, 8, 11–20, 23–29, 56–58, 60).** Preserve pinned desktop rail, mobile swipeable sheet, persistent layout/preferences, searchable transcript, keyboard shortcuts without hijacking typing, per-segment overrides and cue source navigation. Ensure focus-visible, touch/drag/click/keyboard parity, reduced motion, high contrast, one-tap export with markers. Priority context stays visible and flows into on-demand local Ollama. Grounding Exact/Fuzzy/Free controls how text can be cited; exact cannot fabricate quotations. Do not claim generated AI advice is transcript evidence. Implement offline interruption/repetition/topic-shift/commitment detection with clear uncertain states; add deduplicated source-linked action and decision ledger, editable per-card suggestions, per-card regeneration, Continue Thought without copying stale cues, bounded local regex/keyword rules with safe execution and priority, voice-note annotation as non-transcript stream.

**Phase 4 — integrity and recovery (IDs 43, 44, 46–55).** Per-stage ASR/embedding/Ollama timings and queue dashboard, lease age/owner and explicit transfer, pressure/backoff/skip reasons, high-water memory visibility, bounded debug replay, health and model probes. Explicit snapshot/restore of sessions only with owner's action: schema version, SHA-256, atomic writing, restoration of speaker labels/turns/bookmarks/coach thread, missing-data disclosures, corrupt/mismatched/older schema tests. Audio and voice vectors are **not** silently persisted. Dedicated opt-in profile export/import is versioned and integrity-checked. Avoid remote/cloud services.

**Phase 5 — acceptance and release.** Run focused tests after each group, cross-cutting backend+frontend+E2E after integration, real Brave microphone tests on MacBook (start/stop/permission denial/device unplug/restart/multi-tab), natural conversation with two clearly different voices and an overlapping/mixed segment, skip+retry, latency comparison to baseline and 45+ minute memory/queue trial when practical. Test desktop and ~375px mobile layout. Watch input-to-visible-cue latency, recognition turnaround, missed/doubled speech and worker starvation. Do not promise any recognition guarantee: report measured confusion, latency and environment. Include a repeatable QA script and final matrix for all 60 rows. Only call a row Done when an observable test passes.

## Preservation and constraints

- Absolutely preserve user-created files, local uncommitted work, baseline app launcher, existing authoring and transcript behaviors. Do not replace server.py with the prototype server or discard previously working code to make tests pass.
- Keep capture on `127.0.0.1`; only local optional Ollama, no Docker or new network telemetry. Keep deterministic local linguistic coaching when Ollama is absent. Prefer no dependency changes. No always-on data retention; memory bounded; user's exports/snapshots explicit. Session Stop/Erase/Tabs must revoke stale writes and late messages.
- No invented diagnostic statuses or fake working controls. Track unimplemented dependencies, disabled states and errors directly in the interface.
- Treat individual words like “Dale” as a possible name only when voice enrollment and score thresholds justify it. No name-learning from mixed or short/poor-quality audio. User manually selecting a name must not silently reinforce a voice print.
- Do not include private relationship/chat content in tests, logs, fixture transcripts, commits, markdown or screenshots. Use synthetic names and data only. GitHub is currently public unless live-verified otherwise.
- Git mutations: the user requested stage, commit and push. On the MacBook, first distinguish the preserved pre-existing edits from this implementation and audit the diff. You may create cohesive ordinary commits and push non-destructively to the correct authorized repo and branch once tests and secret checks pass. **No force, no rebase/clean/reset, no destructive operation or unrelated file staging.** If the working tree/remote diverges, resolve non-destructively and do not publish mixed unverified changes; report the exact hold instead.

## Validation and stopping rules

Use tests as proof, not checkboxes. After each phase: inspect the actual code and changed-file diff; test success/error/race/mobile cases; repair introduced regressions before proceeding. Extend tests only for concrete behavior, not for a static text assertion that a control name exists. Test clean restart and stale captures. Keep total resources appropriate for an M1/8 GB MacBook; never assume Big Mac is powered or accessible. Preferred sequencing: one bounded implementation + one bounded repair pass per phase, then document blockers and continue safe independent phases rather than infinite retries.

Never declare completion without a 60-row matrix linked to test evidence and no unresolved mandatory failures. If a phase cannot be finished due to actual hardware/models/permissions, mark affected rows BLOCKED and provide the exact Mac terminal validation command and smallest required action; do not overclaim.

## Deliverables and completion report

1. Integrated, production-usable Conversation Lens in original repo; no duplicate replacement product.
2. Source changes plus purposeful regression, integration, user-journey, real-mic and latency tests; actually runnable and evidence-backed.
3. Updated owner-facing README/launcher instructions, operational-state/project Bible appended; track changed architecture and fallback/rollback.
4. A **60/60 evidence matrix**: ID, implementation path, test/check, PASS/PARTIAL/BLOCKED, honest open issues.
5. `git status`, branch, commits, remote push verification (when successful); otherwise exact uncommitted/unpushed state and blocker.
6. Concise final explanation: what changed, what passed, how to launch in Brave, which items remain, no unsupported certainty.

Begin with the actual Mac working tree. Protect existing uncommitted work before merging Packet A. Do not ask for information that the repository and attached handoff already provide.
