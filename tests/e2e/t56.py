import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 行事のボーナス：ホームの案内、チェックインしたときの表示、経営の「受け取る」に足す
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
EV = [{'id': 'newyear-2027', 'name': '年末年始ボーナス', 'starts_at': (now - timedelta(days=1)).isoformat(), 'ends_at': (now + timedelta(days=3)).isoformat(), 'bonus': 5000, 'rare_mult': 2, 'note': None, 'open': True}]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); window.__events = " + json.dumps(EV) + "; window.__bonus = [{event:'newyear-2027', name:'年末年始ボーナス', amount:5000}];")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        await pg.wait_for_selector('#eventBar:not([hidden])', timeout=5000)
        await pg.locator('#homeSheet .sbody').screenshot(path=os.path.join(WORK,'t56_home.png')); t = await pg.inner_text('#eventBar')
        print('案内:', '年末年始ボーナス' in t and '5,000万円' in t and '2倍' in t, '| 受け取り方:', '「受け取る」' in t)
        await c.grant_permissions(['geolocation']); await c.set_geolocation({'latitude':42.7752,'longitude':141.6923,'accuracy':20})
        await pg.press('#checkin','Enter'); await pg.wait_for_timeout(400); await c.set_geolocation({'latitude':42.7753,'longitude':141.6924,'accuracy':18}); await pg.wait_for_timeout(1800)
        print('チェックイン:', '経営の資金 +5,000万円' in (await pg.inner_text('#msg')))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); window.__evb = {pending:5000, total:5000, count:1}")
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(1500)
        btn = await pg.inner_text('#coCollect')
        print('受け取る:', '行事のボーナス 5,000万円を含む' in btn)
        await pg.click('#coCollect'); await pg.wait_for_timeout(800)
        print('受け取ったあと:', '行事のボーナス' not in (await pg.inner_text('#coCollect')), '|', await pg.inner_text('#coMsg'))
        # 経営の公開前
        await pg.evaluate("GAME_RELEASED = false; renderEventBar()")
        print('公開前の案内:', '公開後に' in (await pg.inner_text('#eventBar')))
        print('errors', errs); await b.close()
asyncio.run(main())
