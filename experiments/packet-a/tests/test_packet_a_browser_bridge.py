"""Packet A browser->actual HTTP server integration via a local test proxy.

Chromium navigation is blocked by this runtime policy. Serve the real page bytes
with set_content; intercept fetch in-page and forward unchanged request data and
headers to a REAL 127.0.0.1 Python HTTP server. The proxy supplies the browser's
same-origin header and a test-only SHA-256 host binding because about:blank lacks
SubtleCrypto. This proves UI/state/HTTP contracts, not a real microphone route.
"""
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BROWSER=os.environ.get('LENS_BROWSER_EXECUTABLE') or next((path for path in ('/Applications/Brave Browser.app/Contents/MacOS/Brave Browser','/usr/bin/chromium','/usr/bin/chromium-browser') if Path(path).is_file()),'/usr/bin/chromium')
sys.path.insert(0,str(ROOT))
import packet_a_server as app
from lens_stop_drain import CaptureDrainCoordinator

HTML=(ROOT/'packet_a_lab.html').read_text()
for f in ('lens_pcm_core.js','lens_pcm_capture.js','lens_stop_client.js','lens_packet_a_transport.js'):
    HTML=HTML.replace('<script src="./'+f+'"></script>', '<script>\n'+(ROOT/f).read_text()+'\n</script>')

BRIDGE='''<script>
  window.fetch=async(path,opts={})=>{
    let body=null;
    if(opts.body instanceof Blob){
      const bytes=new Uint8Array(await opts.body.arrayBuffer());
      let value='';for(let i=0;i<bytes.length;i+=8192)value+=String.fromCharCode(...bytes.subarray(i,i+8192));
      body=btoa(value);
    }else if(typeof opts.body==='string')body=btoa(unescape(encodeURIComponent(opts.body)));
    const result=await window.__testHttp({path,body,headers:opts.headers||{},method:opts.method||'GET'});
    return new Response(JSON.stringify(result.payload),{status:result.status,headers:{'Content-Type':'application/json'}});
  };
</script>'''
HTML=HTML.replace('<script>\n(()=>',BRIDGE+'\n<script>\n(()=>')

class TestServer:
 def __enter__(self):
    app.COORDINATOR=CaptureDrainCoordinator()
    self.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
    self.server.daemon_threads=True;self.server.whisper=None;self.server.model=None
    self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    self.base=f'http://127.0.0.1:{self.server.server_port}'
    return self
 def __exit__(self,*args):
    self.server.shutdown();self.thread.join(4);self.server.server_close()
 def do_http(self,source,request):
    headers={**request.get('headers',{})}
    if request.get('method')!='GET':headers['Origin']=self.base
    body=base64.b64decode(request['body']) if request['body'] is not None else None
    try:
      req=urllib.request.Request(self.base+request['path'],data=body,headers=headers,method=request['method'])
      with urllib.request.urlopen(req,timeout=8) as response:
        return {'status':response.status,'payload':json.load(response)}
    except urllib.error.HTTPError as err:return {'status':err.code,'payload':json.load(err)}
 def do_hash(self,source,b64):return sha256(base64.b64decode(b64)).hexdigest()


