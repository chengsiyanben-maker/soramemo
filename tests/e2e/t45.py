import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営の公開スイッチ：公開前は見えない（デモでは試せる）、サーバーで公開すると出る
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 1) サーバーなし・公開前（config.js の gameReleased:false）
        c=await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        print('公開前：切り替え', await pg.is_visible('#modeSw'), '| 設定の経営', await pg.is_visible('#gameRow') if await pg.locator('#gameRow').count() else None)
        await pg.click('#openSettings'); print('  設定の経営（ダイアログ内）', await pg.is_visible('#gameRow')); await pg.click('#toggleDemo'); await pg.wait_for_timeout(300)
        print('デモ：切り替え', await pg.is_visible('#modeSw'))
        await pg.select_option('#demoAirport','t:HND-T1'); await pg.click('#checkin'); await pg.wait_for_timeout(700)
        print('  デモの守り神', await pg.locator('#dStamp .meet').count()); await pg.click('#dStamp [data-close]')
        await pg.click('#openSettings'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(300)
        print('デモ終了：切り替え', await pg.is_visible('#modeSw'), '| 表示中', await pg.evaluate('MODE'))
        print('errors', errs); await c.close()
        # 2) サーバー版：公開前 → 公開
        c=await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); window.__gameReleased = false;")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        print('サーバー公開前：切り替え', await pg.is_visible('#modeSw'), '| 会社の計算を頼んだ', await pg.evaluate('window.__coCalls || 0'))
        await pg.evaluate('window.__gameReleased = true; loadAppStatus()'); await pg.wait_for_timeout(500)
        print('運営が公開：切り替え', await pg.is_visible('#modeSw'), '| 会社の計算を頼んだ', await pg.evaluate('window.__coCalls || 0'))
        await pg.click('[data-mode=game]'); await pg.wait_for_timeout(200); print('  会社の画面', await pg.evaluate("document.querySelector('section.view.on').id"))
        print('errors', errs); await b.close()
asyncio.run(main())
