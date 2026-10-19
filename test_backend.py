"""v6 backend HTTP/FFmpeg, revocation, replay and privacy tests; synthetic audio and fake Whisper output."""
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave
from http.server import ThreadingHTTPServer

ROOT=pathlib.Path(__file__).parent/'Conversation_Lens_Intelligent_Speaker_v6'
spec=importlib.util.spec_from_file_location('lens_v6',ROOT/'server.py')
backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)

def req(url,payload=None,headers=None,timeout=18):
  r=urllib.request.Request(url,data=payload,headers=headers or {},method='POST' if payload is not None else 'GET')
  try:
    with urllib.request.urlopen(r,timeout=timeout) as res:return res.status,json.load(res)
  except urllib.error.HTTPError as exc:return exc.code,json.load(exc)

def vec(i=0,sec=4.0):
  unit=[0.0]*256;unit[i]=1.0
  return {'full':unit,'first':unit,'second':unit,'speech_seconds':sec}

for word,expected in [('This is Dale.','Dale'),('I am Morgan, and here is the issue.','Morgan'),('Hello, my name is Dale.','Dale'),('Someone said this is Dale',None),('This is what we mean.',None),("I'm sorry to hear that",None),('"This is Dale."',None),('Is this Dale?',None)]:
  assert backend.parse_self_introduction(word)==expected,(word,expected)
print('PASS introduction parsing, no text-only speaker attribution')