def check(browser,server,width):
 page=browser.new_page(viewport={'width':width,'height':900},accept_downloads=True)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.expose_binding('__testHttp',server.do_http)
 page.expose_binding('__testHash',server.do_hash)
 page.set_content(HTML)
 page.evaluate('''() => {window.LensBench.transport.digest=async bytes=>{
   let out='';for(let i=0;i<bytes.length;i+=8192)out+=String.fromCharCode(...bytes.subarray(i,i+8192));
   return window.__testHash(btoa(out));
 }}''')
 page.wait_for_function("window.LensBench.transport.phase==='ready'")
 page.locator('#fixtureBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='live' && LensBench.timeline().segments.length===3")
 assert 'FIXTURE · SERVER READY' in page.locator('#modePill').inner_text()
 # Actual PCM edit before server drain; the result must block name learning.
 page.locator('#windowChoice').select_option('w3')
 page.locator('#preRoll').fill('100')
 page.locator('#stopBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='frozen' && document.querySelector('#stopDialog').open")
 assert page.locator('#keepList input').count()==3
 page.locator('#keepList input').nth(1).uncheck()
 page.locator('#keepBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='ready' && document.querySelector('#stopBtn').disabled")
 assert page.locator('#serverResults .result').count()==2
 assert page.locator('#serverResults .result.failed').count()==0
 assert page.evaluate('LensBench.timeline().segments.map(x=>x.status)')==['done','dropped','done']
 assert page.evaluate('LensBench.transport.lastManifest.map(x=>x.window_id)')==['w1','w3']
 assert page.evaluate('LensBench.transport.lastManifest[1].force_mixed') is True
 assert 'No Whisper model configured' in page.locator('#serverResults').inner_text()
 assert '2 accepted' in page.locator('#status').inner_text()
 assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=1
 assert not errors,errors
 page.screenshot(path=str(ROOT / ('packet_a_connected_desktop.png' if width>800 else 'packet_a_connected_mobile.png')),full_page=True)
 page.close()
 print('PASS bridged browser',width,'exact PCM->SHA manifest->freeze->keep 2/drop 1->actual HTTP WAV->server results')


def check_drop_all(browser,server):
 page=browser.new_page(viewport={'width':1000,'height':750})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.expose_binding('__testHttp',server.do_http)
 page.set_content(HTML)
 page.wait_for_function("window.LensBench.transport.phase==='ready'")
 page.locator('#fixtureBtn').click();page.wait_for_function("window.LensBench.transport.phase==='live'")
 page.locator('#stopBtn').click();page.wait_for_function("window.LensBench.transport.phase==='frozen' && document.querySelector('#stopDialog').open")
 page.locator('#dropAllBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='ready' && document.querySelector('#stopBtn').disabled")
 assert page.locator('#serverResults .result').count()==0
 assert page.evaluate('LensBench.timeline().segments.map(x=>x.status)')==['dropped']*3
 assert app.COORDINATOR.state()['occupied'] is False
 assert 'No WAV audio sent' in page.locator('#status').inner_text()
 assert not errors,errors
 page.close()
 print('PASS bridged browser Drop All: no upload, no transcript, capture revoked')



def check_choice_cap_and_reopen(browser,server):
 page=browser.new_page(viewport={'width':850,'height':800})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.expose_binding('__testHttp',server.do_http)
 page.set_content(HTML);page.wait_for_function("window.LensBench.transport.phase==='ready'")
 page.locator('#fixtureBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='live'")
 page.evaluate('''() => {
    const ring=LensBench.ring(),timeline=LensBench.timeline();
    ring.append(new Int16Array(48000*2));
    timeline.register(128000,176000,{reason:'extra window 4'});
    timeline.register(176000,224000,{reason:'extra window 5'});
    LensBench.select('w1');
 }''')
 page.locator('#stopBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='frozen' && document.querySelector('#stopDialog').open")
 assert page.locator('#keepList input').count()==5
 assert page.locator('#keepList input:checked').count()==4
 # An attempted fifth selection is rejected immediately, but the others stay checked.
 page.locator('#keepList input').nth(0).click()
 assert page.locator('#keepList input').nth(0).is_checked() is False
 page.locator('#keepList input').nth(4).uncheck()
 page.locator('#keepList input').nth(0).check()
 assert page.locator('#keepList input:checked').count()==4
 # Closing the chooser does NOT cancel the server freeze, nor discard choices.
 page.locator('#cancelStopBtn').click()
 assert page.locator('#stopDialog').evaluate('(el)=>el.open') is False
 page.locator('#stopBtn').click()
 assert page.locator('#stopDialog').evaluate('(el)=>el.open') is True
 assert page.locator('#keepList input').nth(0).is_checked() is True
 assert page.locator('#keepList input').nth(4).is_checked() is False
 page.locator('#dropAllBtn').click()
 page.wait_for_function("window.LensBench.transport.phase==='ready' && document.querySelector('#stopBtn').disabled")
 assert app.COORDINATOR.state()['occupied'] is False
 assert not errors,errors
 page.close()
 print('PASS chooser 5 windows, four-window cap, remembered Keep/Drop selections after reopen')


def main():
 with TestServer() as server,sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,executable_path=BROWSER,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (1200,375):check(browser,server,width)
    check_drop_all(browser,server)
    check_choice_cap_and_reopen(browser,server)
    browser.close()

if __name__=='__main__':main()
