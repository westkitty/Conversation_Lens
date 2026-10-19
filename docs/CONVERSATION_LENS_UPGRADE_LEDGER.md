# Conversation Lens — Live-loop upgrade and remaining implementation plan

**Project:** `westkitty/Conversation_Lens`  
**Working checkout:** `/Users/andrew/Conversation_Lens`  
**Base revision:** `a74e2b0` on `main`, initially clean  
**Date:** October 18, 2026  
**Git state:** Changes applied locally only; no commit or push requested or performed.

## Implemented in the local checkout

The v6 Brave interface now includes a sticky desktop coaching rail and collapsible bottom coaching sheet for narrow screens; editable next-line suggestions; an explicit urgent cue action; persistent Split, Transcript-heavy, Coaching-heavy and Focus layout modes; contrast, reduced-motion and mono toggles; keyboard commands; transcript search and speaker filters; bookmarks and highlights; Markdown exports; local coaching history; and source navigation.

Speaker labels can be changed in any passage. An evidence drawer exposes the exact transcript text and the top cosine score and score margin from full-, first-half and second-half embedding windows. A divergent half-window forces **Mixed** and blocks automatic name learning. Speaker profile chips show sample counts, approximate last-seen time, estimated vector RAM and an optional two-minute threshold boost, still subject to overlap and margin vetoes. None of these scores are calibrated probabilities of identity.

The microphone loop now has an RMS energy graph with the actual measured threshold and meter-resolution cut markers, plus editable silence threshold, minimum speech and maximum recording duration. Completed clip lengths have a rolling median and range. A bounded queue exposes skipped-window reasons and retains at most four skipped clips for reprocessing while the original capture lease remains active. A Pause Intake control, visible stale-result message, bounded retry on temporary worker backpressure and Stop buffer invalidation have been added.

Local AI settings now include localhost Ollama URL/model/timeout/temperature, custom prompt presets, an owner-private note, Exact/Fuzzy/Free grounding, a source-evidence badge and a 'retry looser' action. Recent and high-priority older transcript passages are selected. AI calls remain explicitly optional; local linguistic cues continue when Ollama is off. A lightweight protocol version, health endpoint and bounded timing diagnostics are available.

## Sixty-item backlog coverage

`Done` means the requested basic behavior is implemented; `Partial` identifies an important unmet detail; `Planned` means not implemented. New or modified behavior was tested with simulated Brave/HTTP tests and backend fixtures. Natural multi-speaker microphone accuracy remains unverified.

| # | Requested feature | State | Unfinished detail, where relevant |
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

## Next implementation packets

**A. Editable audio plus explicit Stop disposition.** Add a bounded, timestamped PCM ring and WAV encoding path so the owner can split/merge buffered audio at real sample boundaries and preview pre/post-roll. Merge only contiguous clips within the server length limit. Freeze microphone intake at Stop; present a list of queued/in-flight windows with Keep/Drop and a narrowly scoped, server-authorized draining lease. Test timestamp continuity, absence of lost/doubled samples, memory ceilings, mixed audio and revoke races. Do not concatenate arbitrary compressed WebM chunks and pretend they are independently editable PCM.

**B. Speaker control.** Add a lock for N windows or until unpin, distinct from voice enrollment (manual locks never create or reinforce voice embeddings). Add pre-enrollment quality, a soft-cap merge assistant, normalized evidence strip, overlap heat and optional longer sample flow. Put microphone/Whisper model switching behind model-inventory, warm-up, resource and rollback tests. Do not replace DexDictate's current model.

**C. Durable session and operational telemetry.** Make owner-invoked session snapshots versioned and checksum-verified; include turns, annotations, coaching history and private notes. Gate speaker-profile export/import separately with explicit opt-in; normal sessions remain RAM-only. Add lease owner/age display, robust retry/deadline states, detailed per-stage timing, actual memory-compaction behavior and version-negotiation checks.

