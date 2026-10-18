"""Previous speaker safety behaviors + new model-evidence grounding (mock Ollama response)."""
from pathlib import Path
import importlib.util
import json
import io
root=Path(__file__).parent/'Conversation_Lens_Intelligent_Speaker_v6'
spec=importlib.util.spec_from_file_location('lens_v6_r',root/'server.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

def unit(i):
    x=[0.0]*256;x[i]=1.0;return x

def v(i,j=None,seconds=3.5):
    return {'full':unit(i),'first':unit(i),'second':unit(i if j is None else j),'speech_seconds':seconds}

def clear():s.forget_speakers()
for sent in ('This is what I meant','This is Dale?','Someone said this is Dale','Is this Dale?','Dale told me','She said "I am Dale"','I am sorry about that'):
    assert s.parse_self_introduction(sent) is None,sent
clear();result,event=s.recognize_or_learn('I am Dale.',v(0),False)
assert result['label']=='Unknown' and not event and not s.SPEAKERS
result,event=s.recognize_or_learn('This is Dale.',v(0,seconds=.8),True)
assert result['level']=='heard-only' and not s.SPEAKERS
result,event=s.recognize_or_learn('This is Dale.',v(0,j=1),True)
assert event['state']=='ambiguous' and not s.SPEAKERS
result,event=s.recognize_or_learn('This is Dale and I want to discuss something.',v(0),True,audio_id='clip-a')
assert event['state']=='candidate' and result['level']=='provisional'
result,event=s.recognize_or_learn('Here is why I am worried.',v(0),True,audio_id='clip-a')
assert len(s.SPEAKERS['Dale'])==1,'Duplicate audio was incorrectly treated as new evidence'
result,event=s.recognize_or_learn('Here is why I am worried.',v(0),True,audio_id='clip-b')
assert event['state']=='strengthened' and len(s.SPEAKERS['Dale'])==2
result,event=s.recognize_or_learn('I disagree with that view.',v(2),True,audio_id='clip-c')
assert result['label']=='Unknown'
clear();s.SPEAKERS.update({'Andrew':[unit(0),unit(0)],'Will':[unit(1),unit(1)]})
assert s.identify_speaker(v(0))['label']=='Andrew'
assert s.identify_speaker(v(0,j=1))['label']=='Mixed'
assert s.identify_speaker(v(2))['label']=='Unknown'
clear()

class Dummy:
 def __init__(self, response):self.b=io.BytesIO(json.dumps({'response':json.dumps(response)}).encode())
 def __enter__(self):return self.b
 def __exit__(self,*args):self.b.close()
orig=s.urllib.request.urlopen
try:
 s.urllib.request.urlopen=lambda request,timeout=0:Dummy({'observation':'A feeling was raised.','evidence':'They absolutely said something they never said','next_step':'What did you mean?','caution':''})
 ans=s.call_ollama({'goal':'Understand','turns':[{'speaker':'Me','text':'I need a little time to explain what I meant.'}]})
 assert ans['evidence']=='No matching quotation in the captured transcript'
 assert 'not an exact transcript quotation' in ans['caution']
 s.urllib.request.urlopen=lambda request,timeout=0:Dummy({'observation':'A need was raised.','evidence':'I need a little time','next_step':'Could you say more?','caution':''})
 ans=s.call_ollama({'turns':[{'speaker':'Me','text':'I need a little time to explain what I meant.'}]})
 assert ans['evidence']=='I need a little time'
finally:
 s.urllib.request.urlopen=orig
print('PASS previous v5 speaker safety, unknown/mixed voices, no consent, dedupe, model citation verification')
