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
