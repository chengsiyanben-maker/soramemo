import os, sys, json, asyncio
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 経営を隠している間（KEIEI_VISIBLE = false）のチェックイン側の言葉（11/23 経営担当 keiei/hide #190 からの依頼）
#   1 チェックインの直後の一言に、行事のボーナス（経営の資金）を出さない。切り替えを true にしたときは今までどおり出す
#   2 図鑑の「記号の意味」：地方の色の説明で守り神に触れない。true のときは今までどおり
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
now = datetime.now(timezone.utc)
EV = [{'id': 'newyear-2027', 'name': '年末年始ボーナス', 'starts_at': (now - timedelta(days=1)).isoformat(), 'ends_at': (now + timedelta(days=3)).isoformat(), 'bonus': 5000, 'rare_mult': 2, 'note': None, 'open': True}]
async def run(b, keiei):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo')
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); window.__events = " + json.dumps(EV) + "; window.__bonus = [{event:'newyear-2027', name:'年末年始ボーナス', amount:5000}];" + ("window.__SORAMEMO_TEST_KEIEI = true;" if keiei else ""))
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    await c.grant_permissions(['geolocation']); await c.set_geolocation({'latitude': 42.7752, 'longitude': 141.6923, 'accuracy': 20})
    await pg.press('#checkin', 'Enter'); await pg.wait_for_timeout(400); await c.set_geolocation({'latitude': 42.7753, 'longitude': 141.6924, 'accuracy': 18}); await pg.wait_for_timeout(1800)
    msg = await pg.inner_text('#msg')
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(500)
    await pg.evaluate("setBookSeg('kigou'); renderVisible()"); await pg.wait_for_timeout(500)
    kg = await pg.inner_text('#bookKigou')
    if not keiei: await pg.screenshot(path=os.path.join(WORK, 't171_kigou.png'))
    await c.close(); return msg, kg, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        msg, kg, errs = await run(b, False)
        check('隠している間：チェックインの一言は出る', 'チェックインしました' in msg, msg)
        check('隠している間：行事のボーナス（経営の資金）を言わない', '経営の資金' not in msg and 'ボーナス' not in msg, msg)
        check('隠している間：記号の意味で守り神に触れない', '守り神' not in kg and '地方ごとに色を分けています' in kg, kg[:200])
        check('隠している間：ページのエラーなし', not errs, errs[:2])
        msg, kg, errs = await run(b, True)
        check('切り替えが true：今までどおりボーナスを言う', '経営の資金 +5,000万円' in msg, msg)
        check('切り替えが true：今までどおり「守り神の色」', '地方の色は空港の守り神の色です' in kg, kg[:200])
        check('切り替えが true：ページのエラーなし', not errs, errs[:2])
        await b.close()
    print('\n' + ('全部成功' if not fails else f'失敗 {len(fails)}件：' + ' / '.join(fails)))
    sys.exit(1 if fails else 0)
asyncio.run(main())
