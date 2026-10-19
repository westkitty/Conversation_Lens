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
| 2 | Energy/silence graph; drag split/merge | Production graph distinguishes the manual threshold from each sample's effective adaptive threshold; PCM editor supports sample-index split, draggable shared-boundary adjustment and adjacent merge; QA-venv `test_frontend.py` covers graph and editor at 1200px/375px, physical Brave AudioWorklet capture exercised edits, and regressions cover ring eviction/release | PASS | Natural speech-boundary usefulness and MediaRecorder fallback editing remain unverified |
| 3 | In-place speaker reassignment | Live HTML transcript speaker select; `test_frontend.py` reassignment | PASS | None observed in current browser checks |
| 4 | Grounded evidence drawer | Live HTML evidence drawer; `test_frontend.py` cosine and margin display | PASS | Evidence remains measurements, not calibrated probabilities |
| 5 | Keyboard controls | Live HTML keyboard handlers; `test_frontend.py` M and numeric assignment | PASS | Full shortcut set not independently enumerated |
| 6 | Layout modes with memory | Live HTML layout persistence; `test_frontend.py` mode switch and resize | PASS | None observed in current browser checks |
| 7 | Skipped-window reasons and reprocess | QA-venv `test_frontend.py` pauses intake, verifies the explicit reason and active-lease retry control, reprocesses the buffered clip and confirms a new passage at 1200px/375px | PASS | Browser capture is mocked; every worker failure reason and physical retry path is not separately exercised |
| 8 | Flick-up mobile coaching sheet | Live HTML collapsed/expanded sheet, touch up/down gesture; `test_frontend.py` dispatches upward and downward swipes at 375px | PASS | Physical touchscreen gesture not tested |
| 9 | Per-window Stop keep/drop dialog | Live Stop freeze/drain in `server.py`; exact-hash drain backend test; Packet A chooser browser test; live Brave Stop showed two pending-window decisions and both were dropped | PASS | Physical keep-and-transcribe disposition remains unexercised |
| 10 | Speaker chips, last-seen, boost | Live HTML speaker profile chips; `test_frontend.py` last-seen and boost | PASS | Natural identity accuracy remains unverified |
| 11 | Sticky optional context | Read-only sticky context/private-note summary mirrors owner-entered fields; `test_frontend.py` checks visibility and scroll pin at 1200px/375px | PASS | Sticky summary truncates each displayed field at 500 characters |
| 12 | Custom prompt fragment presets | Live HTML presets and custom field; `test_live_upgrade.py` request assertion | PASS | None observed in current tests |
| 13 | Transcript filters | Live HTML speaker/keyword/coaching filters; `test_frontend.py` | PASS | None observed in current browser checks |
| 14 | Reduced motion/contrast/mono | `test_frontend.py` toggles all three modes at both widths, checks mono font, verifies motion animation removal, and measures primary/muted text contrast on background at ≥7:1 | PASS | Contrast calculation covers theme text tokens, not every hard-coded component/state |
| 15 | Precise empty coaching ingredients | Live HTML missing-input status; `test_frontend.py` | PASS | None observed in current browser checks |
| 16 | Sliding plus priority AI context | `server.py` `chosen_turns`; `test_live_upgrade.py` older-priority retention | PASS | No long-session capacity trial |
| 17 | Exact/Fuzzy/Free grounding dial | `server.py` evidence validation; `test_live_upgrade.py` exact/fuzzy/free | PASS | None observed in current tests |
| 18 | Offline interruption/repetition/topic-shift cards | QA-venv `test_frontend.py` covers explicit turn-taking and interruption acknowledgments, repeated phrases, lexical topic change versus stable wording, and a source-linked half-window divergence cue with uncertainty disclosure at 1200px/375px; real local-stack test verifies the conservative Mixed acoustic signal | PASS | Cues are phrase, lexical, and half-window diagnostics; they do not perform diarization or infer semantic intent, and natural conversation usefulness remains unmeasured |
| 19 | In-place copyable next-step cards | Each historical coaching card now has its own editable next line and copy action; frontend asserts card-local edit and copied value | PASS | Copy uses the browser clipboard when available |
| 20 | Mid-session coaching presets | Live HTML current settings flow to Ollama; `test_frontend.py` request payload | PASS | No provider/model switching during active request test |
| 21 | Full/half speaker confidence strip | Evidence drawer renders accessible native meters for full, first/second half, and half-window consistency; frontend asserts values and probability caveat | PASS | Measures raw cosine only, not a calibrated confidence probability |
| 22 | Speaker lock N windows/unpin | Live HTML lock control; QA-venv `test_frontend.py` at 1200px/375px pins two eligible windows, leaves an acoustic Mixed window Mixed without consuming the pin, verifies expiry and explicit unpin | PASS | Assignment is a temporary manual label, not an acoustic identity result or training input |
| 23 | One-click Markdown/plain exports | `test_frontend.py` downloads and inspects both Markdown session and plain transcript outputs | PASS | None observed in current browser checks |
| 24 | Bookmarks/highlights in export | `test_frontend.py` verifies `★ [highlight]` markers and transcript text in both exports | PASS | None observed in current browser checks |
| 25 | Coaching pause, hot ASR | QA-venv `test_frontend.py` pauses coaching after a local transcript passage, confirms a subsequent capture window is still transcribed, then resumes cues at both 1200px and 375px | PASS | Physical microphone behavior while cues are paused was not separately measured |
| 26 | Smart debounce/manual immediate cue | QA-venv `test_frontend.py` measures automatic request delay/coalescing, manual immediate request, serialized in-flight follow-up, and stale-result suppression at 1200px/375px | PASS | Timing uses a controlled mock endpoint; real Ollama latency and cancellation behavior under network failure remain unmeasured |
| 27 | Coaching timeline and per-card regenerate | Per-card action regenerates only the selected history card through opted-in local Ollama; frontend asserts the selected card's result | PASS | Requires user-enabled Ollama; source uses the current transcript context |
| 28 | Grounding badge/retry looser | Live HTML grounding state and retry control | PASS | Retry interaction not exercised in this turn |
| 29 | Private note/goal for next AI call | `server.py` Ollama payload; `test_live_upgrade.py` private note assertion | PASS | None observed in current tests |
| 30 | Live VAD tunables and preview | Live HTML VAD sliders/graph; `test_frontend.py` synthetic meter segmentation | PASS | Production PCM tuning has not been compared to physical speech |
| 31 | Adaptive noise floor | QA-venv `test_frontend.py` supplies steady low-level background RMS, verifies the effective threshold rises as the estimate adapts and falls as the input drops; live UI exposes adaptive floor/effective threshold and graphs the effective line | PASS | Physical changing-noise behavior was not separately measured |
| 32 | Half-window overlap heat | Evidence drawer shows raw half-window cosine divergence; QA-venv frontend checks the display and `test_real_local_stack.py` overlays local Daniel/Samantha TTS, runs the installed embedding model through production transcription, and verifies half-cosine 0.7315 triggers Mixed with no profile learning | PASS | Controlled synthetic voices, not human conversation; cosine divergence is not a calibrated overlap probability |
| 33 | Enrollment quality meter | QA-venv `test_frontend.py` varies enrollment audio from clean signal to silence and clipping, and verifies the live signal-present/clipping rates plus the explicit non-identity caveat at 1200px/375px | PASS | This is an acoustic signal meter, not a speaker-model recognition-quality score; server enrollment checks remain authoritative |
| 34 | Instant speaker drop | Per-profile Remove immediately clears only that RAM voice profile; `test_frontend.py` verifies no confirmation and transcript label preservation | PASS | Forget All still requires confirmation |
| 35 | Longer follow-up enrollment sample | QA-venv `test_frontend.py` confirms both standard and longer choices change the actual scheduled local recording timeout to 7,000 and 10,000 ms, respectively; prompt reflects the selected duration | PASS | Whether ten seconds improves natural voice recognition remains unmeasured |
| 36 | Raw cosine/margin available | `server.py` evidence and evidence drawer; `test_frontend.py` values | PASS | None observed in current checks |
| 37 | Soft cap/merge suggestion | At six of eight profiles, `speaker_status()` returns up to three cross-profile raw-cosine candidate pairs; frontend displays review hints and never merges automatically; backend and desktop/mobile tests | PASS | Cosine hints are uncalibrated, tested only with synthetic vectors, and require owner judgment |
| 38 | Window-length distribution | Live HTML rolling median/range and observed 1–9 s canvas histogram; `test_frontend.py` verifies histogram pixels after captured windows | PASS | No persisted history; distribution resets per session |
| 39 | Whisper model switcher | Local inventory, UI picker and guarded switch API for already-installed <=600 MB models; generated-silence warm-up; refuses active capture/transcription; tests cover successful selection and failed-load rollback | PASS | MacBook base (141 MiB) and small (465 MiB) loaded through the production warm-up helper; no speech-quality comparison or selection persistence across server restart |
| 40 | Adjustable pre-roll/post-roll | Production UI test asserts both roll controls reach PCM rendering; Packet A core test checks exact 200 ms pre-roll and post-roll sample ranges and preserved primary boundaries | PASS | Device-specific natural-speech roll usefulness was not separately measured |
| 41 | Overlap Mixed + no name learning | `server.py` conservative half-window veto; backend regression and drain hash tests; real local stack synthetic overlapping voices return Mixed and leave session speaker profiles unchanged | PASS | Natural two-speaker overlap not tested |
| 42 | Speaker embedding RAM/compact | Owner-invoked lossy compaction keeps the most cosine-separated pair and reports discarded count; backend unit/HTTP checks and frontend desktop/mobile path | PASS | Compaction changes in-memory match exemplars and cannot be undone; no profile is saved |
| 43 | Structured performance and lease logs | Metadata-only bounded events for decode, VAD, ASR, embedding, speaker match, audio request and Ollama; relative stage graph; lease owner/age; backend and browser tests | PASS | Event log is a 120-entry RAM ring; per-window timestamps and exhaustive failure injection remain untested |
| 44 | Health endpoint and UI status | `/api/health`, UI health indicator; `test_frontend.py` | PASS | None observed in current browser checks |
| 45 | Fallback when speaker worker times out | Existing transcript fallback path; backend tests | PASS | No forced timeout run in this turn |
| 46 | Live Ollama endpoint/model/timeout/temp | `server.py` localhost validation and options; tests plus local stack | PASS | User-facing live settings not all independently exercised |
| 47 | Capture lease rotation and stale notice | `lens_stop_drain.py`, v3 capture protocol; backend/live-upgrade tests | PASS | Physical tab takeover not exercised this turn |
| 48 | Queue dashboard and pause intake | Live per-window in-flight/queued/held/retry metadata list, bounded to four rows; pause-intake control label and state tested alongside PCM hold/release at 1200px and 375px | PASS | Stage timing graph remains uncorrelated by window ID; full saturation/backoff stress was not run |
| 49 | Explicit disk speaker-profile save/load | Owner-triggered JSON download and file picker; schema v1, SHA-256 integrity, strict normalized-vector validation, replacement confirmation and active-capture refusal; backend and desktop/mobile browser checks | PASS | App never writes profiles automatically; exported biometric files are unencrypted and user-managed; no cross-version migration beyond v1 |
| 50 | Rate limit and backpressure | Bounded queue/retry in app; Packet A 429 retention test | PASS | Main app saturation not stress-tested |
| 51 | Finish/drop in-flight shutdown | Freeze, exact-hash drain lease, per-window Keep/Drop; `test_backend.py` now posts a generated PCM WAV through exact-hash Keep authorization, production FFmpeg normalization and local Whisper route; live Brave Stop froze intake and dropped two held PCM windows before returning to NOT LISTENING | PASS | A physical Keep attempt found and triggered a WAV path collision; fixed and covered by the production HTTP regression, but not repeated physically after the fix; adversarial race remains untested |
| 52 | Versioned server-client messages | Protocol v3 required on protected requests; 426 mismatch regression | PASS | No older client compatibility matrix |
| 53 | Recent-window replay/debug | Skipped live clips are reprocessable; last four processed PCM/MediaRecorder clips are available through native browser playback, capped at 2 MB total; frontend verifies both formats and Stop cleanup | PASS | Playback was verified by browser media state, not physical speaker output; history is RAM-only and clears on Stop |
| 54 | Snapshot/restore | Version-1 JSON snapshot with SHA-256 validation, bounded validation, transcript labels/turns, bookmarks/highlights, coaching cards and private text restore; frontend tests verify corrupt-checksum and unsupported-version rollback | PASS | Audio voice notes and speaker profiles are excluded and explicitly disclosed; the separate profile export is opt-in; limits are 1 MB/300 turns and no long-session performance trial was run |
| 55 | Multi-tab lease visibility/transfer | Explicit takeover/invalidation; `/api/health` exposes opaque tab owner and age; backend and browser tests plus a real Brave two-tab takeover verify owner visibility and stale-tab failure | PASS | None for lease transfer; the live microphone smoke did not assess transcript accuracy |
| 56 | Custom local cue rules | New session-only rule editor with max 8 literal phrase matches, bounded observation/question text, priority and source link; `test_frontend.py` asserts a live match and cleanup on Erase | PASS | Rules are literal substrings, not semantic conditions; no persistence |
| 57 | Running action-item/decision extraction | New local source-linked candidate ledger; `test_frontend.py` asserts decision/action extraction and passage navigation | PASS | Phrase-based candidates only; no semantic deduplication or persistence |
| 58 | Hotkey voice-note annotation | `A` toggles a private local MediaRecorder note attached to selected/latest passage; RAM-only bounded playback list is outside transcript; browser test checks audio node and transcript isolation | PASS | Mocked browser capture tested; physical note recording and snapshot export are not tested, audio is deliberately excluded from snapshots |
| 59 | Speaker comparison/talk-time stats | UI reports only measured `speechSeconds` from enrolled, non-overlap acoustic matches; Mixed/overlap/unknown/pinned/unmeasured windows are separately excluded; `test_frontend.py` verifies denominator and overlap accounting | PASS | Depends on the worker returning eligible speech-span measurements; manual labels never add speaker time |
| 60 | Continue last coaching thought | `continueThoughtBtn` sends the latest selected prior card plus current transcript through the explicit local AI request; backend bounds and instructs continuation | PASS | Local Ollama remains opt-in and must be reachable; only mocked UI and prompt composition tested |

