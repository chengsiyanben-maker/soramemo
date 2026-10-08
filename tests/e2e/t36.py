import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for scheme in ['light','dark']:
            c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2, color_scheme=scheme); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
            pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
            vis = lambda: pg.evaluate("[...document.querySelectorAll('nav.tabs button')].filter(b=>!b.hidden).map(b=>b.textContent)")
            print(scheme, 'rally tabs:', await vis(), '| mode', await pg.evaluate('MODE'))
            await pg.click('#openSettings'); await pg.click('#toggleDemo')
            cts = await pg.evaluate("'a:'+A.find(a=>a.iata=='CTS').id")
            for v in ['t:HND-T1', cts]:
                await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(600)
                if v=='t:HND-T1': print('  meet:', (await pg.inner_text('#dStamp .meet')).replace('\n',' '))
                await pg.click('#dStamp .row2 .btn2')
            await pg.click('[data-mode=game]'); await pg.wait_for_timeout(200)
            print('  game tabs:', await vis(), '| on view:', await pg.evaluate("document.querySelector('section.view.on').id"))
            if scheme=='light': await pg.screenshot(path=os.path.join(WORK,'m_game.png'))
            await pg.click('nav.tabs button[data-v=fleet]'); print('  fleet view:', await pg.evaluate("document.querySelector('section.view.on').id"))
            await pg.evaluate('goTab("gods")')
            await pg.click('nav.tabs button[data-v=gods]'); print('  gods count:', await pg.locator('#coGods .god').count())
            if scheme=='dark': await pg.screenshot(path=os.path.join(WORK,'m_gods_dark.png'))
            await pg.click('[data-mode=rally]'); print('  back to rally view:', await pg.evaluate("document.querySelector('section.view.on').id"))
            await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400); print('  after reload mode:', await pg.evaluate('MODE'))
            # 経営をオフ
            await pg.click('[data-mode=game]'); await pg.click('#openSettings'); await pg.click('#gameToggle'); await pg.click('#closeSettings')
            print('  game off: mode', await pg.evaluate('MODE'), '| switch hidden', await pg.is_hidden('#modeSw'), '| tabs', await vis())
            await pg.click('#openSettings'); await pg.click('#toggleDemo')
            await pg.select_option('#demoAirport', 't:HND-T1'); await pg.click('#checkin'); await pg.wait_for_timeout(600)
            print('  meet when off:', await pg.locator('#dStamp .meet').count())
            if scheme=='light': await pg.click('#dStamp .row2 .btn2'); await pg.screenshot(path=os.path.join(WORK,'m_rally_off.png'))
            print('  errors', errs); await c.close()
        await b.close()
asyncio.run(main())
