import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 国際線の残り：国際線を記録する（記録帳の欄・乗る便のカードから）、運用タブに海外の航空会社の便（推定）
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': [{'h': h, 'flights': 0, 'late': 0, 'cancel': 0, 'ref': 0} for h in range(24)], 'next_arr': [],
         'next_dep': [{'flight': 'NH106', 'other': 'LAX', 'sched': iso(40), 'intl': True, 't': iso(40)}]}
FOREIGN = {'iata': 'HND', 'planes': [{'flight': 'KE2707', 'airline': 'KE', 'kind': 'arr', 'other': 'GMP', 'status': 'approach', 'alt_ft': 4000, 'type': 'A333', 'km': 22},
                                     {'flight': 'UA838', 'airline': 'UA', 'kind': 'dep', 'other': 'SFO', 'status': 'departed', 'alt_ft': 9000, 'type': 'B789', 'km': 30}]}
LIVE = {'flight': 'NH106', 'found': True, 'source': 'odpt', 'dep': 'HND', 'arr': 'LAX', 'std': iso(-240), 'sta': iso(375), 'atd': iso(-230), 'phase': 'air', 'progress': 0.4,
        'pos': {'lat': 45, 'lon': 170, 'alt_ft': 37000, 'kt': 560, 'at': iso(0)}, 'eta_pred': iso(360)}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            data = BOARD if name == 'airport_board' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/flight-live**', lambda r: r.fulfill(status=200, body=json.dumps(LIVE), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/airport-foreign**', lambda r: r.fulfill(status=200, body=json.dumps(FOREIGN), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        # 1. 運用タブ：海外の航空会社の便（推定）
        await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_selector('#opsBoard:not([hidden])', timeout=8000)
        t = await pg.inner_text('#opsBoard')
        check('海外の航空会社・到着:', 'ソウル（金浦）から' in t and 'KE2707' in t and '大韓航空' in t and '着陸に向かっています' in t and '推定' in t)
        await pg.locator('#opsBoard').screenshot(path=os.path.join(WORK, 't60_ops.png'))
        await pg.click('[data-board-dir="dep"]'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#opsBoard')
        check('海外の航空会社・出発:', 'サンフランシスコへ' in t and 'UA838' in t and 'ソウル（金浦）から' not in t)
        await pg.click('[data-board-kind="dom"]'); await pg.wait_for_timeout(600)
        check('国内線では出さない:', '海外の航空会社' not in (await pg.inner_text('#opsBoard')))
        # 2. 記録帳の欄から国際線を足す
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(500)
        await pg.click('[data-lseg="book"]'); await pg.wait_for_timeout(200)
        await pg.fill('#iFrom', '羽田'); await pg.fill('#iTo', 'HND'); await pg.fill('#iDate', '2026-08-01'); await pg.click('#iAdd'); await pg.wait_for_timeout(200)
        check('国内どうしは断る:', '記録帳' in (await pg.inner_text('#iMsg')))
        await pg.fill('#iTo', 'ソウル'); await pg.fill('#iNo', 'nh 863'); await pg.click('#iAdd'); await pg.wait_for_timeout(800)
        check('足せた:', '国際線に追加しました' in (await pg.inner_text('#iMsg')))
        row = await pg.evaluate("__fake.db.intl_flights[0]")
        check('保存した中身:', row['dep'] == 'HND' and row['arr'] == 'ICN' and row['flight_no'] == 'NH863' and row['flown_on'] == '2026-08-01' and 1150 < row['distance_km'] < 1250)
        await pg.fill('#iFrom', 'ICN'); await pg.fill('#iTo', 'ソウル（金浦）'); await pg.click('#iAdd'); await pg.wait_for_timeout(200)
        check('海外どうしは断る:', '日本の空港' in (await pg.inner_text('#iMsg')))
        lt = await pg.inner_text('#intlList')
        check('一覧に出る:', '国際線　1件' in lt and 'ICN' in lt and 'NH 863' in lt)
        await pg.evaluate("$('logSheet').sheetGo && $('logSheet').sheetGo('full')"); await pg.wait_for_timeout(400); await pg.evaluate("$('intlH').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(300); await pg.screenshot(path=os.path.join(WORK, 't60_book.png'))
        # 3. 乗る便のカードから記録する
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300)
        await pg.fill('#rideNo', 'NH106'); await pg.click('#rideAdd button'); await pg.wait_for_selector('#rideCard [data-ride-rec]', timeout=5000)
        await pg.click('[data-ride-rec]'); await pg.wait_for_timeout(800)
        rows = await pg.evaluate("__fake.db.intl_flights")
        r2 = rows[-1] if rows else {}
        check('乗る便から記録:', len(rows) == 2 and r2.get('flight_no') == 'NH106' and r2.get('arr') == 'LAX' and bool(r2.get('dep_at')) and (r2.get('arr_at') is None or r2['arr_at'] > r2['dep_at']))
        await pg.locator('#rideCard').screenshot(path=os.path.join(WORK, 't60_ride.png'))
        check('記録済みの表示:', '国際線の記録に入れました' in (await pg.inner_text('#rideCard')))
        # 4. 消す（2回押す）
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(400); await pg.click('[data-lseg="book"]'); await pg.wait_for_timeout(200)
        await pg.locator('[data-intl-del]').first.click(); await pg.wait_for_timeout(100)
        check('1回目は確かめる:', 'もう一度押すと消します' in (await pg.inner_text('#intlList')))
        await pg.locator('[data-intl-del]').first.click(); await pg.wait_for_timeout(800)
        check('消せた:', len(await pg.evaluate("__fake.db.intl_flights")) == 1)
        print('errors', errs + fails); await b.close()
asyncio.run(main())