### Current phase evidence

- Recovery checkpoint remains local-only at `/Users/andrew/Conversation_Lens_recovery_20261018/`; the starting tree and untracked files were preserved. Current target is the MacBook checkout `/Users/andrew/Conversation_Lens`, remote `git@github.com:westkitty/Conversation_Lens.git`, branch `codex/conversation-lens-integration`.
- Current HEAD is `271f2def482e9257ffc1262f21c708b8b967a0d5`, pushed to `origin/codex/conversation-lens-integration`; local and remote hashes match and the worktree is clean. No merge to `main` occurred.
- Current combined suite passed: `test_backend.py`, `test_regressions.py`, `test_live_upgrade.py`; QA-venv `test_frontend.py` at 1200px and 375px; QA-venv `test_e2e.py` at both widths; and `test_real_local_stack.py` with local Whisper, the installed speaker model, synthetic overlap, and localhost Ollama. Single-run observations were ASR 1.96s, 9.53s synthetic clip duration, half-window cosine 0.7315, and Ollama 5.21s; these are not a comparative latency benchmark.
- Packet A passed 29 Node and 12 Python tests, plus the browser workbench, inline UI, and HTTP bridge checks at 1200px and 375px. These isolated tests do not replace the integrated v6 application.
- Physical Brave AudioWorklet PCM capture produced held windows; the editor moved a sample boundary, split and merged PCM; physical Stop showed two per-window choices and both were dropped. In a separate physical MediaRecorder run, a generated local phrase was captured and transcribed into two passages. A further Stop displayed the pending-window Keep confirmation and ended NOT LISTENING with an empty queue and four total passages, but the final generated phrase was not distinguishable in the resulting transcript; count this Keep-and-transcribe route as INCONCLUSIVE, not PASS. The test session was erased in the app and the local server was stopped. No natural two-person conversation or natural overlap accuracy run has been completed. A 45-minute memory/queue soak and matched latency comparison also remain untested.
- The 60-row matrix records tested requested behaviors; several limitations and acceptance gaps remain explicitly listed. Do not treat that matrix as proof of the outstanding physical acceptance runs.

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

