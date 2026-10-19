import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 国際線：運用タブの国内線・国際線の切り替え、ホームで国際線・海外の航空会社の便を出発から到着まで追う
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
BOARD = lambda kind: {'iata': 'HND', 'now': iso(0), 'hours': [{'h': h, 'flights': 0, 'late': 0, 'cancel': 0, 'ref': 0} for h in range(24)], 'next_arr': [],
  'next_dep': ([{'flight': 'NH106', 'other': 'LAX', 'sched': iso(40), 'intl': True, 't': iso(40)}] if kind in ('all', 'intl') else []) + ([{'flight': 'JL555', 'other': 'KIX', 'sched': iso(30), 'intl': False, 't': iso(30)}] if kind in ('all', 'dom') else [])}
LIVE = {'NH106': {'flight': 'NH106', 'found': True, 'source': 'odpt', 'dep': 'HND', 'arr': 'LAX', 'std': iso(-240), 'sta': iso(375), 'phase': 'air', 'progress': 0.4,
                  'pos': {'lat': 45, 'lon': 170, 'alt_ft': 37000, 'kt': 560, 'at': iso(0)}, 'eta_pred': iso(360), 'reg': 'JA791A', 'type': 'B77W'},
        'KE703': {'flight': 'KE703', 'found': True, 'source': 'route_estimate', 'dep': 'ICN', 'arr': 'NRT', 'std': None, 'sta': None, 'phase': 'air', 'progress': 0.7,
                  'pos': {'lat': 36, 'lon': 135, 'alt_ft': 33000, 'kt': 480, 'at': iso(0)}, 'eta_pred': iso(50), 'reg': 'HL7789', 'type': 'A333'}}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
            if name == 'airport_board': data = BOARD(body.get('p_kind', 'all'))
            elif name == 'inbound_aircraft': data = {'flight': 'NH106', 'found': True, 'dep': 'HND', 'arr': 'LAX', 'std': iso(60)} if body.get('p_flight') == 'NH106' else {'flight': body.get('p_flight'), 'found': False}
            else: data = []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        async def live(r):
            f = r.request.url.split('flight=')[1].split('&')[0]
            await r.fulfill(status=200, body=json.dumps(LIVE.get(f, {'flight': f, 'found': False})), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/functions/v1/flight-live**', live)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        # 運用タブ：国際線の印と、海外の空港の日本語の名前、国内線・国際線の切り替え
        await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_selector('#opsBoard:not([hidden])', timeout=8000)
        await pg.click('[data-board-dir="dep"]'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#opsBoard .bdseq')
        print('すべて:', 'ロサンゼルスへ' in t and '国際' in t and '関西へ' in t)
        await pg.click('[data-board-kind="intl"]'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#opsBoard .bdseq')
        print('国際線だけ:', 'ロサンゼルス' in t and '関西' not in t)
        await pg.click('[data-board-kind="dom"]'); await pg.wait_for_timeout(600)
        print('国内線だけ:', 'ロサンゼルス' not in (await pg.inner_text('#opsBoard')))
        # ホーム：JAL・ANA の国際線
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300)
        await pg.fill('#rideNo', 'NH106'); await pg.click('#rideAdd button'); await pg.wait_for_selector('#rideCard:not([hidden])', timeout=5000)
        t = await pg.inner_text('#rideCard')
        print('国際線を追う:', '羽田 → ロサンゼルス' in t, '| 飛行中:', '飛行中' in t and '37,000ft' in t, '| 現地時刻:', '（現地）' in t, '| 進み具合:', await pg.locator('#rideCard .rbar').count() == 1)
        await pg.locator('#homeSheet .sbody').screenshot(path=os.path.join(WORK, 't59_intl.png'))
        await pg.click('[data-ride-off]'); await pg.wait_for_timeout(200)
        # 海外の航空会社（時刻表にない。いま飛んでいる便を機体の位置と経路のデータから）
        await pg.fill('#rideNo', 'KE703'); await pg.click('#rideAdd button'); await pg.wait_for_selector('#rideCard:not([hidden])', timeout=5000)
        t = await pg.inner_text('#rideCard')
        print('海外の航空会社:', 'ソウル（仁川） → 成田' in t and '（推定）' in t)
        await pg.click('[data-ride-off]'); await pg.wait_for_timeout(200)
        await pg.fill('#rideNo', 'XX9'); await pg.click('#rideAdd button'); await pg.wait_for_timeout(800)
        print('見つからない:', '見つかりませんでした' in (await pg.inner_text('#rideMsg')))
        print('errors', errs); await b.close()
asyncio.run(main())
