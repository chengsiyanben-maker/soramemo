import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def geo_checkin(pg, c, lat, lon):
    await pg.click('#checkin'); await pg.wait_for_timeout(300)
    await c.set_geolocation({'latitude':lat,'longitude':lon,'accuracy':20}); await pg.wait_for_timeout(1200)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, geolocation={'latitude':35,'longitude':135,'accuracy':20}, permissions=['geolocation'])
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        await c.route('https://cdn.jsdelivr.net/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        # 1) 端末がオフライン → 保留
        await c.set_offline(True)
        await geo_checkin(pg, c, 35.5489, 139.7844)
        print('1 msg:', await pg.inner_text('#msg')); print('  bar:', (await pg.inner_text('#queueBar')).replace('\n',' '))
        # 2) オンライン表示だがサーバーに届かない → 保留
        await c.set_offline(False); await pg.evaluate('window.__offline = true')
        await geo_checkin(pg, c, 35.5508, 139.7881)
        print('2 msg:', await pg.inner_text('#msg')); print('  bar:', (await pg.inner_text('#queueBar')).replace('\n',' '))
        await pg.screenshot(path=os.path.join(WORK,'q_bar.png'))
        # 3) 今すぐ送る（まだ届かない）
        await pg.click('[data-flush]'); await pg.wait_for_timeout(300); print('3 msg:', await pg.inner_text('#msg'))
        # 4) つながる → online イベントで自動送信
        await pg.evaluate('window.__offline = false; window.dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(800)
        print('4 msg:', await pg.inner_text('#msg')); print('  bar hidden:', await pg.is_hidden('#queueBar'))
        print('  calls:', await pg.evaluate('JSON.stringify(window.__calls.map(c=>c.queued))'), '| checkins on server:', await pg.evaluate('__fake.db.checkins.length'))
        # 5) 次の通常チェックインは保留なしで送られる
        await geo_checkin(pg, c, 35.5444, 139.7679); print('5 msg:', await pg.inner_text('#msg'))
        print(errs); await b.close()
asyncio.run(main())