**D. Local intelligence.** Add bounded regex/keyword rules, deduplicated source-linked decisions/actions, editable per-card next steps and a Continue Thought mode. Build talk-time comparisons only once acoustic boundaries and overlap accounting are trustworthy. Make voice notes a separate non-transcript annotation stream.

## Verification state

Completed on the real MacBook checkout before the remote connection was lost:

- `python3 test_backend.py` — PASS
- `python3 test_regressions.py` — PASS
- `python3 test_live_upgrade.py` — PASS (speaker score/margin, Mixed guard, boost, Ollama settings, grounding, priority context, health/log ring)
- Playwright `test_frontend.py` — PASS at 1200px and 375px, including new UI controls, source drawer, keyboard, clipboard/export, boost, model checks and diagnostics
- Playwright `test_e2e.py` — PASS at 1200px and 375px (run before the last bounded speaker-boost adjustment)
- `python3 test_real_local_stack.py` — PASS with synthetic local speech: one 2.62 s Whisper/speaker processing sample and one 4.73 s Ollama response (run before the last bounded speaker-boost adjustment)
- `git diff --check` — PASS on an earlier change set, **not rerun after the last modifications due to the remote connection loss**

**Not verified:** Live Brave physical microphone with actual natural conversation and multiple speakers, matched before/after latency, long-session pressure, complete Stop-window disposition, arbitrary audio splitting or saved/restored profiles. A single synthetic smoke is not a statistically meaningful speed benchmark.

## Local launch and next full regression

```bash
cd "$HOME/Conversation_Lens" && /bin/zsh ./Conversation_Lens_Intelligent_Speaker_v6/Launch_Conversation_Lens.command
```

The live server must be restarted if it was already running before the source changes; an already running Python process does not reload its backend automatically. To run the full test sequence once the Mac connection is restored:

```bash
cd "$HOME/Conversation_Lens" && python3 test_backend.py && python3 test_regressions.py && python3 test_live_upgrade.py && "$HOME/Library/Application Support/ConversationLensQA/venv/bin/python" test_frontend.py && "$HOME/Library/Application Support/ConversationLensQA/venv/bin/python" test_e2e.py && python3 test_real_local_stack.py && git diff --check && git status --short
```

**State:** Source and tests were modified in the MacBook's checkout; no Git commit or push. This design/backlog packet is a separate downloadable file, not verified to exist in the MacBook checkout.

## Additive execution checkpoint — October 18, 2026

### Recovery and source state

- Verified target: `MacBook-Air.local`, macOS 26.6.2, checkout `/Users/andrew/Conversation_Lens`, remote `git@github.com:westkitty/Conversation_Lens.git`.
- Started at `main` / `a74e2b0ca9edbdd6c9e8f9591d0367d5048002bd`, upstream `origin/main`; the pre-existing modified `server.py`, live HTML, `test_frontend.py`, and untracked `test_live_upgrade.py` were preserved.
- Recovery copies and patch, SHA-256 verified before integration: `/Users/andrew/Conversation_Lens_recovery_20261018/` (`working-tree.patch`, `files/`, `BASELINE.txt`, `SHA256SUMS`).
- Fetched and inspected `origin/feat/conversation-lens-packet-a-handoff` at `46727fe93b4575eb66b110fd13d35e2b388dd51b`. It is a child of the verified base and adds only `docs/` plus the isolated `experiments/packet-a/` prototype and tests. Cherry-picked without conflict as `dc4b52c` onto `codex/conversation-lens-integration`; no rebase/reset/stash was used.
- GitHub API readback reports this repository is public. Keep all future fixtures synthetic and exclude private transcript/session/voice data.

### Implemented in this checkpoint