## Historical coaching controls — 2026-10-18

- Each recent coaching card now owns an editable/copyable next-line field. The opt-in per-card Regenerate button sends the current transcript and selected local Ollama settings, then updates only that card; unavailable or busy AI states are explicit and leave existing cards intact.
- QA-venv `test_frontend.py` passed at 1200px and 375px. It edits and copies a card-specific line, then verifies a local mocked Ollama response changes that card's suggestion. Rows 19 and 27 are PASS for this exercised path.

## Acoustic span accounting — 2026-10-18

- Added session-only per-speaker speech-span totals using `speechSeconds` supplied by the voice worker. The denominator includes only measured enrolled-speaker spans without overlap; Mixed, overlap, unknown, manually pinned, and missing measurements are called out separately. Transcript reassignment does not alter acoustic totals.
- QA-venv `test_frontend.py` passed at 1200px and 375px, asserting a 2.5-second enrolled-speaker attribution and 1.2-second overlap exclusion. Row 59 is PASS for this measured-worker path; speech spans unavailable from the worker remain explicitly unmeasured.

## Session-local owner cues — 2026-10-18

- Added an owner-defined cue form capped at eight rules. Rules match literal case-insensitive phrases, use bounded text for the observation/question, provide low/normal/high priority, and link each cue to its matched passage. No regex, script, or code execution is accepted. Erase clears the rules; ordinary transcript clearing retains them for the session.
- QA-venv `test_frontend.py` passed at 1200px and 375px, exercising a rule against an existing passage, verifying the source link, and verifying Erase cleanup. Requirement 56 is PASS for literal local phrase rules.

## Session snapshot follow-up — 2026-10-19

- Added owner-triggered JSON snapshot download with schema/version and SHA-256 checksum. It includes transcript text/labels/times, bookmarks/highlights, recent coaching cards, and private context/note/aim. It excludes audio, evidence metrics, and speaker profiles. Restore validates file size, schema, counts, field limits, source references, and checksum before replacing live data; capture must be stopped first.
- QA-venv `test_frontend.py` passed at 1200px and 375px. It downloads/parses a snapshot, corrupts the checksum and confirms current transcript remains unchanged, then restores a valid snapshot and confirms the private note and transcript are restored. The snapshot reports omitted voice-note count but does not restore audio notes or speaker profiles, so requirement 54 remains PARTIAL; large-session storage limits and non-Chromium engines were not tested.
- Follow-up QA now also submits an unsupported version and verifies live session state is unchanged. Requirement 54 is PASS for explicit version-1 session-state export/restore with omitted audio/profile disclosures; profiles use the separate opt-in integrity-checked file flow, and large-session performance remains unmeasured.

## Continue Thought follow-up — 2026-10-19

- Added an explicit button that sends the newest coaching card as bounded continuation context with the current transcript to the existing opt-in local Ollama endpoint. Server instructions require advancing the thought without repeating it and re-grounding claims in the current transcript. The UI reports success/failure and retains the older card.
- `test_live_upgrade.py` verifies continuation context reaches the Ollama prompt and is bounded by the existing 900-character limit. QA-venv `test_frontend.py` verifies the button sends the prior card and receives a new response at desktop/mobile widths. Requirement 60 is PASS for mocked request flow; natural model quality remains unmeasured.

## Lease ownership follow-up — 2026-10-19

- Capture-open records a validated opaque per-tab label and monotonic elapsed age; local `/api/health` reports both while a capture or drain lease is active and clears them on final close or erase. The diagnostics health label displays the current owner and age.
- `test_live_upgrade.py` opens a capture with a synthetic tab identity and verifies active owner/age fields. Requirement 55 remains PARTIAL until a physical multi-tab takeover is exercised in Brave.

## Sticky context follow-up — 2026-10-19

- Added a top-of-page sticky summary of optional context and the private owner note. The fields remain separate, summary text is inserted as text, each display truncates at 500 characters, and the summary stays hidden when both inputs are blank. It ignores pointer events so it cannot block controls beneath it.
- QA-venv `test_frontend.py` passed at 1200px and 375px, checking the populated summary and sticky position after scrolling. Requirement 11 is PASS for the tested browser layouts.

## Private voice-note follow-up — 2026-10-19

- Added `A` hotkey and button for a private voice note attached to the selected/latest passage. Notes require conversation capture to be stopped, use local MediaRecorder only, cap each note at 15 seconds/2 MB, cap the session at eight notes/8 MB, and provide playback/delete controls. Notes remain separate from transcript and exports, stay in memory only, and are cleared on Erase/page exit. Session snapshots disclose and exclude note audio.
- QA-venv `test_frontend.py` passed at 1200px and 375px; synthetic capture verifies the audio playback element appears without transcript mutation. Physical audio-note recording and cross-browser playback remain unverified. Requirement 58 is PASS for the exercised mocked path.

## Export evidence follow-up — 2026-10-19

