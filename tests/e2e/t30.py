import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, base64
from playwright.async_api import async_playwright
CSV = "日付,出発,到着,航空会社\n2025-08-01,HND,CTS,JAL\n2025/08/03,新千歳,羽田,ANA\n2025-09-10,伊丹,那覇\n2025-09-11,OKA,OKA\n2025-13-01,HND,FUK\n2025-10-01,HND,XXX\n2025-10-02,福岡,羽田,ほげ航空\n2099-01-01,HND,CTS"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        # 1) 端末版（未加入）
        c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { const id=i=>A.find(a=>a.iata===i).id, t0=Date.parse('2026-02-01T08:00:00+09:00');
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:[{a:id('HND'),t:t0,acc:20,term:null},{a:id('CTS'),t:t0+7.2e6,acc:20,term:null}], flights:[{id:'a1',from:id('HND'),to:id('CTS'),dep:t0,arr:t0+7.2e6,km:820,airline:'JL',no:null}], manual:[]})); }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400); await pg.click('nav.tabs button[data-v=log]')
        print('local locked:', await pg.locator('#yrPlus .locked').count() == 1)
        await pg.click('nav.tabs button[data-v=log]')
        await pg.click('#importBox summary'); await pg.click('#impCheck'); print('local import:', await pg.inner_text('#impPreview'))
        await pg.click('#openSettings'); print('settings:', await pg.inner_text('#plusInfo')); await pg.click('#closeSettings')
        # 2) デモ（お試し）
        await pg.click('#openSettings'); await pg.click('#toggleDemo'); await pg.click('nav.tabs button[data-v=home]')
        cts = await pg.evaluate("'a:'+A.find(a=>a.iata=='CTS').id")
        for v in ['t:HND-T1', cts]:
            await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(600); await pg.click('#dStamp .row2 .btn2')
        await pg.click('nav.tabs button[data-v=log]'); await pg.wait_for_timeout(200)
        print('demo year plus:', (await pg.inner_text('#yrPlus')).replace('\n',' ')[:200])
        await pg.locator('#yrPlus').scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(WORK,'plus_year.png'))
        await pg.click('#yrShare'); await pg.wait_for_timeout(900)
        src=await pg.get_attribute('#shareImg','src'); open(os.path.join(WORK,'plus_card.png'),'wb').write(base64.b64decode(src.split(',')[1])); await pg.click('#shareClose')
        await pg.click('nav.tabs button[data-v=log]')
        await pg.evaluate('document.getElementById("importBox").open = true'); await pg.fill('#impText', CSV); await pg.click('#impCheck')
        print('preview:', (await pg.inner_text('#impPreview')).replace('\n',' | '))
        await pg.locator('#importBox').scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(WORK,'plus_import.png'))
        await pg.click('#impGo'); await pg.wait_for_timeout(200); print('after import:', await pg.inner_text('#impPreview'), '| manual', await pg.evaluate('S.manual.length'))
        print('errors:', errs); await c.close()
        # 3) サーバー版（偽）：未加入→加入
        c=await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        await pg.click('#openSettings'); print('server not plus:', await pg.inner_text('#plusInfo'), '|', await pg.inner_text('#plusBtn')); await pg.click('#closeSettings')
        await pg.click('nav.tabs button[data-v=log]'); print('server locked:', await pg.locator('#yrPlus .locked').count() == 1)
        await pg.evaluate('window.__plus = true'); await pg.evaluate('reload()'); await pg.wait_for_timeout(500); await pg.click('nav.tabs button[data-v=log]')
        print('server plus unlocked:', await pg.locator('#yrPlus .locked').count() == 0)
        await pg.click('#openSettings'); print('server plus:', await pg.inner_text('#plusInfo'), '|', await pg.inner_text('#plusBtn')); await pg.click('#closeSettings')
        await pg.click('nav.tabs button[data-v=log]')
        await pg.evaluate('document.getElementById("importBox").open = true'); await pg.fill('#impText', "2025-08-01,HND,CTS,JAL\n2025-08-03,CTS,HND"); await pg.click('#impCheck'); await pg.click('#impGo'); await pg.wait_for_timeout(500)
        print('server import:', await pg.inner_text('#impPreview'), '| server manual', await pg.evaluate('__fake.db.manual_flights.length'))
        print('errors:', errs); await b.close()
asyncio.run(main())