- Added `Conversation_Lens_Intelligent_Speaker_v6/lens_stop_drain.py`, the tested in-memory lease coordinator, while retaining the existing v6 server, transcription route, capture token, speaker flow, and MediaRecorder fallback.
- Added freeze and selected-drain routes to v6. Freeze revokes old admissions; drain requires the original frozen lease and exact selected clip hashes; each upload is one-use. Forced-mixed requests bypass speaker embedding/learning and are labeled `Mixed`.
- Updated production Stop to freeze first, stop the current recorder, collect up to four queued/in-flight/finalized windows, ask Keep/Drop for each, send only kept bytes through the exact-hash drain lease, then close it. Failed freeze fails closed and drops local pending audio. A failed drain remains visibly incomplete; retry after an ambiguous network timeout is still a gap.
- Bumped the capture protocol to version 3. The UI requires a matching server version, and protected capture/transcribe requests reject mismatches with HTTP 426.
- Updated README privacy wording after live GitHub visibility readback and documented the current Stop behavior and remaining PCM editor gap.

### Evidence observed in this checkpoint

- Before integration, `test_backend.py`, `test_regressions.py`, and `test_live_upgrade.py` passed. The browser tests initially could not import Playwright with system Python; the configured `ConversationLensQA` virtual environment already had Playwright. Its Chromium runtime was installed in the user cache, not in the repository.
- After integration, `test_backend.py`, `test_regressions.py`, and `test_live_upgrade.py` passed, including stale-stop revocation, protocol mismatch rejection, exact hash rejection, one-use drain, and mixed-learning veto.
- Updated `test_frontend.py` passed at 1200px and 375px in Playwright Chromium, including Stop and recorder finalization. This is simulated microphone evidence, not physical-device acceptance.
- `test_e2e.py` passed at 1200px and 375px using generated speech through the actual localhost/FFmpeg/Whisper/speaker HTTP path. It is not natural multi-speaker or microphone evidence.
- `test_real_local_stack.py` passed with generated speech: Whisper recognized the synthetic 144-character sample in 3.55s; optional local Ollama returned grounded output in 3.02s; test-only voice profiles were erased. These timings are one run and not a comparative latency benchmark.
- Packet A Node suite: 29/29 passed. Packet A Python coordinator/server suite: 12/12 passed. Browser Packet A tests must be rerun with the configured QA Python; running discovery under system Python 3.9 failed collection because Playwright is absent there.

### Current phase status and remaining gates

- Phase 0 recovery: PASS for target identity, dirty-work preservation, recovery copy verification, branch inspection, and base verification.
- Phase 1: PARTIAL. Production Stop freeze/Keep/Drop and versioned admission are integrated. Production app still records WebM via MediaRecorder; Packet A AudioWorklet PCM capture, sample-boundary editing, split/merge, WAV pre/post-roll, bounded replay of already processed PCM, timeout-safe transactional retry, and PCM Stop drain are not yet integrated.
- Phase 2–4: not closed. Existing local work covers many controls, but the complete 60-row acceptance matrix still needs current code/test mapping and identified gaps need implementation or explicit blocked evidence.
- Phase 5: NOT COMPLETE. No physical Brave microphone permission/device interruption/restart test, natural two-speaker or overlap acceptance, 45-minute resource trial, M1/8GB resource measurement, or controlled baseline-vs-current latency comparison has been performed in this checkpoint.
- No implementation commit beyond the handoff cherry-pick has been created or pushed. Main was not changed. Do not publish until the diff and public-repository privacy audit pass and the authorized release evidence is complete.

Continue from this branch and preserve the recovery checkpoint. Do not call all 60 upgrades complete from these results.

### Follow-up execution checkpoint — October 18, 2026

