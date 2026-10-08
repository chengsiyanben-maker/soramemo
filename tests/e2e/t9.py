import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c=await b.new_context(geolocation={'latitude':35.5491,'longitude':139.7845,'accuracy':30}, permissions=['geolocation'], viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html'))
        await pg.click('details.dev summary >> nth=0')
        await pg.click('#probe'); await pg.wait_for_timeout(500)
        await c.set_geolocation({'latitude':35.5508,'longitude':139.7881,'accuracy':20}); await pg.wait_for_timeout(1000)
        print('probe:', await pg.inner_text('#probeOut'))
        await pg.click('#checkin'); await pg.wait_for_timeout(400)
        await c.set_geolocation({'latitude':35.5509,'longitude':139.7882,'accuracy':18}); await pg.wait_for_timeout(1500)
        print('checkin:', await pg.inner_text('#msg'))
        await pg.screenshot(path=os.path.join(WORK,'u_stamp_real.png'))
        print(errs); await b.close()
asyncio.run(main())
