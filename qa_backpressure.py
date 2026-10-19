"""Exercise main-app STT saturation and verify its bounded 429 retry contract.

This is an HTTP integration smoke with synthetic audio and a controlled slow
transcriber. It does not invoke the microphone or Whisper model.
"""
from pathlib import Path
import importlib.util
import json
import threading
import time
import urllib.error
import urllib.request
import http.server


ROOT = Path(__file__).resolve().parent
APP = ROOT / "Conversation_Lens_Intelligent_Speaker_v6"
spec = importlib.util.spec_from_file_location("lens_backpressure", APP / "server.py")
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def request(origin, path, body=None, headers=None, method=None):
    data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
    req = urllib.request.Request(origin + path, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as error:
        payload = error.read()
        return error.code, json.loads(payload) if payload else {}


entered = threading.Event()
release = threading.Event()
original_transcribe = s.transcribe_audio


def controlled_transcribe(*args, **kwargs):
    entered.set()
    if not release.wait(4):
        raise RuntimeError("controlled transcriber timed out")
    return {"text": "synthetic recovered window", "engine": "test", "speaker": {"label": "Unknown"}}


with http.server.ThreadingHTTPServer(("127.0.0.1", 0), s.Handler) as server:
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = "http://127.0.0.1:%d" % server.server_port
    common = {
        "Origin": origin,
        "X-Lens-Token": s.APP_TOKEN,
        "X-Lens-Protocol": str(s.PROTOCOL_VERSION),
        "Content-Type": "application/json",
    }
    code, opened = request(origin, "/api/capture/open", {"consent": True, "owner": "qa-backpressure"}, common, "POST")
    assert code == 200, (code, opened)
    audio = b"RIFF" + b"S" * 1196
    audio_headers = {
        "Origin": origin,
        "X-Lens-Token": s.APP_TOKEN,
        "X-Lens-Protocol": str(s.PROTOCOL_VERSION),
        "X-Lens-Capture-Session": opened["capture"],
        "X-Lens-Language": "en",
        "Content-Type": "audio/wav",
    }
    first_done = {}

    def first_request():
        first_done["result"] = request(
            origin, "/api/transcribe", audio,
            {**audio_headers, "X-Lens-Window-ID": "slow-window"}, "POST")

    s.transcribe_audio = controlled_transcribe
    worker = threading.Thread(target=first_request, daemon=True)
    worker.start()
    try:
        assert entered.wait(3), "first request never entered the controlled transcriber"
        busy_code, busy_body = request(
            origin, "/api/transcribe", audio,
            {**audio_headers, "X-Lens-Window-ID": "retry-window"}, "POST")
        assert busy_code == 429 and "busy" in busy_body.get("error", "").lower(), (busy_code, busy_body)
        release.set()
        worker.join(4)
        assert not worker.is_alive(), "first transcription did not finish"
        assert first_done["result"][0] == 200, first_done
        retry_code, retry_body = request(
            origin, "/api/transcribe", audio,
            {**audio_headers, "X-Lens-Window-ID": "retry-window"}, "POST")
        assert retry_code == 200 and retry_body["text"] == "synthetic recovered window", (retry_code, retry_body)
    finally:
        release.set()
        worker.join(4)
        s.transcribe_audio = original_transcribe
        request(origin, "/api/capture/close", {"capture": opened["capture"]}, common, "POST")
        server.shutdown()
        thread.join(5)

html = (APP / "Conversation_Lens_Live.html").read_text()
assert "if(stt.queue.length>=3){skipWindow(stt.queue.shift(),'Transcription backlog')" in html, "main app queue must cap pending windows at three"
assert "if(rsp.status===429&&(item.retries||0)<2)" in html, "main app retry count must remain bounded"
assert "stt.queue.unshift(item);await new Promise(resolve=>setTimeout(resolve,700*item.retries))" in html, "429 retry must retain the same window at the queue head"
assert "X-Lens-Window-ID':item.id" in html, "retry must preserve the window identity"
print("PASS main-app STT lock rejects saturated request with 429; same window succeeds on retry after capacity frees")
print("PASS main-app queue caps pending work at three and retains at most two delayed retries with the original window ID")
