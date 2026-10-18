#!/bin/zsh
# One-time, isolated ONNX speaker-recognition setup; no changes to DexDictate.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ROOT="$HOME/Library/Application Support/ConversationLensSpeakerID"
MODEL="$ROOT/wespeaker_en_voxceleb_resnet34.onnx"
PY="$ROOT/venv/bin/python"
URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/wespeaker_en_voxceleb_resnet34.onnx"
SHA="5ef208a9da1453335308a6b6f4e6dfbd7e183a38b604de0a57664f45d257fe94"
if [ ! -x /opt/homebrew/bin/python3.13 ]; then
  echo 'Requires Homebrew Python 3.13 (verified on the original MacBook).'
  echo 'You can install it separately with: brew install python@3.13'
  exit 1
fi
mkdir -p "$ROOT"
if [ ! -x "$PY" ]; then
  echo 'Creating an isolated Python environment for speaker recognition…'
  /opt/homebrew/bin/python3.13 -m venv "$ROOT/venv"
fi
if ! "$PY" -c 'import sherpa_onnx,numpy' >/dev/null 2>&1; then
  echo 'Installing local speaker embedding engine (sherpa-onnx, NumPy)…'
  "$PY" -m pip install --disable-pip-version-check 'sherpa-onnx==1.13.8' 'numpy>=2.2,<3'
fi
if [ ! -s "$MODEL" ]; then
  echo 'Downloading the 25 MiB public speaker embedding model (one time)…'
  /usr/bin/curl -fL --retry 2 --connect-timeout 8 --max-time 120 -o "$MODEL.part" "$URL"
  /bin/mv "$MODEL.part" "$MODEL"
fi
ACTUAL=$(/usr/bin/shasum -a 256 "$MODEL" | /usr/bin/cut -c 1-64)
if [ "$ACTUAL" != "$SHA" ]; then
  echo 'Voice model checksum mismatch. Refusing to run. Remove the incorrect model only after inspecting it.'
  exit 1
fi
"$PY" -c 'import os,sherpa_onnx as s;c=s.SpeakerEmbeddingExtractorConfig(model=os.path.expanduser("~/Library/Application Support/ConversationLensSpeakerID/wespeaker_en_voxceleb_resnet34.onnx"),num_threads=1,provider="cpu");assert c.validate();e=s.SpeakerEmbeddingExtractor(c);assert e.dim==256;print("Local speaker model OK (256-dimensional embeddings).")'