- QA-venv `test_frontend.py` downloaded and inspected the Markdown session export and plain transcript export. Both contain the selected passage text and `★ [highlight]` markers; the plain export uses its distinct filename and omits coaching sections. Rows 23 and 24 are PASS for these exercised exports.

## Speaker soft-cap follow-up — 2026-10-19

- Added a six-profile soft cap before the existing eight-profile hard cap. The server computes up to three bidirectional average-best cosine candidate pairs from the latest four vectors per enrolled profile. The UI labels the raw score as a review hint, states it is not identity proof, and does not merge profiles.
- `test_live_upgrade.py` verifies synthetic normalized vectors produce the expected candidate; QA-venv `test_frontend.py` verifies the soft-cap text and non-automatic behavior at 1200px and 375px. Requirement 37 is PASS for that suggestion path; real voice-profile similarity calibration is not established.

## Processing-stage telemetry — 2026-10-19

- Added metadata-only timings for decode, speech gate, Whisper ASR, speaker embedding, speaker match, full audio request, and Ollama. The on-demand diagnostics panel renders the latest duration per stage as a relative bar and clearly labels that bars are not performance targets. Event fields exclude transcript text and embeddings.
- `test_backend.py` checks stage events on a synthetic ASR/speaker path; `test_frontend.py` checks the rendered ASR and embedding stages at 1200px and 375px; `test_live_upgrade.py` checks the bounded 120-event metadata ring and lease owner/age. Requirement 43 is PASS for these measured stages; row 48 remains partial because the graph is not a per-window live queue view.

## Accessibility preference checks — 2026-10-19

- QA-venv `test_frontend.py` toggled high contrast, mono font, and reduced motion at 1200px and 375px. It verified the high-contrast `--ink` and `--muted` tokens against `--bg` exceed 7:1 and the status pulse animation is disabled in reduced-motion mode. Requirement 14 is PASS for these theme and control paths; every hard-coded UI color/state was not audited.

## Half-window evidence heat — 2026-10-19

- Added a divergence bar from the measured first/second-half raw cosine values. When the worker flags possible overlap, the same panel keeps the explicit learning veto. Text and accessibility labels state the divergence is a diagnostic, not an overlap probability or identity score.
- QA-venv `test_frontend.py` verifies the 0.0080 synthetic cosine gap and visible diagnostic bar at both widths. Requirement 32 remains PARTIAL because no natural overlap classification run is available.

## Speaker profile RAM compaction — 2026-10-19

- Added an explicit per-profile action available at three or more samples. It retains the most cosine-separated pair, reports the number discarded, and states that this is lossy and irreversible. The profile remains RAM-only; compaction is refused when the audio-processing lock is busy.
- `test_live_upgrade.py` checks representative retention, missing-profile and insufficient-sample errors, plus the authenticated loopback endpoint. `test_frontend.py` exercises confirmation, UI refresh and the reported sample count at 1200px and 375px. Requirement 42 is PASS for this owner-invoked compaction scope; recognition quality after compaction is not calibrated on natural voices.

## Enrollment signal preview — 2026-10-19

- During an explicit, consented seven-second enrollment recording, the UI samples microphone RMS and clipped-frame rate and updates a visible pre-activation meter. The label explicitly says this is a signal check, not identity or recognition quality. A near-silent capture is rejected locally without changing a voice profile; the local server's existing checks remain in force.
- QA-venv `test_frontend.py` supplies deterministic synthetic microphone frames, verifies the meter reaches the expected value and that cancel stops the sample at 1200px and 375px. Requirement 33 remains PARTIAL until natural microphone quality is measured and tied to the actual speaker model's enrollment-quality behavior.

## Longer enrollment follow-up — 2026-10-19

- Added an explicit 7-second standard and 10-second longer follow-up selection. The chosen duration is used by the recorder timer; the existing server 10-second audio cap remains authoritative. `test_frontend.py` verifies that the control updates the record action at both target widths.
- Requirement 35 remains PARTIAL because no natural voice comparison has measured enrollment quality or recognition improvement from a longer sample.

## Processed PCM replay — 2026-10-19

- The latest successfully processed PCM window remains available as one in-memory WAV with native playback controls while capture is active. Stop revokes its object URL and clears the retained clip; MediaRecorder clips are not retained for replay.
- QA-venv `test_frontend.py` checks that the replay control receives a blob URL after synthetic PCM transcription and releases it on Stop at 1200px and 375px. Requirement 53 remains PARTIAL because replay history is limited to one PCM clip and playback was validated through browser state, not a physical speaker.

## Production PCM window editor — 2026-10-19

- Connected the Packet A `WindowTimeline` to a production hold/review flow. While the owner holds PCM intake, bounded buffered WAV windows appear in a sample-indexed waveform editor. The owner can split a window, move the shared boundary between adjacent windows, merge adjacent windows, and then release the queue for transcription. Every edited segment is re-rendered from the original 16 kHz ring and forces Mixed/no-name-learning. Stop still owns Keep/Drop disposition; edits do not bypass capture leases.
- QA-venv `test_frontend.py` drives the production synthetic capture path through hold, split, boundary move, merge, split, two WAV submissions, Mixed veto, replay and Stop cleanup at 1200px and 375px. `lens_pcm_core.js` separately covers exact sample continuity and WAV encoding. Requirements 2 and 40 remain PARTIAL because the physical microphone AudioWorklet path and real pre/post-roll content have not been accepted on-device; MediaRecorder fallback remains unchanged.

## Local Whisper model selection — 2026-10-19

- Added an inventory and picker for models already installed in the DexDictate model directory or current configured directory. It offers models up to 600 MB, exposes opaque IDs rather than local paths, refuses switching during capture or transcription, and changes the active path only after loading the candidate with a generated one-second silent WAV. A failed warm-up leaves the previous model active. No download, service, persistence, or replacement of the configured default is performed.
- MacBook inventory: `ggml-base.bin` 141 MiB and `ggml-small.bin` 465 MiB. Both passed the production `warm_whisper_model` helper on generated silence. `test_live_upgrade.py` covers inventory, active-capture refusal, successful switch and rollback; QA-venv `test_frontend.py` covers the picker at 1200px/375px. Requirement 39 is PASS for installed-model switching; relative speech accuracy and latency remain unmeasured.

## Opt-in speaker profile files — 2026-10-19

- Added explicit profile export and import endpoints with schema version 1, canonical SHA-256 validation, strict name/vector/normalization/profile-count checks, atomic RAM replacement, active-capture refusal and audio-processing exclusion. Export is available only after a user confirmation, creates a local JSON download, and makes no app-managed disk copy. The UI warns that files contain biometric voice data; import also requires replacement confirmation.
- `test_live_upgrade.py` covers round-trip helper integrity, authenticated HTTP export/import, active-capture refusal, corrupt checksum rejection and preservation of prior profiles. QA-venv `test_frontend.py` exercises file import and export download at 1200px and 375px. Requirement 49 is PASS for opt-in local files; files are intentionally not encrypted by the app.

## Per-window queue dashboard — 2026-10-19

