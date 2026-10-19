"""Focused upgrade regression: evidence, name-learning guard, tunable AI and local diagnostics."""
from pathlib import Path
import importlib.util
import json
import io
import http.server
import threading
import urllib.request
import contextlib

app=Path(__file__).parent/'Conversation_Lens_Intelligent_Speaker_v6'/'server.py'
spec=importlib.util.spec_from_file_location('lens_upgraded',app)
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

def unit(i):
    a=[0.0]*256;a[i]=1.0
    return a

def vectors(first=0,second=0):
    return {'full':unit(first),'first':unit(first),'second':unit(second),'speech_seconds':3.4}

s.forget_speakers()
s.SPEAKERS.update({'Dale':[unit(0),unit(0)],'Morgan':[unit(1),unit(1)]})
matching=s.speaker_evidence(vectors(0,0))
assert matching['full']['best']=='Dale'
assert matching['full']['cosine']==1.0 and matching['full']['margin']==1.0
assert matching['halfCosine']==1.0 and not matching['possibleOverlap']
divergent=s.speaker_evidence(vectors(0,1))
assert divergent['possibleOverlap'] and divergent['halfCosine']==0.0
s.forget_speakers()
result,event=s.recognize_or_learn('This is Dale and I have something to say.',vectors(0,1),True,audio_id='one')
assert result['label']=='Mixed' and event['state']=='ambiguous'
assert not s.SPEAKERS,'Ambiguous audio must never create new speaker embeddings'
print('PASS half-window cosine/margin evidence and forced Mixed anti-learning')

import math,time
s.SPEAKERS['Dale']=[unit(0)]
s.SPEAKER_META['Dale']={'source':'introduction','seen_audio':set()}
near=[0.86,math.sqrt(1-0.86**2)]+[0.0]*254
sample={'full':near,'first':near,'second':near,'speech_seconds':3.1}
assert s._automatic_match(sample)['label']=='Unknown'
s.SPEAKER_BOOST_UNTIL['Dale']=time.monotonic()+120
assert s._automatic_match(sample)['label']=='Dale','Temporary boost should change only the named threshold'
assert s.speaker_status()['profiles'][0]['boostSeconds']>0
s.forget_speakers()
assert not s.SPEAKER_BOOST_UNTIL
print('PASS temporary per-speaker boost expires with profile erase and retains overlap veto')

assert s.ollama_options({'ollama':{'url':'http://localhost:11435','model':'gemma3:4b','timeout':20,'temperature':0.5}})['temperature']==0.5
for invalid in ('https://localhost:11435','http://example.org:11435','http://127.0.0.1','http://127.0.0.1:11435/other','http://localhost:11435/?x=1'):
    try: s.ollama_options({'ollama':{'url':invalid}})
    except ValueError: pass
    else: raise AssertionError('External or nonlocal model URL accepted: '+invalid)
for invalid in (-1,1.1):
    try: s.ollama_options({'ollama':{'temperature':invalid}})
    except ValueError: pass
    else: raise AssertionError('Invalid temperature accepted')
print('PASS configurable Ollama endpoint constrained to localhost and bounded numeric tuning')

turns=[{'speaker':'Unassigned','text':'Unimportant detail '+str(i)} for i in range(24)]
turns[0]['text']='We decided the release needs testing.'
turns[4]['text']='I need the old requirement preserved.'
prioritized=s.chosen_turns(turns)
assert len(prioritized)==12
assert prioritized[-1]['text']=='Unimportant detail 23'
assert 'We decided the release needs testing.' in [t['text'] for t in prioritized]
assert 'I need the old requirement preserved.' in [t['text'] for t in prioritized]
print('PASS priority context retains older decisions without ejecting latest eight turns')

captured=[]
class Dummy:
    def __init__(self, response):
        self.content=io.BytesIO(json.dumps({'response':json.dumps(response)}).encode())
    def __enter__(self):return self.content
    def __exit__(self,*args):self.content.close()
response={'observation':'More time was requested.','evidence':'I need more time today',
          'next_step':'What time would work?','caution':''}
original=s.urllib.request.urlopen
def intercept(req,timeout=0):
    captured.append((req.full_url,timeout,json.loads(req.data)))
    return Dummy(response)
try:
    s.urllib.request.urlopen=intercept
    payload={'grounding':'fuzzy','goal':'Resolve','note':'Find the next concrete decision',
        'context':'Timeline coordination','system_fragment':'Ask one short question.',
        'ollama':{'url':'http://localhost:11435','model':'another:4b','timeout':7,'temperature':0.1},
        'turns':[{'speaker':'Dale','manual':True,'text':'I need a little more time to finish.'}]}
    fuzzy=s.call_ollama(payload)
    assert fuzzy['evidence_status']=='approximate',fuzzy
    url,timeout,posted=captured[-1]
    assert url=='http://localhost:11435/api/generate' and timeout==7
    assert posted['model']=='another:4b' and posted['options']['temperature']==0.1
    for word in ('Find the next concrete decision','Ask one short question.','Timeline coordination','owner-assigned label'):
        assert word in posted['prompt'],word
    free=s.call_ollama(dict(payload,grounding='free'))
    assert free['evidence_status']=='ungrounded' and free['evidence']=='I need more time today'
    exact=s.call_ollama(dict(payload,grounding='exact'))
    assert exact['evidence_status']=='rejected'
    assert exact['evidence']=='No matching quotation in the captured transcript'
    payload['turns']=[{'speaker':'Dale','manual':False,'text':'I need a little more time to finish.'}]
    s.call_ollama(payload)
    assert '"speaker": "Unassigned"' in captured[-1][2]['prompt'],'Unverified acoustic label was promoted'
