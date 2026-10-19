import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ターゲット向けの4つ：乗る便の機体はいまどこ・乗った機体の図鑑・修行の計画・順光の目安
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
IB = {'flight': 'JL0509', 'found': True, 'dep': 'HND', 'arr': 'CTS', 'std': iso(120), 'etd': None, 'atd': None, 'reg': 'JA305J', 'phase': None,
      'inbound': {'flight': 'JL0500', 'dep': 'ITM', 'arr': 'HND', 'std': iso(-20), 'sta': iso(50), 'atd': iso(-15), 'eta': None, 'ata': None, 'cancelled': False,
                  'phase': 'air', 'reg': 'JA305J', 'type': 'B738', 'takeoff': None, 'pos': {'lat': 35, 'lon': 137, 'alt': 30000, 'at': iso(0)}, 'share': 0.67, 'seen': 2},
      'arr_at': iso(150), 'arr_src': 'predicted', 'turn': 35, 'ready': iso(185), 'late': 65}
RO = {'dep': 'HND', 'arr': 'OKA', 'days': 30, 'flights': 120, 'measured': 90, 'ontime': 72, 'cancelled': 1}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
            if name == 'inbound_aircraft': data = IB
            elif name == 'route_ontime': data = RO
            elif name == 'flight_facts': data = [{'f': x['f'], 'd': x['d'], 'a': x['a'], 'reg': 'JA01XJ' if i % 2 == 0 else 'JA301J', 'type': 'A359' if i % 2 == 0 else 'B738', 'ata': None} for i, x in enumerate(body.get('p', []))]
            else: data = []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        # 1. 乗る便
        await pg.evaluate("""() => { const d = new Date(Date.now() + 9*36e5).toISOString().slice(0, 10);
          localStorage.setItem('soramemo.plan', JSON.stringify({ from:A.find(a => a.iata === 'HND').id, to:A.find(a => a.iata === 'CTS').id, airline:'JL', no:'JL509', day:d })); renderRide(true); }""")
        await pg.wait_for_selector('#rideCard:not([hidden])', timeout=5000)
        t = await pg.inner_text('#rideCard')
        print('乗る便:', 'JL509' in t, '| 遅れの見込み:', '約65分遅れの見込み' in t, '| 前の便:', 'JL500' in t and '伊丹' in t, '| 推定の割合:', '67%' in t)
        await pg.locator('#homeSheet .sbody').screenshot(path=os.path.join(WORK,'t57_ride.png'))
        await pg.click('[data-ride-off]'); await pg.wait_for_timeout(200)
        print('やめる:', await pg.is_hidden('#rideCard'), '| 入れる欄が出る:', await pg.is_visible('#rideAdd'))
        await pg.fill('#rideNo', 'xx'); await pg.click('#rideAdd button'); await pg.wait_for_timeout(200)
        print('形の違う便名:', '2文字と数字' in (await pg.inner_text('#rideMsg')))
        await pg.fill('#rideNo', 'jl509'); await pg.click('#rideAdd button'); await pg.wait_for_selector('#rideCard:not([hidden])', timeout=5000)
        print('便名を入れて調べる:', 'JL509' in (await pg.inner_text('#rideCard')), '| 入れる欄は隠れる:', await pg.is_hidden('#rideAdd'))
        await pg.click('[data-ride-off]'); await pg.wait_for_timeout(200)
        # 2. 乗った機体の図鑑（便名を記録したフライトを2便足す）
        await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, k = A.find(a => a.iata === 'CTS').id;
          S.flights.push({ id:91, from:h, to:k, dep:Date.now() - 2*864e5, arr:Date.now() - 2*864e5 + 5400000, km:820, airline:'JL', no:'JL501', status:'with_flight_no' },
                         { id:92, from:k, to:h, dep:Date.now() - 864e5, arr:Date.now() - 864e5 + 5400000, km:820, airline:'JL', no:'JL502', status:'with_flight_no' }); FACTS_KEY = ''; }""")
        await pg.evaluate("goTab('stats')"); await pg.wait_for_timeout(1500)
        fb = await pg.inner_text('#fleetBook')
        print('図鑑:', 'JA01XJ' in fb and 'JA301J' in fb, '| 特別塗装機:', 'A350 1号機' in fb, '| 機種:', 'エアバスA350-900' in fb)
        # 3. 修行の計画（そらメモ＋なしでも出る）
        await pg.click('[data-plan-q="HND-OKA"]'); await pg.wait_for_timeout(800)
        pl = await pg.inner_text('#statusBox .plan')
        print('修行の計画:', '修行の計画' in pl and 'あと' in pl, '| 路線の定時率:', '定時 80%' in pl)
        await pg.fill('#planPrice', '30000'); await pg.dispatch_event('#planPrice', 'change'); await pg.wait_for_timeout(300)
        print('単価:', 'PP単価' in (await pg.inner_text('#statusBox .plan')))
        await pg.locator('#statusBox .plan').screenshot(path=os.path.join(WORK,'t57_plan.png'))
        # 4. 順光の目安（計算だけ確かめる：正午に、南の線を見る場所は逆光、北の線を見る場所は順光）
        lt = await pg.evaluate("""() => { const t = Date.parse('2026-10-19T12:00:00+09:00'), s = [35.55, 139.78];
          return [lightAt(t, s, [35.50, 139.78]), lightAt(t, s, [35.60, 139.78]), lightAt(Date.parse('2026-10-19T22:00:00+09:00'), s, [35.6, 139.78])]; }""")
        print('順光:', lt)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(2500)
        print('よく見える場所に光の向き:', await pg.locator('#opsSpots .lt').count() > 0 or 'unknown-op', '|', ((await pg.inner_text('#opsSpots')) if await pg.is_visible('#opsSpots') else '')[:60].replace('\n', ' '))
        print('errors', errs); await b.close()
asyncio.run(main())