- Added manual speaker pin/unpin for 1–20 future audio windows in the production UI. The pin is marked as an owner-provided label, not an acoustic result; it does not override `Mixed`, suppresses spoken-name learning while active, and clears after the requested count or profile removal. Frontend regression covers the one-window expiry and learning veto.
- Tightened protocol 3 enforcement on capture open/close/freeze/drain and transcription endpoints. A mismatched version returns HTTP 426. The frontend checks the version from `/api/status` before enabling capture.
- Full suite rerun after these changes: backend, safety regressions, live-upgrade HTTP tests, frontend Chromium at 1200px and 375px, E2E Chromium at both widths, generated-speech real local stack, all Packet A Python/Node suites, Packet A workbench UI, and HTTP bridge passed. Packet A reported 29 Node + 12 Python + inline/workbench/bridge browser checks with no failures.
- Physical Brave check: foreground Brave opened `http://127.0.0.1:56069/`; microphone permission was granted for this local site until site close. The MacBook Air built-in microphone produced live meter readings (5%, then 14% during local speech playback); app reported `LOCAL MIC ACTIVE / UNVERIFIED` and later `LOCAL TRANSCRIPT · REVIEW WORDS`. A local macOS synthetic speech sample reached the local Whisper path, but its transcript contained substantial hallucinated text and word errors. This is a failure for reliable speech accuracy, not a successful natural-speech acceptance. A real two-person, natural overlap, device-unplug, and restart test was not performed because no consenting second speaker was available.
- Physical Stop test: pressing Stop opened the Keep/Drop prompt for one pending window; the window was dropped, the app showed `NOT LISTENING`, and “Erase all session data” was confirmed. The page returned to 0 passages; no enrollment was enabled. The local server was stopped. The one temporary browser tab may remain in Brave; it contains no transcript.
- One physical check exposed sample durations around 8.9 seconds despite the text UI reporting 9 seconds maximum. No controlled latency comparison or 45-minute memory trial was performed.
- GitHub visibility remains public. No transcript, recording, private note, embedding, token, or screenshot was staged or pushed. No push has occurred.

Current additions beyond the prior checkpoint: requirement 22 has a focused production UI test. Physical mic capture and Stop are tested; physical ASR quality is PARTIAL/FAIL for the synthetic speech attempt, and natural multi-speaker acceptance remains NOT TESTED.

## Evidence matrix — 2026-10-18 handoff continuation

This is an executable-evidence status snapshot, not a completion declaration. `PASS` means the current app behavior had a focused browser/backend/real-stack assertion in this checkout. `PARTIAL` means some behavior exists but the requested feature or proof is incomplete. `BLOCKED` means the behavior needs an unverified runtime/model capability. No requirement is counted complete from a control label alone.