- Added a metadata-only list of the current in-flight and queued windows, with explicit local-transcription, held-for-edit and retry states. It exposes no transcript or audio contents and is refreshed with the existing bounded queue/status updates. The existing pause-intake action remains available beside the window controls.
- QA-venv `test_frontend.py` checks a held PCM entry, in-flight state after release and pause/resume label state at 1200px and 375px. Requirement 48 is PASS for per-window queue visibility and intake pause; stage timing is not correlated to window IDs and sustained saturation remains untested.

## Skipped-window retry — 2026-10-19

- Extended browser coverage for the existing bounded skipped-window path: pause intake, stop a buffered MediaRecorder window, verify the reason and retry action, reprocess while the active capture lease remains valid, and confirm the returned passage.
- QA-venv `test_frontend.py` exercises this at 1200px and 375px. Requirement 7 is PASS for the paused-intake/retry path; worker-timeout and every skip reason remain outside this focused run.

## Bounded recent-window replay — 2026-10-19

- Expanded replay to the last four successfully processed audio clips from either PCM WAV or MediaRecorder, with a two-megabyte total cap and a 512 KB per-clip cap. Native audio controls select and play a clip; Stop releases every clip and object URL. No audio is written to disk by this feature.
- QA-venv `test_frontend.py` verifies MediaRecorder and PCM entries, selection, two-window split submissions, and Stop cleanup at 1200px and 375px. Requirement 53 is PASS for bounded in-memory replay; physical speaker output was not tested.

## Brave physical microphone smoke — 2026-10-19

- Launched the committed local app in Brave using the project launcher, granted microphone permission for `127.0.0.1`, observed a live input meter and local transcription passages, then pressed Stop. Stop returned the UI to `NOT LISTENING`, set the input meter to idle, and dropped the pending window. The local server process was then terminated, clearing its RAM session state.
- This confirms permission, capture, local ASR activity and Stop/drop on this MacBook Air. The captured audio source was not controlled or attributable, so transcript accuracy is not accepted; no two-person/overlap, latency comparison, physical PCM editor, or long-session test was established. No audio or transcript was intentionally exported or saved by this smoke.

## Local topic-shift vocabulary cue — 2026-10-19

- Added an offline comparison of content words in the latest three passages against the preceding three. The cue requires at least five distinct terms in each window and very low lexical overlap; it links to the newest source passage and states that the result may reflect wording rather than a true topic change. It sends no data to a service.
- QA-venv `test_frontend.py` passed at 1200px and 375px with a synthetic astronomy-to-cooking shift and a stable cooking-vocabulary control. Requirement 18 remains PARTIAL because this does not infer interruption order or semantic topic changes, and the heuristic has not been assessed in natural conversation.

## Brave two-tab capture lease — 2026-10-19

- On Brave, the first localhost tab started real microphone capture. A second tab received the existing-session prompt; confirming takeover made the first tab fail its next local capture request with “Capture unavailable or frozen” while the second tab remained active. During the second lease, `/api/health` reported `captureActive: true`, an opaque `captureOwner`, and age 8 seconds. The second tab was stopped and the local server exited, clearing its RAM session.
- Requirement 55 is PASS for physical lease transfer and owner/age visibility. Audio content from this brief smoke was uncontrolled and was not used as recognition evidence or exported.

## Coaching debounce and stale-response checks — 2026-10-19

- Extended the browser test endpoint with controllable response delay and request timestamps. The desktop/mobile user flow now verifies that rapid automatic updates coalesce inside the debounce/rate-limit window, manual Get Cue starts without that wait, a changed passage queues behind the active request, and the older response is not rendered over current content.
- QA-venv `test_frontend.py` passed at 1200px and 375px. Requirement 26 is PASS for client scheduling and stale-result suppression; the endpoint is mocked, so live Ollama network cancellation and end-to-end provider latency remain unmeasured.


### Follow-up execution checkpoint — October 19, 2026 (physical PCM editor and Stop/drop)

- Verified the actual checkout before action: branch `codex/conversation-lens-integration`, clean and at `6d33301f7bc77989fb22ed490fd45576db8b08b1`, matching its origin branch. No source edits were made during the physical run.
- Launched the committed app in Brave at `http://127.0.0.1:57828/`; granted local microphone access. Selected AudioWorklet PCM hold/edit, enabled consent, and set pre-roll and post-roll controls to 200 ms. App showed `LOCAL MIC ACTIVE / UNVERIFIED`, bounded in-memory PCM ring and PCM edit hold. A local synthetic speech signal generated two held PCM windows; both remained held for edit and were not released to transcription during edit.
- Exercised production sample edits in the live UI: moved a shared boundary (sample index 125423), split the selected window, then merged the adjacent split back together. The resulting window duration returned to the combined duration (5.22 seconds). This establishes mechanical physical-path PCM editing, not that the selected acoustic boundary is useful for natural conversation. One older held window aged out of the bounded ring while testing; long-held-window retention/visibility deserves separate coverage.
- Pressed Stop with two PCM windows held. Brave presented a separate keep/drop decision for each pending window. Chose drop twice; UI returned to `NOT LISTENING`. No transcript passage was created. The local server process was then stopped. The recorded speech was synthetic test audio, not user conversation.
- Requirement #2 advances to PASS for graph/edit controls on physical AudioWorklet PCM; acoustic usefulness remains unverified. Requirements #9 and #51 now include a physical multi-pending-window Stop/drop execution; the keep path and adversarial race remain untested. Requirement #40 remains PARTIAL: the controls were set, but sample-level pre/post-roll inclusion was not measured.
- No source/runtime data was added to Git in this checkpoint. Git publication state remains the prior commit until the ledger-only update is committed and pushed after review. No merge to `main`.

### Follow-up execution checkpoint — October 19, 2026 (held PCM ring eviction)

- Inspection of the physical run's reported aging window found that PCM windows can remain in the bounded transcription queue after their source samples age out of the 45-second ring. Their canonical WAV remains available for submit or Stop disposition, but the PCM editor correctly cannot redraw or edit evicted samples. The UI previously hid those windows without explaining why and disabled the release button when all held windows had aged out.
- Updated the editor to count held items separately from still-editable ring windows. When a held source has been evicted, it now explains that editing is unavailable, the original WAV remains retained, and the owner can submit it or choose Keep/Drop at Stop. The Transcribe button stays enabled whenever a held WAV remains in the queue.
- Added a focused `test_frontend.py` regression that advances the mocked PCM ring past the held window, checks the explicit eviction message and enabled release, then confirms the retained original WAV is submitted. The full frontend suite passed at 1200px and 375px, including the existing PCM edit/release/replay/Stop flow.
- The regression proves behavior for the bounded hold queue only. Natural speech segmentation, longer hold usability, and edited audio on the MediaRecorder fallback remain unverified. No capture audio is committed; this test uses synthetic frames and mocked HTTP.

### Follow-up execution checkpoint — October 19, 2026 (pre/post-roll sample coverage)

- Added exact post-roll assertions to the PCM core test: a 200 ms post-roll returns exactly the following 3,200 PCM frames, keeps the primary boundary unchanged, and marks contextual audio ineligible for voice-name learning. Existing pre-roll assertions already verify the corresponding preceding samples.
- Extended the production frontend regression to set both sliders and assert that the live timeline render receives both values. The full QA-venv frontend suite passed again at 1200px and 375px; the 14-case Packet A PCM core suite passed.
- Requirement #40 advances to PASS for exact sample crop behavior and production control wiring. Acoustic usefulness under natural speech remains unmeasured; no speech is persisted by these tests.

