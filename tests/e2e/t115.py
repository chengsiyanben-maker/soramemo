import os, sys, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 確認コードのけた数（config.js の otpLength = 6。本番の Supabase の Email OTP Length と同じ）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, re
from playwright.async_api import async_playwright
d = os.path.join(WORK, 'otp6'); os.makedirs(d, exist_ok=True)
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(d, 'index.html'))
open(os.path.join(d, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon", otpLength: 6 };')
SHOTS = os.path.join(WORK, 'signup_shots'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def open_page(b, shots=False):
    c = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2 if shots else 1)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); window.__otpCode = '246810'; window.__profiles = [{user_id:'u1', display_name:null, persona:'unanswered', terms_version:null, privacy_version:null, agreed_at:null}];")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(d,'index.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    return c, pg, errs
async def step(pg): return await pg.evaluate('$("dAuth").open ? AU.step : "closed"')
async def main():
    # 本番の設定が6けたになっていること
    cfg = open(os.path.join(WEB, 'config.js'), encoding='utf-8').read()
    check('本番の設定は6けた', re.search(r'otpLength:\s*6\b', cfg) is not None)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. 新規登録：6けたで受け付ける
        c, pg, errs = await open_page(b, shots=True)
        check('けた数を読む', await pg.evaluate('OTP_LEN') == 6)
        await pg.evaluate('authOpen("signup", "email")'); await pg.wait_for_timeout(200)
        await pg.fill('#auEmail', 'six@example.jp'); await pg.click('#dAuth [data-au=signup-send]'); await pg.wait_for_timeout(200)
        check('コードの画面', await step(pg) == 'code')
        check('入力欄は6けたまで', await pg.get_attribute('#auCode', 'maxlength') == '6')
        await pg.type('#auCode', '24681'); await pg.wait_for_timeout(100)
        check('5けたでは確かめるを押せない', await pg.is_disabled('#dAuth [data-au=verify]'))
        await pg.screenshot(path=os.path.join(SHOTS, '07-code6.png'))
        await pg.type('#auCode', '0'); await pg.wait_for_timeout(600)
        check('6けた入れると自動で確かめる', (await pg.evaluate('window.__verify && window.__verify.token')) == '246810')
        check('コードが合うと表示名へ', await step(pg) == 'name')
        check('新規登録：エラーなし', not errs, errs); await c.close()
        # 2. ログイン：貼り付けた8けたは6けたに切る・違うコードは断る
        c, pg, errs = await open_page(b)
        await pg.evaluate('authOpen("login")'); await pg.wait_for_timeout(200)
        await pg.fill('#auEmail', 'six@example.jp'); await pg.click('#dAuth [data-au=login-send]'); await pg.wait_for_timeout(200)
        check('ログイン：コードの画面', await step(pg) == 'code')
        await pg.fill('#auCode', '13579135'); await pg.dispatch_event('#auCode', 'input'); await pg.wait_for_timeout(500)
        check('長いコードは6けたに切って確かめる', (await pg.evaluate('window.__verify && window.__verify.token')) == '135791')
        check('違うコードは断る', 'コードが違う' in await pg.inner_text('#auMsg') and await step(pg) == 'code')
        check('ログイン：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
