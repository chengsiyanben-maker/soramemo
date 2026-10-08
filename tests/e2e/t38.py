import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        # サーバーに2,500件のチェックインがある
        await pg.evaluate("""() => { const db = __fake.db; db.checkins.length = 0; let t = Date.parse('2024-01-01T09:00:00+09:00');
          for(let i=0;i<2500;i++) db.checkins.push({id:i+1, airport_id: A[i % 50].id, terminal_id:null, created_at:new Date(t += 36e5*5).toISOString(), accuracy_m:20}); }""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        print('読み込んだチェックイン:', await pg.evaluate('S.checkins.length'), '| 図鑑の空港:', await pg.evaluate('visited().size'))
        print('会社の計算を頼んだ:', await pg.evaluate("(window.__rpcs||[]).filter(n=>n==='co_state').length"))
        # 経営をオフにして読み込み直す
        await pg.evaluate("setGameOn(false); window.__rpcs = []"); await pg.evaluate('reload()'); await pg.wait_for_timeout(400)
        print('オフで読み込み直し → 会社の計算を頼んだ:', await pg.evaluate("window.__rpcs.filter(n=>n==='co_state').length"))
        await pg.evaluate("setGameOn(true)"); await pg.wait_for_timeout(400)
        print('オンに戻す → 会社の計算を頼んだ:', await pg.evaluate("window.__rpcs.filter(n=>n==='co_state').length"))
        print(errs); await b.close()
asyncio.run(main())
