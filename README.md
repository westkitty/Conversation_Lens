# Conversation Lens v6 — Adaptive Speaker Edition

Local-first, experimental live conversation observation and coaching for macOS. **New sessions are context-agnostic by default**: no topic, prior situation, relationship, or named participants are preloaded. Add optional context only when you want to. Brave records audio with consent; the MacBook transcribes locally through Whisper; the speaker-embedding worker attempts session-scoped speaker identification; optional AI coaching runs on a private Big Mac Ollama tunnel.

## Setup

See [`Conversation_Lens_Intelligent_Speaker_v6/README.txt`](Conversation_Lens_Intelligent_Speaker_v6/README.txt) for the exact launch command, requirements, privacy contract, and limitations.

From this repository root:

```bash
/bin/zsh ./Conversation_Lens_Intelligent_Speaker_v6/Launch_Conversation_Lens.command
```

## Tests

Python backend and interaction regression scripts are included at the repository root. The browser tests require Playwright and an installed Chromium browser; the backend tests exercise local HTTP/FFmpeg with synthetic or stubbed speech models. These tests **do not** certify multi-person voice-identification accuracy.

## Privacy and security

This repository is **private**. The current app ships with an empty optional context field and a neutral default observation mode. Erase all session data also clears the optional context and reverts the goal and speaker selection. **Earlier Git history may still contain a previous private scenario**, so do not make the repository public without separately reviewing and, if explicitly authorized, cleaning its history. Do not commit voice recordings, session transcript exports, audio models, runtime tokens, or voiceprints. The local server is intended to bind to 127.0.0.1 only. All participants must consent to live transcription and speaker identification.

Speaker self-introductions are provisional name claims, not identity verification. Overlapping speech and similar voices can be mislabeled. Do not use this app for monitoring non-consenting speakers or to establish facts about a person.

## Status

v6 source package plus test scripts. Browser and backend tests have passed in simulated environments. Physical microphone, real multi-speaker accuracy and production deployment remain to be validated.
