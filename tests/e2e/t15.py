import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(700)
        await pg.click('#openSettings'); await pg.click('#toggleDemo')
        cts = await pg.evaluate("'a:'+A.find(a=>a.iata=='CTS').id"); isg = await pg.evaluate("'a:'+A.find(a=>a.iata=='ISG').id")
        seq = ['t:HND-T1', cts]*5 + ['t:HND-T2','t:HND-T3', isg]
        for i,v in enumerate(seq):
            await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(650)
            na = await pg.locator('#dStamp .newach').all_inner_texts()
            if na: print(i, v, '->', na[0].replace('\n',' '))
            if 'HND' in v and i==8: print('tier dlg:', (await pg.inner_text('#dStampBody')).replace(chr(10),' '))
            if i==len(seq)-1: await pg.screenshot(path=os.path.join(WORK,'a_stamp.png'))
            await pg.click('#dStamp .row2 .btn2')
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(200)
        print('prog:', await pg.inner_text('#achProg')); await pg.screenshot(path=os.path.join(WORK,'a_tab.png'))
        await pg.click('nav.tabs button[data-v=book]'); await pg.click('#v-book [data-seg=main]'); await pg.wait_for_timeout(200)
        print('vcounts:', await pg.locator('#book .vcount').all_inner_texts())
        await pg.click('#book .cell.got >> nth=0'); print('detail:', (await pg.inner_text('#dAirportBody')).replace('\n',' '))
        print(errs); await b.close()
asyncio.run(main())
