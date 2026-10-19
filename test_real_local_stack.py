#!/usr/bin/env python3
"""Optional macOS smoke: real FFmpeg, Whisper, speaker model and Big Mac with SYNTHETIC speech.

Runs only against localhost with a fresh test-only server. Does not touch the microphone,
store recordings, or validate human speaker identity. Skips if required models are absent.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = pathlib.Path(__file__).parent / "Conversation_Lens_Intelligent_Speaker_v6"
spec = importlib.util.spec_from_file_location("lens_live_smoke", ROOT / "server.py")
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def call(url, body=None, headers=None):
    req = urllib.request.Request(
        url, data=body, headers=headers or {}, method="POST" if body is not None else "GET"
    )
    with urllib.request.urlopen(req, timeout=55) as response:
        return response.status, json.load(response)


def main():
    if sys.platform != "darwin":
        print("SKIP: optional full-stack smoke runs on the macOS target")
        return
    if not s.whisper_status()["ready"] or not s.speaker_status()["ready"]:
        print("SKIP: Whisper or speaker embedding model not provisioned")
        return

    with tempfile.TemporaryDirectory(prefix="lens-real-model-smoke-") as tmp:
        tmp = pathlib.Path(tmp)
        audio = tmp / "spoken.aiff"
        webm = tmp / "speech.webm"
        words = (
            "Hello, this is Dale, and I would like to review the testing plan today. "
            "The next meeting will be on Thursday, after we have checked the remaining issues."
        )
        subprocess.run(["/usr/bin/say", "-v", "Alex", "-r", "178", words, "-o", str(audio)],
                       check=True, timeout=18)
        subprocess.run([str(s.FFMPEG_BIN), "-nostdin", "-loglevel", "error", "-y",
                        "-i", str(audio), "-t", "8", "-c:a", "libopus", "-b:a", "32k",
                        str(webm)], check=True, timeout=15)
        payload = webm.read_bytes()
        app = ThreadingHTTPServer(("127.0.0.1", 0), s.Handler)
        runner = threading.Thread(target=app.serve_forever, daemon=True)
        runner.start()
        base = "http://127.0.0.1:" + str(app.server_address[1])
        try:
            _, status = call(base + "/api/status")
            headers = {"X-Lens-Token": status["token"], "Origin": base}
            _, opened = call(base + "/api/capture/open", b'{"consent":true}',
                             {**headers, "Content-Type": "application/json"})
            lease = opened["capture"]
            t0 = time.monotonic()
            code, speech = call(base + "/api/transcribe", payload,
                                 {**headers, "Content-Type": "audio/webm",
                                  "X-Lens-Capture-Session": lease,
                                  "X-Lens-Voice-Consent": "confirmed",
                                  "X-Lens-Auto-Names": "enabled",
                                  "X-Lens-Language": "en"})
            elapsed = time.monotonic() - t0
            assert code == 200 and len(speech.get("text", "")) > 18, speech
            assert speech.get("engine") == "whisper-cpp"
            print("REAL_ASR_PASS: %.2fs, %d chars, label=%s" %
                  (elapsed, len(speech["text"]), speech["speaker"]["label"]))
            _, stopped = call(base + "/api/capture/close",
                               json.dumps({"capture": lease}).encode(),
                               {**headers, "Content-Type": "application/json"})
            assert stopped["closed"]
            if s.ollama_status()["ready"]:
                t1 = time.monotonic()
                result = s.call_ollama({"goal": "Observe neutrally",
                     "turns": [{"speaker": "Unassigned", "text": speech["text"]}]})
                assert result["observation"] and result["next_step"], result
                print("REAL_OLLAMA_PASS: %.2fs, evidence=%s" %
                      (time.monotonic() - t1, result["evidence"][:80]))
            else:
                print("REAL_OLLAMA_SKIP: Big Mac model not available")
            _, erased = call(base + "/api/session/erase", b'{"confirm":true}',
                             {**headers, "Content-Type": "application/json"})
            assert erased["erased"] and not s.SPEAKERS and not s.SPEAKER_META
            print("REAL_LOCAL_STACK_PASS: test-only voice profiles erased")
        finally:
            app.shutdown()
            app.server_close()


if __name__ == "__main__":
    main()