### Follow-up execution checkpoint — October 19, 2026 (coaching pause and hot transcription)

- Extended the local browser flow to pause coaching after the first transcript passage, allow a second audio window to complete, assert its transcription request and passage still arrive, and resume coaching. This distinguishes the cue pause from microphone/ASR capture.
- QA-venv `test_frontend.py` passed at 1200px and 375px. Requirement #25 advances to PASS for the tested capture path; the mock verifies client behavior, not a physical microphone pause/resume run.

### Follow-up execution checkpoint — October 19, 2026 (adaptive noise-floor visibility)

- Corrected the energy graph: the dashed line is the configured minimum RMS threshold, while the solid adaptive line now plots the effective per-sample cut threshold used by segmentation. The UI also reports the current adaptive RMS floor and effective cut value.
- Added a varying-background fixture to the production frontend regression. It supplies steady low-level ambient input, observes the effective threshold rise as the noise estimate adapts, then drops the input and observes the threshold fall. QA-venv `test_frontend.py` passed at 1200px and 375px.
- Requirement #31 advances to PASS for tested meter adaptation and visible threshold reporting. Physical changing-noise behavior remains unmeasured; no user audio is used.

### Follow-up execution checkpoint — October 19, 2026 (enrollment preview and duration)

- Corrected the permission-stage enrollment prompt to use the selected 7- or 10-second duration and reject unsupported duration values. The record timer remains tied to that same value.
- Extended the mocked local microphone regression to vary enrollment audio from clean signal to silence to clipping and verify the acoustic signal meter changes. It also captures the real timer delays scheduled by the app for both seven- and ten-second samples. QA-venv `test_frontend.py` passed at 1200px and 375px.
- Requirements #33 and #35 advance to PASS for their controls and behavior. The meter does not claim speaker-identity quality, and no recognition benefit from the longer sample is inferred.

### Follow-up execution checkpoint — October 19, 2026 (offline interruption and repetition cues)

- Added an explicit, cautious `Possible interruption` card for direct interruption acknowledgments. It states that transcript wording alone does not establish timing, intent, or who had the floor.
- Expanded production frontend coverage for a request to finish, an interruption acknowledgment and its uncertainty text, repeated phrases and their non-definitive wording, and existing clear-change/stable-vocabulary topic checks. QA-venv `test_frontend.py` passed at 1200px and 375px.
- Requirement #18 remains PARTIAL because text alone cannot prove interruption order or semantic topic changes. The engine does not present these lexical cues as acoustic or semantic certainty.

### Follow-up execution checkpoint — October 19, 2026 (local two-voice overlap)

- Extended `test_real_local_stack.py` with a generated Daniel/Samantha speech mix whose voices overlap for the middle of the clip. It uses temporary AIFF/WAV/WebM files only, then calls the production local `/api/transcribe` path with the installed Whisper and speaker models.
- On this MacBook run the 9.53-second mix produced half-window cosine 0.7315, the app returned `Mixed`, and the speaker profile set did not change despite name-learning consent being enabled. The full optional local-stack test passed, including ASR, the new overlap flow, Ollama response, and test-only profile erase.
- Requirements #32 and #41 now pass for controlled synthetic overlap through the real local model/server path. This does not establish human speaker/overlap accuracy or turn separation; the displayed cosine remains an uncalibrated diagnostic.

### Follow-up execution checkpoint — October 19, 2026 (acoustic cue integration)

- The UI now turns server-provided half-window divergence into a source-linked `Possible acoustic overlap` local cue. Its text says the difference may reflect a speaker change or overlap and cannot establish turn order or separate words. It stays local and does not call a cosine score an overlap probability.
- Frontend regressions passed at 1200px/375px for the new cue/source link, text interruption acknowledgment, turn-taking request, repeated wording, topic transition and stable-topic control. The real local-stack synthetic two-voice overlap test passed with the production Mixed veto and no profile learning.
- Requirement #18 advances to PASS for these explicit offline diagnostic cards. Natural semantic interpretation and human conversation usefulness remain unmeasured; the implementation does not claim diarization.

### Follow-up execution checkpoint — October 19, 2026 (resource soak interruption and matched latency)

- The production-handler resource soak was stopped at the user's requested 14-minute point. The interrupt arrived after the final emitted sample at 889.052 seconds (14 minutes 49 seconds), so this is a partial run, not the required 45-minute pass. Its metadata-only JSONL report recorded 88 health/queue samples, 19 successful local transcriptions including warm-up, 3 rate limits and 3 successful retries. Health remained true and the final observed drain queue was empty. These 10-second samples do not establish a sustained memory trend; the previous harness retained 1-second RSS samples only in process memory, which were lost on interrupt.
- The harness now flushes each 1-second aggregate process-tree RSS sample as metadata to the same JSONL report, under a write lock shared with health samples. This makes interrupted runs retain their sampled memory history; it does not upgrade the interrupted run's evidence. No soak was restarted.
- After that harness change, an 8-second production-handler smoke passed: four local transcriptions including warm-up, four health/queue samples, eight durable one-second RSS rows, healthy status and zero queued/in-flight drain at each health sample. The harness reported a 319,840 KiB sampled peak. This validates the recorder path only, not sustained resource stability.
- A matched localhost comparison ran 20 requests per revision against identical generated synthetic speech, alternating order through local Whisper and speaker processing. Baseline `origin/main` (`a74e2b0ca9edbdd6c9e8f9591d0367d5048002bd`) median was 0.526 s and P95 0.543 s; current `d61f4d6d29fa55f005818ff895feaea6d0ae14bd` median was 0.529 s (+0.49%) and P95 0.553 s. Mean synthetic word error rate was 0 for both. The JSON summary is `/var/folders/lm/f_zcrpb94bvg69m2y35klb8r0000gn/T/conversation-lens-latency-1792390134.json`. Scope is localhost transcription turnaround on this MacBook and installed model; it excludes browser input-to-visible-cue timing and natural speech accuracy.
- Remaining acceptance gaps include the uncompleted 45-minute soak and browser-visible cue latency. The natural two-person conversation and acoustic usefulness gates remain distinct from the controlled synthetic overlap test. Physical PCM Stop/drop was exercised; physical Keep-and-transcribe remains inconclusive.

### Follow-up execution checkpoint — October 19, 2026 (speaker pin eligibility)

- Clarified the live speaker-pin control: its count applies to eligible future windows; a Mixed/overlap result remains Mixed and does not consume a pin. Status text also reiterates that the owner-provided label is not an acoustic identity result.
- Expanded `test_frontend.py` at 1200px and 375px to apply a two-window pin across an Unknown result, an intervening Mixed result, and another Unknown result. The two eligible results receive the manual label, Mixed remains Mixed, the count expires after the second eligible result, automatic name learning stays disabled, and a separate five-window pin can be explicitly unpinned. Both browser runs passed.
- This is UI behavior evidence with mocked capture and transcription responses; natural speaker labeling and physical pin interaction remain unmeasured.

