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
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        await pg.evaluate('goTab("co")')
        await pg.evaluate('goTab("co")')
        print('stars:', await pg.inner_text('#coStars'))
        await pg.evaluate('goTab("co")')
        await pg.select_option('#facPick', '5'); await pg.click('[data-build=new]'); await pg.wait_for_timeout(300)
        await pg.evaluate('goTab("co")')
        print('build:', await pg.inner_text('#coMsg'), '| fac', await pg.evaluate('JSON.stringify(CO.facilities)'), '| pts', await pg.evaluate('coRepPoints()'))
        print(errs); await b.close()
asyncio.run(main())
