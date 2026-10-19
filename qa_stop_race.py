"""Adversarial loopback checks for Stop revocation vs in-flight transcript replies.

Uses the production HTTP handler and capture coordinator, while replacing only
the expensive ASR function with a barrier-controlled synthetic worker.
"""
import hashlib
import http.server
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import urllib.error
import urllib.request

APP = Path(__file__).parent / 'Conversation_Lens_Intelligent_Speaker_v6' / 'server.py'
spec = importlib.util.spec_from_file_location('lens_stop_race_qa', APP)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def post(base, path, payload, capture=None, window=None):
    headers = {'Origin': base, 'X-Lens-Token': s.APP_TOKEN,
               'X-Lens-Protocol': str(s.PROTOCOL_VERSION)}
    if isinstance(payload, bytes):
        headers['Content-Type'] = 'audio/webm'
        headers['X-Lens-Capture-Session'] = capture or ''
        headers['X-Lens-Window-ID'] = window or 'race_window'
        headers['X-Lens-Language'] = 'en'
        headers['X-Lens-Voice-Consent'] = 'confirmed'
        headers['X-Lens-Auto-Names'] = 'enabled'
        method_body = payload
    else:
        headers['Content-Type'] = 'application/json'
        method_body = json.dumps(payload).encode()
    request = urllib.request.Request(base + path, data=method_body,
                                     headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def wait(event, name):
    assert event.wait(4), f'timed out waiting for {name}'


payload = b'RIFF' + b'R' * 1400
entered = threading.Event()
resume = threading.Event()
original_transcribe = s.transcribe_audio
original_decode = s.decode_audio
original_is_speech = s.is_speech
original_speaker_vectors = s.speaker_vectors
original_run = s.subprocess.run

tmp = tempfile.TemporaryDirectory(prefix='lens-stop-race-')
tmp_path = Path(tmp.name)
s.WHISPER_BIN = str(tmp_path / 'synthetic-whisper')
s.Path(s.WHISPER_BIN).write_text('#!/bin/sh\n')
s.WHISPER_MODEL = tmp_path / 'whisper-model.bin'
s.WHISPER_MODEL.write_bytes(b'M' * 1_000_100)
s.SPEAKER_PYTHON = tmp_path / 'speaker-python'
s.SPEAKER_PYTHON.write_text('#!/bin/sh\n')
s.SPEAKER_MODEL = tmp_path / 'speaker-model.onnx'
s.SPEAKER_MODEL.write_bytes(b'S' * 5_000_100)
s.SPEAKER_WORKER = tmp_path / 'speaker-worker.py'
s.SPEAKER_WORKER.write_text('# synthetic worker fixture\n')
s.decode_audio = lambda *_: tmp_path / 'synthetic.wav'
s.is_speech = lambda _wav: True

def fake_whisper(args, *pargs, **kwargs):
    if args and args[0] == s.WHISPER_BIN:
        output_base = args[args.index('-of') + 1]
        Path(output_base + '.txt').write_text('A synthetic transcript survives Stop.')
        return SimpleNamespace(returncode=0)
    return original_run(args, *pargs, **kwargs)


def vector_unit():
    vector = [0.0] * 256
    vector[0] = 1.0
    return {'full': vector, 'first': vector, 'second': vector,
            'speech_seconds': 3.0}

def blocked_speaker_vectors(_wav):
    entered.set()
    wait(resume, 'synthetic ASR release')
    return vector_unit()


s.subprocess.run = fake_whisper
s.speaker_vectors = blocked_speaker_vectors
with http.server.ThreadingHTTPServer(('127.0.0.1', 0), s.Handler) as server:
    server.daemon_threads = True
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    try:
        code, opened = post(base, '/api/capture/open', {'consent': True, 'takeover': True})
        assert code == 200
        live_capture = opened['capture']
        response = {}
        upload = threading.Thread(target=lambda: response.setdefault(
            'result', post(base, '/api/transcribe', payload, live_capture, 'live_race')))
        upload.start()
        wait(entered, 'live upload after admission')

        code, frozen = post(base, '/api/capture/freeze', {'capture': live_capture})
        assert code == 200 and frozen['frozen'] is True
        resume.set()
        upload.join(5)
        assert not upload.is_alive(), 'live upload failed to finish after release'
        code, result = response['result']
        assert code == 200 and result.get('discarded') is True, result
        assert result.get('text', '') == '' and 'synthetic transcript' not in json.dumps(result), result
        assert not s.SPEAKERS, 'A frozen live ticket must not learn a speaker'
        print('PASS Stop freeze after live admission discards late HTTP transcript result')

        entered.clear(); resume.clear()
        code, stale = post(base, '/api/transcribe', payload, live_capture, 'after_stop')
        assert code == 409, (code, stale)
        assert not entered.is_set()
        print('PASS upload submitted after freeze is rejected before transcription')

        code, opened = post(base, '/api/capture/open', {'consent': True, 'takeover': True})
        assert code == 200
        code, frozen = post(base, '/api/capture/freeze', {'capture': opened['capture']})
        assert code == 200
        selected_hash = hashlib.sha256(payload).hexdigest()
        code, drain = post(base, '/api/capture/drain', {
            'capture': opened['capture'],
            'windows': [{'window_id': 'keep_race', 'sha256': selected_hash,
                         'force_mixed': False}]})
        assert code == 200
        entered.clear(); resume.clear(); response.clear()
        upload = threading.Thread(target=lambda: response.setdefault(
            'result', post(base, '/api/transcribe', payload, drain['capture'], 'keep_race')))
        upload.start()
        wait(entered, 'selected Keep upload after admission')
        code, closed = post(base, '/api/capture/close', {'capture': drain['capture']})
        assert code == 200 and closed['closed'] is True
        resume.set()
        upload.join(5)
        assert not upload.is_alive(), 'Keep upload failed to finish after close'
        code, result = response['result']
        assert code == 200 and result.get('discarded') is True, result
        assert result.get('text', '') == '' and 'synthetic transcript' not in json.dumps(result), result
        assert not s.SPEAKERS, 'A closed drain ticket must not learn a speaker'
        print('PASS closing an in-flight Keep drain discards late result')

        code, replacement = post(base, '/api/capture/open', {'consent': True})
        assert code == 200
        code, stale = post(base, '/api/transcribe', payload, drain['capture'], 'keep_race')
        assert code == 409, (code, stale)
        assert s.CAPTURE_SESSION == replacement['capture']
        print('PASS stale Keep lease cannot affect replacement capture')
    finally:
        resume.set()
        s.transcribe_audio = original_transcribe
        s.decode_audio = original_decode
        s.is_speech = original_is_speech
        s.speaker_vectors = original_speaker_vectors
        s.subprocess.run = original_run
        s.close_capture_session(erase=True)
        server.shutdown()
        server_thread.join(5)
        tmp.cleanup()

print('PASS adversarial Stop/drain HTTP race checks')
