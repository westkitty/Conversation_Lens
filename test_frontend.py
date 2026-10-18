"""Chromium runtime + mocked microphone and fetch; validates v6 UI state, not real device accuracy."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).parent
html=(root/'Conversation_Lens_Intelligent_Speaker_v6'/'Conversation_Lens_Live.html').read_text()
html=html.replace("if(!/^https?:$/.test(location.protocol)||!['127.0.0.1','localhost'].includes(location.hostname))","if(false)")
stub='''<script>
window.fake={recorders:[],stopped:0,quiet:false,meterReads:0,transcribe:0,token:'ready-token',capture:null,closed:[],profiles:[],transcriptQueue:[],
             dataSize:950,errors:[],voiceEnabled:[],captureLeaseSequence:0};
window.fetch=async(path,opts={})=>{
 const ok=(v)=>new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}});
 if(path==='/api/status')return ok({app:'conversation-lens',token:window.fake.token,ready:false,stt:{ready:true},speakers:{ready:true,profiles:window.fake.profiles}});
 if(path==='/api/capture/open'){
  const request=JSON.parse(opts.body);if(!request.consent)throw Error('consent missing');
  window.fake.capture='id-'+(++window.fake.captureLeaseSequence)+'-'+'x'.repeat(30);
  return ok({capture:window.fake.capture});
 }
 if(path==='/api/capture/close'){
  window.fake.closed.push(JSON.parse(opts.body).capture);
  if(window.fake.capture===JSON.parse(opts.body).capture)window.fake.capture=null;
  return ok({closed:true});
 }
 if(path==='/api/session/erase'){
  if(!JSON.parse(opts.body).confirm)throw Error('Not confirmed');
  window.fake.profiles=[];window.fake.capture=null;
  return ok({closed:true,erased:true,speakers:{ready:true,profiles:[]}});
 }
 if(path==='/api/speakers')return ok({speakers:{ready:true,profiles:window.fake.profiles}});
 if(path==='/api/speakers/forget'){
  const name=JSON.parse(opts.body).name;
  window.fake.profiles=window.fake.profiles.filter(x=>name&&x.name!==name);
  return ok({speakers:{ready:true,profiles:window.fake.profiles}});
 }
 if(path==='/api/transcribe'){
  window.fake.transcribe++;window.fake.voiceEnabled.push(opts.headers['X-Lens-Auto-Names']);
  if(!opts.headers['X-Lens-Capture-Session']||opts.headers['X-Lens-Capture-Session']!==window.fake.capture)throw Error('Capture session missing');
  const item=window.fake.transcriptQueue.shift()||{text:'Sample sentence',speaker:{label:'Unknown'}};
  await new Promise((resolve,reject)=>{const id=setTimeout(resolve,15);opts.signal?.addEventListener('abort',()=>{clearTimeout(id);reject(new DOMException('Cancelled','AbortError'))},{once:true})});
  if(item.introduction?.state==='candidate')window.fake.profiles.push({name:item.introduction.name,samples:1,active:false,source:'conversation'});
  if(item.introduction?.state==='strengthened'){
    const p=window.fake.profiles.find(x=>x.name===item.introduction.name);if(p){p.samples=2;p.active=true}
  }
  return ok(item);
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
 createAnalyser(){return {fftSize:1024,getByteTimeDomainData(a){window.fake.meterReads++;for(let i=0;i<a.length;i++)a[i]=window.fake.quiet?128:128+Math.round(17*Math.sin(i/7));}}}
 resume(){return Promise.resolve()}
 close(){return Promise.resolve()}
};
window.confirm=()=>true;
</script>'''
assert html.count('<script>\n(()=>')==1
html=html.replace('<script>\n(()=>',stub+'<script>\n(()=>')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (1200,375):
        page=browser.new_page(viewport={'width':width,'height':830})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html)
        page.wait_for_function("document.querySelector('#capability').textContent.includes('LOCAL WHISPER READY')")
        assert not page.locator('#startBtn').is_enabled()
        assert not page.locator('#autoNames').is_checked()
        page.locator('#consent').check();page.locator('#autoNames').check()
        page.evaluate("window.fake.transcriptQueue.push({text:'Hi, this is Dale, and I would like to talk about how I feel.',speaker:{label:'Dale',level:'provisional',reason:'Spoken introduction'},introduction:{name:'Dale',state:'candidate',message:'Self introduced'}})")
        page.locator('#startBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
        assert page.evaluate('window.fake.capture') is not None
        page.wait_for_function('window.fake.meterReads>2')
        assert page.locator('#levelText').inner_text().startswith('Input')
        # Ensure a bit of energy registered before forced early window close.
        page.wait_for_timeout(340)
        page.evaluate('window.fake.recorders.at(-1).stop()')
        page.wait_for_function("document.querySelectorAll('.turn').length===1")
        assert page.locator('.who').last.inner_text()=='Dale ?'
        assert page.evaluate('window.fake.transcribe')==1
        # Second window closes on ~900ms of detected silence, after a minimum ~2.8s.
        page.evaluate("window.fake.transcriptQueue.push({text:'I want us to understand each other.',speaker:{label:'Dale',level:'probable',reason:'Tentative acoustic'},introduction:{name:'Dale',state:'strengthened',message:'Two matching windows'}})")
        page.wait_for_timeout(950)
        page.evaluate('window.fake.quiet=true')
        page.wait_for_function('window.fake.recorders.length>=3',timeout=9000)
        page.wait_for_function("document.querySelectorAll('.turn').length>=2")
        assert page.locator('.who').last.inner_text()=='Dale'
        assert page.locator('#levelText').inner_text().startswith('Quiet')
        assert page.locator('#levelRail').get_attribute('aria-valuenow')=='0'
        page.screenshot(path=str(root/('qa_v6_desktop.png' if width>800 else 'qa_v6_mobile.png')),full_page=True)
        page.locator('#stopBtn').click()
        page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
        page.wait_for_function('window.fake.closed.length>=1')
        assert page.evaluate('window.fake.capture') is None
        assert page.evaluate('window.fake.stopped')>=1
        assert page.locator('#levelFill').get_attribute('style')=='width: 0%;'
        # The user can start again without unintentionally resuming old capture.
        page.locator('#startBtn').click();page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
        assert page.evaluate('window.fake.capture') is not None
        page.locator('#eraseAllBtn').click()
        page.wait_for_function("document.querySelectorAll('.turn').length===0")
        assert page.evaluate('window.fake.capture') is None
        assert not page.locator('#autoNames').is_checked()
        assert not page.locator('#speakerProfiles').inner_text().startswith('Dale')
        assert not errors,errors
        overflow=page.evaluate('document.documentElement.scrollWidth-innerWidth')
        assert overflow<=0,overflow
        print('PASS Chromium',width,'simulated voice, capture lease, meter, silence auto-segmentation, transcript, Stop, Erase, lifecycle, no overflow')
        page.close()
    browser.close()
