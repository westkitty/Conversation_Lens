#!/usr/bin/env python3
"""One-shot local speaker embeddings; emits JSON to stdout only. No audio or profile persistence."""
import array
import json
import math
import sys
import wave
from pathlib import Path


def run(model_path, wav_path):
    import numpy as np
    import sherpa_onnx

    with wave.open(str(wav_path), "rb") as handle:
        if handle.getnchannels() != 1 or handle.getframerate() != 16000 or handle.getsampwidth() != 2:
            raise ValueError("Expected 16 kHz mono PCM16")
        samples = np.frombuffer(handle.readframes(handle.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    if samples.size < 24000 or samples.size > 16000 * 11:
        raise ValueError("Clip must have 1.5 to 11 seconds of audio")

    config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(model_path), num_threads=1, provider="cpu", debug=False)
    if not config.validate():
        raise RuntimeError("Invalid local speaker model")
    extractor = sherpa_onnx.SpeakerEmbeddingExtractor(config)

    def embed(segment):
        if len(segment) < 16000 * 1.8 or float(np.sqrt(np.mean(segment * segment))) < 0.0045:
            return None
        stream = extractor.create_stream()
        stream.accept_waveform(sample_rate=16000, waveform=np.ascontiguousarray(segment))
        stream.input_finished()
        if not extractor.is_ready(stream):
            return None
        vec = np.asarray(extractor.compute(stream), dtype=np.float64)
        mag = float(np.linalg.norm(vec))
        if not np.all(np.isfinite(vec)) or mag < 1e-6:
            return None
        return (vec / mag).round(7).tolist()

    # A 6.5-second window containing only "This is Dale" may have too little voiced
    # sound to support a biometric comparison. Surface this quality limit to the UI.
    hop = 320  # 20ms at 16kHz
    usable = samples[: (len(samples) // hop) * hop]
    frames = usable.reshape(-1, hop) if len(usable) >= hop else np.empty((0, hop))
    rms = np.sqrt(np.mean(frames * frames, axis=1)) if len(frames) else np.array([])
    voice_seconds = float(np.sum(rms > 0.0075) * 0.02)
    length = len(samples)
    half = length // 2
    out = {"full": embed(samples), "first": None, "second": None,
           "speech_seconds": round(voice_seconds, 2)}
    if length >= 16000 * 5.0:
        out["first"] = embed(samples[:half])
        out["second"] = embed(samples[half:])
    print(json.dumps(out, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Expected model and WAV path"}))
        raise SystemExit(2)
    try:
        run(Path(sys.argv[1]), Path(sys.argv[2]))
    except Exception as exc:
        # Avoid file paths, data or diagnostic traces in user-facing responses.
        print(json.dumps({"error": str(exc)[:130]}), flush=True)
        raise SystemExit(1)
