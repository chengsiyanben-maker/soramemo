import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c=await b.new_context(geolocation={'latitude':35.0,'longitude':135.0,'accuracy':20}, permissions=['geolocation'], viewport={'width':400,'height':860})
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(800)
        print('before login:', await pg.is_visible('#loginBox'), '|', await pg.inner_text('#checkin'), '| disabled', await pg.is_disabled('#checkin'))
        await pg.fill('#email','test@example.com'); await pg.click('#sendLink'); await pg.wait_for_timeout(300)
        print('link:', await pg.inner_text('#loginMsg'))
        await pg.screenshot(path=os.path.join(WORK,'s_login.png'))
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        print('after login:', await pg.is_visible('#loginBox'), '|', await pg.inner_text('#checkin'))
        await pg.click('#checkin'); await pg.wait_for_timeout(300)
        await c.set_geolocation({'latitude':35.548889,'longitude':139.784444,'accuracy':25}); await pg.wait_for_timeout(1200)
        print('checkin:', await pg.inner_text('#msg'), '| stamp dialog', await pg.is_visible('#dStamp'))
        if await pg.is_visible('#dStamp .row2 .btn2'): await pg.click('#dStamp .row2 .btn2')
        print('tally airports:', await pg.inner_text('#tAirports'))
        await pg.click('nav.tabs button[data-v=log]')
        await pg.select_option('#mFrom', label='新千歳空港'); await pg.select_option('#mTo', label='那覇空港'); await pg.fill('#mDate','2025-08-01')
        await pg.click('#mAdd'); await pg.wait_for_timeout(400); print('manual:', await pg.inner_text('#mMsg'), await pg.evaluate('__fake.db.manual_flights.length'))
        await pg.click('#openSettings'); print('acct:', await pg.is_visible('#acctRow'), await pg.inner_text('#acctEmail'), '| wipe visible', await pg.is_visible('#wipeRow'))
        print(errs); await b.close()
asyncio.run(main())
