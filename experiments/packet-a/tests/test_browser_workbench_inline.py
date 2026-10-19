"""Offline Playwright proof of PCM editing UI when this runtime blocks all browser navigation.

Loads the same workbench bytes, with its local scripts inlined, via set_content.
This does not certify AudioWorklet/microphone APIs: about:blank lacks localhost security.
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BROWSER=os.environ.get('LENS_BROWSER_EXECUTABLE') or next((path for path in ('/Applications/Brave Browser.app/Contents/MacOS/Brave Browser','/usr/bin/chromium','/usr/bin/chromium-browser') if Path(path).is_file()),'/usr/bin/chromium')
HTML = (ROOT / 'audio_window_workbench.html').read_text(encoding='utf-8')
for module in ('lens_pcm_core.js', 'lens_pcm_capture.js'):
    HTML = HTML.replace('<script src="./'+module+'"></script>',
                        '<script>\n'+(ROOT / module).read_text(encoding='utf-8')+'\n</script>')


def check(width):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=BROWSER,
                                   args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': width, 'height': 850}, accept_downloads=True)
        errors=[]
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.set_content(HTML)
        page.locator('#fixtureBtn').click()
        assert page.locator('.clip').count()==3
        assert page.evaluate('LensBench.ring().end')==128000
        assert page.evaluate('LensBench.timeline().segments.map(x=>x.end-x.start)')==[40000,48000,40000]
        rect=page.locator('#waveCanvas').bounding_box()
        page.mouse.move(rect['x']+rect['width']*.36,rect['y']+rect['height']*.54)
        page.mouse.down();page.mouse.move(rect['x']+rect['width']*.4,rect['y']+rect['height']*.54,steps=6);page.mouse.up()
        page.locator('#splitBtn').click()
        assert page.locator('.clip').count()==4
        assert page.evaluate('LensBench.timeline().segments.reduce((a,s)=>a+s.end-s.start,0)')==128000
        assert page.evaluate('LensBench.timeline().segments[0].learningBlocked') is True
        assert page.evaluate('LensBench.timeline().segments[1].learningBlocked') is True
        page.locator('#mergeBtn').click()
        assert page.locator('.clip').count()==3
        assert page.evaluate('LensBench.timeline().segments[0].end')==40000
        page.locator('#timelineCanvas').scroll_into_view_if_needed()
        layout=page.locator('#timelineCanvas').bounding_box()
        xpos=layout['x']+40000/128000*layout['width']
        ypos=layout['y']+.5*layout['height']
        page.mouse.move(xpos,ypos);page.mouse.down()
        page.mouse.move(xpos+layout['width']*.035,ypos,steps=9);page.mouse.up()
        first_end=page.evaluate('LensBench.timeline().segments[0].end')
        assert first_end!=40000,(first_end,page.locator('#status').inner_text())
        assert page.evaluate('LensBench.timeline().segments[1].start')==first_end
        assert page.evaluate('LensBench.timeline().segments.reduce((a,s)=>a+s.end-s.start,0)')==128000
        page.locator('#preRoll').fill('100')
        page.locator('#previewBtn').click()
        page.wait_for_function("document.querySelector('#preview').getAttribute('src').startsWith('blob:')")
        assert page.evaluate('LensBench.render().wav.byteLength===44+LensBench.render().pcm.length*2')
        assert page.evaluate('LensBench.render().forceMixed') is True
        # The Stop dialog shows actual buffered clips, not fictional placeholders.
        page.locator('#stopBtn').click()
        assert page.locator('#stopDialog').evaluate('(d)=>d.open')
        assert page.locator('#keepList input').count()==3
        page.locator('#keepList input').nth(1).uncheck()
        page.locator('#keepBtn').click()
        assert page.evaluate('LensBench.timeline().segments.map(s=>s.status)')==['done','dropped','done']
        assert '2 Keep' in page.locator('#status').inner_text()
        assert page.evaluate('document.documentElement.scrollWidth-innerWidth')<=1
        assert not errors,errors
        print('PASS INLINE UI',width,'click/drag split-merge, exact PCM counts, pre-roll, Keep/Drop, layout')
        page.close();browser.close()


if __name__=='__main__':
    for size in (1200,375): check(size)
    print('NOTE: AudioWorklet/browser microphone tests require the actual localhost Brave runtime.')
