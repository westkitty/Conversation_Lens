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

saved_profiles=s.SPEAKERS
s.SPEAKERS={f'Profile{i}':[unit(0 if i<2 else i),unit(0 if i<2 else i)] for i in range(6)}
soft_cap=s.speaker_status()
assert soft_cap['softCap']==6 and soft_cap['hardCap']==8
assert any(item['left']=='Profile0' and item['right']=='Profile1' and item['cosine']==1.0 for item in soft_cap['mergeSuggestions'])
s.SPEAKERS=saved_profiles
print('PASS speaker soft-cap similarity suggestions are bounded raw-vector hints')

s.forget_speakers();s.SPEAKERS['Compact Me']=[unit(0),unit(0),unit(1),unit(2)]
compacted=s.compact_speaker('Compact Me')
assert compacted['before']==4 and compacted['after']==2 and compacted['removed']==2
assert {tuple(v) for v in s.SPEAKERS['Compact Me']}=={tuple(unit(0)),tuple(unit(1))}
assert s.speaker_status()['profiles'][0]['samples']==2
try:s.compact_speaker('Missing')
except ValueError:pass
else:raise AssertionError('Compaction accepted a missing profile')
print('PASS explicit speaker compaction retains two diverse RAM exemplars and reports sample loss')

bundle=s.speaker_profile_bundle();saved_names=set(s.SPEAKERS)
s.SPEAKERS={'Discarded':[unit(3),unit(3)]}
restored=s.import_speaker_profile_bundle(bundle)
assert {profile['name'] for profile in restored['profiles']}==saved_names and 'Discarded' not in s.SPEAKERS
bad_bundle=dict(bundle);bad_bundle['sha256']='0'*64
try:s.import_speaker_profile_bundle(bad_bundle)
except ValueError as error:assert 'integrity' in str(error).lower()
else:raise AssertionError('Corrupt speaker profile bundle was imported')
bad_version=dict(bundle);bad_version['schemaVersion']=True
try:s.import_speaker_profile_bundle(bad_version)
except ValueError:pass
else:raise AssertionError('Boolean schema version was accepted as integer version one')
assert {profile['name'] for profile in s.speaker_status()['profiles']}==saved_names
s.forget_speakers()
print('PASS explicit speaker profile export/import integrity and atomic replacement')

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
        'continuation':'Earlier cue: ask what delivery date works.',
        'ollama':{'url':'http://localhost:11435','model':'another:4b','timeout':7,'temperature':0.1},
        'turns':[{'speaker':'Dale','manual':True,'text':'I need a little more time to finish.'}]}
    fuzzy=s.call_ollama(payload)
    assert fuzzy['evidence_status']=='approximate',fuzzy
    url,timeout,posted=captured[-1]
    assert url=='http://localhost:11435/api/generate' and timeout==7
    assert posted['model']=='another:4b' and posted['options']['temperature']==0.1
    for word in ('Find the next concrete decision','Ask one short question.','Timeline coordination','owner-assigned label','Earlier cue: ask what delivery date works.','Advance it using the current transcript'):
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
    with urllib.request.urlopen('http://127.0.0.1:%d/api/whisper/models'%port,timeout=4) as res:
        whisper_inventory=json.load(res)
    assert whisper_inventory['models'] and whisper_inventory['active']==s.WHISPER_MODEL.name
    assert all('path' not in model for model in whisper_inventory['models']),'Inventory must not expose local model paths'
    origin='http://127.0.0.1:%d'%port
    s.SPEAKERS.update({'Dale':[unit(0),unit(0)],'Morgan':[unit(1),unit(1)]})
    export_request=urllib.request.Request(origin+'/api/speakers/export',headers={'X-Lens-Token':s.APP_TOKEN})
    with urllib.request.urlopen(export_request,timeout=4) as res:profile_bundle=json.load(res)
    assert len(profile_bundle['profiles'])==2 and len(profile_bundle['sha256'])==64
    def post(path,body,extra=None):
        headers={'Origin':origin,'X-Lens-Token':s.APP_TOKEN,'Content-Type':'application/json','X-Lens-Protocol':'3'}
        headers.update(extra or {})
        req=urllib.request.Request(origin+path,data=body if isinstance(body,bytes) else json.dumps(body).encode(),headers=headers,method='POST')
        try:
            with urllib.request.urlopen(req,timeout=4) as res:return res.status,json.load(res)
        except urllib.error.HTTPError as err:return err.code,json.load(err)
    code,opened=post('/api/capture/open',{'consent':True,'owner':'tab-a1b2c3d4'})
    assert code==200 and opened['capture']
    code,_=post('/api/speakers/import',profile_bundle)
    assert code==409,'Profile import must refuse to replace profiles during capture'
    alternative=next((model for model in whisper_inventory['models'] if not model['active']),None)
    if alternative:
        original_model=s.WHISPER_MODEL
        code,_=post('/api/whisper/switch',{'model':alternative['id']})
        assert code==409 and s.WHISPER_MODEL==original_model,'Model switch must fail while capture is active'
    with urllib.request.urlopen('http://127.0.0.1:%d/api/health'%port,timeout=4) as res:lease_health=json.load(res)
    assert lease_health['captureActive'] is True and lease_health['captureOwner']=='tab-a1b2c3d4' and lease_health['captureAgeSeconds']>=0
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
    if alternative:
        original_model=s.WHISPER_MODEL;original_warm=s.warm_whisper_model;warmed=[]
        s.warm_whisper_model=lambda path:warmed.append(path)
        code,switched=post('/api/whisper/switch',{'model':alternative['id']})
        assert code==200 and switched['active']==alternative['name'] and s.WHISPER_MODEL.name==alternative['name'] and warmed
        selected_id=next(model['id'] for model in whisper_inventory['models'] if model['name']==original_model.name)
        s.warm_whisper_model=lambda path:(_ for _ in ()).throw(RuntimeError('synthetic load failure'))
        code,_=post('/api/whisper/switch',{'model':selected_id})
        assert code==503 and s.WHISPER_MODEL.name==alternative['name'],'Failed warm-up must retain the active model'
        s.WHISPER_MODEL=original_model;s.warm_whisper_model=original_warm
        print('PASS installed Whisper inventory, active-capture refusal, successful switch, and rollback on failed warm-up')
    code,imported=post('/api/speakers/import',profile_bundle)
    assert code==200 and len(imported['speakers']['profiles'])==2
    corrupt=dict(profile_bundle);corrupt['sha256']='0'*64
    code,_=post('/api/speakers/import',corrupt)
    assert code==422 and len(s.SPEAKERS)==2,'Corrupt profile import must preserve existing in-memory profiles'
    print('PASS authenticated profile export/import endpoints and import integrity rejection')
    print('PASS Stop freeze, exact-hash Keep authorization, changed-clip rejection, Mixed veto, and one-use drain')
    s.SPEAKERS['Dale']=[unit(0),unit(0)]
    boost_body=json.dumps({'name':'Dale','seconds':120}).encode()
    req=urllib.request.Request('http://127.0.0.1:%d/api/speakers/boost'%port,data=boost_body,
        headers={'Origin':'http://127.0.0.1:%d'%port,'X-Lens-Token':s.APP_TOKEN,
                 'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=4) as res: boosted=json.load(res)
    assert boosted['speakers']['profiles'][0]['boostSeconds']>0
    s.SPEAKERS['Dale']=[unit(0),unit(0),unit(1)]
    code,compacted=post('/api/speakers/compact',{'name':'Dale'})
    assert code==200 and compacted['compacted']['removed']==1 and compacted['speakers']['profiles'][0]['samples']==2
    code,_=post('/api/speakers/compact',{'name':'Dale'})
    assert code==422,'Server must reject compacting a two-example profile'
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
