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
window.fake={recorders:[],stopped:0,quiet:false,meterReads:0,transcribe:0,confirmCount:0,pcmUploads:[],drains:[],token:'ready-token',capture:null,closed:[],frozen:[],profiles:[],mergeSuggestions:[],transcriptQueue:[],
             dataSize:950,errors:[],voiceEnabled:[],captureLeaseSequence:0,aiRequests:0,aiBodies:[],busy:false,takeovers:0};
window.fetch=async(path,opts={})=>{
 const ok=(v)=>new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}});
 if(path==='/api/status')return ok({app:'conversation-lens',protocol:3,token:window.fake.token,ready:true,model:'mock-local',stt:{ready:true},speakers:{ready:true,profiles:window.fake.profiles,mergeSuggestions:window.fake.mergeSuggestions}});
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
 if(path==='/api/speakers/boost'){
  const body=JSON.parse(opts.body),entry=window.fake.profiles.find(p=>p.name===body.name);
  if(entry)entry.boostSeconds=body.seconds;
  return ok({speakers:{ready:true,profiles:window.fake.profiles,ramBytes:2048}});
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
    const p=window.fake.profiles.find(x=>x.name===item.introduction.name);if(p){p.samples=2;p.active=true;p.lastSeenSeconds=3}
  }
  return ok(item);
 }
 if(path==='/api/analyze'){window.fake.aiRequests++;window.fake.aiBodies.push(JSON.parse(opts.body));return ok({insight:{evidence_status:'exact',observation:'A clarification request was captured.',evidence:'I want to clarify the precise delivery date.',next_step:'What date should we agree on?',caution:'Automatic transcript may have errors'}})}
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
 createAnalyser(){return {fftSize:1024,getByteTimeDomainData(a){window.fake.meterReads++;for(let i=0;i<a.length;i++)a[i]=window.fake.quiet?128:128+Math.round(17*Math.sin(i/7));}}}
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
        if width<810:
            expected=['setupTitle','listenTitle','cueTitle','transcriptTitle','signalTitle','aiTitle','speakerTitle','anchorTitle']
            dom_order=lambda:page.evaluate("() => [...document.querySelectorAll('.grid > section')].map(e => e.querySelector('h2')?.id)")
            assert dom_order()==expected,dom_order()
            # Resize twice: moving existing panels must preserve actual element identity and tab order.
            page.set_viewport_size({'width':940,'height':830})
            page.wait_for_function("!document.querySelector('.grid').classList.contains('mobile-layout')")
            assert page.locator('.left-col > section').count()==4 and page.locator('.right-col > section').count()==4
            page.set_viewport_size({'width':width,'height':830})
            page.wait_for_function("document.querySelector('.grid').classList.contains('mobile-layout')")
            assert dom_order()==expected
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
        assert page.evaluate('window.fake.transcribe')==1
        # Second window closes on ~900ms of detected silence, after a minimum ~2.8s.
        page.evaluate("window.fake.transcriptQueue.push({text:'I want us to understand each other.',speaker:{label:'Dale',level:'probable',reason:'Tentative acoustic',evidence:{full:{best:'Dale',cosine:.9345,margin:.1456},first:{best:'Dale',cosine:.901,margin:.101},second:{best:'Dale',cosine:.909,margin:.112},halfCosine:.85,possibleOverlap:false,speechSeconds:2.5}},introduction:{name:'Dale',state:'strengthened',message:'Two matching windows'}})")
        page.wait_for_timeout(950)
        page.evaluate('window.fake.quiet=true')
        page.wait_for_function('window.fake.recorders.length>=3',timeout=9000)
        page.wait_for_function("document.querySelectorAll('.turn').length>=2")
        assert page.locator('.who').last.inner_text()=='Dale'
        assert 'Dale · 2.5s (100% of attributed spans)' in page.locator('#talkTimeStats').inner_text()
        assert page.locator('#levelText').inner_text().startswith('Quiet')
        assert page.locator('#levelRail').get_attribute('aria-valuenow')=='0'
        page.get_by_role('button',name='Boost for two minutes: Dale').click()
        page.wait_for_function("document.querySelector('#speakerProfiles').textContent.includes('Boost 120s')")
        assert 'last seen 3s ago' in page.locator('#speakerProfiles').inner_text()
        page.get_by_role('button',name='Disable boost for Dale').click()
        page.wait_for_function("document.querySelector('#speakerProfiles').textContent.includes('Boost 2m')")
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
        page.locator('#speakerLockCount').fill('1')
        page.locator('#speakerLockBtn').click()
        assert 'Pinned Dale for 1 future audio window' in page.locator('#speakerLockStatus').inner_text()
        page.evaluate("window.fake.transcriptQueue.push({text:'A later pinned conversation window.',speaker:{label:'Unknown',reason:'No match'}})")
        page.evaluate('window.fake.quiet=false')
        page.wait_for_timeout(2900)
        page.evaluate('window.fake.quiet=true')
        page.wait_for_function('window.fake.recorders.length>=4',timeout=5000)
        page.wait_for_function("[...document.querySelectorAll('.turn-text')].some(e=>e.textContent==='A later pinned conversation window.')",timeout=6000)
        assert page.locator('.turn').last.locator('.who').inner_text()=='Dale'
        assert 'Owner-pinned speaker label' in page.locator('.turn').last.inner_text()
        assert page.evaluate("window.fake.voiceEnabled.at(-1)")=='disabled','Manual speaker locks must bypass name learning'
        assert page.locator('#speakerLockStatus').inner_text()=='No speaker label pinned.'
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
        page.wait_for_function("document.querySelectorAll('#actionLedger .action-item').length===2")
        assert 'possible decision' in page.locator('#actionLedger').inner_text().lower()
        assert 'possible action' in page.locator('#actionLedger').inner_text().lower()
        page.locator('#manualText').fill('Please let me finish.')
        page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Turn-taking')")
        page.locator('#manualText').fill('On a different topic, I will send the updated file.')
        page.get_by_role('button',name='Add line').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Topic transition')")
        page.locator('#customRulesPanel').evaluate('e=>e.open=true')
        page.locator('#customRulePhrase').fill('outline')
        page.locator('#customRuleObservation').fill('The owner asked to notice this outline phrase.')
        page.locator('#customRuleNext').fill('Should we confirm the outline contents?')
        page.locator('#customRulePriority').select_option('5')
        page.locator('#addCustomRule').click()
        page.wait_for_function("document.querySelector('#signals').textContent.includes('Custom cue matched: outline')")
        assert 'Review passage 4' in page.locator('#signals').text_content()
        page.get_by_role('button',name='Review passage 4').first.click()
        assert page.evaluate('document.activeElement.id')=='passage-4'
        page.screenshot(path=str(root/('qa_v6_desktop.png' if width>800 else 'qa_v6_mobile.png')),full_page=True)
        page.locator('#stopBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
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
            page.locator('#restoreSnapshotFile').set_input_files(snapshot_path)
        page.wait_for_function("document.querySelector('#snapshotStatus').textContent.includes('Snapshot restored')")
        assert 'Temporary replacement text' not in page.locator('#transcript').inner_text()
        assert 'Private snapshot note'==page.locator('#privateNote').input_value()
        assert '1 private voice note(s) were not imported' in page.locator('#snapshotStatus').inner_text()
        assert page.locator('#voiceNoteList audio').count()==0
        assert page.locator('#customRuleList').inner_text().find('outline')>=0,'owner cue rules intentionally remain session local'
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
        page.evaluate("window.fake.transcriptQueue.push({text:'Overlapping test speakers.',speaker:{label:'Mixed',evidence:{possibleOverlap:true,speechSeconds:1.2}}})")
        page.locator('#consent').check();page.locator('#pcmMode').check();page.locator('#startBtn').click()
        page.wait_for_function("document.querySelector('#captureModeStatus').textContent.includes('bounded in-memory ring')")
        page.wait_for_function(f'window.fake.transcribe>{before_pcm}',timeout=7000)
        page.wait_for_function("window.fake.pcmUploads.length>0",timeout=3000)
        pcm=page.evaluate('window.fake.pcmUploads.at(-1)')
        assert pcm['contentType']=='audio/wav' and pcm['bytes']>50000 and pcm['forceMixed']=='true',pcm
        page.wait_for_function("document.querySelectorAll('.turn').length===1",timeout=3000)
        assert 'overlap 1 (1.2s)' in page.locator('#talkTimeStats').inner_text()
        page.locator('#stopBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        assert page.evaluate('window.fake.drains.length')==0
        assert not errors,errors
        overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
        assert overflow<=0,overflow
        print('PASS Brave/Chromium',width,'simulated voice, capture lease, meter, silence auto-segmentation, PCM WAV integration, transcript, Stop, Erase, lifecycle, no overflow')
        page.close()
    browser.close()