### Follow-up execution checkpoint — October 19, 2026 (Stop Keep PCM WAV failure and repair)

- In Brave on the MacBook, an actual AudioWorklet microphone window (6.443 seconds) was held for edit. Stop froze intake and displayed the per-window Keep prompt. Choosing Keep reached the local Stop drain, but the transcript remained empty and the app reported `Audio codec conversion failed`.
- The cause was in production `decode_audio`: an `audio/wav` request was written to the same path FFmpeg used for normalized output. The uploaded PCM was therefore read and overwritten at once. The input is now written as `audio-input.wav`, separate from the normalized `audio.wav` output.
- Added executable coverage in `test_backend.py`: a generated WAV decodes to normalized mono 16 kHz PCM, and the authenticated production HTTP path freezes the capture, authorizes a selected WAV by SHA-256, posts that exact WAV through the local FFmpeg/Whisper route, receives the synthetic expected passage, and preserves the forced-Mixed/name-learning veto. `python3 test_backend.py` passed all cases, including this new Keep route.
- A post-fix physical Keep retest was not completed. The localhost origin's microphone setting was temporarily allowed during the browser attempt, then restored to `Ask`; no capture lease or server remains active. The prior physical result stays a failure of the pre-fix build, not post-fix acceptance. The current test proves the production HTTP path but not a second physical microphone/UI run.

### Repository publication checkpoint — October 19, 2026

- The PCM WAV decoder fix and production Stop Keep regression were committed as `ac5b603f74c9e756ad2f7a0be029b2a4a2d49f93` on `codex/conversation-lens-integration` and pushed normally. `git ls-remote` matched that SHA. No merge to `main` was performed. This checkpoint supersedes the older branch-head values in the historical Phase 0 notes above.

### Follow-up execution checkpoint — October 19, 2026 (speaker timeout and backpressure regressions)

- Requirement #45 now has a forced speaker-worker timeout regression in `test_backend.py`. The test injects `subprocess.TimeoutExpired` only for the speaker worker while leaving the ASR path active, then verifies that transcript text is preserved, identity abstains as `Unknown`, the prior speaker profile is not trained, and an embedding error event is recorded. `python3 test_backend.py` passed.
- Requirement #50 now has `qa_backpressure.py`, an HTTP integration check against the main app handler with a controlled slow transcriber. The first transcription occupies the single STT slot, a concurrent request receives 429, and the same window ID succeeds when retried after capacity frees. The check also asserts the browser queue cap of three and at most two retained retries at the queue head. `python3 qa_backpressure.py` passed.
- These tests use controlled/synthetic transcription. They do not prove real Whisper saturation throughput, browser retry timing under physical capture, or adversarial Stop/drain races. Those acceptance gaps remain open.
- The tested files are not yet published in this checkpoint; the exact Git commit and push state must be recorded after review and publication.

### Follow-up execution checkpoint — October 19, 2026 (end-to-end cue latency and Stop races)

- Added `qa_browser_cue_latency.py` for local Brave end-to-end timing. It launches the real app server and installed local models, replays generated speech through Brave's file-backed virtual microphone, and opens a fresh browser process for each of three trials. Each trial confirms visible transcript, visible local cue, browser error absence, and Stop returning to `NOT LISTENING`; the report contains timings/counts, not transcript text or audio.
- Three generated-speech trials passed. Start-button-to-visible transcript was 7,139–7,521 ms (median 7,404 ms; nearest-rank P95 7,521 ms); start-button-to-visible local cue was 7,263–7,638 ms (median 7,524 ms; nearest-rank P95 7,638 ms). With only three trials, P95 equals the maximum and is not a stable population estimate. Timing begins at the Start button, not a physical acoustic-onset timestamp. This measures the complete generated virtual-microphone-to-visible app path on this MacBook; it does not establish physical-mic latency or natural-speech accuracy.
- Added `qa_stop_race.py` covering four deterministic loopback HTTP races through the production handler/transcription path. `python3 qa_stop_race.py` passed: Stop freeze after live admission discards the late result; upload after freeze is rejected before transcription; closing an in-flight exact-hash Keep drain discards its late result; and a stale Keep lease cannot affect a replacement capture. Synthetic Whisper output and a barrier inside speaker extraction are used; all instruction-level timing interleavings, physical Brave input, and edited-audio UI races remain outside this test.
- The earlier checkpoint records the passing #45 speaker-timeout test and #50 saturation/backpressure test. Together these add focused evidence for those failure paths but do not close natural two-speaker/human acceptance, the explicitly stopped 45-minute soak, physical post-fix Keep, or device-specific acoustic tuning.
- The new latency and Stop-race harnesses are not yet published at this checkpoint; record their Git state after review/publication.

### Follow-up execution checkpoint — October 19, 2026 (cross-cutting regression and physical permission attempt)

- Ran the current cross-cutting suites from the repository root: `python3 test_backend.py`, `python3 test_regressions.py`, `python3 test_live_upgrade.py`, QA-venv `test_frontend.py`, QA-venv `test_e2e.py`, and `python3 test_real_local_stack.py`. All passed. Frontend and E2E covered Brave/Chromium desktop (1200px) and mobile-width (375px) flows; the real local stack passed generated local ASR, synthetic overlap/Mixed veto/no-learning, and the opted-in local Ollama route. These tests do not prove human voice accuracy or actual microphone input.
- Attempted a post-fix physical Brave microphone Keep retest on a fresh local server. PCM mode, edit hold and consent were selected; pressing Start left the page at `REQUESTING MIC`, with the capture lease inactive. Stop returned the UI to `NOT LISTENING` and reported no server lease. The local origin's microphone setting remained `Ask` (no persistent permission change); no audio reached transcription. The test server was stopped and `curl` confirmed the port no longer accepted connections. This is BLOCKED/NOT VERIFIED physical acceptance, not a Keep pass.
- No 45-minute soak was restarted; the earlier user-directed stop at 14:49 remains partial. Natural two-speaker/overlap evaluation still requires a consenting second speaker and human review.

### Follow-up execution checkpoint — October 19, 2026 (physical microphone Stop Keep passes)

- Added repeatable opt-in acceptance harness `qa_physical_keep.py` and documented it in `README.md`. The command requires `--confirm-local-mic-test`, launches an isolated Brave automation context, grants microphone permission only to that temporary browser context, and deliberately omits the fake-device flag. It plays one locally generated phrase through the Mac speakers, holds the captured PCM window, exercises Stop and the per-window Keep decision, and erases the test session before closing the temporary server.
- On this MacBook, the reported default input was `MacBook Air Microphone (Built-in)`. The physical input meter peaked at 100; one PCM window was held and kept; all seven checked phrase terms were recognized; Stop returned to `NOT LISTENING`; the transcript/session was erased; and the browser reported no page errors. `qa_physical_keep.py --confirm-local-mic-test` passed.
- This closes the post-fix physical generated-speech Keep path for requirements #9 and #51. It is not natural speech accuracy evidence, and does not validate real speaker identity, human overlap, or acoustic usefulness. Requirement #41 remains synthetic-overlap-only pending consenting human participants. The 45-minute soak remains partial and was not restarted.

