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
        await pg.select_option('#demoAirport','t:HND-T1'); await pg.click('#checkin'); await pg.wait_for_timeout(700); await pg.click('#dStamp .row2 .btn2')
        for k, al, no in [('CTS','JL','501'),('OKA','NH','995'),('ITM',None,None)]:
            await pg.select_option('#demoAirport', ids[k]); await pg.click('#checkin'); await pg.wait_for_timeout(800)
            if al: await pg.click('#dStamp [data-flight]'); await pg.select_option('#fAirline',al); await pg.fill('#fNo',no); await pg.click('#fSave'); await pg.wait_for_timeout(150)
            else: await pg.click('#dStamp .row2 .btn2')
        async def snap(mode):
            t = await pg.inner_text('.tally'); print(mode, 'tally:', t.replace('\n',' '), '| bar:', (await pg.inner_text('#focusBar')).replace('\n',' '))
            await pg.click('nav.tabs button[data-v=book]'); print('  book:', await pg.inner_text('#bookProg'), '| dim:', await pg.locator('#book .cell.dim').count())
            await pg.click('nav.tabs button[data-v=stats]'); print('  stats:', (await pg.inner_text('#airlineStats')).replace('\n',' | '))
            await pg.click('nav.tabs button[data-v=log]')
            print('  flights:', await pg.locator('#flights .flight').count(), '| map routes:', await pg.locator('#map path').count()-1)
            await pg.click('nav.tabs button[data-v=home]')
        await snap('ALL')
        for m in ['JAL','ANA']:
            await pg.click('#openSettings'); await pg.click(f'[data-focus={m}]'); await pg.click('#closeSettings'); await pg.wait_for_timeout(150)
            await snap(m)
            if m=='JAL':
                await pg.screenshot(path=os.path.join(WORK,'f_home_jal.png'))
                await pg.click('nav.tabs button[data-v=book]'); await pg.screenshot(path=os.path.join(WORK,'f_book_jal.png')); await pg.click('nav.tabs button[data-v=home]')
                await pg.click('nav.tabs button[data-v=log]'); await pg.click('#shareMap'); await pg.wait_for_timeout(900)
                src=await pg.get_attribute('#shareImg','src'); open(os.path.join(WORK,'f_mapcard_jal.png'),'wb').write(base64.b64decode(src.split(',')[1])); await pg.click('#shareClose'); await pg.click('nav.tabs button[data-v=home]')
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500); print('persist:', await pg.evaluate('FOCUS'))
        await pg.click('#focusOff'); print('after off:', await pg.evaluate('FOCUS'), await pg.is_visible('#focusBar'))
        print(errs); await b.close()
asyncio.run(main())
