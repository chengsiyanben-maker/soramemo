import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運営画面の情報集めの表示（偽のサーバー）
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':760,'height':1000}, device_scale_factor=1)
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_admin.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'admin_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        await pg.evaluate('__fa.login(true)'); await pg.wait_for_timeout(400)
        for pane in ['metrics','usage','errors','quality']:
            await pg.click(f'[data-at={pane}]'); await pg.wait_for_timeout(300)
            txt = (await pg.inner_text(f'[data-pane={pane}]')).replace('\n',' ')
            print(pane, '|', txt[:170])
            await pg.screenshot(path=os.path.join(WORK, f'admin_{pane}.png'), full_page=True)
        print('warn rows:', await pg.locator('#qtable tr.warn').count())
        await pg.select_option('#days', '7'); await pg.wait_for_timeout(200); print('days changed ok')
        print(errs); await b.close()
asyncio.run(main())
