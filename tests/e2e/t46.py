import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運営コンソールのバックアップ：前回から7日以上で知らせる、書き出したファイルが落ちてくる
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':760,'height':1000}, accept_downloads=True)
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_admin.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'admin_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        await pg.evaluate('__fa.login(true)'); await pg.wait_for_timeout(500)
        print('知らせ（未実施）:', await pg.inner_text('#msg'))
        await pg.click('[data-at=backup]'); await pg.wait_for_timeout(200)
        async with pg.expect_download() as d: await pg.click('#bkGo')
        dl = await d.value; data = json.load(open(await dl.path()))
        print('ファイル:', dl.suggested_filename[:24], '| 中身:', data['app'], len(data['checkins']))
        print('結果:', await pg.inner_text('#bkResult')); print('前回:', (await pg.inner_text('#bkLast'))[:18], '| 知らせ:', repr(await pg.inner_text('#msg')))
        await pg.evaluate("window.__lastBk = new Date(Date.now() - 9*864e5).toISOString(); checkBackupAge()"); await pg.wait_for_timeout(200)
        print('9日後の知らせ:', await pg.inner_text('#msg'))
        print(errs); await b.close()
asyncio.run(main())
