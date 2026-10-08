import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, base64
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(800)
        await pg.click('#openSettings'); await pg.click('#toggleDemo')
        ids = {k: await pg.evaluate(f"'a:'+A.find(a=>a.iata=='{k}').id") for k in ['CTS','OKA','ITM']}
        await pg.select_option('#demoAirport','t:HND-T1'); await pg.click('#checkin'); await pg.wait_for_timeout(800); await pg.click('#dStamp .row2 .btn2')
        await pg.select_option('#demoAirport', ids['CTS']); await pg.click('#checkin'); await pg.wait_for_timeout(900)
        await pg.screenshot(path=os.path.join(WORK,'al_stamp.png'))
        await pg.click('#dStamp [data-flight]'); await pg.wait_for_timeout(200)
        await pg.select_option('#fAirline','JL'); await pg.fill('#fNo','501'); await pg.screenshot(path=os.path.join(WORK,'al_dialog.png')); await pg.click('#fSave'); await pg.wait_for_timeout(200)
        await pg.select_option('#demoAirport', ids['OKA']); await pg.click('#checkin'); await pg.wait_for_timeout(900); await pg.click('#dStamp [data-flight]')
        await pg.select_option('#fAirline','NH'); await pg.fill('#fNo','12a'); await pg.click('#fSave'); await pg.wait_for_timeout(100)
        print('bad no msg:', await pg.inner_text('#fMsg'))
        await pg.fill('#fNo','995'); await pg.click('#fSave'); await pg.wait_for_timeout(200)
        await pg.select_option('#demoAirport', ids['ITM']); await pg.click('#checkin'); await pg.wait_for_timeout(900); await pg.click('#dStamp .row2 .btn2')
        await pg.click('nav.tabs button[data-v=stats]'); await pg.wait_for_timeout(300)
        print('stats:', (await pg.inner_text('#airlineStats')).replace('\n',' | '))
        h = await pg.locator('h2:has-text("航空会社別")').bounding_box(); await pg.evaluate(f"window.scrollTo(0,{h['y']-70})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(WORK,'al_stats.png'))
        await pg.click('nav.tabs button[data-v=log]'); await pg.wait_for_timeout(200)
        print('flights:', (await pg.inner_text('#flights')).replace('\n',' | '))
        # edit existing: clear JAL
        await pg.click('#flights .flight.tap >> nth=2'); await pg.select_option('#fAirline',''); await pg.click('#fSave'); await pg.wait_for_timeout(200)
        print('after clear:', (await pg.inner_text('#flights')).replace('\n',' | '))
        await pg.select_option('#mFrom', label='新千歳空港'); await pg.select_option('#mTo', label='那覇空港'); await pg.fill('#mDate','2025-08-01'); await pg.select_option('#mAirline','BC'); await pg.click('#mAdd'); await pg.wait_for_timeout(200)
        print('manual:', (await pg.inner_text('#manualList')).replace('\n',' | '))
        await pg.click('#shareMap'); await pg.wait_for_timeout(1000)
        src=await pg.get_attribute('#shareImg','src'); open(os.path.join(WORK,'al_mapcard.png'),'wb').write(base64.b64decode(src.split(',')[1]))
        print(errs); await b.close()
asyncio.run(main())