| ID | Requirement | Current evidence / implementation | Status | Remaining gap |
|---:|---|---|---|---|
| 1 | Persistent pinned coaching rail | Live HTML `.hero-cue`; `test_frontend.py` desktop/mobile | PASS | None observed in current browser checks |
| 2 | Energy/silence graph; drag split/merge | Live HTML VAD graph; production PCM timeline in `experiments/packet-a/lens_pcm_core.js` | PARTIAL | Graph is meter based; PCM split/merge editor is not connected to production UI |
| 3 | In-place speaker reassignment | Live HTML transcript speaker select; `test_frontend.py` reassignment | PASS | None observed in current browser checks |
| 4 | Grounded evidence drawer | Live HTML evidence drawer; `test_frontend.py` cosine and margin display | PASS | Evidence remains measurements, not calibrated probabilities |
| 5 | Keyboard controls | Live HTML keyboard handlers; `test_frontend.py` M and numeric assignment | PASS | Full shortcut set not independently enumerated |
| 6 | Layout modes with memory | Live HTML layout persistence; `test_frontend.py` mode switch and resize | PASS | None observed in current browser checks |
| 7 | Skipped-window reasons and reprocess | Live HTML skipped queue and retry action | PARTIAL | Browser suite does not exercise every skip/reprocess transition |
| 8 | Flick-up mobile coaching sheet | Live HTML collapsed/expanded sheet, touch up/down gesture; `test_frontend.py` dispatches upward and downward swipes at 375px | PASS | Physical touchscreen gesture not tested |
| 9 | Per-window Stop keep/drop dialog | Live Stop freeze/drain in `server.py`; exact-hash drain backend test; Packet A chooser browser test | PASS | Physical microphone Stop/drain with multiple pending windows not exercised |
| 10 | Speaker chips, last-seen, boost | Live HTML speaker profile chips; `test_frontend.py` last-seen and boost | PASS | Natural identity accuracy remains unverified |
| 11 | Sticky optional context | Live HTML optional context and AI prompt | PARTIAL | Context is not visually sticky during scrolling |
| 12 | Custom prompt fragment presets | Live HTML presets and custom field; `test_live_upgrade.py` request assertion | PASS | None observed in current tests |
| 13 | Transcript filters | Live HTML speaker/keyword/coaching filters; `test_frontend.py` | PASS | None observed in current browser checks |
| 14 | Reduced motion/contrast/mono | Live HTML preference controls and CSS | PARTIAL | Runtime accessibility contrast and motion audit not done |
| 15 | Precise empty coaching ingredients | Live HTML missing-input status; `test_frontend.py` | PASS | None observed in current browser checks |
| 16 | Sliding plus priority AI context | `server.py` `chosen_turns`; `test_live_upgrade.py` older-priority retention | PASS | No long-session capacity trial |
| 17 | Exact/Fuzzy/Free grounding dial | `server.py` evidence validation; `test_live_upgrade.py` exact/fuzzy/free | PASS | None observed in current tests |
| 18 | Offline interruption/repetition/topic-shift cards | Live HTML has repetition cues plus explicit “let me finish” and “different topic” phrase triggers; frontend exercises both | PARTIAL | No turn-level interruption or semantic topic-change classifier; trigger scope is intentionally literal |
| 19 | In-place copyable next-step cards | Current next-line editor/copy control in live HTML | PARTIAL | Historical cards do not each have independent edit/copy controls |
| 20 | Mid-session coaching presets | Live HTML current settings flow to Ollama; `test_frontend.py` request payload | PASS | No provider/model switching during active request test |
| 21 | Full/half speaker confidence strip | Evidence drawer renders accessible native meters for full, first/second half, and half-window consistency; frontend asserts values and probability caveat | PASS | Measures raw cosine only, not a calibrated confidence probability |
| 22 | Speaker lock N windows/unpin | Live HTML lock control; `test_frontend.py` one-window pin and expiry | PASS | None observed in current browser checks |
| 23 | One-click Markdown/plain exports | Live HTML export actions; `test_frontend.py` download assertion | PASS | Plain export not independently checked in the current run |
| 24 | Bookmarks/highlights in export | Live HTML marker actions and exporter; `test_frontend.py` bookmark/highlight actions | PARTIAL | Current export assertion does not verify marker contents |
| 25 | Coaching pause, hot ASR | Live HTML pause and capture lifecycle | PARTIAL | Hot ASR action is not separately measured in this run |
| 26 | Smart debounce/manual immediate cue | Live HTML scheduling and manual cue action | PARTIAL | Debounce latency and cancellation races lack focused timing tests |
| 27 | Coaching timeline and per-card regenerate | Live HTML source-linked history | PARTIAL | Regeneration remains current-cue oriented, not per historical card |
| 28 | Grounding badge/retry looser | Live HTML grounding state and retry control | PASS | Retry interaction not exercised in this turn |
| 29 | Private note/goal for next AI call | `server.py` Ollama payload; `test_live_upgrade.py` private note assertion | PASS | None observed in current tests |
| 30 | Live VAD tunables and preview | Live HTML VAD sliders/graph; `test_frontend.py` synthetic meter segmentation | PASS | Production PCM tuning has not been compared to physical speech |
| 31 | Adaptive noise floor | Live HTML RMS noise estimate; browser meter regression | PARTIAL | No ambient-noise or changing-noise physical run |
| 32 | Half-window overlap heat | `server.py` overlap/forced Mixed logic | PARTIAL | No heat visualization; natural overlap accuracy unverified |
| 33 | Enrollment quality meter | Existing enrollment checks and rejection | PARTIAL | Pre-activation quality gauge is absent |
| 34 | Instant speaker drop | Per-profile Remove immediately clears only that RAM voice profile; `test_frontend.py` verifies no confirmation and transcript label preservation | PASS | Forget All still requires confirmation |
| 35 | Longer follow-up enrollment sample | Existing sample guidance | PARTIAL | Guided longer follow-up flow is absent |
| 36 | Raw cosine/margin available | `server.py` evidence and evidence drawer; `test_frontend.py` values | PASS | None observed in current checks |
| 37 | Soft cap/merge suggestion | Existing profile count cap | PARTIAL | No soft-cap merge suggestion workflow |
| 38 | Window-length distribution | Live HTML rolling median/range and observed 1–9 s canvas histogram; `test_frontend.py` verifies histogram pixels after captured windows | PASS | No persisted history; distribution resets per session |
| 39 | Whisper model switcher | No production model switcher | BLOCKED | Must inventory installed models and verify reload/rollback before exposing switch |
| 40 | Adjustable pre-roll/post-roll | Live HTML PCM controls; production PCM rendering uses `WindowTimeline.render` | PARTIAL | No production sample-boundary edit UI or physical roll-content proof |
| 41 | Overlap Mixed + no name learning | `server.py` force-Mixed veto; backend regression and drain hash tests | PASS | Natural two-speaker overlap not tested |
| 42 | Speaker embedding RAM/compact | Server RAM estimate is displayed | PARTIAL | Explicit compact action is absent |
| 43 | Structured performance and lease logs | Bounded diagnostics/health; `test_live_upgrade.py` | PARTIAL | Per-stage timing and lease owner/age telemetry are incomplete |
| 44 | Health endpoint and UI status | `/api/health`, UI health indicator; `test_frontend.py` | PASS | None observed in current browser checks |
| 45 | Fallback when speaker worker times out | Existing transcript fallback path; backend tests | PASS | No forced timeout run in this turn |
| 46 | Live Ollama endpoint/model/timeout/temp | `server.py` localhost validation and options; tests plus local stack | PASS | User-facing live settings not all independently exercised |
| 47 | Capture lease rotation and stale notice | `lens_stop_drain.py`, v3 capture protocol; backend/live-upgrade tests | PASS | Physical tab takeover not exercised this turn |
| 48 | Queue dashboard and pause intake | Live queue status and pause-intake control | PARTIAL | Full worker-stage graph is absent |
| 49 | Explicit disk speaker-profile save/load | Not implemented; RAM-only remains default | PARTIAL | Explicit opt-in export/import is still required |
| 50 | Rate limit and backpressure | Bounded queue/retry in app; Packet A 429 retention test | PASS | Main app saturation not stress-tested |
| 51 | Finish/drop in-flight shutdown | Freeze, exact-hash drain lease, per-window Keep/Drop; backend tests | PASS | No physical multi-pending-window race test |
| 52 | Versioned server-client messages | Protocol v3 required on protected requests; 426 mismatch regression | PASS | No older client compatibility matrix |
| 53 | Recent-window replay/debug | Skipped live clips can be reprocessed while lease remains active | PARTIAL | Processed-window debug replay is absent |
| 54 | Snapshot/restore | No session snapshot/restore implementation | PARTIAL | Versioned checksum/atomic restore flow is not built |
| 55 | Multi-tab lease visibility/transfer | Explicit takeover and invalidation; browser/backend tests | PARTIAL | Owner/age visibility is absent; physical multi-tab test remains |
| 56 | Custom local cue rules | Existing built-in local rules | PARTIAL | Owner-defined bounded rule editor/execution is absent |
| 57 | Running action-item/decision extraction | New local source-linked candidate ledger; `test_frontend.py` asserts decision/action extraction and passage navigation | PASS | Phrase-based candidates only; no semantic deduplication or persistence |
| 58 | Hotkey voice-note annotation | Separate private typed note exists | PARTIAL | Hotkey voice-note capture is absent |
| 59 | Speaker comparison/talk-time stats | No eligible-span accounting | PARTIAL | No talk-time UI or denominator disclosure |
| 60 | Continue last coaching thought | Existing coaching history only | PARTIAL | Thread-aware continuation call is absent |