with tempfile.TemporaryDirectory(prefix='lens-v6-qa-') as td:
  tmp=pathlib.Path(td);model=tmp/'fake-ggml.bin';model.write_bytes(b'M'*1_000_200)
  fake=tmp/'whisper-cli';output=tmp/'voice.txt'
  fake.write_text('''#!/usr/bin/env python3
import os,sys,time,pathlib
args=sys.argv
if os.path.exists(os.environ['LENS_FAKE_WAIT']):
 pathlib.Path(os.environ['LENS_FAKE_WORK_STARTED']).write_text('started')
 time.sleep(1.6)
pathlib.Path(args[args.index('-of')+1]+'.txt').write_text(pathlib.Path(os.environ['LENS_FAKE_TEXT']).read_text())
''');fake.chmod(0o700)
  backend.WHISPER_BIN=str(fake);backend.WHISPER_MODEL=model
  backend.SPEAKER_PYTHON=tmp/'speaker-python';backend.SPEAKER_PYTHON.write_text('#!test');backend.SPEAKER_PYTHON.chmod(0o700)
  backend.SPEAKER_MODEL=tmp/'speaker-model.onnx';backend.SPEAKER_MODEL.write_bytes(b'O'*5_000_150)
  backend.speaker_vectors=lambda wav:vec(0)
  os.environ['LENS_FAKE_TEXT']=str(output);output.write_text('Hello, this is Dale, and I want us to hear each other.')
  os.environ['LENS_FAKE_WAIT']=str(tmp/'sleep-marker')
  os.environ['LENS_FAKE_WORK_STARTED']=str(tmp/'work-started')
  sample=tmp/'voice.webm'
  subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-f','lavfi','-i','sine=frequency=510:duration=3.2','-c:a','libopus',str(sample)],check=True)
  clip=sample.read_bytes()
  pcm_sample=tmp/'voice.wav'
  subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',str(sample),'-ac','1','-ar','16000','-c:a','pcm_s16le',str(pcm_sample)],check=True)
  with tempfile.TemporaryDirectory(prefix='lens-wav-decode-') as decode_dir:
    normalized=backend.decode_audio(pcm_sample.read_bytes(),'audio/wav',decode_dir)
    with wave.open(str(normalized),'rb') as decoded:
      assert decoded.getnchannels()==1 and decoded.getframerate()==16000 and decoded.getnframes()>40000
  print('PASS production WAV decoder keeps uploaded PCM separate from normalized output')
  app=ThreadingHTTPServer(('127.0.0.1',0),backend.Handler)
  thread=threading.Thread(target=app.serve_forever,daemon=True);thread.start()
  base='http://127.0.0.1:'+str(app.server_address[1])
  try:
    status,data=req(base+'/api/status');assert status==200 and data['captureControl'] and data['stt']['ready'] and data['speakers']['ready']
    h={'X-Lens-Token':data['token'],'Content-Type':'application/json','Origin':base,'X-Lens-Protocol':'3'}
    audio_h={'X-Lens-Token':data['token'],'Content-Type':'audio/webm','Origin':base,'X-Lens-Protocol':'3','X-Lens-Language':'en','X-Lens-Auto-Names':'enabled','X-Lens-Voice-Consent':'confirmed'}
    assert req(base+'/api/capture/open',b'{"consent":false}',h)[0]==403
    assert req(base+'/api/capture/open',b'{"consent":true}',{**h,'Origin':'http://evil.invalid'})[0]==403
    assert req(base+'/api/capture/open',b'{"consent":true}',{**h,'X-Lens-Token':'wrong'})[0]==403
    assert req(base+'/api/transcribe',clip,audio_h)[0]==422, 'Capture session must be explicit'
    assert req(base+'/api/capture/open',b'{"consent":true}',{**h,'X-Lens-Protocol':'2'})[0]==426, 'Mismatched clients must fail closed'
    code,data=req(base+'/api/capture/open',b'{"consent":true}',h)
    assert code==200 and isinstance(data['capture'],str)
    lease=data['capture'];assert lease==backend.CAPTURE_SESSION
    assert req(base+'/api/capture/open',b'{"consent":true}',h)[0]==409, 'A second tab must not silently steal capture'
    assert backend.CAPTURE_SESSION==lease
    code,body=req(base+'/api/transcribe',clip,{**audio_h,'X-Lens-Capture-Session':lease})
    assert code==200 and body['speaker']['label']=='Dale' and body['introduction']['state']=='candidate',body
    assert len(backend.SPEAKERS['Dale'])==1
    stage_kinds={event['kind'] for event in backend.EVENTS}
    assert {'decode','vad','asr','embedding','speaker_match','audio'}<=stage_kinds,stage_kinds
    assert req(base+'/api/capture/close',json.dumps({'capture':'wrong'}).encode(),h)[1]['closed'] is False
    assert backend.CAPTURE_SESSION==lease
    # Now simulate an STT worker blocked mid-transcription. STOP must revoke immediately,
    # no late text or biometric learning is permitted after revocation.
    (tmp/'sleep-marker').touch()
    result={}
    def slow_request():result['response']=req(base+'/api/transcribe',clip,{**audio_h,'X-Lens-Capture-Session':lease},timeout=22)
    work=threading.Thread(target=slow_request);work.start()
    for _ in range(70):
      if (tmp/'work-started').exists():break
      time.sleep(.035)
    assert (tmp/'work-started').exists(),'Slow Whisper did not start'
    before=len(backend.SPEAKERS['Dale'])
    t0=time.monotonic()
    code,stop=req(base+'/api/capture/close',json.dumps({'capture':lease}).encode(),h)
    assert code==200 and stop['closed'] is True and time.monotonic()-t0<0.7
    work.join(timeout=8)
    assert not work.is_alive()
    assert result['response'][0]==200 and result['response'][1]['discarded'] is True,result
    assert len(backend.SPEAKERS['Dale'])==before
    assert req(base+'/api/transcribe',clip,{**audio_h,'X-Lens-Capture-Session':lease})[0]==409
    # Another open starts a brand new ID; close(old) may never kill new capture.
    code,new=req(base+'/api/capture/open',b'{"consent":true}',h)
    assert new['capture']!=lease
    assert req(base+'/api/capture/close',json.dumps({'capture':lease}).encode(),h)[1]['closed'] is False
    assert backend.CAPTURE_SESSION==new['capture']
    code,takeover=req(base+'/api/capture/open',b'{"consent":true,"takeover":true}',h)
    assert code==200 and takeover['capture']!=new['capture'] and backend.CAPTURE_SESSION==takeover['capture']
    assert req(base+'/api/transcribe',clip,{**audio_h,'X-Lens-Capture-Session':new['capture']})[0]==409
    import hashlib
    kept_wav=pcm_sample.read_bytes()
    code,frozen=req(base+'/api/capture/freeze',json.dumps({'capture':takeover['capture']}).encode(),h)
    assert code==200 and frozen['frozen'] is True
    code,drain=req(base+'/api/capture/drain',json.dumps({'capture':takeover['capture'],'windows':[
      {'window_id':'kept_pcm_wav','sha256':hashlib.sha256(kept_wav).hexdigest(),'force_mixed':True}]}).encode(),h)
    assert code==200
    kept_headers={**audio_h,'Content-Type':'audio/wav','X-Lens-Capture-Session':drain['capture'],
      'X-Lens-Window-ID':'kept_pcm_wav','X-Lens-Force-Mixed':'true'}
    code,kept_result=req(base+'/api/transcribe',kept_wav,kept_headers)
    assert code==200 and kept_result['text']=='Hello, this is Dale, and I want us to hear each other.'
    assert kept_result['speaker']['label']=='Mixed', 'Edited/forced-Mixed kept PCM must retain the learning veto'
    print('PASS Stop Keep drain transcribes an exact-hash PCM WAV through production FFmpeg/Whisper route')
    assert req(base+'/api/session/erase',b'{"confirm":false}',h)[0]==403
    code,wipe=req(base+'/api/session/erase',b'{"confirm":true}',h)
    assert code==200 and wipe['erased'] is True
    assert not backend.SPEAKERS and not backend.SPEAKER_META and backend.CAPTURE_SESSION is None
    # Replaying one exact enrollment clip must never count as two independent voice samples.
    backend.speaker_vectors=lambda wav:vec(0)
    one=backend.enroll_speaker('Morgan',clip,'audio/webm')
    assert one['samples']==1
    try:
      backend.enroll_speaker('Morgan',clip,'audio/webm')
      assert False,'Duplicate enrollment unexpectedly accepted'
    except ValueError as exc:
      assert 'already used' in str(exc)
    assert len(backend.SPEAKERS['Morgan'])==1
    try:
      backend.enroll_speaker('Casey',clip,'audio/webm')
      assert False,'Same audio under a different name unexpectedly accepted'
    except ValueError as exc:
      assert 'another speaker name' in str(exc)
    assert 'Casey' not in backend.SPEAKERS
    backend.forget_speakers()
    assert not backend.ENROLLMENT_AUDIO_IDS and not backend.SPEAKERS
    # Even an explicitly consented enrollment finishing after a wipe may not resurrect profiles.
    (tmp/'sleep-marker').unlink()
    epoch=backend.PROFILE_EPOCH
    entry=threading.Event();proceed=threading.Event();failure=[]
    def paused_embedding(wav):
      entry.set();assert proceed.wait(5)
      return vec(0)
    backend.speaker_vectors=paused_embedding
    def late_enroll():
      try:backend.enroll_speaker('Dale',clip,'audio/webm')
      except ValueError as exc:failure.append(str(exc))
    run=threading.Thread(target=late_enroll);run.start();assert entry.wait(5)
    backend.forget_speakers()
    proceed.set();run.join(timeout=10)
    assert failure and 'erased' in failure[0] and not backend.SPEAKERS
    assert backend.PROFILE_EPOCH>epoch
    assert not list(pathlib.Path('/tmp').glob('lens-stt-*'))
    print('PASS backend localhost HTTP: consent, token, origin, real FFmpeg conversion, Whisper transcript, provisional Dale, async STOP revocation, stale upload rejection, no stale voice learning, erase, enrollment race')
  finally:
    app.shutdown();app.server_close()
