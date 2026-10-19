"""Chromium runtime + mocked microphone and fetch; validates v6 UI state, not real device accuracy."""
from pathlib import Path
import os
import json
import tempfile
from playwright.sync_api import sync_playwright

BROWSER_EXECUTABLE=os.environ.get('LENS_BROWSER_EXECUTABLE') or next((p for p in ('/Applications/Brave Browser.app/Contents/MacOS/Brave Browser','/usr/bin/chromium','/usr/bin/chromium-browser') if Path(p).is_file()),'/usr/bin/chromium')

root=Path(__file__).parent
html=(root/'Conversation_Lens_Intelligent_Speaker_v6'/'Conversation_Lens_Live.html').read_text()
html=html.replace("if(!/^https?:$/.test(location.protocol)||!['127.0.0.1','localhost'].includes(location.hostname))","if(false)")
for module in ('lens_pcm_core.js','lens_pcm_capture.js'):
    source=(root/'experiments'/'packet-a'/module).read_text()
    html=html.replace(f'<script src="/packet-a/{module}"></script>',f'<script>{source}</script>')
stub='''<script>
window.fake={recorders:[],stopped:0,quiet:false,noiseRms:null,meterReads:0,transcribe:0,confirmCount:0,pcmUploads:[],drains:[],token:'ready-token',capture:null,closed:[],frozen:[],profiles:[],mergeSuggestions:[],transcriptQueue:[],whisperActive:'base',enrollmentTimerMs:[],
             dataSize:950,errors:[],voiceEnabled:[],pcmRenderOptions:[],captureLeaseSequence:0,aiRequests:0,aiBodies:[],aiRequestTimes:[],aiActive:0,aiMaxActive:0,aiDelayMs:0,aiEchoLatest:false,busy:false,takeovers:0};
const PCM16Ring=window.LensPCM.PCM16Ring;
window.LensPCM.PCM16Ring=class extends PCM16Ring{constructor(options){super(options);window.fake.pcmRing=this}};
const renderPCM=window.LensPCM.WindowTimeline.prototype.render;
window.LensPCM.WindowTimeline.prototype.render=function(id,options){window.fake.pcmRenderOptions.push({...options});return renderPCM.call(this,id,options)};
const trackedTimeout=window.setTimeout.bind(window);
window.setTimeout=function(callback,delay,...args){if(delay===7000||delay===10000)window.fake.enrollmentTimerMs.push(delay);return trackedTimeout(callback,delay,...args)};
window.fetch=async(path,opts={})=>{
 const ok=(v)=>new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}});
 if(path==='/api/status')return ok({app:'conversation-lens',protocol:3,token:window.fake.token,ready:true,model:'mock-local',stt:{ready:true},speakers:{ready:true,profiles:window.fake.profiles,mergeSuggestions:window.fake.mergeSuggestions}});
 if(path==='/api/whisper/models')return ok({active:window.fake.whisperActive+'.bin',switchAvailable:true,models:[{id:'aaaaaaaaaaaaaaaa',name:'base.bin',bytes:140000000,active:window.fake.whisperActive==='base'},{id:'bbbbbbbbbbbbbbbb',name:'small.bin',bytes:465000000,active:window.fake.whisperActive==='small'}]});
 if(path==='/api/whisper/switch'){const body=JSON.parse(opts.body);window.fake.whisperActive=body.model==='bbbbbbbbbbbbbbbb'?'small':'base';return ok({active:window.fake.whisperActive+'.bin',previous:'base.bin',model:{id:body.model,active:true}})}
 if(path==='/api/capture/open'){
  const request=JSON.parse(opts.body);if(!request.consent)throw Error('consent missing');
  if(window.fake.busy&&!request.takeover)return new Response(JSON.stringify({error:'Capture already active in another tab. Stop it or explicitly approve takeover.'}),{status:409,headers:{'Content-Type':'application/json'}});
  if(request.takeover)window.fake.takeovers++;
  window.fake.busy=false;
  window.fake.capture='id-'+(++window.fake.captureLeaseSequence)+'-'+'x'.repeat(30);
  return ok({capture:window.fake.capture});
 }
 if(path==='/api/capture/close'){
  window.fake.closed.push(JSON.parse(opts.body).capture);
  if(window.fake.capture===JSON.parse(opts.body).capture)window.fake.capture=null;
  return ok({closed:true});
 }
 if(path==='/api/capture/freeze'){const capture=JSON.parse(opts.body).capture;window.fake.frozen.push(capture);return ok({frozen:true,deadlineSeconds:90});}
 if(path==='/api/capture/drain'){window.fake.drains.push(JSON.parse(opts.body));window.fake.capture='drain-'+(++window.fake.captureLeaseSequence)+'-'+'x'.repeat(30);return ok({capture:window.fake.capture,deadlineSeconds:120});}
 if(path==='/api/session/erase'){
  if(!JSON.parse(opts.body).confirm)throw Error('Not confirmed');
  window.fake.profiles=[];window.fake.capture=null;
  return ok({closed:true,erased:true,speakers:{ready:true,profiles:[]}});
 }
 if(path==='/api/speakers')return ok({speakers:{ready:true,profiles:window.fake.profiles}});
 if(path==='/api/speakers/export')return ok({schemaVersion:1,profiles:[{name:'Temporary',vectors:[[1,...Array(255).fill(0)],[1,...Array(255).fill(0)]]}],sha256:'a'.repeat(64)});
 if(path==='/api/speakers/import'){const body=JSON.parse(opts.body);window.fake.profiles=body.profiles.map(p=>({name:p.name,samples:p.vectors.length,active:p.vectors.length>=2}));return ok({speakers:{ready:true,profiles:window.fake.profiles,ramBytes:2048}})}
 if(path==='/api/speakers/boost'){
  const body=JSON.parse(opts.body),entry=window.fake.profiles.find(p=>p.name===body.name);
  if(entry)entry.boostSeconds=body.seconds;
  return ok({speakers:{ready:true,profiles:window.fake.profiles,ramBytes:2048}});
 }
 if(path==='/api/speakers/compact'){
  const body=JSON.parse(opts.body),entry=window.fake.profiles.find(p=>p.name===body.name);
  if(!entry||entry.samples<3)return new Response(JSON.stringify({error:'At least three samples are required to compact'}),{status:422,headers:{'Content-Type':'application/json'}});
  const removed=entry.samples-2;entry.samples=2;
  return ok({compacted:{name:body.name,before:removed+2,after:2,removed},speakers:{ready:true,profiles:window.fake.profiles,ramBytes:1024}});
 }
 if(path==='/api/ollama/check')return ok({ready:true,model:'gemma3:4b',reason:'Model available'});
 if(path==='/api/health')return ok({ok:true,protocol:3,speakerRamBytes:2048,captureActive:!!window.fake.capture,captureOwner:window.fake.capture?'tab-a1b2c3d4':null,captureAgeSeconds:window.fake.capture?12:null});
 if(path==='/api/diagnostics')return ok({protocol:3,events:[{at:0,kind:'decode',state:'ok',elapsedMs:20},{at:1,kind:'vad',state:'speech',elapsedMs:8},{at:2,kind:'asr',state:'ok',elapsedMs:140},{at:3,kind:'embedding',state:'ok',elapsedMs:210},{at:4,kind:'speaker_match',state:'ok',elapsedMs:1},{at:5,kind:'audio',state:'ok',elapsedMs:380}]});
 if(path==='/api/speakers/forget'){
  const name=JSON.parse(opts.body).name;
  window.fake.profiles=window.fake.profiles.filter(x=>name&&x.name!==name);
  return ok({speakers:{ready:true,profiles:window.fake.profiles}});
 }
 if(path==='/api/transcribe'){
  if(opts.headers['Content-Type']==='audio/wav')window.fake.pcmUploads.push({contentType:opts.headers['Content-Type'],forceMixed:opts.headers['X-Lens-Force-Mixed']||'',bytes:opts.body.size||opts.body.byteLength});
  window.fake.transcribe++;window.fake.voiceEnabled.push(opts.headers['X-Lens-Auto-Names']);
  if(!opts.headers['X-Lens-Capture-Session']||opts.headers['X-Lens-Capture-Session']!==window.fake.capture)throw Error('Capture session missing');
  const item=window.fake.transcriptQueue.shift()||{text:'Sample sentence',speaker:{label:'Unknown'}};
  await new Promise((resolve,reject)=>{const id=setTimeout(resolve,15);opts.signal?.addEventListener('abort',()=>{clearTimeout(id);reject(new DOMException('Cancelled','AbortError'))},{once:true})});
  if(item.introduction?.state==='candidate')window.fake.profiles.push({name:item.introduction.name,samples:1,active:false,source:'conversation'});
  if(item.introduction?.state==='strengthened'){
    const p=window.fake.profiles.find(x=>x.name===item.introduction.name);if(p){p.samples=3;p.active=true;p.lastSeenSeconds=3}
  }
  return ok(item);
 }
if(path==='/api/analyze'){
 const body=JSON.parse(opts.body);window.fake.aiRequests++;window.fake.aiBodies.push(body);window.fake.aiRequestTimes.push(performance.now());window.fake.aiActive++;window.fake.aiMaxActive=Math.max(window.fake.aiMaxActive,window.fake.aiActive);
 try{if(window.fake.aiDelayMs)await new Promise((resolve,reject)=>{const id=setTimeout(resolve,window.fake.aiDelayMs);opts.signal?.addEventListener('abort',()=>{clearTimeout(id);reject(new DOMException('Cancelled','AbortError'))},{once:true})})}
 finally{window.fake.aiActive--}
 return ok({insight:{evidence_status:'exact',observation:window.fake.aiEchoLatest?'Echo: '+(body.turns.at(-1)?.text||'empty'):'A clarification request was captured.',evidence:'I want to clarify the precise delivery date.',next_step:'What date should we agree on?',caution:'Automatic transcript may have errors'}})
}
 if(path==='/api/speakers/enroll')return ok({name:opts.headers['X-Lens-Speaker'],samples:1,message:'Record another sample'});
 throw Error('Unexpected fetch '+path);
};
Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{
 const track={stop(){window.fake.stopped++},addEventListener(){}};
 return {getTracks:()=>[track],getAudioTracks:()=>[track]};
}}});
window.MediaRecorder=class{
 static isTypeSupported(x){return x.includes('webm')}
 constructor(s,opt){this.state='inactive';this.mimeType='audio/webm';window.fake.recorders.push(this)}
 start(){this.state='recording'}
 stop(){if(this.state==='inactive')return;this.state='inactive';setTimeout(()=>{
   this.ondataavailable?.({data:new Blob([new Uint8Array(window.fake.dataSize)],{type:'audio/webm'})});this.onstop?.();},0)}
};
window.AudioContext=class{
 createMediaStreamSource(){return {connect(){},disconnect(){}}}
 createAnalyser(){return {fftSize:1024,getByteTimeDomainData(a){window.fake.meterReads++;const amp=window.fake.noiseRms==null ? 17 : Math.SQRT2*window.fake.noiseRms*128;for(let i=0;i<a.length;i++)a[i]=window.fake.quiet?128:128+Math.round(amp*Math.sin(i/7));},getFloatTimeDomainData(a){const amp=window.fake.noiseRms==null ? .08 : Math.SQRT2*window.fake.noiseRms;for(let i=0;i<a.length;i++)a[i]=window.fake.quiet?0:amp*Math.sin(i/7)}}}
 resume(){return Promise.resolve()}
 close(){return Promise.resolve()}
};
window.confirm=()=>{window.fake.confirmCount++;return true};
</script>'''
assert html.count('<script>\n(()=>')==1
html=html.replace('<script>\n(()=>',stub+'<script>\n(()=>')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=BROWSER_EXECUTABLE,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (1200,375):
        page=browser.new_page(viewport={'width':width,'height':830})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('http://localhost/**',lambda route:route.fulfill(status=200,content_type='text/html',body=html))
        page.goto('http://localhost/')
        page.wait_for_function("document.querySelector('#capability').textContent.includes('LOCAL WHISPER READY')")
        page.wait_for_function("document.querySelector('#whisperModel').options.length===2")
        page.locator('#whisperModel').select_option('bbbbbbbbbbbbbbbb')
        page.locator('#switchWhisperModel').click()
        page.wait_for_function("document.querySelector('#whisperModelStatus').textContent.includes('Active model: small.bin')")
        assert page.locator('#capability').inner_text().endswith('small.bin')
        assert not page.locator('#startBtn').is_enabled()
        assert not page.locator('#aiToggle').is_checked(),'Big Mac AI must be opt-in even when available'
        assert page.locator('#aiToggle').is_enabled()
        assert not page.locator('#autoNames').is_checked()
        # Even a browser-restored old value must not preload a private scenario.
        assert page.locator('#context').input_value()==''
        assert page.locator('#aim').input_value()=='observe'
        assert page.locator('#manualSpeaker').input_value()=='shared'
        assert 'not assuming a topic' in page.locator('#northStar').inner_text().lower() or 'without assuming a topic' in page.locator('#northStar').inner_text().lower()
        assert 'Waiting for conversation' in page.locator('#cueTitle').inner_text()
        page.locator('#contrastMode').check()
        assert page.locator('html').get_attribute('data-contrast')=='high'
        contrast=page.evaluate("""()=>{const rgb=s=>{let v=getComputedStyle(document.documentElement).getPropertyValue(s).trim().replace('#','');if(v.length===3)v=[...v].map(x=>x+x).join('');const a=[0,2,4].map(i=>parseInt(v.slice(i,i+2),16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return .2126*a[0]+.7152*a[1]+.0722*a[2]};const bg=rgb('--bg');return [rgb('--ink'),rgb('--muted')].map(x=>(Math.max(x,bg)+.05)/(Math.min(x,bg)+.05))}""")
        assert min(contrast)>=7.0,contrast
        page.locator('#contrastMode').uncheck()
        page.locator('#monoMode').check();assert 'monospace' in page.evaluate("getComputedStyle(document.body).fontFamily");page.locator('#monoMode').uncheck()
        page.locator('#motionMode').check();assert page.locator('html').get_attribute('data-low-motion')=='on';assert page.evaluate("getComputedStyle(document.querySelector('#status .led')).animationName")=='none';page.locator('#motionMode').uncheck()
        page.locator('#enrollName').fill('Preview')
        page.locator('#enrollConsent').check()
        page.locator('#enrollDuration').select_option('10')
        assert page.get_by_role('button',name='Record a voice sample (10s)').is_visible()
        page.locator('#enrollDuration').select_option('7')
        page.get_by_role('button',name='Record a voice sample (7s)').click()
        page.wait_for_function("document.querySelector('#enrollQuality').getAttribute('aria-valuenow')==='100'")
        assert 'not speaker identity' in page.locator('#enrollQualityText').inner_text()
        page.evaluate('window.fake.noiseRms=0')
        page.wait_for_function("Number(document.querySelector('#enrollQuality').getAttribute('aria-valuenow'))<100")
        page.evaluate('window.fake.noiseRms=.75')
        page.wait_for_function("()=>{const m=document.querySelector('#enrollQualityText').textContent.match(/clipping in (\\d+)%/);return m&&Number(m[1])>0}")
        assert page.evaluate('window.fake.enrollmentTimerMs.at(-1)')==7000
        assert 'for seven seconds' not in page.locator('#enrollMessage').inner_text(),'Enrollment prompt must reflect the selected duration'
        page.get_by_role('button',name='Cancel voice sample').click()
        page.wait_for_function("document.querySelector('#enrollMessage').textContent.includes('Sample canceled')")
        page.evaluate('window.fake.noiseRms=null')
        page.locator('#enrollDuration').select_option('10')
        page.get_by_role('button',name='Record a voice sample (10s)').click()
        page.wait_for_function("document.querySelector('#enrollMessage').textContent.includes('Recording Preview for 10 seconds')")
        assert page.evaluate('window.fake.enrollmentTimerMs.at(-1)')==10000,'Long follow-up must change the actual capture timer'
        page.get_by_role('button',name='Cancel voice sample').click()
        page.wait_for_function("document.querySelector('#enrollMessage').textContent.includes('Sample canceled')")
        page.locator('#enrollConsent').uncheck()
        import_bundle={'schemaVersion':1,'profiles':[{'name':'Temporary','vectors':[[1.0]+[0.0]*255,[1.0]+[0.0]*255]}],'sha256':'a'*64}
        page.locator('#importProfiles').set_input_files({'name':'profiles.json','mimeType':'application/json','buffer':json.dumps(import_bundle).encode()})
        page.wait_for_function("document.querySelector('#profileFileStatus').textContent.includes('Imported 1 profile')")
        with page.expect_download() as download_info:
            page.locator('#exportProfiles').click()
        assert download_info.value.suggested_filename=='conversation-lens-voice-profiles-v1.json'
        assert 'No profile file is stored' in page.locator('#profileFileStatus').inner_text()
        page.get_by_role('button',name='Forget Temporary').click()
        page.wait_for_function("!document.querySelector('#speakerProfiles').textContent.includes('Temporary')")
        if width<810:
            expected=['listenTitle','cueTitle','transcriptTitle','signalTitle','aiTitle','speakerTitle','setupTitle','anchorTitle']
            dom_order=lambda:page.evaluate("() => [...document.querySelectorAll('.grid > section')].map(e => e.querySelector('h2')?.id)")
            assert dom_order()==expected,dom_order()
            # Resize twice: moving existing panels must preserve actual element identity and tab order.
            page.set_viewport_size({'width':940,'height':830})
            page.wait_for_function("!document.querySelector('.grid').classList.contains('mobile-layout')")
            assert page.locator('.left-col > section').count()==4 and page.locator('.right-col > section').count()==4
            page.set_viewport_size({'width':width,'height':830})
            page.wait_for_function("document.querySelector('.grid').classList.contains('mobile-layout')")
            assert dom_order()==expected
        else:
            left_tops=page.evaluate("() => ['#listenPanel','#transcriptPanel','#speakerPanel','#setupPanel'].map(s => document.querySelector(s).getBoundingClientRect().top)")
            assert left_tops==sorted(left_tops),f'Desktop left column must order Listen -> Transcript -> Speakers -> Setup, got {left_tops}'
            right_tops=page.evaluate("() => ['#heroCuePanel','#signalPanel','#aiPanel','#anchorPanel'].map(s => document.querySelector(s).getBoundingClientRect().top)")
            assert right_tops==sorted(right_tops),f'Desktop right column must order Hero Cue -> Local Signals -> AI -> Anchor, got {right_tops}'
        assert 'solidarity' not in page.content().lower()
        # Optional user context is allowed during a session, but Erase resets it.
        page.locator('#context').fill('Discuss project documentation')
        page.locator('#aim').select_option('resolve')
        assert page.locator('#contextPin').is_visible()
        assert 'Discuss project documentation' in page.locator('#contextPinText').inner_text()
        assert page.locator('#contextPin').evaluate("e=>getComputedStyle(e).position")=='sticky'
        page.evaluate('window.scrollTo(0,700)')
        assert page.locator('#contextPin').evaluate('e=>e.getBoundingClientRect().top')<=12
        page.evaluate('window.scrollTo(0,0)')
        page.locator('#enrollName').fill('Morgan')
        page.locator('#consent').check();page.locator('#autoNames').check()
        page.evaluate("window.fake.transcriptQueue.push({text:'Hi, this is Dale, and I would like to talk about how I feel.',speaker:{label:'Dale',level:'provisional',reason:'Spoken introduction'},introduction:{name:'Dale',state:'candidate',message:'Self introduced'}})")
        page.locator('#startBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
        assert page.evaluate('window.fake.capture') is not None
        page.locator('#loadDiagnostics').evaluate("e=>e.closest('details').open=true")
        page.locator('#loadDiagnostics').click()
        page.wait_for_function("document.querySelector('#healthPill').textContent.includes('tab-a1b2c3d4 owns capture · 12s')")
        page.wait_for_function('window.fake.meterReads>2')
        assert page.locator('#levelText').inner_text().startswith('Input')
        # Ensure a bit of energy registered before forced early window close.
        page.wait_for_timeout(340)
        page.evaluate('window.fake.recorders.at(-1).stop()')
        page.wait_for_function("document.querySelectorAll('.turn').length===1")
        assert page.locator('.who').last.inner_text()=='Dale ?'
        assert 'MediaRecorder audio' in page.locator('#pcmReplaySelect').inner_text(),'Default WebM recorder clips should also enter bounded replay history'
        assert page.evaluate('window.fake.transcribe')==1
        page.locator('#pauseBtn').click()
        assert page.locator('#pauseBtn').inner_text()=='Resume cues'
        # Second window closes on ~900ms of detected silence, after a minimum ~2.8s.
        page.evaluate("window.fake.transcriptQueue.push({text:'I want us to understand each other.',speaker:{label:'Dale',level:'probable',reason:'Tentative acoustic',evidence:{full:{best:'Dale',cosine:.9345,margin:.1456},first:{best:'Dale',cosine:.901,margin:.101},second:{best:'Dale',cosine:.909,margin:.112},halfCosine:.85,possibleOverlap:false,speechSeconds:2.5}},introduction:{name:'Dale',state:'strengthened',message:'Two matching windows'}})")
        page.wait_for_timeout(950)
        page.evaluate('window.fake.quiet=true')
        page.wait_for_function('window.fake.recorders.length>=3',timeout=9000)
        page.wait_for_function("document.querySelectorAll('.turn').length>=2")
        assert page.evaluate('window.fake.transcribe')>=2,'Pausing coaching cues must not stop hot local transcription'
        assert page.locator('.who').last.inner_text()=='Dale'
        page.locator('#pauseBtn').click()
        assert page.locator('#pauseBtn').inner_text()=='Pause cues'
        assert 'Dale · 2.5s (100% of attributed spans)' in page.locator('#talkTimeStats').inner_text()
        assert page.locator('#levelText').inner_text().startswith('Quiet')
        assert page.locator('#levelRail').get_attribute('aria-valuenow')=='0'
        page.get_by_role('button',name='Boost for two minutes: Dale').click()
        page.wait_for_function("document.querySelector('#speakerProfiles').textContent.includes('Boost 120s')")
        assert 'last seen 3s ago' in page.locator('#speakerProfiles').inner_text()
        page.get_by_role('button',name='Disable boost for Dale').click()
        page.wait_for_function("document.querySelector('#speakerProfiles').textContent.includes('Boost 2m')")
        compact=page.get_by_role('button',name='Compact Dale voice samples to two representative examples')
        assert compact.count()==1 and compact.is_visible()
        compact.click()
        page.wait_for_function("document.querySelector('#speakerProfiles').textContent.includes('2 windows')")
        assert 'discarded 1 from server RAM' in page.locator('#enrollMessage').inner_text()
        # The newest audio window's true meter samples and timing are visible, not a synthetic audio graphic.
        assert page.locator('#energyCanvas').count()==1
        assert page.locator('#durationHistogram').count()==1
        assert page.locator('#durationHistogram').evaluate("e=>{const d=e.getContext('2d').getImageData(0,0,e.width,e.height).data;return d.some((v,i)=>i%4===0&&v>50)}"),'The duration histogram must be drawn from observed windows'
        assert 'windows' in page.locator('#durationDistribution').inner_text()
        assert 'silence at' in page.locator('#cutHistory').inner_text()
        page.get_by_role('button',name='Evidence for passage 2').click()
        assert page.locator('#evidenceDrawer').is_visible()
        assert '0.9345' in page.locator('#evidenceScores').inner_text()
        assert '0.1456' in page.locator('#evidenceScores').inner_text()
        assert page.locator('#evidenceScores meter').count()==4,'Full, half, and two half-window cosine strips should be visible'
        assert 'not an identity probability' in page.locator('#evidenceScores meter').first.get_attribute('aria-label')
        assert 'cosine gap 0.0080' in page.locator('#evidenceScores').inner_text()
        assert page.locator('.overlap-heat-fill').count()==1
        assert 'not an overlap probability' in page.locator('.overlap-heat').inner_text()
        page.locator('#closeEvidence').click()
        # Manual speaker assignment never changes the recorded acoustic score.
        speaker_choice=page.locator('#passage-2 select[aria-label="Correct speaker for this passage"]')
        speaker_choice.select_option('mixed')
        assert page.locator('#passage-2 .who').inner_text()=='Mixed'
        speaker_choice=page.locator('#passage-2 select[aria-label="Correct speaker for this passage"]')
        speaker_choice.select_option('name:Dale')
        assert page.locator('#passage-2 .who').inner_text().startswith('Dale')
        page.locator('#filterKeyword').fill('understand')
        assert page.locator('.turn').count()==1
        page.locator('#filterKeyword').fill('')
        page.locator('#filterSpeaker').select_option('name:Dale')
        assert page.locator('.turn').count()==2
        page.locator('#filterSpeaker').select_option('all')
        page.locator('#speakerLockName').select_option('Dale')
        page.locator('#speakerLockCount').fill('2')
        page.locator('#speakerLockBtn').click()
        assert 'Pinned Dale for 2 eligible future window' in page.locator('#speakerLockStatus').inner_text()
        page.evaluate("window.fake.transcriptQueue.push({text:'First window under the speaker pin.',speaker:{label:'Unknown',reason:'No match'}},{text:'Overlapped window under the speaker pin.',speaker:{label:'Mixed',reason:'Acoustic overlap'}},{text:'Second eligible window under the speaker pin.',speaker:{label:'Unknown',reason:'No match'}})")
        page.evaluate('window.fake.quiet=false')
        page.wait_for_function("[...document.querySelectorAll('.turn-text')].some(e=>e.textContent==='First window under the speaker pin.')",timeout=10000)
        assert page.locator('.turn').last.locator('.who').inner_text()=='Dale'
        assert 'Owner-pinned speaker label' in page.locator('.turn').last.inner_text()
        page.wait_for_function("[...document.querySelectorAll('.turn-text')].some(e=>e.textContent==='Overlapped window under the speaker pin.')",timeout=10000)
        assert page.locator('.turn').last.locator('.who').inner_text().startswith('Mixed'), 'A speaker pin must not override the acoustic Mixed veto'
        assert 'Pinned Dale for 1 eligible future window' in page.locator('#speakerLockStatus').inner_text(), 'Mixed results must not consume eligible pin windows'
        page.wait_for_function("[...document.querySelectorAll('.turn-text')].some(e=>e.textContent==='Second eligible window under the speaker pin.')",timeout=10000)
        assert page.locator('.turn').last.locator('.who').inner_text()=='Dale'
        assert page.evaluate("window.fake.voiceEnabled.slice(-3)")==['disabled','disabled','disabled'],'Manual speaker locks must bypass name learning'
        assert 'No speaker label pinned.' in page.locator('#speakerLockStatus').inner_text()
        page.evaluate('window.fake.quiet=true')
        page.locator('#speakerLockName').select_option('Dale')
        page.locator('#speakerLockCount').fill('5')
        page.locator('#speakerLockBtn').click()
        assert 'Pinned Dale for 5 eligible future window' in page.locator('#speakerLockStatus').inner_text()
        page.locator('#speakerLockName').select_option('')
        page.locator('#speakerLockBtn').click()
        assert 'No speaker label pinned.' in page.locator('#speakerLockStatus').inner_text()
        page.get_by_role('button',name='Bookmark passage 2').click()
        assert page.locator('#passage-2').evaluate("(e)=>e.classList.contains('bookmarked')")
        page.get_by_role('button',name='Highlight passage 2').click()
        assert page.locator('#passage-2').evaluate("(e)=>e.classList.contains('highlighted')")
        page.locator('#layoutMode').select_option('transcript')
        assert page.locator('.grid').get_attribute('data-layout')=='transcript'
        page.locator('#layoutMode').select_option('split')
        if width<810:
            page.locator('#sheetToggle').click()
            assert page.locator('.hero-cue').get_attribute('data-collapsed')=='false'
            page.locator('#sheetToggle').click()
            page.evaluate('''() => {const sheet=document.querySelector('.hero-cue');const fire=(type,y,key)=>{const e=new Event(type,{bubbles:true});Object.defineProperty(e,key,{value:[{clientY:y}]});sheet.dispatchEvent(e)};fire('touchstart',250,'touches');fire('touchend',150,'changedTouches')}''')
            assert page.locator('.hero-cue').get_attribute('data-collapsed')=='false','Upward flick should expand the mobile coaching sheet'
            page.evaluate('''() => {const sheet=document.querySelector('.hero-cue');const fire=(type,y,key)=>{const e=new Event(type,{bubbles:true});Object.defineProperty(e,key,{value:[{clientY:y}]});sheet.dispatchEvent(e)};fire('touchstart',150,'touches');fire('touchend',250,'changedTouches')}''')
            assert page.locator('.hero-cue').get_attribute('data-collapsed')=='true','Downward flick should collapse the mobile coaching sheet'
        page.locator('#signals .evidence-link').first.wait_for(timeout=4000)
        page.locator('#signals .evidence-link').first.click()
        assert page.evaluate('document.activeElement.id')=='passage-2','Grounded cue must focus its source passage'
        page.get_by_role('button',name='Correct words in passage 2').click()
        assert page.locator('#editDialog').evaluate('(e)=>e.open')
        page.locator('#editText').fill('I want to clarify the precise delivery date.')
        page.locator('#editForm button[type="submit"]').click()
        assert page.locator('#passage-2 .turn-text').inner_text()=='I want to clarify the precise delivery date.'
        assert 'words corrected' in page.locator('#passage-2 .turn-meta').inner_text()
        assert page.evaluate('window.fake.aiRequests')==0,'AI was invoked before explicit opt-in'
        page.locator('#privateNote').fill('Remember my objective without changing the transcript')
        page.locator('#coachPreset').select_option('custom')
        page.locator('#customFragment').fill('Prefer concise questions and observable facts.')
        page.locator('#groundingMode').select_option('fuzzy')
        page.locator('#loadDiagnostics').evaluate("e=>e.closest('details').open=true")
        page.locator('#loadDiagnostics').click()
        page.wait_for_function("document.querySelector('#healthPill').textContent.includes('LOCAL HEALTH OK')")
        assert 'audio ok 380ms' in page.locator('#diagnosticLog').inner_text()
        assert 'Whisper ASR · ok' in page.locator('#workerStageGraph').inner_text()
        assert 'Speaker embedding · ok' in page.locator('#workerStageGraph').inner_text()
        page.locator('#checkModelBtn').evaluate("e=>e.closest('details').open=true")
        page.locator('#checkModelBtn').click()
        page.locator('#aiToggle').check()
        page.wait_for_function('window.fake.aiRequests>=1',timeout=6500)
        body=page.evaluate('window.fake.aiBodies.at(-1)')
        assert body['note']=='Remember my objective without changing the transcript'
        assert body['grounding']=='fuzzy'
        assert body['system_fragment']=='Prefer concise questions and observable facts.'
        assert body['ollama']['model']=='gemma3:4b'
        assert any(t['speaker']=='Dale' and t['manual'] for t in body['turns'])
        assert page.locator('#groundingBadge').inner_text()=='EXACT'
        if width<810:page.locator('#sheetToggle').click()  # open the bottom sheet to reach the cue controls
        page.locator('#getCueBtn').click()
        if width<810:page.locator('#sheetToggle').click()
        page.wait_for_function('window.fake.aiRequests>=2',timeout=3500)
        history_card=page.locator('#coachingTimeline .history-card').first
        card_line=history_card.locator('.history-actions input')
        card_line.fill('Card-specific suggested question?')
        assert card_line.input_value()=='Card-specific suggested question?'
        page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>window.fake.copied=text}});Object.defineProperty(window,'isSecureContext',{configurable:true,value:true})")
        history_card.locator('.history-actions button').nth(0).click()
        page.wait_for_function("window.fake.copied==='Card-specific suggested question?'")
        regen=history_card.get_by_role('button',name='Regenerate')
        assert regen.is_enabled()
        regen.click();page.wait_for_function('window.fake.aiRequests>=3',timeout=4000)
        page.wait_for_function("document.querySelector('#coachingTimeline .history-actions input').value==='What date should we agree on?'")
        if width<810:page.locator('#sheetToggle').click()
        page.locator('#continueThoughtBtn').click()
        page.wait_for_function('window.fake.aiRequests>=4',timeout=4000)
        continuation=page.evaluate('window.fake.aiBodies.at(-1).continuation')
        assert 'AI regeneration' in continuation and 'current transcript' not in continuation
        page.wait_for_function("document.querySelector('#continueThoughtStatus').textContent.includes('Generated')")
        page.wait_for_function('window.fake.aiActive===0')
        debounce_before=page.evaluate('window.fake.aiRequests')
        page.evaluate('''() => {
          window.fake.debounceStarted=performance.now();
          for(const text of ['The owner confirmed the first review date.','The team needs the final outline before Friday.','We agreed to share the revised draft tomorrow.']){
            const input=document.querySelector('#manualText');input.value=text;
            document.querySelector('#manualForm').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
          }
        }''')
        page.wait_for_function(f'window.fake.aiRequests==={debounce_before+1}',timeout=6500)
        debounce_ms=page.evaluate('window.fake.aiRequestTimes.at(-1)-window.fake.debounceStarted')
        assert 250<=debounce_ms<=5700, f'Automatic cue request should respect the debounce/rate-limit window, got {debounce_ms:.0f}ms'
        page.wait_for_timeout(400)
        assert page.evaluate('window.fake.aiRequests')==debounce_before+1,'Rapid transcript updates should coalesce into one automatic request'
        page.evaluate('window.fake.aiDelayMs=350;window.fake.aiEchoLatest=true;window.fake.manualAt=performance.now()')
        page.locator('#getCueBtn').click()
        page.wait_for_function(f'window.fake.aiRequests==={debounce_before+2}',timeout=1000)
        manual_ms=page.evaluate('window.fake.aiRequestTimes.at(-1)-window.fake.manualAt')
        assert manual_ms<250, f'Manual cue should bypass debounce, got {manual_ms:.0f}ms'
        page.evaluate('''() => {
          const input=document.querySelector('#manualText');input.value='The latest change needs a new delivery date.';
          document.querySelector('#manualForm').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
        }''')
        page.locator('#getCueBtn').click()  # Explicitly request the queued latest passage while the prior call is still in flight.
        page.wait_for_function(f'window.fake.aiRequests==={debounce_before+3}',timeout=2000)
        assert page.evaluate('window.fake.aiMaxActive')==1,'A newer passage must queue behind an in-flight request, not overlap it'
        assert not page.locator('#aiObservation').inner_text().startswith('Echo:'),'A stale response must not replace the prior result'
        page.wait_for_function("document.querySelector('#aiObservation').textContent==='Echo: The latest change needs a new delivery date.'",timeout=2000)
        page.evaluate('window.fake.aiDelayMs=0;window.fake.aiEchoLatest=false')
        page.locator('#aiEvidenceJump').wait_for(timeout=4000)
        page.locator('#aiEvidenceJump').click()
        assert page.evaluate('document.activeElement.id')=='passage-2'
        assert 'Up to date' in page.locator('#queueText').inner_text()
        with page.expect_download() as download_event:
            page.locator('#exportTranscriptBtn').click()
        assert download_event.value.suggested_filename=='conversation-lens-session.md'
        exported=Path(download_event.value.path()).read_text()
        assert '★ [highlight]' in exported
        with page.expect_download() as plain_event:
            page.locator('#exportPlainBtn').click()
        assert plain_event.value.suggested_filename=='conversation-lens-transcript.md'
        plain_export=Path(plain_event.value.path()).read_text()
        assert '★ [highlight]' in plain_export and 'I want to clarify the precise delivery date.' in plain_export
        # The keyboard layer works only outside form controls.
        page.evaluate('document.activeElement.blur()')
        page.keyboard.press('m')
        assert page.locator('#passage-2 .who').inner_text()=='Mixed'
        page.evaluate('document.activeElement.blur()')
        page.keyboard.press('1')
        assert page.locator('#passage-2 .who').inner_text()=='Me'
        confirms_before=page.evaluate('window.fake.confirmCount')
        page.get_by_role('button',name='Forget Dale').click()
        page.wait_for_function("!document.querySelector('#speakerProfiles').textContent.includes('Dale')")
        assert page.evaluate('window.fake.confirmCount')==confirms_before,'Removing one session speaker should be immediate'
        assert page.locator('#passage-2 .who').inner_text()=='Me','Removing a voice profile must not rewrite transcript labels'
        page.locator('#aiToggle').uncheck()
        page.locator('#manualText').fill('We decided to review the outline Friday. I will send it Thursday.')
        page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelectorAll('#actionLedger .action-item').length>=2")
        assert 'possible decision' in page.locator('#actionLedger').inner_text().lower()
        assert 'possible action' in page.locator('#actionLedger').inner_text().lower()
        page.locator('#manualText').fill('Please let me finish.')
        page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Turn-taking')")
        page.locator('#manualText').fill('On a different topic, I will send the updated file.')
        page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Topic transition')")
        page.locator('#manualText').fill('I interrupted you and talked over your answer.')
        page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Possible interruption')",timeout=5000)
        assert 'does not independently establish timing' in page.locator('#signals').inner_text()
        page.locator('#customRulesPanel').evaluate('e=>e.open=true')
        page.locator('#customRulePhrase').fill('delivery date')
        page.locator('#customRuleObservation').fill('The owner asked to notice this delivery-date phrase.')
        page.locator('#customRuleNext').fill('Should we confirm the delivery date?')
        page.locator('#customRulePriority').select_option('5')
        page.locator('#addCustomRule').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Custom cue matched: delivery date')")
        custom_card=page.locator('#signals .insight').filter(has_text='Custom cue matched: delivery date')
        assert custom_card.locator('button.evidence-link').count()==1
        custom_card.locator('button.evidence-link').click()
        assert page.evaluate("document.activeElement.id.startsWith('passage-')")
        for _ in range(12):
            page.locator('#manualText').fill('The delivery outline remains ready for review.')
            page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Possible loop')",timeout=5000)
        assert 'does not prove a stalemate' in page.locator('#signals').inner_text()
        for line in [
            'The orbital telescope measured distant galaxies with infrared sensors.',
            'Researchers calibrated the observatory using reference stars.',
            'Spectral measurements reveal ancient nebulae around massive stars.',
            'The kitchen recipe needs toasted sesame ginger and scallions.',
            'Roast vegetables with cumin before adding chickpeas.',
            'Serve lentils beside warm flatbread and yogurt.',
        ]:
            page.locator('#manualText').fill(line);page.get_by_role('button',name='Add line').click()
        page.wait_for_timeout(250)
        assert 'Recent wording has shifted' in page.locator('#signals').text_content(), (page.locator('#signals').inner_text(),page.locator('.turn-text').all_inner_texts())
        lexical_card=page.locator('#signals .insight').filter(has_text='Recent wording has shifted')
        assert lexical_card.count()==1 and 'Recent wording has shifted' in lexical_card.inner_text(),page.locator('#signals').inner_text()
        assert lexical_card.locator('button.evidence-link').count()==1
        for line in [
            'Lentils simmer with cumin, sesame, yogurt, and flatbread.',
            'Serve lentils with cumin, sesame, yogurt, and flatbread.',
            'Cook lentils with cumin, sesame, yogurt, and flatbread.',
            'Lentils pair with cumin, sesame, yogurt, and flatbread.',
            'Add cumin, sesame, yogurt, and flatbread beside lentils.',
            'Warm lentils with cumin, sesame, yogurt, and flatbread.',
        ]:
            page.locator('#manualText').fill(line);page.get_by_role('button',name='Add line').click()
        page.wait_for_timeout(250)
        assert 'Recent wording has shifted' not in page.locator('#signals').inner_text(), 'A stable vocabulary window should not raise a topic-shift cue'
        page.evaluate('window.fake.quiet=false');page.wait_for_function("window.fake.recorders.at(-1)?.state==='recording'");page.wait_for_timeout(350)
        page.locator('#pauseIntakeBtn').click();page.evaluate('window.fake.recorders.at(-1).stop()')
        page.wait_for_function("document.querySelector('#skippedWindows').textContent.includes('Intake paused') && document.querySelector('#skippedWindows').textContent.includes('Reprocess buffered audio')")
        retry_count=page.evaluate('window.fake.transcribe')
        turn_count=page.locator('.turn').count()
        page.get_by_role('button',name='Reprocess buffered audio').click()
        page.wait_for_function(f'window.fake.transcribe>{retry_count}')
        page.wait_for_function(f'document.querySelectorAll(".turn").length>{turn_count}')
        assert '1 skipped' in page.locator('#skipCount').inner_text()
        page.locator('#pauseIntakeBtn').click();page.evaluate('window.fake.quiet=true');page.wait_for_timeout(200)
        page.screenshot(path=str(root/('qa_v6_desktop.png' if width>800 else 'qa_v6_mobile.png')),full_page=True)
        page.evaluate("window.confirm=(message)=>{window.fake.confirmCount++;return !String(message||'').startsWith('Keep pending audio window')}")
        page.locator('#stopBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        page.evaluate("window.confirm=()=>{window.fake.confirmCount++;return true}")
        page.wait_for_function('window.fake.closed.length>=1')
        assert page.evaluate('window.fake.capture') is None
        assert page.evaluate('window.fake.stopped')>=1
        assert page.locator('#levelFill').get_attribute('style')=='width: 0%;'
        transcript_before_note=page.locator('#transcript').inner_text()
        page.evaluate('document.activeElement.blur()')
        page.keyboard.press('a')
        page.wait_for_function("document.querySelector('#voiceNoteStatus').textContent.includes('Recording a private note')")
        page.keyboard.press('a')
        page.wait_for_function("document.querySelector('#voiceNoteStatus').textContent.includes('saved in memory')")
        assert page.locator('#voiceNoteList audio').count()==1
        assert page.locator('#transcript').inner_text()==transcript_before_note,'voice note must remain outside the transcript'
        page.locator('#privateNote').fill('Private snapshot note')
        with page.expect_download() as snapshot_event:
            page.locator('#snapshotBtn').click()
        snapshot_path=snapshot_event.value.path()
        snapshot=json.loads(Path(snapshot_path).read_text())
        assert snapshot['payload']['schema']=='conversation-lens-session' and snapshot['payload']['version']==1
        assert snapshot['payload']['omittedVoiceNoteCount']==1
        assert 'evidence' not in snapshot['payload']['turns'][0] and 'audio' not in snapshot['payload']
        page.locator('#manualText').fill('Temporary replacement text')
        page.get_by_role('button',name='Add line').click()
        with tempfile.TemporaryDirectory() as td:
            bad=dict(snapshot);bad['sha256']='0'*64;bad_path=Path(td)/'bad.json';bad_path.write_text(json.dumps(bad))
            page.locator('#restoreSnapshotFile').set_input_files(str(bad_path))
            page.wait_for_function("document.querySelector('#snapshotStatus').textContent.includes('Checksum mismatch')")
            assert 'Temporary replacement text' in page.locator('#transcript').inner_text(),'bad snapshot must leave live data untouched'
            old=dict(snapshot);old['payload']=dict(snapshot['payload']);old['payload']['version']=0;old_path=Path(td)/'old.json';old_path.write_text(json.dumps(old))
            page.locator('#restoreSnapshotFile').set_input_files(str(old_path))
            page.wait_for_function("document.querySelector('#snapshotStatus').textContent.includes('Unsupported or malformed snapshot')")
            assert 'Temporary replacement text' in page.locator('#transcript').inner_text(),'older schema must leave live data untouched'
            page.locator('#restoreSnapshotFile').set_input_files(snapshot_path)
        page.wait_for_function("document.querySelector('#snapshotStatus').textContent.includes('Snapshot restored')")
        assert 'Temporary replacement text' not in page.locator('#transcript').inner_text()
        assert 'Private snapshot note'==page.locator('#privateNote').input_value()
        assert '1 private voice note(s) were not imported' in page.locator('#snapshotStatus').inner_text()
        assert page.locator('#voiceNoteList audio').count()==0
        assert page.locator('#customRuleList').inner_text().find('delivery date')>=0,'owner cue rules intentionally remain session local'
        # A second tab cannot silently steal capture: user must approve the explicit takeover.
        page.evaluate('window.fake.busy=true')
        page.locator('#startBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
        assert page.evaluate('window.fake.capture') is not None
        assert page.evaluate('window.fake.takeovers')==1
        page.evaluate("window.fake.profiles=Array.from({length:6},(_,i)=>({name:'Profile'+i,samples:2,active:true}));window.fake.mergeSuggestions=[{left:'Profile0',right:'Profile1',cosine:.94}]")
        page.locator('#aiReconnect').click()
        page.wait_for_function("document.querySelector('#speakerMergeSuggestions').textContent.includes('raw cosine 0.940')")
        assert 'no profiles are merged automatically' in page.locator('#speakerMergeSuggestions').inner_text().lower()
        page.locator('#eraseAllBtn').click()
        page.wait_for_function("document.querySelectorAll('.turn').length===0")
        assert page.locator('#voiceNoteList audio').count()==0,'Erase all must discard private voice-note audio'
        assert page.evaluate('window.fake.capture') is None
        assert not page.locator('#autoNames').is_checked()
        assert not page.locator('#speakerProfiles').inner_text().startswith('Dale')
        assert page.locator('#context').input_value()==''
        assert page.locator('#aim').input_value()=='observe'
        assert page.locator('#customRuleList').inner_text()=='No owner-defined rules.'
        assert page.locator('#manualSpeaker').input_value()=='shared'
        assert page.locator('#enrollName').input_value()==''
        assert not page.locator('#consent').is_checked()
        assert page.locator('#editDialog').evaluate('(e)=>!e.open')
        # Exercise the production PCM adapter with deterministic synthetic frames.
        page.evaluate('''() => {
          window.LensPCMCapture.MicCapture=class {
            constructor({onPCM}){this.onPCM=onPCM;this.timer=null}
            async start(){let i=0;this.timer=setInterval(()=>{
              const block=new Float32Array(2048);
              if(i>=5&&i<33)for(let j=0;j<block.length;j++)block[j]=.2*Math.sin((i*block.length+j)*.03);
              this.onPCM(window.LensPCM.StreamingResampler.prototype.push.call({
                inputRate:16000,outputRate:16000,interval:1,nextOutputAt:0,inputFrames:0,prev:0,
                filterCoefficient:1,low1:0,low2:0
              },block));
              i++;if(i>=48)clearInterval(this.timer);
            },1);return this}
            async stop(){clearInterval(this.timer)}
          };
        }''')
        before_pcm=page.evaluate('window.fake.transcribe')
        page.locator('#pcmPreRoll').fill('100')
        page.locator('#pcmPostRoll').fill('100')
        page.evaluate("window.fake.transcriptQueue.push({text:'Overlapping test speakers.',speaker:{label:'Mixed',evidence:{possibleOverlap:true,speechSeconds:1.2}}})")
        page.locator('#consent').check();page.locator('#pcmMode').check();page.locator('#pcmEditHold').check();page.locator('#startBtn').click()
        page.wait_for_function("document.querySelector('#captureModeStatus').textContent.includes('bounded in-memory ring')")
        page.wait_for_function("!document.querySelector('#pcmEditor').hidden && document.querySelector('#pcmEditWindow').options.length===1",timeout=7000)
        assert page.evaluate('window.fake.transcribe')==before_pcm,'Held PCM must remain unsubmitted during editing'
        assert page.evaluate("window.fake.pcmRenderOptions.some(o=>o.preRollMs===100&&o.postRollMs===100)"),'Production capture must pass both roll controls into PCM rendering'
        assert 'held for PCM edit' in page.locator('#workerQueue').inner_text() and 'pcm_' in page.locator('#workerQueue').inner_text()
        page.locator('#pcmEditApply').click()
        page.wait_for_function("document.querySelector('#pcmEditWindow').options.length===2")
        page.locator('#pcmEditBoundary').fill('600')
        page.locator('#pcmEditApply').click()
        assert 'Moved the shared boundary' in page.locator('#pcmEditStatus').inner_text()
        page.locator('#pcmEditMerge').click()
        page.wait_for_function("document.querySelector('#pcmEditWindow').options.length===1")
        page.locator('#pcmEditApply').click()
        page.wait_for_function("document.querySelector('#pcmEditWindow').options.length===2")
        page.locator('#pcmEditRelease').click()
        page.wait_for_function("document.querySelector('#workerQueue').textContent.includes('transcribing locally')")
        page.wait_for_function(f'window.fake.transcribe>={before_pcm+2}',timeout=7000)
        page.wait_for_function("window.fake.pcmUploads.length>0",timeout=3000)
        pcm=page.evaluate('window.fake.pcmUploads.at(-1)')
        assert pcm['contentType']=='audio/wav' and pcm['bytes']>50000 and pcm['forceMixed']=='true',pcm
        assert page.evaluate('window.fake.pcmUploads.length')==2,'Split windows must both be sent as canonical WAV'
        page.wait_for_function("document.querySelectorAll('.turn').length===2",timeout=3000)
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Possible acoustic overlap')",timeout=5000)
        overlap_cue=page.locator('#signals .insight').filter(has_text='Possible acoustic overlap')
        assert 'does not identify turn order or separate the words' in overlap_cue.inner_text()
        assert overlap_cue.locator('button.evidence-link').count()==1,'Acoustic overlap cue must link back to its source passage'
        assert page.locator('#pcmReplaySelect option').count()==2 and page.locator('#replayPCM').is_visible() and page.locator('#pcmReplayAudio').get_attribute('src').startswith('blob:'), 'Recent processed audio should be replayable from its bounded in-memory list'
        page.locator('#pcmReplaySelect').select_option(index=0)
        assert page.locator('#pcmReplayAudio').get_attribute('src').startswith('blob:')
        assert 'overlap 1 (1.2s)' in page.locator('#talkTimeStats').inner_text()
        page.locator('#pauseIntakeBtn').click();assert page.locator('#pauseIntakeBtn').inner_text()=='Resume intake';page.locator('#pauseIntakeBtn').click()
        page.locator('#stopBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        assert page.locator('#replayPCM').is_hidden() and page.locator('#pcmReplaySelect').is_hidden() and page.locator('#pcmReplayAudio').get_attribute('src') is None,'Stop must release replay clips and URLs'
        assert page.evaluate('window.fake.drains.length')==0
        before_evicted=page.evaluate('window.fake.transcribe')
        page.locator('#pcmEditHold').check();page.locator('#startBtn').click()
        page.wait_for_function("!document.querySelector('#pcmEditor').hidden && document.querySelector('#pcmEditWindow').options.length===1",timeout=7000)
        page.evaluate("window.fake.pcmRing.end+=window.fake.pcmRing.capacity;window.fake.pcmRing.length=window.fake.pcmRing.capacity;document.querySelector('#pcmEditWindow').dispatchEvent(new Event('change'))")
        assert page.locator('#pcmEditWindow option').count()==0
        assert 'older than the 45-second ring' in page.locator('#pcmEditStatus').inner_text()
        assert page.locator('#pcmEditRelease').is_enabled(),'Evicted original WAV must remain releasable'
        page.locator('#pcmEditRelease').click()
        page.wait_for_function(f'window.fake.transcribe>{before_evicted}',timeout=7000)
        assert page.evaluate('window.fake.pcmUploads.length')==3,'Evicted held original must still submit its retained WAV'
        page.locator('#stopBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        page.locator('#pcmMode').uncheck();page.evaluate('window.fake.quiet=false;window.fake.noiseRms=.007')
        page.locator('#startBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
        initial_cut=float(page.locator('#vadNoiseStatus').inner_text().split('effective cut: ')[1])
        page.wait_for_function("parseFloat(document.querySelector('#vadNoiseStatus').textContent.split('effective cut: ')[1])>0.0105",timeout=5000)
        raised_cut=float(page.locator('#vadNoiseStatus').inner_text().split('effective cut: ')[1])
        assert raised_cut>initial_cut, (initial_cut,raised_cut)
        page.evaluate('window.fake.noiseRms=0')
        page.wait_for_function(f"parseFloat(document.querySelector('#vadNoiseStatus').textContent.split('effective cut: ')[1])<{raised_cut}",timeout=5000)
        page.locator('#stopBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        # --- OMNI ZERO-LOSS UX TRANSFORMATION VERIFICATION ---
        # 01. Prevent accidental demo destruction on populated transcript
        page.evaluate("window.confirm=()=>{window.fake.confirmCount++;return true}")
        page.locator('#clearBtn').click()
        assert page.locator('.turn').count()==0
        # Empty session loads demo without confirm
        c0=page.evaluate('window.fake.confirmCount')
        page.locator('#sampleBtn').click()
        assert page.evaluate('window.fake.confirmCount')==c0,'Empty session demo load should not require confirm'
        assert page.locator('.turn').count()==3
        # Populated session requires confirm; canceling preserves existing transcript
        page.locator('#manualText').fill('Important live passage that must not be lost.')
        page.get_by_role('button',name='Add line').click()
        assert page.locator('.turn').count()==4
        page.evaluate("window.confirm=()=>{window.fake.confirmCount++;return false}")
        page.locator('#sampleBtn').click()
        assert page.locator('.turn').count()==4 and 'Important live passage' in page.locator('#transcript').inner_text(),'Canceled demo load must preserve populated transcript'
        page.evaluate("window.confirm=()=>{window.fake.confirmCount++;return true}")
        page.locator('#sampleBtn').click()
        assert page.locator('.turn').count()==3 and 'Important live passage' not in page.locator('#transcript').inner_text()
        # 02. Follow live without scroll hijack + unread count + return to live
        assert page.locator('#followLiveBtn').get_attribute('aria-pressed')=='true'
        page.locator('#followLiveBtn').click()
        assert page.locator('#followLiveBtn').get_attribute('aria-pressed')=='false'
        page.locator('#manualText').fill('New passage while paused 1.')
        page.get_by_role('button',name='Add line').click()
        page.locator('#manualText').fill('New passage while paused 2.')
        page.get_by_role('button',name='Add line').click()
        assert '2 newer passages' in page.locator('#followLiveStatus').inner_text()
        assert page.locator('#returnToLiveBtn').is_visible()
        page.locator('#returnToLiveBtn').click()
        assert page.locator('#followLiveBtn').get_attribute('aria-pressed')=='true'
        assert page.locator('#returnToLiveBtn').is_hidden()
        # 06. Chronological transcript gap marker on skipped window
        page.evaluate('window.fake.quiet=false;window.fake.noiseRms=null')
        page.locator('#consent').check();page.locator('#startBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
        assert page.locator('#headerStopBtn').is_visible(),'Header Stop button must remain accessible while recording'
        page.wait_for_timeout(320)
        page.locator('#pauseIntakeBtn').click()
        page.evaluate('window.fake.recorders.at(-1).stop()')
        page.wait_for_function("document.querySelectorAll('.transcript-gap').length>=1")
        gap_text=page.locator('.transcript-gap').first.inner_text()
        assert 'MISSING AUDIO COVERAGE' in gap_text and 'Speech during this gap was not transcribed' in gap_text,gap_text
        page.locator('#pauseIntakeBtn').click()
        page.locator('#headerStopBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        # 08 & 09. Speaker uncertainty badges + Scoped bulk speaker correction
        assert page.locator('.who-badge').count()>=3
        page.locator('.turn-bulk-check').nth(0).check()
        page.locator('.turn-bulk-check').nth(1).check()
        assert page.locator('#bulkCorrectionBar').is_visible()
        assert '2 passages selected' in page.locator('#bulkSelectedCount').inner_text()
        page.locator('#bulkSpeakerSelect').select_option('other')
        page.locator('#bulkApplySpeakerBtn').click()
        assert page.locator('.turn').nth(0).locator('.who').inner_text()=='Other'
        assert page.locator('.turn').nth(1).locator('.who').inner_text()=='Other'
        assert page.locator('#bulkCorrectionBar').is_hidden()
        # 10. Two-sample enrollment progress stepper states
        page.locator('#enrollName').fill('Alex')
        page.locator('#enrollConsent').check()
        assert '0 of 2 samples' in page.locator('#enrollStageBadge').inner_text()
        assert 'Two-sample enrollment · Alex' in page.locator('#enrollTargetLabel').inner_text()
        assert 'two separate voice samples' in page.locator('#enrollStageDetail').inner_text()
        # 11. Immediate Goal & Language controls sync with Setup
        page.locator('#quickAim').select_option('repair')
        assert page.locator('#aim').input_value()=='repair'
        page.locator('#quickLanguage').select_option('es-MX')
        assert page.locator('#language').input_value()=='es-MX'
        page.locator('#quickLanguage').select_option('en-US')
        page.locator('#quickAim').select_option('observe')
        # 12 & 14. Evidence inspector return navigation + Coaching freshness/staleness
        page.locator('#manualText').fill('I want to clarify the precise delivery date.')
        page.get_by_role('button',name='Add line').click()
        page.locator('#aiToggle').check()
        page.locator('#getCueBtn').evaluate('e=>e.click()')
        page.wait_for_function("document.querySelector('#cueSourceBadge').textContent.includes('Big Mac AI') && document.querySelector('#cueFreshnessBadge').textContent.includes('Current')",timeout=4000)
        assert 'Current' in page.locator('#cueFreshnessBadge').text_content()
        page.locator('#manualText').fill('Additional turn one after AI.')
        page.get_by_role('button',name='Add line').click()
        page.locator('#manualText').fill('Additional turn two after AI.')
        page.get_by_role('button',name='Add line').click()
        assert 'STALE' in page.locator('#aiFreshnessBadge').inner_text()
        page.locator('#aiToggle').uncheck()
        # 16. Contextual recovery banner on second-tab conflict decline
        page.evaluate("window.fake.busy=true;window.confirm=()=>false")
        page.locator('#consent').check();page.locator('#startBtn').click()
        page.wait_for_function("!document.querySelector('#engineRecoveryBanner').hidden")
        assert 'another tab holds the microphone session' in page.locator('#recoveryTitle').inner_text()
        assert page.locator('#recoveryTakeoverBtn').is_visible()
        page.evaluate("window.fake.busy=false;window.confirm=()=>{window.fake.confirmCount++;return true}")
        page.locator('#recoveryManualBtn').click()
        assert page.evaluate("document.activeElement.id==='manualText'")
        # 17 & D. Keyboard shortcuts (F, S, W, T, L, ?) and Quiet density mode
        if page.locator('#followLiveBtn').get_attribute('aria-pressed')=='false':
            page.locator('#returnToLiveBtn').click()
        assert page.locator('#followLiveBtn').get_attribute('aria-pressed')=='true'
        page.evaluate('document.activeElement.blur()')
        page.keyboard.press('?')
        assert page.locator('#shortcutDialog').evaluate('e=>e.open')
        page.keyboard.press('Escape')
        assert page.locator('#shortcutDialog').evaluate('e=>!e.open')
        page.evaluate('document.activeElement.blur()')
        page.keyboard.press('f')
        assert page.locator('#followLiveBtn').get_attribute('aria-pressed')=='false'
        page.keyboard.press('f')
        assert page.locator('#followLiveBtn').get_attribute('aria-pressed')=='true'
        page.keyboard.press('s')
        assert page.evaluate("document.activeElement.classList.contains('turn-speaker')")
        page.evaluate('document.activeElement.blur()')
        page.keyboard.press('w')
        assert page.locator('#editDialog').evaluate('e=>e.open')
        page.locator('#cancelEditBtn').click()
        assert not page.locator('#editDialog').evaluate('e=>e.open')
        page.locator('#densityMode').check()
        assert page.locator('html').get_attribute('data-density')=='quiet'
        page.locator('#densityMode').uncheck()
        # Observatory telemetry strip & turn ribbon interaction + workspaceNav tabindex/focus-layout regression
        assert page.locator('#observatoryStrip').is_visible()
        assert 'passages' in page.locator('#obsCadenceValue').inner_text()
        assert 'tentative' in page.locator('#obsCertaintyValue').inner_text()
        assert page.locator('#obsTurnRibbon .obs-node').count()>=1
        page.locator('#obsTurnRibbon .obs-node').first.click()
        assert page.locator('#evidenceDrawer').is_visible()
        page.locator('#evidenceReturnScrollBtn').click()
        assert page.locator('#evidenceDrawer').is_hidden()
        page.locator('#workspaceNav [data-jump="manualText"]').click()
        assert page.evaluate("document.activeElement.id==='manualText'")
        assert page.locator('#manualText').get_attribute('tabindex') is None,'Jumping to manualText must not set tabindex="-1"'
        if width>=810:
            page.locator('#layoutMode').select_option('focus')
            assert page.locator('#anchorPanel').is_hidden() and page.locator('#speakerPanel').is_hidden()
            page.locator('#workspaceNav [data-jump="speakerPanel"]').click()
            assert page.locator('#layoutMode').input_value()=='split' and page.locator('#speakerPanel').is_visible()
        # Verify direct click on #voiceNoteBtn starts and stops cleanly without duplicate listener race
        vn_before=page.locator('#voiceNoteList .voice-note-item').count()
        page.locator('#voiceNoteBtn').click()
        page.wait_for_function("document.querySelector('#voiceNoteBtn').textContent.includes('Stop voice note')")
        page.wait_for_timeout(560)
        page.locator('#voiceNoteBtn').click()
        page.wait_for_function(f"document.querySelectorAll('#voiceNoteList .voice-note-item').length==={vn_before+1}")
        # 18 & F. Long-session capacity banner at >=240 and rotation marker at >300 + Session review summary
        page.evaluate('''() => {
          const input=document.querySelector('#manualText'),form=document.querySelector('#manualForm');
          for(let i=0;i<245;i++){input.value='Synthetic turn '+i;form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))}
        }''')
        assert page.locator('#capacityBanner').is_visible()
        assert 'Approaching in-memory transcript limit' in page.locator('#capacityBannerText').inner_text()
        page.evaluate('''() => {
          const input=document.querySelector('#manualText'),form=document.querySelector('#manualForm');
          for(let i=245;i<305;i++){input.value='Synthetic turn '+i;form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))}
        }''')
        assert 'rotated out of memory' in page.locator('#capacityBannerText').inner_text()
        assert '300 passages (+' in page.locator('#summaryPassageCount').inner_text()
        page.locator('#clearBtn').click()
        assert page.locator('#capacityBanner').is_hidden()
        assert not errors,errors
        overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
        assert overflow<=0,overflow
        print('PASS Brave/Chromium',width,'simulated voice, capture lease, meter, PCM split/move/merge WAV editing, replay, transcript, Stop, Erase, lifecycle, UX 01-20 & A-F, observatory strip, no overflow')
        page.close()
    for extra_width in (1440,810):
        page=browser.new_page(viewport={'width':extra_width,'height':900})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('http://localhost/**',lambda route:route.fulfill(status=200,content_type='text/html',body=html))
        page.goto('http://localhost/')
        page.wait_for_function("document.querySelector('#capability').textContent.includes('LOCAL WHISPER READY')")
        overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
        assert overflow<=0,f'Overflow at {extra_width}: {overflow}'
        assert not errors,errors
        page.screenshot(path=str(root/f'qa_v6_{extra_width}.png'),full_page=True)
        print('PASS Brave/Chromium',extra_width,'responsive layout and zero horizontal overflow')
        page.close()
    browser.close()
