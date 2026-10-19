#!/usr/bin/env python3
"""Local executable validation host for Packet A's PCM editor + two-phase Stop.

The normal Conversation Lens server is untouched. This host is only for inspecting
Packet A and testing the wire contract until the MacBook's worktree is accessible.
Without --whisper-cli and --model, uploads are validated but NOT transcribed.
"""
import argparse
import io
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import wave
from lens_stop_drain import CaptureDrainCoordinator, LeaseConflict, InvalidWindow

HERE = Path(__file__).resolve().parent
TOKENS = secrets.token_urlsafe(32)
COORDINATOR = CaptureDrainCoordinator()
WHISPER_LOCK = threading.Lock()
FILE_MAP = {
    '/': ('packet_a_lab.html', 'text/html; charset=utf-8'),
    '/lens_pcm_core.js': ('lens_pcm_core.js', 'text/javascript; charset=utf-8'),
    '/lens_pcm_capture.js': ('lens_pcm_capture.js', 'text/javascript; charset=utf-8'),
    '/lens_stop_client.js': ('lens_stop_client.js', 'text/javascript; charset=utf-8'),
    '/lens_packet_a_transport.js': ('lens_packet_a_transport.js', 'text/javascript; charset=utf-8'),
}


def wav_frames(audio):
    try:
        with wave.open(io.BytesIO(audio), 'rb') as r:
            assert r.getnchannels() == 1 and r.getsampwidth() == 2 and r.getframerate() == 16000
            assert 500 <= len(audio) <= 320044
            frames = r.getnframes()
            assert 200 <= frames <= 160000
            assert len(audio) == 44 + frames * 2
            return frames
    except (wave.Error, AssertionError, ValueError) as exc:
        raise InvalidWindow('Expected canonical mono 16k PCM16 WAV') from exc


