import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 6桁のコードでのログインと、ログイン前の記録の引き継ぎ
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        # ログイン前の端末の記録（フライト3件・記録帳2件、うち1件はサーバーの記録帳と重複）
        await pg.evaluate("""() => { const id=i=>A.find(a=>a.iata===i).id, t=Date.parse('2026-03-01T09:00:00+09:00');
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:[{a:id('HND'),t,acc:20,term:null},{a:id('CTS'),t:t+7e6,acc:20,term:null}],
            flights:[{id:'a1',from:id('HND'),to:id('CTS'),dep:t,arr:t+7e6,km:820,airline:'JL',no:null},{id:'a2',from:id('CTS'),to:id('HND'),dep:t+864e5,arr:t+864e5+7e6,km:820,airline:null,no:null},{id:'a3',from:id('HND'),to:id('OKA'),dep:t+2*864e5,arr:t+2*864e5+9e6,km:1555,airline:'NH',no:null}],
            manual:[{from:id('ITM'),to:id('FUK'),d:'2025-05-05',airline:null},{from:id('HND'),to:id('KIX'),d:'2025-06-06',airline:null}]}));
          __fake.db.manual_flights.push({id:900, from_airport:id('HND'), to_airport:id('KIX'), flown_on:'2025-06-06', airline:null}); }""")
        await pg.fill('#email', 'me@example.com'); await pg.click('#sendLink'); await pg.wait_for_timeout(200)
        print('コード欄:', await pg.is_visible('#codeBox'))
        await pg.fill('#loginCode', '111111'); await pg.click('#verifyCode'); await pg.wait_for_timeout(200); print('違うコード:', await pg.inner_text('#loginMsg'))
        await pg.fill('#loginCode', '12345678'); await pg.click('#verifyCode'); await pg.wait_for_timeout(700)
        print('ログイン後:', await pg.evaluate('user && user.email'), '| ログイン欄:', await pg.is_hidden('#loginBox'))
        print('引き継ぎの案内:', (await pg.inner_text('#migrateBar')).replace('\n',' ')[:120])
        await pg.click('[data-migrate=go]'); await pg.wait_for_timeout(700)
        print('結果:', await pg.inner_text('#msg'))
        rows = await pg.evaluate("JSON.stringify(__fake.db.manual_flights.map(r=>[r.from_airport,r.to_airport,r.flown_on,r.airline]))")
        print('サーバーの記録帳:', rows, '| 印はサーバーに増えない:', await pg.evaluate('__fake.db.checkins.length'))
        print('案内は消える:', await pg.is_hidden('#migrateBar'))
        await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(800); await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        print('読み込み直しても出ない:', await pg.is_hidden('#migrateBar'))
        print(errs); await b.close()
asyncio.run(main())
