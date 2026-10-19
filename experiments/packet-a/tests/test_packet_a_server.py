"""Actual localhost HTTP contract for Packet A; no installed speech model needed."""
from __future__ import annotations
from hashlib import sha256
import io
import json
import pathlib
import sys
import threading
import unittest
import urllib.error
import urllib.request
import wave
from http.server import ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import packet_a_server as app
from lens_stop_drain import CaptureDrainCoordinator


def make_wav(frames=16000, value=129):
    output=io.BytesIO()
    with wave.open(output,'wb') as writer:
        writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(16000)
        writer.writeframes(bytes((value % 256, 0))*frames)
    return output.getvalue()


class HTTPIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.COORDINATOR = CaptureDrainCoordinator()
        cls.server=ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.server.daemon_threads=True
        cls.server.whisper=None
        cls.server.model=None
        cls.server_thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.server_thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server_thread.join(5);cls.server.server_close()

    def setUp(self):
        app.COORDINATOR.drop_all()

    def request(self,path,data=None,token=True,origin=True,headers=None):
        opts=dict(headers or {})
        if data is not None:
            if token:opts['X-Lens-Token']=app.TOKENS
            if origin:opts['Origin']=self.base
            if isinstance(data,dict):
                data=json.dumps(data).encode('utf-8')
                opts['Content-Type']='application/json'
        req=urllib.request.Request(self.base+path, data=data,headers=opts,
                                   method='POST' if data is not None else 'GET')
        try:
            with urllib.request.urlopen(req,timeout=6) as resp:
                raw=resp.read()
                return resp.status, json.loads(raw) if resp.headers.get('Content-Type','').startswith('application/json') else raw
        except urllib.error.HTTPError as err:
            return err.code, json.load(err)

    def test_main_page_and_transport_source_actually_served(self):
        code,html=self.request('/')
        self.assertEqual(code,200)
        self.assertIn(b'Connected Audio Workbench',html)
        self.assertIn(b'lens_packet_a_transport.js',html)
        for path in ('lens_pcm_core.js','lens_pcm_capture.js','lens_stop_client.js','lens_packet_a_transport.js'):
            code,asset=self.request('/'+path)
            self.assertEqual(code,200,path)
            self.assertGreater(len(asset),200)
        code,status=self.request('/api/status')
        self.assertEqual(code,200)
        self.assertEqual(status['engine'],'audio-validation-only')
        self.assertEqual(status['protocol'],1)
        self.assertGreater(len(status['token']),12)

    def test_full_open_freeze_select_drain_two_and_stale_replay(self):
        code,opened=self.request('/api/capture/open',{})
        self.assertEqual(code,200)
        old=opened['capture']
        wav1=make_wav(16000,117);wav2=make_wav(24000,223)
        code,none=self.request('/api/transcribe',wav1,headers={
            'Content-Type':'audio/wav','X-Lens-Capture-Session':old,
            'X-Lens-Window-ID':'w1','X-Lens-Force-Mixed':'false'})
        self.assertEqual(code,200)
        self.assertEqual(none['engine'],'audio-validation-only')
        code,freeze=self.request('/api/capture/freeze',{'capture':old})
        self.assertEqual(code,200);self.assertTrue(freeze['frozen'])
        # All old live upload rights are revoked, regardless of clip bytes.
        code,_=self.request('/api/transcribe',wav1,headers={
            'Content-Type':'audio/wav','X-Lens-Capture-Session':old,
            'X-Lens-Window-ID':'w42','X-Lens-Force-Mixed':'false'})
        self.assertEqual(code,409)
        manifest=[{'window_id':'w2','sha256':sha256(wav1).hexdigest(),'force_mixed':False},
                  {'window_id':'w3','sha256':sha256(wav2).hexdigest(),'force_mixed':True}]
        code,data=self.request('/api/capture/drain',{'capture':old,'windows':manifest})
        self.assertEqual(code,200);drain=data['capture']
        self.assertNotEqual(old,drain)
        # A busy worker must not consume the approved drain; the same clip remains retryable.
        acquired=app.WHISPER_LOCK.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            busy_code,busy=self.request('/api/transcribe',wav1,headers={
                'Content-Type':'audio/wav','X-Lens-Capture-Session':drain,
                'X-Lens-Window-ID':'w2','X-Lens-Force-Mixed':'false'})
            self.assertEqual(busy_code,429)
            self.assertTrue(busy['retryable'])
            self.assertEqual(app.COORDINATOR.state()['queuedDrain'],2)
        finally:app.WHISPER_LOCK.release()
        # The authorization is exact: not a different hash/clip/window ID.
        for wrong,frames,mixed,expected in [('w2',wav2,'false',422),('w4',wav1,'false',422),('w3',wav2,'false',422)]:
            code,_=self.request('/api/transcribe',frames,headers={
                'Content-Type':'audio/wav','X-Lens-Capture-Session':drain,
                'X-Lens-Window-ID':wrong,'X-Lens-Force-Mixed':mixed})
            self.assertEqual(code,expected,wrong)
        for window_id,payload,mixed,frames in [('w2',wav1,'false',16000),('w3',wav2,'true',24000)]:
            headers={'Content-Type':'audio/wav','X-Lens-Capture-Session':drain,
                     'X-Lens-Window-ID':window_id,'X-Lens-Force-Mixed':mixed}
            code,data=self.request('/api/transcribe',payload,headers=headers)
            self.assertEqual(code,200)
            self.assertEqual(data['frames'],frames)
            self.assertIsNone(data['text'])
            self.assertFalse(data['autoNameLearning'])
            self.assertTrue(data['draining'])
            replay_code,_=self.request('/api/transcribe',payload,headers=headers)
            self.assertEqual(replay_code,422)
        code,closed=self.request('/api/capture/close',{'capture':drain})
        self.assertEqual(code,200);self.assertTrue(closed['closed'])
        code,status=self.request('/api/status');self.assertFalse(status['capture']['occupied'])

    def test_all_drop_never_uploads_and_remote_origin_is_rejected(self):
        code,bad=self.request('/api/capture/open',{},token=False)
        self.assertEqual(code,403)
        code,bad=self.request('/api/capture/open',{},origin=False)
        self.assertEqual(code,403)
        code,opened=self.request('/api/capture/open',{})
        self.assertEqual(code,200)
        capture=opened['capture']
        self.assertEqual(self.request('/api/capture/freeze',{'capture':capture})[0],200)
        self.assertEqual(self.request('/api/capture/drain',{'capture':capture,'windows':[]})[0],422)
        self.assertTrue(self.request('/api/capture/close',{'capture':capture})[1]['closed'])
        self.assertFalse(app.COORDINATOR.state()['occupied'])


if __name__=='__main__':unittest.main(verbosity=2)
