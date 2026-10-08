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
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept('  羽田エアライン ')))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        await pg.evaluate('goTab("co")'); await pg.wait_for_timeout(200)
        await pg.evaluate('goTab("co")')
        print('state:', await pg.inner_text('#coCash'), '|', await pg.inner_text('#coRate'), '|', await pg.inner_text('#coCollect'))
        await pg.evaluate('goTab("co")')
        await pg.click('#coCollect'); await pg.wait_for_timeout(300); print('collect:', await pg.inner_text('#coCash'), '|', await pg.inner_text('#coMsg'))
        await pg.evaluate('goTab("fleet")')
        await pg.click('[data-up="5-6"]'); await pg.wait_for_timeout(300); print('upgrade:', await pg.inner_text('#coCash'), '|', await pg.inner_text('#coMsg'), '|', await pg.evaluate('CO.routes.get("5-6").level'))
        await pg.evaluate('goTab("co")')
        await pg.select_option('[data-role=crew]', '5'); await pg.wait_for_timeout(300); print('role:', await pg.inner_text('#coRate'), await pg.evaluate('JSON.stringify(CO.roles)'))
        await pg.evaluate('goTab("co")')
        await pg.click('#coName'); await pg.wait_for_timeout(400); print('name:', await pg.inner_text('#coName'))
        print('local key untouched:', await pg.evaluate('Object.keys(localStorage).filter(k=>k.startsWith("soramemo.company"))'))
        print(errs); await b.close()
asyncio.run(main())
