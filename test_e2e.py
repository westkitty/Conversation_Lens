"""v6 end-to-end: real Chromium + local HTTP + FFmpeg conversion; Whisper and voice vectors are simulated.
This is NOT validation of actual human biometric identification or physical microphone hardware."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import tempfile
import threading
import time
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright

BROWSER_EXECUTABLE=os.environ.get('LENS_BROWSER_EXECUTABLE') or next((p for p in ('/Applications/Brave Browser.app/Contents/MacOS/Brave Browser','/usr/bin/chromium','/usr/bin/chromium-browser') if Path(p).is_file()),'/usr/bin/chromium')
ROOT=Path(__file__).parent/'Conversation_Lens_Intelligent_Speaker_v6'
spec=importlib.util.spec_from_file_location('lens_v6_server',ROOT/'server.py')
backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)
with tempfile.TemporaryDirectory(prefix='lens-v6-e2e-') as tmp:
    d=Path(tmp)
    fake=d/'fake-whisper';txt=d/'words.txt'
    fake.write_text("#!/usr/bin/env python3\nimport sys,pathlib,os\na=sys.argv\npathlib.Path(a[a.index('-of')+1]+'.txt').write_text(pathlib.Path(os.environ['LENS_TEST_SPOKEN_TEXT']).read_text())\n")
    fake.chmod(0o700); txt.write_text('Hi, this is Dale, and I want us to understand each other.')
    os.environ['LENS_TEST_SPOKEN_TEXT']=str(txt)
    backend.WHISPER_BIN=str(fake)
    backend.WHISPER_MODEL=d/'model.bin'; backend.WHISPER_MODEL.write_bytes(b'M'*1_000_100)
    backend.SPEAKER_PYTHON=d/'venv-python';backend.SPEAKER_PYTHON.write_text('test');backend.SPEAKER_PYTHON.chmod(0o700)
    backend.SPEAKER_MODEL=d/'model.onnx';backend.SPEAKER_MODEL.write_bytes(b'O'*5_000_200)
    u=[1.0]+[0.0]*255
    backend.speaker_vectors=lambda wav:{'full':u,'first':u,'second':u,'speech_seconds':4.0}
    backend.ollama_status=lambda:{'ready':False,'model':'offline','reason':'AI offline during browser tests'}
    clips=[]
    for i,hz in enumerate((465,533,612,678)):
        clip=d/f'voice{i}.webm'
        subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-f','lavfi','-i',f'sine=frequency={hz}:duration=4','-c:a','libopus',str(clip)],check=True)
        clips.append(list(clip.read_bytes()))
    app=ThreadingHTTPServer(('127.0.0.1',0),backend.Handler)
    th=threading.Thread(target=app.serve_forever,daemon=True);th.start()
    base='http://127.0.0.1:'+str(app.server_address[1])
    try:
      with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=BROWSER_EXECUTABLE,args=['--no-sandbox','--disable-dev-shm-usage'])
        for vw in (1200,375):
          # Each viewport is independent; do not inherit the preceding test's mock speech.
          txt.write_text('Hi, this is Dale, and I want us to understand each other.')
          backend.forget_speakers()
          page=browser.new_page(viewport={'width':vw,'height':800})
          errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
          page.add_init_script('''
            window.fake={recorders:[],audio:[],stopped:0,quiet:false,meterReads:0};
            Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:async()=>{
             const track={stop(){window.fake.stopped++},addEventListener(){}};
             return {getTracks:()=>[track],getAudioTracks:()=>[track]};
            }}});
            window.MediaRecorder=class{
             static isTypeSupported(x){return x.includes('webm')}
             constructor(s,opt){this.state='inactive';this.mimeType='audio/webm';window.fake.recorders.push(this)}
             start(){this.state='recording'}
             stop(){if(this.state==='inactive')return;this.state='inactive';const a=window.fake.audio.shift();
              if(!a){this.onerror?.(new Event('error'));return;}setTimeout(()=>{
                this.ondataavailable?.({data:new Blob([Uint8Array.from(a)],{type:'audio/webm'})});this.onstop?.();},0)}
            };
            window.AudioContext=class{
             constructor(){this.state='running'}
             createMediaStreamSource(){return {connect(){},disconnect(){}}}
             createAnalyser(){return {fftSize:1024,getByteTimeDomainData(arr){window.fake.meterReads++;for(let i=0;i<arr.length;i++)arr[i]=window.fake.quiet?128:128+Math.round(17*Math.sin(i/7));}}}
             resume(){return Promise.resolve()}
             close(){return Promise.resolve()}
            };
            window.confirm=()=>true;
          ''')
          page.goto(base+'/');page.wait_for_function("document.querySelector('#capability').textContent.includes('LOCAL WHISPER READY')")
          page.evaluate('(a)=>window.fake.audio=a',clips)
          page.locator('#consent').check()
          page.locator('#autoNames').evaluate("el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}")
          page.locator('#startBtn').click()
          page.wait_for_function("document.querySelector('#statusText').textContent.includes('LOCAL MIC ACTIVE')")
          assert backend.CAPTURE_SESSION
          page.wait_for_function('window.fake.meterReads>1')
          assert page.locator('#levelText').inner_text().startswith(('Input','Mic ')),page.locator('#levelText').inner_text()
          # First clip manually finalized. The recorder should enqueue and read it via backend.
          page.evaluate('window.fake.recorders.at(-1).stop()')
          page.wait_for_function("document.querySelectorAll('.turn').length===1",timeout=12000)
          assert page.locator('.who').last.inner_text()=='Dale ?',page.locator('.who').last.inner_text()
          assert len(backend.SPEAKERS['Dale'])==1
          txt.write_text('I would like you to hear what I mean before you answer.')
          # Automatic segmentation: resume audible -> transition to silence -> recorder stops after threshold.
          page.wait_for_timeout(950)
          page.evaluate('window.fake.quiet=true')
          page.wait_for_function('window.fake.recorders.length>=3',timeout=10000)
          page.wait_for_function("document.querySelectorAll('.turn').length===2",timeout=16000)
          assert page.locator('.who').last.inner_text()=='Dale'
          assert len(backend.SPEAKERS['Dale'])==2
          page.wait_for_function("document.querySelector('#levelText').textContent.startsWith('Quiet')")
          assert page.locator('#levelText').inner_text().startswith('Quiet')
          assert page.locator('#levelRail').get_attribute('aria-valuenow')=='0'
          page.screenshot(path=str(Path(__file__).parent/('qa_v6_desktop.png' if vw>800 else 'qa_v6_mobile.png')),full_page=True)
          page.locator('#stopBtn').click()
          page.wait_for_function("document.querySelector('#statusText').textContent==='NOT LISTENING'")
          for _ in range(20):
            if backend.CAPTURE_SESSION is None: break
            time.sleep(.06)
          assert backend.CAPTURE_SESSION is None,'Stop did not revoke server capture lease'
          assert page.evaluate('window.fake.stopped')>=1
          assert page.locator('#levelFill').get_attribute('style')=='width: 0%;'
          # Transcript clears, voiceprints wiped server-side by explicit privacy erase.
          page.locator('#eraseAllBtn').evaluate('(el)=>el.click()')
          page.wait_for_function('document.querySelectorAll(".turn").length===0')
          assert not backend.SPEAKERS and not backend.SPEAKER_META
          assert not page.locator('#autoNames').is_checked()
          assert not errors,errors
          size=page.evaluate('document.documentElement.scrollWidth-window.innerWidth')
          assert size<=0,f'Horizontal overflow: {size}'
          page.close()
          print(f'PASS Brave/Chromium viewport {vw}: microphone simulation, meter, real HTTP/WebM/ffmpeg, intro, learned voice, silence auto-boundary, Stop revoke, erase all, no console errors')
        browser.close()
    finally:
      app.shutdown();app.server_close()
print('v6 browser integration complete; actual microphone/voice accuracy remains unverified')