finally:
    s.urllib.request.urlopen=original
print('PASS explicit grounding modes, private note, custom prompt and manually assigned voice label')

with http.server.ThreadingHTTPServer(('127.0.0.1',0),s.Handler) as server:
    server.daemon_threads=True
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    port=server.server_address[1]
    with urllib.request.urlopen('http://127.0.0.1:%d/api/health'%port,timeout=4) as res:
        health=json.load(res)
    assert health['ok'] is True and health['protocol']==3 and 'speakerRamBytes' in health
    origin='http://127.0.0.1:%d'%port
    def post(path,body,extra=None):
        headers={'Origin':origin,'X-Lens-Token':s.APP_TOKEN,'Content-Type':'application/json','X-Lens-Protocol':'3'}
        headers.update(extra or {})
        req=urllib.request.Request(origin+path,data=body if isinstance(body,bytes) else json.dumps(body).encode(),headers=headers,method='POST')
        try:
            with urllib.request.urlopen(req,timeout=4) as res:return res.status,json.load(res)
        except urllib.error.HTTPError as err:return err.code,json.load(err)
    code,opened=post('/api/capture/open',{'consent':True})
    assert code==200 and opened['capture']
    frozen,freeze_result=post('/api/capture/freeze',{'capture':opened['capture']})
    assert frozen==200 and freeze_result['frozen'] is True
    kept=b'RIFF'+b'K'*2400;wrong=b'RIFF'+b'W'*2400
    import hashlib
    code,drain=post('/api/capture/drain',{'capture':opened['capture'],'windows':[
        {'window_id':'keep_1','sha256':hashlib.sha256(kept).hexdigest(),'force_mixed':True}]})
    assert code==200 and drain['capture']!=opened['capture']
    code,_=post('/api/capture/open',{'consent':True},{'X-Lens-Protocol':'99'})
    assert code==426,'Server must fail closed on a protocol mismatch'
    original=s.transcribe_audio
    seen=[]
    s.transcribe_audio=lambda raw,*args,**kwargs:(seen.append((raw,kwargs.get('force_mixed'))) or
        {'text':'safe synthetic test','engine':'test','speaker':{'label':'Mixed'},'introduction':None})
    audio_headers={'X-Lens-Capture-Session':drain['capture'],'X-Lens-Window-ID':'keep_1','X-Lens-Force-Mixed':'true','X-Lens-Language':'en'}
    code,_=post('/api/transcribe',wrong,{**audio_headers,'Content-Type':'audio/wav'})
    assert code==422,'A changed clip must fail before transcription'
    code,transcript=post('/api/transcribe',kept,{**audio_headers,'Content-Type':'audio/wav'})
    assert code==200 and transcript['text']=='safe synthetic test' and seen==[(kept,True)]
    code,_=post('/api/transcribe',kept,{**audio_headers,'Content-Type':'audio/wav'})
    assert code==422,'A completed selected window must be one use'
    s.transcribe_audio=original
    post('/api/capture/close',{'capture':drain['capture']})
    print('PASS Stop freeze, exact-hash Keep authorization, changed-clip rejection, Mixed veto, and one-use drain')
    s.SPEAKERS['Dale']=[unit(0),unit(0)]
    post=json.dumps({'name':'Dale','seconds':120}).encode()
    req=urllib.request.Request('http://127.0.0.1:%d/api/speakers/boost'%port,data=post,
        headers={'Origin':'http://127.0.0.1:%d'%port,'X-Lens-Token':s.APP_TOKEN,
                 'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=4) as res: boosted=json.load(res)
    assert boosted['speakers']['profiles'][0]['boostSeconds']>0
    s.forget_speakers()
    s.event_record('audio','ok',0.1)
    with urllib.request.urlopen('http://127.0.0.1:%d/api/diagnostics'%port,timeout=4) as res:
        diagnostic=json.load(res)
    assert diagnostic['events'][-1]['elapsedMs']==100 and diagnostic['events'][-1]['kind']=='audio'
    server.shutdown();t.join(5)
for k in range(125):s.event_record('audio','ok',0.1,k)
assert len(s.EVENTS)==120,'Structured log buffer grew without a bound'
assert all('text' not in x and 'name' not in x for x in s.EVENTS),'Diagnostics leaked utterance details'
print('PASS loopback health endpoint and bounded metadata-only diagnostics')
