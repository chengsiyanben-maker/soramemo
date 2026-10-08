import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ログインのロボット除け（Turnstile）：鍵があるときは合図つきで送り、送ったら使い捨てる。防御設定（CSP）の違反がないこと
import asyncio, shutil
from playwright.async_api import async_playwright
async def main():
    d = os.path.join(WORK, 'captcha'); os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(d, 'index.html'))
    open(os.path.join(d, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon", turnstileSiteKey: "0x4AAAAAAATEST" };')
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });; window.__csp = []; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://challenges.cloudflare.com/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_turnstile.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(d,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(800)
        print('部品の鍵:', await pg.evaluate('window.__tsOpts && window.__tsOpts.sitekey'))
        await pg.fill('#email', 'test@example.com'); await pg.click('#sendLink'); await pg.wait_for_timeout(300)
        print('送った合図:', await pg.evaluate('window.__otp && window.__otp.options.captchaToken'), '| 使い捨て:', await pg.evaluate('window.__tsReset'))
        print('メッセージ:', await pg.inner_text('#loginMsg'))
        print('防御設定の違反:', await pg.evaluate('window.__csp'))
        print(errs); await b.close()
asyncio.run(main())