### Current phase evidence

- Recovery checkpoint remains local-only at `/Users/andrew/Conversation_Lens_recovery_20261018/`; the starting tree and untracked files were preserved.
- Packet A integration commit `dc4b52c` is on `codex/conversation-lens-integration`; production changes remain uncommitted and unpushed.
- `python3 test_backend.py`, `python3 test_regressions.py`, `python3 test_live_upgrade.py`, QA-venv `test_frontend.py` (1200px and 375px, including synthetic production PCM-to-WAV queue), QA-venv `test_e2e.py` (both widths, HTTP/FFmpeg/Whisper/speaker path), and `python3 test_real_local_stack.py` passed. Latest local-stack sample: ASR 2.64s; Ollama 4.73s. These numbers are single-run observations, not a comparative latency benchmark.
- Packet A tests passed with `/Users/andrew/Library/Application Support/ConversationLensQA/venv/bin/python`: 12 Python and 29 Node tests; browser workbench, inline UI, and server bridge checks passed at 1200px and 375px. System Python 3.9 lacks Playwright, so do not use it for those browser tests.
- Physical Brave MediaRecorder microphone access, mic meter, Stop/drop and erase were exercised earlier. Production AudioWorklet PCM was not conclusively started on the physical device in this pass; a pending browser microphone request remained unresolved. Mark physical PCM, natural multi-speaker/overlap, 45-minute memory soak, and comparative latency as NOT TESTED.

