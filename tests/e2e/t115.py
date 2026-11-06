import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# コードのメールが送れなかったときの言い方（広告担当の依頼 2）
#   全体の上限（1時間100通）→「混み合っています」／同じアドレスへの送り直しが早すぎた → あと何秒／ほかの失敗 → 少し待って
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(WORK, 'send_busy_shots'); os.makedirs(SHOTS, exist_ok=True)
BUSY = '混み合っています。1時間ほどあとで試してください。'
WORD = {'signup':'いま登録が', 'login':'いまコードの送信が'}
CASES = [
  ('1時間の上限（Supabase の形）', "{status:429, code:'over_email_send_rate_limit', message:'email rate limit exceeded'}", BUSY),
  ('送りすぎ（429 だけ）', "{status:429, message:''}", BUSY),
  ('送りすぎ（code だけ）', "{status:400, code:'over_request_rate_limit', message:'Request rate limit reached'}", BUSY),
  ('同じアドレスへ早すぎる', "{status:429, code:'over_email_send_rate_limit', message:'For security purposes, you can only request this after 42 seconds.'}", 'あと42秒待ってください'),
  ('ほかの失敗', "{status:500, message:'Error sending confirmation email'}", '送れませんでした'),
]
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, init, shots=False):
    c = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2 if shots else 1, geolocation={'latitude':35.55,'longitude':139.78,'accuracy':20}, permissions=['geolocation'])
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    return c, pg, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for i, (name, err, want) in enumerate(CASES):
            c, pg, errs = await page(b, f"window.__otpErr = {err};", shots=(i == 0))
            # 新規登録の画面
            await pg.evaluate('authOpen("signup", "email")'); await pg.fill('#auEmail', 'sora@example.jp')
            await pg.click('#dAuth [data-au=signup-send]'); await pg.wait_for_timeout(250)
            msg = await pg.inner_text('#auMsg')
            check('新規登録：' + name, want in msg and (want != BUSY or WORD['signup'] in msg) and await pg.evaluate('AU.step') == 'email', msg)
            check('新規登録：' + name + '：もう一度押せる', await pg.is_enabled('#dAuth [data-au=signup-send]'))
            check('新規登録：' + name + '：送った時刻は残さない', await pg.evaluate('localStorage.getItem("soramemo.sentAt")') is None)
            if i == 0: await pg.screenshot(path=os.path.join(SHOTS, '01-signup-busy.png'))
            # ログインの画面（登録済みのメール）
            await pg.evaluate('authOpen("login", "login")'); await pg.wait_for_timeout(100)
            await pg.fill('#auEmail', 'sora@example.jp')
            await pg.click('#dAuth [data-au=login-send]'); await pg.wait_for_timeout(250)
            msg = await pg.inner_text('#auMsg')
            check('ログイン：' + name, want in msg and (want != BUSY or WORD['login'] in msg) and await pg.evaluate('AU.step') == 'login', msg)
            if i == 0: await pg.screenshot(path=os.path.join(SHOTS, '02-login-busy.png'))
            check(name + '：エラーなし', not errs, errs); await c.close()
        # 送れたときは今まで通りコードの画面へ
        c, pg, errs = await page(b, "")
        await pg.evaluate('authOpen("signup", "email")'); await pg.fill('#auEmail', 'sora@example.jp')
        await pg.click('#dAuth [data-au=signup-send]'); await pg.wait_for_timeout(250)
        check('送れたときはコードの画面', await pg.evaluate('AU.step') == 'code')
        check('送れたとき：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
