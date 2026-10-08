import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運営コンソール：コードでのログイン、2段階認証の設定と確認、非常停止の切り替え
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':760,'height':1000})
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_admin.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('file://'+os.path.join(WORK,'admin_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        await pg.fill('#email', 'user@example.com'); await pg.click('#send'); await pg.wait_for_timeout(100)
        print('新規作成しない:', await pg.evaluate('__fa.otpOpts && __fa.otpOpts.shouldCreateUser === false'))
        await pg.fill('#code', '000000'); await pg.click('#verify'); await pg.wait_for_timeout(200); print('違うコード:', await pg.inner_text('#msg'))
        await pg.fill('#code', '123456'); await pg.click('#verify'); await pg.wait_for_timeout(300); print('運営者でない人:', await pg.inner_text('#msg'), '| 本体', await pg.is_visible('#main'))
        await pg.click('#mfaOut') if await pg.is_visible('#mfaOut') else None
        await pg.evaluate("supabase && 0"); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        await pg.fill('#email', 'admin@example.com'); await pg.click('#send'); await pg.fill('#code', '123456'); await pg.click('#verify'); await pg.wait_for_timeout(400)
        print('2段階認証の設定画面:', await pg.is_visible('#mfa'), '| QR:', await pg.locator('#mfaQr img').count(), '| 本体', await pg.is_visible('#main'))
        await pg.fill('#mfaCode', '111111'); await pg.click('#mfaGo'); await pg.wait_for_timeout(200); print('違うコード:', await pg.inner_text('#msg'))
        await pg.fill('#mfaCode', '654321'); await pg.click('#mfaGo'); await pg.wait_for_timeout(500); print('認証後 本体:', await pg.is_visible('#main'))
        await pg.click('[data-at=flags]'); await pg.wait_for_timeout(300)
        print('非常停止:', (await pg.inner_text('#flagsBox')).replace('\n',' ')[:120])
        await pg.click('[data-flag=checkin_enabled]'); await pg.wait_for_timeout(300)
        print('チェックイン停止 →', await pg.evaluate("__fa.flags().checkin_enabled.value"), '|', await pg.inner_text('#msg'))
        await pg.fill('#mmsg', '<b>点検</b>中'); await pg.click('[data-flag=maintenance_message]'); await pg.wait_for_timeout(300)
        print('お知らせ文:', await pg.evaluate("__fa.flags().maintenance_message.value"))
        print(errs); await b.close()
asyncio.run(main())
