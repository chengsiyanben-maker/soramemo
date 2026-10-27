import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行の画面（窓で開く。下のタブに修行がない構成＝気軽に）：成績から開く、この路線に乗ったら（会員情報のボーナス・支払いのマイル）、会員情報の保存、計画を作って予定に入れる、路線の運航状況、予算、フライトの金額
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
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','casual')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        RT = [{'flight': 'NH461', 'std': iso(-300), 'sta': iso(-140), 'atd': iso(-298), 'ata': iso(-150), 'cancelled': False, 'aircraft': 'B789'},
              {'flight': 'NH463', 'std': iso(-60), 'sta': iso(100), 'etd': iso(-30), 'atd': iso(-30), 'cancelled': False},
              {'flight': 'NH467', 'std': iso(60), 'sta': iso(220), 'cancelled': True},
              {'flight': 'NH469', 'std': iso(120), 'sta': iso(280), 'cancelled': False}]
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            body = json.loads(r.request.post_data or '{}')
            data = RT if name == 'route_today' and body.get('p_dep') == 'HND' else [] if name == 'route_today' else {'measured': 40, 'ontime': 34, 'cancelled': 1} if name == 'route_ontime' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        NOW = {'weather': {'sky': '晴れ', 'temp': 24, 'wdir': 180, 'wspd': 14}, 'taf': None, 'flights': None}
        await c.route('https://fake.supabase.co/functions/v1/airport-now**', lambda r: r.fulfill(status=200, body=json.dumps(NOW), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(900)
        await pg.evaluate("goTab('stats')"); await pg.wait_for_timeout(300)
        await pg.click('#v-stats [data-sg-open="main"]'); await pg.wait_for_timeout(400)
        check('修行の画面が開く:', await pg.evaluate("$('dShugyo').open") and '年の修行' in await pg.inner_text('#dShugyo'))
        await pg.wait_for_timeout(500)
        t = await pg.inner_text('#dShugyo'); check('路線の運航状況（今日の便・遅れ・欠航）:', '今日 4便' in t and '遅れ 1便' in t and '欠航 1便' in t)
        # この路線に乗ったら（羽田→那覇・JAL）
        await pg.click('#dShugyo .sg-search'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#dShugyo'); check('この路線：JAL のいちばん貯まる運賃 3,352 FOP:', '3,352' in t and '984マイル' in t)
        check('スカイメイトの行がある:', 'スカイメイト' in t)
        # 会員情報（サファイア・CLUB-A・ショッピングマイル・プレミアム・JALカードで払う）
        await pg.click('#dShugyo [data-sg-go="profile"]'); await pg.wait_for_timeout(200)
        await pg.click('[data-sg-pick="jal.status"][data-v="sapphire"]'); await pg.click('[data-sg-pick="jal.card"][data-v="cluba"]')
        await pg.click('[data-sg-tog="jal.smp"]'); await pg.click('[data-sg-tog="jal.pay"]'); await pg.click('[data-sg-saveprof]'); await pg.wait_for_timeout(300)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0] && __fake.db.shugyo_prefs[0].data")
        check('会員情報がサーバーに保存される:', d and d['jal']['status'] == 'sapphire' and d['jal']['card'] == 'cluba' and d['jal']['pay'] is True)
        await pg.click('#dShugyo .sg-back'); await pg.wait_for_timeout(200)
        await pg.select_option('#sgQmf', 'JAL:J_FLEX'); await pg.fill('#sgQmp', '52000'); await pg.dispatch_event('#sgQmp', 'change'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#dShugyo .sg-res.rj'); print('MINE', t.replace('\n', ' | '))
        check('あなたの場合：1,082 ＋ サファイア105% 1,136 ＋ 支払い 1,040 ＝ 3,258:', '1,082' in t and '+1,136' in t and '+1,040' in t and '3,258' in t and '2,564' in t)
        # 計画に入れる → 予定に入れる
        await pg.click('[data-sg-q2trip]'); await pg.wait_for_timeout(300)
        check('計画の画面へ:', '自分で区間を入れて計算する' in await pg.inner_text('#dShugyo'))
        await pg.fill('#sgTripD', '2026-12-05'); await pg.dispatch_event('#sgTripD', 'change'); await pg.wait_for_timeout(200)
        await pg.click('[data-sg-addtrip]'); await pg.wait_for_timeout(300)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data")
        check('予定の便が保存される:', len(d['plans']) == 1 and d['plans'][0]['d'] == '2026-12-05' and d['plans'][0]['price'] == 52000)
        # 運賃をくらべる：金額を入れて1ポイントあたり
        await pg.locator('[data-sg-fp="Y_SAVER"]').fill('19800'); await pg.dispatch_event('[data-sg-fp="Y_SAVER"]', 'change'); await pg.wait_for_timeout(200)
        check('運賃くらべの1ポイントあたり（19,800円 ÷ 1,676 ＝ 11.8円）:', '11.8円' in await pg.inner_text('#dShugyo'))
        # 予算
        await pg.click('#dShugyo [data-sg-go="budget"]'); await pg.wait_for_timeout(200)
        await pg.fill('#sgBudget', '600000'); await pg.dispatch_event('#sgBudget', 'change'); await pg.wait_for_timeout(300)
        check('予算が保存され、のこりが出る:', (await pg.evaluate("__fake.db.shugyo_prefs[0].data.budget")) == 600000 and 'のこり' in await pg.inner_text('#dShugyo'))
        await pg.screenshot(path=os.path.join(WORK, 't64_budget.png'))
        # 路線の運航状況
        await pg.click('#dShugyo [data-sg-go="planner"]'); await pg.wait_for_timeout(100); await pg.click('#dShugyo .sg-back'); await pg.wait_for_timeout(100)
        await pg.evaluate("sgGo('ops')"); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#dShugyo'); print('OPS', t[:300].replace('\n', ' | '))
        check('運航状況：欠航・遅れ・定時率・天気:', '欠航' in t and '30分遅れ' in t and '85%' in t and '晴れ' in t)
        await pg.evaluate("$('dShugyo').close()")
        # フライトに金額を入れる
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(300)
        await pg.evaluate("openFlight(fid(S.flights.find(f => f.id === 7)))"); await pg.wait_for_timeout(300)
        await pg.select_option('#fAirline', 'JL'); await pg.dispatch_event('#fAirline', 'change'); await pg.wait_for_timeout(100)
        await pg.fill('#fPrice', '38900'); await pg.click('#fSave'); await pg.wait_for_timeout(500)
        check('フライトの金額が保存される:', (await pg.evaluate("__fake.db.flights.find(f => f.id === 7).price")) == 38900)
        print('errors', errs, 'fails', fails); await b.close()
asyncio.run(main())
