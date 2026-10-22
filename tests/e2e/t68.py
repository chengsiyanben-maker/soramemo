import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 見る・遊ぶ：特別塗装機の図鑑・機体の1日・あの日の空・空港の傾向
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc); now = datetime(_d.year, _d.month, _d.day, 3, 0, tzinfo=timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
today = (now + timedelta(hours=9)).strftime('%Y-%m-%d')
HIST = [{'day': today, 'callsign': 'JAL501', 'dep': 'HND', 'arr': 'CTS', 'first': iso(-240), 'last': iso(-150), 'type': 'A359'}, {'day': today, 'callsign': 'JAL313', 'dep': 'HND', 'arr': None, 'first': iso(-30), 'last': iso(-2), 'type': 'A359'}]
PRED = {'reg': 'JA01XJ', 'src': 'reg', 'known': {'callsign': 'JAL313', 'dep': 'HND', 'arr': 'FUK'}, 'next': [{'callsign': 'JAL320', 'dep': 'FUK', 'arr': 'HND', 'time': '15:30', 'seen': 5, 'share': 0.82}]}
TREND = {'iata': 'HND', 'days': 30, 'wind': {'N': {'north': 900, 'south': 20}, 'S': {'south': 700, 'city': 80}, 'calm': {'north': 40, 'south': 60}}, 'hours': {str(h): (h % 7) + 3 for h in range(6, 24)}, 'arr_days': 20, 'ga': {'n': 4, 'windy': 3, 'low': 1}}
LEARN = {'iata': 'HND', 'n': 200, 'rows': [{'dir': 'arr', 'rwy': '34L', 'sec': 0, 'n': 60}, {'dir': 'arr', 'rwy': '34R', 'sec': 0, 'n': 40}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.view.ops', 'photo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        calls = []
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}'); calls.append((name, body))
            out = {'reg_history': HIST, 'predict_rotation': {'reg': body.get('p_reg'), 'known': None, 'next': []}, 'predict_rotation_reg': PRED, 'airport_trend': TREND, 'rwy_learned': LEARN,
                   'airport_day': {'iata': 'HND', 'day': body.get('p_day'), 'daily': {'flights': 1200, 'modes': {'south': 900, 'north': 100}, 'max_wind': 18}, 'rwy': {'arr:22': 300, 'dep:16R': 280}, 'ga': 1},
                   'airport_tracks': [], 'airport_board': {'iata': 'HND', 'now': iso(0), 'hours': [], 'next_arr': [], 'next_dep': []}}.get(name, [])
            await r.fulfill(status=200, body=json.dumps(out), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); await pg.clock.set_fixed_time(now); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate("window.__livSeen = [{ reg:Object.keys(LIVERY_NAMES)[0], iata:'HND', at:new Date().toISOString() }]")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        # 特別塗装機の図鑑
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(500)
        await pg.click('#v-book [data-seg="liv"]'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#bookLiv'); n = await pg.evaluate('Object.keys(LIVERY_NAMES).length'); print('LIV', t[:200].replace('\n', ' | '))
        check('特別塗装機の図鑑（全機と見た1機）:', n >= 30 and f'1 / {n}' in t and await pg.locator('#bookLiv .lvcard.got').count() == 1 and '見た・' in t)
        await pg.click('#bookLiv [data-livtab="seen"]'); await pg.wait_for_timeout(200)
        check('見ただけに絞る:', await pg.locator('#bookLiv .lvcard').count() == 1)
        await pg.screenshot(path=os.path.join(WORK, 't68_liv.png'), full_page=True)
        # 機体の1日
        await pg.locator('#bookLiv .lvcard').first.click(); await pg.wait_for_timeout(800)
        tp = await pg.inner_text('#dPlane'); print('PLANE', tp[:300].replace('\n', ' | '))
        check('機体の1日（飛んだ便・飛行中・予想）:', await pg.evaluate("$('dPlane').open") and 'JL501' in tp and 'いま飛行中' in tp and 'JL320' in tp and '82%' in tp)
        await pg.fill('#plReg', 'ja219a'); await pg.press('#plReg', 'Enter'); await pg.wait_for_timeout(500)
        check('登録記号で探す:', any(n == 'reg_history' and b.get('p_reg') == 'JA219A' for n, b in calls))
        await pg.screenshot(path=os.path.join(WORK, 't68_plane.png'))
        await pg.click('#dPlane [data-close]')
        # あの日の空
        await pg.evaluate("goTab('stats')"); await pg.wait_for_timeout(500)
        await pg.click('[data-thatday]'); await pg.wait_for_timeout(1200)
        td = await pg.inner_text('#dThatDay'); print('THATDAY', td[:300].replace('\n', ' | '))
        check('あの日の空（その日の運用・滑走路）:', await pg.evaluate("$('dThatDay').open") and '22' in td and '16R' in td and '1200' in td and '18kt' in td)
        await pg.click('#dThatDay [data-tdtab="ago"]'); await pg.wait_for_timeout(800)
        check('1年前の今日（記録の前の日）:', '10月18日より前' in await pg.inner_text('#dThatDay'))
        await pg.screenshot(path=os.path.join(WORK, 't68_thatday.png'))
        await pg.click('#dThatDay [data-close]')
        # 空港の傾向
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        await pg.click('[data-vw="ops:photo"]'); await pg.wait_for_timeout(600)
        await pg.click('#opsPhoto [data-trend]'); await pg.wait_for_timeout(900)
        tt = await pg.inner_text('#dTrend'); print('TREND', tt[:400].replace('\n', ' | '))
        check('空港の傾向（風ごと・時間帯・ゴーアラウンド）:', '北の風' in tt and '南の風' in tt and '時間帯ごとの着陸' in tt and '4機' in tt and '20日分' in tt)
        await pg.screenshot(path=os.path.join(WORK, 't68_trend.png'), full_page=True)
        print('errors', errs)
        await b.close()
asyncio.run(main())
if fails: print('NG', fails); sys.exit(1)
