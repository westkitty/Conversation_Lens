# Conversation Lens v6 — Adaptive Speaker Edition

Local-first, experimental live conversation observation and coaching for macOS. **New sessions are context-agnostic by default**: no topic, prior situation, relationship, or named participants are preloaded. Add optional context only when you want to. Brave records audio with consent; the MacBook transcribes locally through Whisper; the speaker-embedding worker attempts session-scoped speaker identification; optional AI coaching runs on a private Big Mac Ollama tunnel.

## Setup

See [`Conversation_Lens_Intelligent_Speaker_v6/README.txt`](Conversation_Lens_Intelligent_Speaker_v6/README.txt) for the exact launch command, requirements, privacy contract, and limitations.

From this repository root:

```bash
/bin/zsh ./Conversation_Lens_Intelligent_Speaker_v6/Launch_Conversation_Lens.command
```

## Improvements in the latest source

- **Explicit analysis permission:** the local AI/Big Mac option starts OFF. A user must enable it before transcript text or optional context is sent over the existing local tunnel; raw audio and voiceprints never leave the MacBook in this workflow.
- **Correctable words:** edit any recorded passage and regenerate cues without discarding other passages.
- **Source navigation:** grounded local cue cards and AI evidence point to the exact captured passage when one exists.
- **Capture ownership:** a second tab must request takeover rather than silently replacing the recording lease. Stop revokes capture.
- **Voice enrollment safeguards:** the identical recording cannot count as a second sample or be registered under another name. Similar human voices remain unverified.
- **Visible audio backlog:** see outstanding windows and whether windows were skipped due to transcription lag.
- **Mobile-first reading order:** setup and listening precede cues; DOM order changes with viewport to preserve keyboard navigation.
- **No browser speech fallback:** when local Whisper is unavailable, transcription falls back to manual text input, NOT a remote browser speech provider.

## Tests

Run on the MacBook from this repository root using the following separate commands:

    python3 test_backend.py
    python3 test_regressions.py
    "$HOME/Library/Application Support/ConversationLensQA/venv/bin/python" test_frontend.py
    "$HOME/Library/Application Support/ConversationLensQA/venv/bin/python" test_e2e.py
    python3 test_real_local_stack.py

The two browser tests require **Playwright plus an installed Brave (macOS) or Chromium (Linux)**; the QA venv is optional and may be replaced by another Python environment with playwright installed. The real-stack test uses synthesized speech and installed local models, not a physical microphone or actual conversations. Unit and integration tests **do not** certify human multi-speaker voice accuracy. For exact evidence see Conversation_Lens_Intelligent_Speaker_v6/QA_REPORT.txt.

## Privacy and security

This repository is **private**. The current app ships with an empty optional context field and a neutral default observation mode. Erase all session data also clears the optional context and reverts the goal and speaker selection. **Earlier Git history may still contain a previous private scenario**, so do not make the repository public without separately reviewing and, if explicitly authorized, cleaning its history. Do not commit voice recordings, session transcript exports, audio models, runtime tokens, or voiceprints. The local server is intended to bind to 127.0.0.1 only. All participants must consent to live transcription and speaker identification.

Speaker self-introductions are provisional name claims, not identity verification. Overlapping speech and similar voices can be mislabeled. Do not use this app for monitoring non-consenting speakers or to establish facts about a person.

## Status

v6 browser UX, local HTTP/FFmpeg tests, speaker-safety regressions, and a synthetic-speech test of the actual Whisper/speaker/Big Mac stack have been run on the MacBook. The complete Brave + physical microphone + two consenting real speakers flow and speaker accuracy remain unverified.
