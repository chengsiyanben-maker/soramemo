import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        await pg.click('nav.tabs button[data-v=log]'); await pg.click('#flights .flight.tap >> nth=0')
        await pg.select_option('#fAirline','NH'); await pg.fill('#fNo','61'); await pg.click('#fSave'); await pg.wait_for_timeout(500)
        print('rpc:', await pg.evaluate('JSON.stringify(window.__lastRpc)'))
        print('list:', (await pg.inner_text('#flights')).replace('\n',' | '))
        await pg.click('nav.tabs button[data-v=stats]')
        print('stats head:', await pg.inner_text('.alhead'))
        print(errs); await b.close()
asyncio.run(main())
