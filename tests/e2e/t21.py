import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        await pg.click('#openSettings'); await pg.click('#toggleDemo')
        ids = {k: await pg.evaluate(f"'a:'+A.find(a=>a.iata=='{k}').id") for k in ['CTS','OKA','ISG']}
        for i,v in enumerate(['t:HND-T1', ids['CTS'], 't:HND-T2', ids['OKA'], ids['ISG']]):
            await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(650)
            if i==0: await pg.screenshot(path=os.path.join(WORK,'co_meet.png')); print('meet:', await pg.locator('#dStamp .meet').inner_text())
            await pg.click('#dStamp .row2 .btn2')
        await pg.evaluate('goTab("co")'); await pg.wait_for_timeout(200)
        await pg.evaluate('goTab("co")')
        print('rate:', await pg.inner_text('#coRate')); print('collect btn:', await pg.inner_text('#coCollect'), await pg.is_disabled('#coCollect'))
        # 3日たったことにする
        await pg.evaluate("CO.last = Date.now() - 3*864e5; coSave(); renderCompany();")
        await pg.evaluate('goTab("co")')
        print('after 3d:', await pg.inner_text('#coCollect'))
        await pg.evaluate('goTab("co")')
        await pg.click('#coCollect'); print('cash:', await pg.inner_text('#coCash'), '|', await pg.inner_text('#coMsg'))
        # 役職
        hnd = await pg.evaluate("A.find(a=>a.iata=='HND').id")
        await pg.evaluate('goTab("co")')
        await pg.select_option('[data-role=sales]', str(hnd)); await pg.wait_for_timeout(100)
        await pg.evaluate('goTab("co")')
        print('rate w/ role:', await pg.inner_text('#coRate'))
        await pg.evaluate('goTab("co")')
        await pg.select_option('[data-role=crew]', str(hnd)); print('roles:', await pg.evaluate('JSON.stringify(CO.roles)'))
        # 増便
        await pg.evaluate('goTab("fleet")')
        btn = pg.locator('[data-up]:not([disabled]) >> nth=0')
        await pg.evaluate('goTab("co")')
        if await btn.count(): await btn.click(); print('upgrade:', await pg.inner_text('#coMsg'), '| cash', await pg.inner_text('#coCash'))
        # 10日放置は7日で上限
        await pg.evaluate('goTab("co")')
        await pg.evaluate("CO.last = Date.now() - 10*864e5; renderCompany();"); print('cap:', await pg.inner_text('#coCollect'))
        await pg.screenshot(path=os.path.join(WORK,'co_tab.png'), full_page=True)
        await pg.evaluate('goTab("gods")')
        await pg.click('[data-god] >> nth=0'); await pg.wait_for_timeout(200); print('god:', (await pg.inner_text('#dGodBody')).replace('\n',' ')[:120])
        print(errs); await b.close()
asyncio.run(main())