def whisper_text(audio, cli, model):
    if not (cli and model):
        return {'engine': 'audio-validation-only', 'text': None}
    with tempfile.TemporaryDirectory(prefix='lens-packet-a-') as directory:
        stem = Path(directory) / 'window'
        wav_file = stem.with_suffix('.wav')
        wav_file.write_bytes(audio)
        result = subprocess.run([str(cli), '-m', str(model), '-f', str(wav_file),
                                 '-l', 'en', '-t', '4', '-nt', '-np', '-sns',
                                 '-otxt', '-of', str(stem)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=35, check=False)
        outfile = stem.with_suffix('.txt')
        if result.returncode != 0 or not outfile.is_file():
            raise RuntimeError('Local Whisper transcription failed')
        return {'engine': 'whisper-cpp', 'text': ' '.join(outfile.read_text(encoding='utf-8').split())[:2500]}


class Handler(BaseHTTPRequestHandler):
    server_version = 'LensPacketA/1.0'

    def log_message(self, fmt, *args):
        return

    def reply(self, status, payload):
        data = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass

    def allowed_host(self):
        return self.headers.get('Host') in (
            '127.0.0.1:%d' % self.server.server_port,
            'localhost:%d' % self.server.server_port)

    def do_GET(self):
        if not self.allowed_host():
            self.reply(403, {'error': 'Host denied'}); return
        path = urlsplit(self.path).path
        if path == '/api/status':
            self.reply(200, {'app':'lens-packet-a','protocol':1,'token':TOKENS,
                             'engine':'whisper-cpp' if self.server.whisper else 'audio-validation-only',
                             'capture':COORDINATOR.state()});return
        if path not in FILE_MAP:
            self.reply(404, {'error': 'Not found'});return
        name, mime = FILE_MAP[path]
        content = (HERE/name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(content)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        try: self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError): pass

    def do_POST(self):
        path=urlsplit(self.path).path
        if not self.allowed_host() or path not in ('/api/capture/open','/api/capture/freeze','/api/capture/drain',
                                                  '/api/capture/close','/api/transcribe'):
            self.reply(403,{'error':'Host/path denied'});return
        if self.headers.get('Origin') != 'http://'+self.headers.get('Host','') or self.headers.get('X-Lens-Token') != TOKENS:
            self.reply(403,{'error':'Request token/origin denied'});return
        try:
            length=int(self.headers.get('Content-Length','-1'))
            max_size=320044 if path=='/api/transcribe' else 2300
            if not 1 <= length <= max_size:
                self.reply(413,{'error':'Invalid upload size'});return
            raw=self.rfile.read(length)
            if path=='/api/transcribe':
                self.transcribe(raw);return
            body=json.loads(raw)
            if not isinstance(body,dict): raise ValueError('Invalid JSON data')
            if path=='/api/capture/open':
                capture=COORDINATOR.open_capture(takeover=body.get('takeover') is True)
                self.reply(200,{'capture':capture});return
            if path=='/api/capture/freeze':
                self.reply(200,COORDINATOR.freeze(body.get('capture')));return
            if path=='/api/capture/drain':
                capture=COORDINATOR.start_drain(body.get('capture'),body.get('windows'))
                self.reply(200,{'capture':capture,'deadlineSeconds':COORDINATOR.DRAIN_TTL_SECONDS});return
            self.reply(200,{'closed':COORDINATOR.close(body.get('capture'))})
        except LeaseConflict as exc:self.reply(409,{'error':str(exc)})
        except InvalidWindow as exc:self.reply(422,{'error':str(exc)})
        except (ValueError,TypeError,KeyError,AttributeError,json.JSONDecodeError):
            self.reply(400,{'error':'Invalid request'})

    def transcribe(self,raw):
        try:
            frames=wav_frames(raw)
            capture=self.headers.get('X-Lens-Capture-Session','')
            window_id=self.headers.get('X-Lens-Window-ID','')
            forced=self.headers.get('X-Lens-Force-Mixed') == 'true'
        except InvalidWindow as exc:
            self.reply(422,{'error':str(exc)});return
        # Busy speech processing is a retryable condition, NOT a consumed one-use
        # drain authorization. Admit only after obtaining the worker lock.
        if not WHISPER_LOCK.acquire(blocking=False):
            self.reply(429,{'error':'Whisper worker busy','retryable':True});return
        ticket=None
        try:
            ticket=COORDINATOR.admit(capture,window_id,raw,force_mixed=forced)
            payload=whisper_text(raw,self.server.whisper,self.server.model)
            # The coordinator checks this ticket atomically with the final result;
            # STOP invalidates any previously admitted live work.
            accepted=COORDINATOR.atomic_commit(ticket)
            if not accepted:
                self.reply(200,{'discarded':True,'reason':'Capture frozen, expired, or revoked'});return
            self.reply(200,dict(payload,discarded=False,frames=frames,
                                window_id=window_id,draining=ticket.draining,
                                forceMixed=forced,autoNameLearning=False))
        except LeaseConflict as exc:
            self.reply(409,{'error':str(exc)})
        except InvalidWindow as exc:
            self.reply(422,{'error':str(exc)})
        except (RuntimeError,OSError,subprocess.TimeoutExpired):
            if ticket is not None:COORDINATOR.reject(ticket)
            self.reply(503,{'error':'Local transcription failed'})
        finally:
            WHISPER_LOCK.release()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--open-brave',action='store_true',help='Launch the localhost lab in Brave on macOS')
    parser.add_argument('--whisper-cli',type=Path)
    parser.add_argument('--model',type=Path)
    args=parser.parse_args()
    if bool(args.whisper_cli)!=bool(args.model):parser.error('--whisper-cli and --model are required together')
    if args.whisper_cli and (not args.whisper_cli.is_file() or not args.model.is_file()):
        parser.error('Local Whisper model or executable unavailable')
    with ThreadingHTTPServer(('127.0.0.1',args.port),Handler) as server:
        server.daemon_threads=True;server.whisper=args.whisper_cli;server.model=args.model
        url='http://127.0.0.1:%d/'%server.server_port
        print('Packet A connected workbench:',url,flush=True)
        print('Transcription:', 'Whisper model selected' if server.whisper else 'Disabled: WAV proof only',flush=True)
        if args.open_brave:
            browser=Path('/Applications/Brave Browser.app')
            if sys.platform=='darwin' and browser.exists():
                try:subprocess.Popen(['open','-a','Brave Browser',url])
                except OSError:print('Open the URL above manually in Brave.',flush=True)
            else:print('Brave auto-launch requires macOS Brave; open the URL above.',flush=True)
        try:server.serve_forever(poll_interval=.15)
        except KeyboardInterrupt:COORDINATOR.drop_all()

if __name__=='__main__':main()
