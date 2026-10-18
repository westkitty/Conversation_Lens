#!/bin/zsh
# Conversation Lens v6: Brave + silence-guided Whisper + session-only voice recognition.
set -euo pipefail
cd -- "$(dirname -- "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v whisper-cli >/dev/null 2>&1; then
  echo 'Whisper or ffmpeg is missing. The working v3 setup is required.'
  exit 1
fi
if [ ! -s "$HOME/Library/Application Support/DexDictate/Models/ggml-base.bin" ]; then
  echo 'The local Whisper model from DexDictate is not available.'
  exit 1
fi
if [ ! -d '/Applications/Brave Browser.app' ]; then
  echo 'Brave Browser is required at /Applications/Brave Browser.app'
  exit 1
fi
/bin/zsh ./Setup_Speakers.command
exec /usr/bin/python3 -u ./server.py
