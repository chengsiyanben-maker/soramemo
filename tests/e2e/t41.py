import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ページの防御設定（CSP）：ふだんの操作で違反が起きないこと、差し込まれたスクリプトは止まること。メンテナンス表示
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });; window.__csp = []; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + (e.blockedURI || '')));")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        for v in ['book','log','stats']: await pg.click(f'nav.tabs button[data-v={v}]'); await pg.wait_for_timeout(150)
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(150)
        await pg.click('[data-mode=game]'); await pg.click('[data-mode=rally]')
        await pg.click('#openSettings'); await pg.click('#closeSettings')
        print('ふだんの操作での違反:', await pg.evaluate('window.__csp'))
        await pg.evaluate("""() => { const s = document.createElement('script'); s.textContent = 'window.__injected = true'; document.body.appendChild(s);
                                     const d = document.createElement('div'); d.innerHTML = '<img src=x onerror="window.__xss=true">'; document.body.appendChild(d); }""")
        await pg.wait_for_timeout(300)
        print('差し込んだスクリプトが動いた:', await pg.evaluate('!!window.__injected'), '| onerror が動いた:', await pg.evaluate('!!window.__xss'))
        # メンテナンス表示
        await pg.evaluate("window.__appStatus = {maintenance:true, checkin_enabled:false, message:'サーバーの点検中です'}; loadAppStatus()"); await pg.wait_for_timeout(300)
        print('お知らせ:', (await pg.inner_text('#statusBar')).replace('\n',' '), '| ボタン:', await pg.inner_text('#checkin'), await pg.is_disabled('#checkin'))
        print(errs); await b.close()
asyncio.run(main())
