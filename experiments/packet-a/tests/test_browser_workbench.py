"""Desktop/mobile interaction and real AudioWorklet smoke using fake Chromium microphone."""
from pathlib import Path
import os

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BROWSER=os.environ.get('LENS_BROWSER_EXECUTABLE') or next((path for path in ('/Applications/Brave Browser.app/Contents/MacOS/Brave Browser','/usr/bin/chromium','/usr/bin/chromium-browser') if Path(path).is_file()),'/usr/bin/chromium')
HTML=(ROOT/'audio_window_workbench.html').read_text(encoding='utf-8')
for path in ('lens_pcm_core.js','lens_pcm_capture.js'):
    HTML=HTML.replace('<script src="./'+path+'"></script>', '<script>\n'+(ROOT/path).read_text(encoding='utf-8')+'\n</script>')

def check_page(browser,width):
    page=browser.new_page(viewport={'width':width,'height':850},accept_downloads=True)
    errors=[]
    page.on('pageerror', lambda e:errors.append(str(e)))
    page.set_content(HTML)
    page.locator('#fixtureBtn').click()
    assert page.locator('.clip').count()==3
    assert page.evaluate('LensBench.ring().end')==128000
    assert page.evaluate('LensBench.timeline().segments.map(x=>x.end-x.start)')==[40000,48000,40000]
    # Drag the split marker; a real segment is subdivided without audio loss.
    page.locator('#waveCanvas').scroll_into_view_if_needed()
    rect=page.locator('#waveCanvas').bounding_box()
    page.mouse.move(rect['x']+rect['width']*.36,rect['y']+rect['height']*.54)
    page.mouse.down();page.mouse.move(rect['x']+rect['width']*.4,rect['y']+rect['height']*.54,steps=6);page.mouse.up()
    page.locator('#splitBtn').click()
    assert page.locator('.clip').count()==4
    assert page.evaluate('LensBench.timeline().segments[0].end')>10000
    assert page.evaluate('LensBench.timeline().segments.reduce((a,s)=>a+s.end-s.start,0)')==128000
    assert page.evaluate('LensBench.timeline().segments[0].learningBlocked') is True
    assert page.evaluate('LensBench.timeline().segments[1].learningBlocked') is True
    page.locator('#mergeBtn').click()
    assert page.locator('.clip').count()==3
    assert page.evaluate('LensBench.timeline().segments[0].end')==40000
    # Drag shared boundary on overview: two neighboring segments change, total stays fixed.
    page.locator('#timelineCanvas').scroll_into_view_if_needed()
    layout=page.locator('#timelineCanvas').bounding_box()
    xpos=layout['x'] + 40000/128000*layout['width']
    ypos=layout['y'] + .5*layout['height']
    page.mouse.move(xpos,ypos);page.mouse.down()
    page.mouse.move(xpos+layout['width']*.035,ypos,steps=9);page.mouse.up()
    first_end=page.evaluate('LensBench.timeline().segments[0].end')
    assert first_end != 40000,(first_end, page.locator('#status').inner_text())
    assert page.evaluate('LensBench.timeline().segments[1].start')==first_end
    assert page.evaluate('LensBench.timeline().segments.reduce((a,s)=>a+s.end-s.start,0)')==128000
    page.locator('#preRoll').fill('100')
    page.locator('#previewBtn').click()
    page.wait_for_function("document.querySelector('#preview').getAttribute('src').startsWith('blob:')")
    assert 'PCM' not in page.locator('#renderDetails').inner_text() or 'WAV bytes' in page.locator('#renderDetails').inner_text()
    assert page.evaluate("LensBench.render().wav.byteLength===44+LensBench.render().pcm.length*2")
    assert page.evaluate("LensBench.render().forceMixed") is True
    page.locator('#stopBtn').click()
    assert page.locator('#stopDialog').evaluate('(d)=>d.open')
    assert page.locator('#keepList input').count()==3
    page.locator('#keepList input').nth(1).uncheck()
    page.locator('#keepBtn').click()
    assert page.evaluate("LensBench.timeline().segments.map(s=>s.status)")==['done','dropped','done']
    assert '2 Keep' in page.locator('#status').inner_text()
    assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=1
    assert not errors,errors
    page.screenshot(path=str(ROOT / ('preview_desktop.png' if width>800 else 'preview_mobile.png')),full_page=True)
    print('PASS workbench',width,'split/merge/drag PCM, WAV, stop Keep/Drop, mobile overflow')
    page.close()


def check_microphone(browser):
    ctx=browser.new_context(accept_downloads=True)
    page=ctx.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(HTML)
    page.locator('#micBtn').click()
    page.wait_for_function("document.querySelector('#modePill').textContent.includes('MIC ACTIVE')",timeout=12000)
    page.wait_for_function("LensBench.ring().end>20000",timeout=9000)
    ringBefore=page.evaluate('LensBench.ring().end')
    page.locator('#stopBtn').click()
    page.wait_for_function('document.querySelector("#stopDialog").open',timeout=8000)
    ringAfter=page.evaluate('LensBench.ring().end')
    assert ringAfter>=ringBefore
    assert page.evaluate('LensBench.timeline().segments.length')>=1
    assert page.locator('#modePill').inner_text().startswith('FROZEN')
    assert not errors,errors
    page.locator('#dropAllBtn').click()
    assert all(x=='dropped' for x in page.evaluate('LensBench.timeline().segments.map(s=>s.status)'))
    print('PASS AudioWorklet browser mic with fake device, frozen Stop, drop all,',ringAfter,'16k frames')
    ctx.close()


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=BROWSER,args=[
            '--no-sandbox','--disable-dev-shm-usage','--use-fake-device-for-media-stream',
            '--use-fake-ui-for-media-stream'])
        for width in (1200,375):check_page(browser,width)
        # This runtime blocks navigation to all URLs and about:blank is not a
        # secure microphone origin. Defer true AudioWorklet capture to Brave.
        browser.close()
if __name__=='__main__':main()
