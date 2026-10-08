import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c=await b.new_context(viewport={'width':400,'height':860}, accept_downloads=True); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { const id=i=>A.find(a=>a.iata===i).id, t0=Date.parse('2026-02-01T08:00:00+09:00');
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:[{a:id('HND'),t:t0,acc:20,term:'HND-T1'},{a:id('CTS'),t:t0+7.2e6,acc:20,term:null}],
            flights:[{id:'a1',from:id('HND'),to:id('CTS'),dep:t0,arr:t0+7.2e6,km:819.6,airline:'JL',no:'JL501'}], manual:[{from:id('ITM'),to:id('OKA'),d:'2025-03-03',airline:'NH'},{from:id('ITM'),to:A.find(a=>a.name.startsWith('新島')).id,d:'2025-04-04',airline:null}]})); }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        await pg.click('#openSettings')
        async with pg.expect_download() as d: await pg.click('[data-export=json]')
        dl = await d.value; path = await dl.path(); j = json.load(open(path)); print('json:', dl.suggested_filename, len(j['checkins']), len(j['flights']), len(j['manual']), j['flights'][0]['flight_no'])
        async with pg.expect_download() as d: await pg.click('[data-export=csv]')
        dl = await d.value; csv = open(await dl.path(), encoding='utf-8-sig').read(); print('csv:', dl.suggested_filename); print(csv)
        # 取り込み形式と互換か（デモで取り込んでみる）
        await pg.click('#toggleDemo'); await pg.click('nav.tabs button[data-v=log]')
        await pg.evaluate('document.getElementById("importBox").open = true'); await pg.fill('#impText', csv); await pg.click('#impCheck')
        print('reimport preview:', (await pg.inner_text('#impPreview')).splitlines()[0])
        print('legal links:', await pg.locator('.legal a').count(), '| errors', errs); await c.close()
        # サーバー版：アカウント削除
        c=await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        answers = iter(['けす', '削除'])
        pg.on('dialog', lambda dg: asyncio.ensure_future(dg.accept(next(answers, '')) if dg.type == 'prompt' else dg.accept()))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        await pg.click('#openSettings'); print('del row visible:', await pg.is_visible('#delRow'))
        await pg.click('#delAcct'); await pg.wait_for_timeout(300); print('wrong word -> called:', await pg.evaluate('!!window.__deleted'))
        await pg.click('#delAcct'); await pg.wait_for_timeout(600)
        print('deleted:', await pg.evaluate('JSON.stringify(window.__deleted)'), '| user:', await pg.evaluate('user'), '|', await pg.inner_text('#msg'))
        print('errors', errs); await b.close()
asyncio.run(main())