## Post-checkpoint verification — 2026-10-18

- Commit `c88638a` was pushed normally to `origin/codex/conversation-lens-integration`; no force push, merge, or `main` mutation was performed.
- Final rerun passed `test_backend.py`, `test_regressions.py`, `test_live_upgrade.py`, QA-venv `test_frontend.py` at 1200px/375px including opt-in PCM synthetic-frame WAV ingestion and awaited Erase/Stop flow, QA-venv `test_e2e.py` at both widths, and `test_real_local_stack.py`. Latest single-run ASR was 2.91s and Ollama 5.45s. These are not a comparative benchmark.
- Public-repository staged diff and new files passed Gitleaks (`no leaks found`); `git diff --cached --check` passed. The four Packet A and two v6 generated screenshot artifacts remain ignored and unstaged.
- Physical AudioWorklet permission/capture did not resolve in Brave; the pending request was explicitly stopped, with no active capture lease or audio retained. Earlier physical MediaRecorder access does not prove this opt-in PCM path.

## UI follow-up — 2026-10-18

- Implemented the mobile coaching sheet's up/down touch gestures, visible raw cosine meters (full/halves and half-window consistency, with explicit non-probability labeling), immediate per-profile RAM removal, and a recent per-session duration histogram.
- Focused QA-venv `test_frontend.py` passed at 1200px and 375px. It asserts swipe expansion/collapse, numeric meters and caveat, single-profile deletion without confirmation while preserving transcript assignment, and rendered histogram pixels.
- Rows 8, 21, 34, and 38 move to PASS within that browser-test scope. Device touch hardware remains untested. The 60-item matrix remains substantially incomplete; rows marked PARTIAL/BLOCKED remain open.

## Local coaching follow-up — 2026-10-18

- Added phrase-grounded “Turn-taking” and explicit “Topic transition” observations with wording that discloses their limits. Existing repetition cues remain local.
- Added a session-derived, source-linked candidate Decisions & Actions list. It is rebuilt from transcript turns, uses `textContent`, does not persist, and labels each match as possible rather than settled.
- QA-venv `test_frontend.py` passed at 1200px and 375px, covering both cue triggers, both candidate categories, and navigation to the supporting passage. Requirement 57 is PASS for that scope; requirement 18 remains PARTIAL because this does not infer interruptions or semantic topic changes.
