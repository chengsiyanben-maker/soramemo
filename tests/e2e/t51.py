import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# サーバー版：運賃を選ぶと保存される、搭乗券で便名・座席が付く、防御設定（CSP）に引っかからない
import asyncio, glob
from playwright.async_api import async_playwright
ZX = glob.glob('/tmp/build/node_modules/@zxing/library/umd/index.min.js')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); window.__csp=[]; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective+' '+e.blockedURI));")
        async def cdn(route):
            if '@zxing' in route.request.url: await route.fulfill(path=ZX[0], content_type='application/javascript')
            else: await route.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript')
        await c.route('https://cdn.jsdelivr.net/**', cdn)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        await pg.click('nav.tabs button[data-v=log]'); await pg.wait_for_timeout(200)
        n = await pg.locator('#flights .flight.tap').count(); print('フライト数:', n)
        await pg.click('#flights .flight.tap >> nth=0'); await pg.wait_for_timeout(200)
        await pg.select_option('#fAirline', 'NH'); await pg.wait_for_timeout(100)
        opts = await pg.locator('#fFare option').count(); print('ANAの運賃の選択肢:', opts)
        await pg.select_option('#fFare', index=3); await pg.click('#fSave'); await pg.wait_for_timeout(500)
        print('保存した運賃:', await pg.evaluate("JSON.stringify(window.__details)"))
        await pg.click('nav.tabs button[data-v=stats]')
        print('ステータス:', (await pg.inner_text('#statusBox')).replace('\n',' ')[:80])
        print('防御設定の違反:', await pg.evaluate('window.__csp'), errs)
        await b.close()
asyncio.run(main())
