import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 管制の交信：日本語の一覧・管制ごとの絞り込み・誘導路の地図・受信の協力（同意・PC用の合言葉）
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': [{'h': h, 'flights': 40, 'late': 0, 'cancel': 0, 'ref': 1} for h in range(24)], 'next_arr': [], 'next_dep': []}
MSGS = [{'id': 2, 'at': iso(-1), 'ch': 'gnd', 'freq': '121.70', 'flight': 'NH106', 'callsign': 'ANA106', 'ja': '16R滑走路へ。誘導路 C・H を通る。22滑走路の手前で待機。', 'tags': ['地上走行', '手前で待機'], 'heard': 2,
         'items': [{'k': 'taxi', 'to': '16R', 'via': ['C', 'H']}, {'k': 'hold', 'at': 'RWY 22'}]},
        {'id': 1, 'at': iso(-2), 'ch': 'twr', 'freq': '118.10', 'flight': 'BC511', 'callsign': 'SKY511', 'ja': 'ゴーアラウンド（着陸をやめて上昇）。', 'tags': ['ゴーアラウンド'], 'heard': 1, 'items': [{'k': 'goaround'}]}]
COV = {'ch': [{'iata': 'HND', 'ch': 'twr', 'live': 2, 'today': 40}, {'iata': 'HND', 'ch': 'gnd', 'live': 1, 'today': 30}, {'iata': 'HND', 'ch': 'app', 'live': 0, 'today': 0}, {'iata': 'HND', 'ch': 'dep', 'live': 0, 'today': 0},
       {'iata': 'NRT', 'ch': 'twr', 'live': 0, 'today': 0}, {'iata': 'NRT', 'ch': 'gnd', 'live': 0, 'today': 0}, {'iata': 'NRT', 'ch': 'app', 'live': 0, 'today': 0}, {'iata': 'NRT', 'ch': 'dep', 'live': 0, 'today': 0}], 'areas': {'ota': 2}}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.view.ops', 'photo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        seen = []
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}'); seen.append((name, body))
            out = BOARD if name == 'airport_board' else ([m for m in MSGS if not body.get('p_ch') or m['ch'] == body['p_ch']] if name == 'atc_recent' else COV if name == 'atc_coverage' else [])
            await r.fulfill(status=200, body=json.dumps(out), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1500)
        await pg.click('[data-vw="ops:photo"]'); await pg.wait_for_timeout(800)
        await pg.click('#opsPhoto [data-atcfeed]'); await pg.wait_for_timeout(800)
        t = await pg.inner_text('#dAtcFeed'); print('FEED', t[:400].replace('\n', ' | '))
        check('交信の一覧（日本語）:', 'NH106' in t and '誘導路 C・H' in t and 'ゴーアラウンド' in t and '受信中 3人' in t and '2人が受信' in t)
        check('英語は出さない:', 'cleared' not in t.lower())
        await pg.screenshot(path=os.path.join(WORK, 't66_feed.png'))
        await pg.click('#dAtcFeed [data-atcft="twr"]'); await pg.wait_for_timeout(400)
        t2 = await pg.inner_text('#dAtcFeed'); check('タワーだけ:', 'BC511' in t2 and 'NH106' not in t2 and any(n == 'atc_recent' and b.get('p_ch') == 'twr' for n, b in seen))
        await pg.click('#dAtcFeed [data-atcft="all"]'); await pg.wait_for_timeout(400)
        await pg.click('#dAtcFeed [data-atctaxi]'); await pg.wait_for_timeout(500)
        tx = await pg.inner_text('#dAtcTaxi'); print('TAXI', tx[:300].replace('\n', ' | '))
        check('誘導路の指示:', await pg.evaluate("$('dAtcTaxi').open") and '誘導路 C を通る' in tx and '22滑走路の手前で待機' in tx and '16R滑走路' in tx and 'OpenStreetMap' in tx)
        await pg.click('#dAtcTaxi [data-close]'); await pg.wait_for_timeout(100)
        await pg.click('#dAtcFeed [data-atcjoin]'); await pg.wait_for_timeout(500)
        tj = await pg.inner_text('#dAtcJoin'); print('JOIN', tj[:400].replace('\n', ' | '))
        check('足りない周波数と地域:', '受信中 2人' in tj and 'だれもいない' in tj and '大田区 2人' in tj)
        await pg.click('#dAtcJoin [data-atcway="pc"]'); await pg.wait_for_timeout(200)
        await pg.select_option('#atcArea', 'ota')
        await pg.click('#dAtcJoin [data-atcstart]'); await pg.wait_for_timeout(300)
        check('同意しないと始めない:', await pg.evaluate('window.__atcFeeder') is None)
        await pg.check('#atcOk'); await pg.click('#dAtcJoin [data-atcstart]'); await pg.wait_for_timeout(400)
        f = await pg.evaluate('window.__atcFeeder'); print('FEEDER', f)
        check('PC用の合言葉:', f and f['p_kind'] == 'pc' and f['p_area'] == 'ota' and f['p_consent'] is True and 'a' * 64 in await pg.inner_text('#dAtcJoin'))
        await pg.screenshot(path=os.path.join(WORK, 't66_join.png'), full_page=True)
        print('errors', errs)
        await b.close()
asyncio.run(main())
if fails: print('NG', fails); sys.exit(1)
