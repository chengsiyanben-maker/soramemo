import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 使われ方とエラーの送信（偽のサーバー）。利用者IDや座標が入らないこと、オフにすると送らないこと
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, geolocation={'latitude':35,'longitude':135,'accuracy':20}, permissions=['geolocation'])
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        sent = []
        async def rpc(route):
            sent.append((route.request.url.split('/')[-1], json.loads(route.request.post_data or '{}'), route.request.headers.get('authorization','')))
            await route.fulfill(status=200, body='1', content_type='application/json')
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        await pg.click('nav.tabs button[data-v=book]'); await pg.click('[data-mode=game]')
        # 範囲外のチェックイン（サーバー側で断られる）
        await pg.click('[data-mode=rally]'); await pg.click('nav.tabs button[data-v=home]'); await pg.click('#checkin'); await pg.wait_for_timeout(300)
        await c.set_geolocation({'latitude':35.6946,'longitude':139.9826,'accuracy':25}); await pg.wait_for_timeout(1500)
        print('msg:', await pg.inner_text('#msg'))
        await pg.evaluate('window.dispatchEvent(new ErrorEvent("error", {message:"テスト用のエラー", filename:"https://x/index.html", lineno:3, colno:4}))')
        await pg.evaluate('flushEvents()'); await pg.wait_for_timeout(400)
        ev = [x for x in sent if x[0]=='log_events']; er = [x for x in sent if x[0]=='log_error']
        events = [e['e'] + (':' + str(e['p']) if e['p'] is not None else '') for x in ev for e in x[1]['p_events']]
        print('events:', events)
        print('error:', [(x[1]['p_kind'], x[1]['p_message'], x[1]['p_detail']) for x in er])
        blob = json.dumps([x[1] for x in sent], ensure_ascii=False)
        print('利用者IDを含む:', 'u1' in blob or 'test@example.com' in blob, '| 座標を含む:', '35.69' in blob or '139.98' in blob, '| 匿名キーで送信:', all(x[2] == 'Bearer anon' for x in sent))
        # オフにすると送らない
        n0 = len(sent); await pg.click('#openSettings'); await pg.click('#anaToggle'); await pg.click('#closeSettings')
        await pg.click('nav.tabs button[data-v=log]'); await pg.evaluate('flushEvents()'); await pg.evaluate('window.dispatchEvent(new ErrorEvent("error", {message:"オフのとき"}))'); await pg.wait_for_timeout(400)
        print('オフ後に送った数:', len([x for x in sent[n0:] if not (x[0]=='log_events' and any(e['e']=='analytics' for e in x[1]['p_events']))]))
        print(errs); await b.close()
asyncio.run(main())
