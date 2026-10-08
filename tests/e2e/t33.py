import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':420,'height':900}, device_scale_factor=2)
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_admin.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept('位置偽装の疑い')))
        await pg.goto('file://'+os.path.join(WORK,'admin_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        print('login shown:', await pg.is_visible('#login'))
        await pg.evaluate('__fa.login(false)'); await pg.wait_for_timeout(300); print('non-admin:', await pg.inner_text('#msg'), '| main hidden:', await pg.is_hidden('#main'))
        await pg.evaluate('__fa.login(true)'); await pg.wait_for_timeout(400)
        print('stats:', (await pg.inner_text('#stats')).replace('\n',' ')); print('count:', await pg.inner_text('#cnt'))
        await pg.screenshot(path=os.path.join(WORK,'admin.png'))
        await pg.click('[data-clear="3"]'); await pg.wait_for_timeout(300); print('clear:', await pg.inner_text('#msg'), await pg.inner_text('#cnt'))
        await pg.click('[data-void="2"]'); await pg.wait_for_timeout(300); print('void:', await pg.inner_text('#msg'), await pg.inner_text('#cnt'), '| reason:', await pg.evaluate('__fa.reason'))
        print(errs); await b.close()
asyncio.run(main())
