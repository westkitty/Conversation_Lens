# Conversation Lens — Packet A / Connected Stop Workbench

**Scope:** isolated next-phase implementation for `westkitty/Conversation_Lens`. This is an independently runnable lab, **not** an installation into your newer uncommitted MacBook checkout. No files from your installed v6 are replaced. GitHub `main` was still on baseline `a74e2b0` during the previous checkout review; do not use it as a substitute for the uncommitted worktree.

## What actually works

- 16 kHz mono PCM capture via an AudioWorklet when Brave has microphone access, with a bounded 45-second in-memory ring. A deterministic synthetic fixture is also available.
- Sample-indexed waveform edits: split, adjacent merge, drag a shared boundary, preview, and 0–500 ms pre/post-roll. A 10-second WAV cap and byte-exact RIFF output are enforced. Edited or mixed windows have a one-way automatic speaker-learning veto.
- A **connected** Stop: halt microphone first, freeze the localhost capture lease, select **at most four** exact buffered WAV windows, authorize their SHA-256 hashes on the server under a **new drain-only lease**, transmit only selected clips, and display actual server responses.
- Drop All closes the frozen lease without uploading clips. Dismissing the Stop dialog leaves the session frozen; returning to Stop restores the checkbox decisions.
- Server-side one-use authorization, duplicate/replay rejection, stale-result revocation, 90-second frozen lease TTL, 120-second drain lease TTL, bounded retry on 429 without consuming the permitted WAV, and truthful failed-close status.
- No automatic speaker profile updates or transcript persistence. The prototype server only performs optional local Whisper.cpp transcription; it does not implement the rest of the Conversation Lens coaching UI.

**Important distinction:** Without an installed Whisper model selected on startup, the server validates WAV format, frame count, authorization, and arrival. It returns `engine: "audio-validation-only"` with `text: null`. The UI explicitly reports that **no transcript was generated**. Neither a successful upload nor this test harness validates live conversation accuracy.

## Run on macOS in Brave

1. Extract this archive into a new directory. Do **not** unzip into an existing Conversation Lens checkout.
2. From the extracted folder, launch `Launch_Packet_A.command`, or run:

   ```bash
   /bin/zsh ./Launch_Packet_A.command
   ```

3. The launcher selects an ephemeral localhost port and opens Brave. It uses the already-installed DexDictate `ggml-base.bin` and `whisper-cli` **read-only** when both are present. Otherwise, it runs in validation-only mode.
4. Choose **Create 8s synthetic sample** for a safe functional check. Split or move boundaries, click **Stop / choose windows**, uncheck one window, then **Finish selected windows**. The result panel must show only kept clip IDs; Drop All must show no server results.
5. To use a microphone, choose **Start local microphone** and grant Brave microphone access. The audio pipeline uses AudioWorklet, not MediaRecorder WebM fragments. Real microphone handling still requires acceptance testing on the MacBook.

If you prefer to specify an exact installed model instead of launcher detection:

```bash
python3 packet_a_server.py --port 0 --open-brave --whisper-cli /opt/homebrew/bin/whisper-cli --model "$HOME/Library/Application Support/DexDictate/Models/ggml-base.bin"
```

**No Docker, Node runtime, npm packages, third-party Python packages, or network service is required to run the basic server.** Node and Python Playwright are only used for test execution.

## Run tests

From the extracted folder:

```bash
node --test tests/test_pcm_core.cjs tests/test_stop_client.cjs tests/test_packet_a_transport.cjs
python3 -m unittest discover -s tests -p 'test_stop_drain.py' -v
python3 -m unittest discover -s tests -p 'test_packet_a_server.py' -v
```

Additional browser QA requires Python `playwright` and a local Brave/Chromium executable:

```bash
python3 tests/test_browser_workbench_inline.py
python3 tests/test_packet_a_browser_bridge.py
```

The **bridged** browser test exists because this hosted QA runtime forbids direct Chromium navigation to localhost. It loads the exact connected UI in Chromium and forwards its API requests to the actual Python localhost server through a test-only Playwright binding; the SHA-256 operation is similarly bridged because `about:blank` lacks secure-origin SubtleCrypto. This covers the browser/HTTP contract, but not direct real Brave microphone and audio model operation. The standalone tests verify deterministic PCM byte invariants and stop/drain races without a browser.

## Integration requirements — not yet done

The current MacBook v6 code must be re-read when the machine is reachable. Preserve all uncommitted UI/backend upgrades. Only then adapt the existing transcription queue to accept this PCM/Stop protocol behind a feature gate, retain a tested fallback recording path, link server-returned transcriptions into the speaker/evidence/coaching rails, and rerun the actual v6 baseline and new regressions on the physical MacBook.

Do **not** replace `Conversation_Lens_Intelligent_Speaker_v6/server.py` with `packet_a_server.py`: the latter is a deliberately narrow development host, not the full Whisper/speaker/Ollama application. Speaker embeddings and coaching are intentionally absent from Packet A.

## Verified versus unverified

- **Verified:** deterministic PCM edits, canonical 16 kHz WAV rendering, exact SHA-256 authorization, selective Keep/Drop, no-upload Drop All, queue/stale nonce behavior, server retry and lease revocation, desktop/mobile Chromium simulated UI and real Python HTTP transactions through the test bridge.
- **Not verified:** genuine Brave microphone/AudioWorklet lifecycle on the owner's hardware; speaker accuracy in natural or overlapping conversation; true transcription with the MacBook's actual installed Whisper model on *this* build; performance gains versus v6; joining this module to the uncommitted production checkout.

Use `127.0.0.1` locally, keep the terminal server running during use, and stop it with Control-C when finished. PCM, lease tokens and capture jobs are process memory, not a persistent speaker archive.
