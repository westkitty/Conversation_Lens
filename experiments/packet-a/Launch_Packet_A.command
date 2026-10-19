#!/bin/zsh
# Isolated Packet A launcher: never changes the installed Conversation Lens checkout.
set -euo pipefail
cd -- "$(dirname -- "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
MODEL="$HOME/Library/Application Support/DexDictate/Models/ggml-base.bin"
args=(--port 0 --open-brave)
if command -v whisper-cli >/dev/null 2>&1 && [ -s "$MODEL" ]; then
  args+=(--whisper-cli "$(command -v whisper-cli)" --model "$MODEL")
  echo 'Using installed local Whisper.cpp and existing read-only DexDictate model.'
else
  echo 'Whisper not found. Audio editing + server verification will work; no transcript text will be generated.'
fi
exec /usr/bin/python3 -u ./packet_a_server.py "${args[@]}"