### Follow-up execution checkpoint — October 19, 2026 (Omni Zero-Loss UX Transformation 01–20 & Completions A–F)

- Implemented all 20 UX improvements and supporting Completions A–F in `Conversation_Lens_Intelligent_Speaker_v6/Conversation_Lens_Live.html` without removing or degrading any existing v6 capability or backend contract:
  - **01 Protected demo loading:** `#sampleBtn` loads immediately on an empty idle session, requires explicit confirmation when `state.turns.length > 0` or `state.wantsListen` is active, and preserves the existing transcript when canceled.
  - **02 Follow live without scroll hijacking:** Added `#followLiveBar`, `#followLiveBtn` (`aria-pressed`), `#followLiveStatus`, and `#returnToLiveBtn` with `ui.programmaticScroll` protection so DOM re-renders and inline edits preserve scroll position while manual upward scrolling pauses auto-follow and counts unseen newer passages.
  - **03 & 14 Persistent coaching rail & freshness/staleness:** Added `#cueSourceBadge` (`Local rule` vs `Big Mac AI`), `#cueFreshnessBadge` (`Current` vs `Stale · covers X/Y (+N newer)`), `#cueEvidenceBar` with `#heroEvidenceBtn`, and `#aiFreshnessBadge` (`STALE` when newer turns arrive after an AI observation).
  - **04 Centralized capture control & status bar:** Added `#headerStopBtn` in the top bar (visible whenever capture is active) and `#sessionStatusBar` with distinct `#micStateBadge`, `#coachingStateBadge`, `#readinessSummaryBadge`, and `#topQueueBadge` so recording state and coaching state are never visually confused.
  - **05 Four-scope data deletion semantics:** Explicitly separated Clear transcript only (`#clearBtn`), Forget one speaker (`Remove` per profile), Forget all voice profiles (`#forgetBtn` / `#forgetProfilesQuickBtn`), and Erase entire session (`#eraseAllBtn`) with a visual `.deletion-matrix` scope summary.
  - **06 Chronological transcript gaps for lost audio:** Skipped/dropped recording windows record in-memory gap metadata (`state.gaps` with `afterTurnId`, `count`, `reason`, `time`) and render `.transcript-gap` markers in chronological position explaining that speech during the gap was not transcribed and no words were invented.
  - **07, 13, 15, 19 Task-centered workspace, progressive disclosure & responsive priority:** Added `#workspaceNav` quick-jump bar, grouped advanced VAD/PCM/diagnostics/profile-portability/snapshot controls into native `<details class="adv-drawer">` disclosures while keeping all element IDs intact in the DOM, and ordered mobile panels (`<=810px`) as Capture -> Pinned Cue -> Transcript -> Local Cues -> AI -> Speakers -> Setup -> Anchor.
  - **08 & 09 Speaker uncertainty badges & scoped bulk correction:** Added explicit `.who-badge` provenance pills (`Manual assignment`, `Pinned label · unverified`, `Tentative acoustic match`, `Provisional intro · unverified`, `Unknown voice · abstained`, `Overlap / Mixed · abstained`, `Unassigned fallback`) and per-passage `.turn-bulk-check` selection with `#bulkCorrectionBar` (`#bulkSpeakerSelect`, `#bulkApplySpeakerBtn`, `#bulkSelectAllBtn`, `#bulkClearSelectionBtn`) that updates only selected passages without mutating voiceprints.
  - **10 Two-sample voice enrollment progress stepper:** Added `#enrollStepper` (`#enrollTargetLabel`, `#enrollStageBadge`, `#enrollStep1`, `#enrollStep2`, `#enrollStageDetail`) showing `0 of 2 samples`, `1 of 2 samples · needs 2nd`, `Ready · 2/2 samples`, `Canceled`, and `Retry needed` states alongside the live signal/clipping meter.
  - **11 Immediate Goal & Language controls:** Added top-bar `#quickAim` and `#quickLanguage` selects synchronized bidirectionally with `#aim` and `#language`.
  - **12 Evidence inspector return navigation:** Added `#evidenceMeta`, `#evidenceJumpBtn`, `#evidenceReturnScrollBtn` (restoring `ui.priorScrollTop`), and `#evidenceReturnCueBtn` (returning focus to `#heroEvidenceBtn` / `#getCueBtn`), plus `Escape` key dismissal.
  - **16 Contextual engine recovery banner:** Added `#engineRecoveryBanner` with contextual recovery actions (`#recoveryRetryServerBtn`, `#recoveryRetryMicBtn`, `#recoveryTakeoverBtn` for 409 second-tab lease conflicts, and `#recoveryManualBtn`).
  - **17 & Completion D Keyboard shortcut reference & Quiet density mode:** Added `#shortcutHelpBtn` and `<dialog id="shortcutDialog">` (`?`), expanded single-key shortcuts (`F` follow live, `S` focus speaker select, `W` correct words, `T` focus manual input, `L` focus start/stop, `?` shortcut help), and added `#densityMode` (`html[data-density="quiet"]`).
  - **18 & Completion F Long-session capacity management & Session Review Summary:** Added `#capacityBanner` warning at `>=240` passages and rotation notice at `>300` passages (`state.evictedTurnsCount`) with `.transcript-retention-marker`, plus `#sessionReviewSummary` displaying live passage/gap counts, speaker attribution overview, bookmarked/highlighted passages, and coaching/action counts with one-click copy/export/erase actions.
  - **Acoustic & Linguistic Observatory Strip, Desktop Visual Hierarchy & Adversarial Defect Repairs:** Added `#observatoryStrip` (`#obsCadenceValue`, `#obsCertaintyValue`, `#obsSignalsValue`, and interactive `#obsTurnRibbon` passage nodes that jump directly to evidence) to expose live structural telemetry (speaker shifts, tentative vs. provisional/manual vs. abstained attribution counts, questions/commitments/grounded cues) without fabricating probabilities. Ordered desktop (`>810px`) columns around the active conversation (`#listenPanel -> #transcriptPanel -> #speakerPanel -> #setupPanel` on the left; `#heroCuePanel -> #signalPanel -> #aiPanel -> #anchorPanel` on the right) and refined the collapsed mobile coaching sheet (`data-collapsed="true"`) to hide secondary rows without internal scrollbars. Removed a duplicate `click` listener on `#voiceNoteBtn` that could race two `getUserMedia` calls on direct button click, and added a `ui.programmaticScroll` guard around scroll restoration in `closeEvidenceAndRestore`.
- Updated `Conversation_Lens_Intelligent_Speaker_v6/QA_REPORT.txt` to document the public GitHub repository visibility readback (`"private": false, "visibility": "public"`) and full verification results.
- Full verification suite passed with zero errors: `test_backend.py`, `test_regressions.py`, `test_live_upgrade.py`, `qa_backpressure.py`, `qa_stop_race.py`, `test_frontend.py` (at `1200px`, `375px`, `1440px`, `810px`), `test_e2e.py` (`1200px`, `375px`), `test_real_local_stack.py`, `node --check`, `py_compile`, `zsh -n`, and `git diff --check`. Committed and pushed to `origin/codex/conversation-lens-integration`.
