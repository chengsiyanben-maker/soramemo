import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ゴーアラウンドの知らせ：運用タブの今日のゴーアラウンド、1件のくわしく（高さの動き・そのときの天気）、着陸の天気（起きやすさ）、知らせの設定、通知から開く
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
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.view.ops','board')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        EV = {'id': 12, 'iata': 'HND', 'at': iso(-10), 'callsign': 'JAL123', 'flight': 'JL123', 'type': 'B738', 'reg': 'JA301J', 'low_ft': 450, 'low_km': 2.1, 'rwy': '34L', 'again_at': iso(-3),
              'wx': {'time': iso(-30), 'wdir': 250, 'wspd': 25, 'wgst': 38, 'vis_m': 9999, 'raw': 'RJTT 210530Z 25025G38KT 9999 FEW025 BKN030 18/10 Q1002'},
              'pts': [[1, 2400, 9], [31, 1400, 6], [61, 600, 3], [91, 450, 2.1], [121, 1200, 1]]}
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            data = BOARD if name == 'airport_board' else [EV] if name == 'ga_recent' else EV if name == 'ga_event' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/airport-foreign**', lambda r: r.fulfill(status=200, body=json.dumps({'planes': []}), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        NOW = {'weather': {'time': iso(-5), 'wdir': 250, 'wspd': 25, 'wgst': 38, 'vis_m': 10000, 'sky': '晴れ', 'ceil_ft': 3000, 'ts': False, 'vcts': False, 'ws': False},
               'taf': {'periods': [{'from': int(now.timestamp()), 'to': int(now.timestamp()) + 7200, 'kind': 'base', 'wdir': 250, 'wspd': 25, 'wgst': 38, 'vis_m': 10000, 'ceil_ft': None, 'sky': '晴れ'},
                                   {'from': int(now.timestamp()) + 7200, 'to': int(now.timestamp()) + 86400, 'kind': 'BECMG', 'wdir': 340, 'wspd': 8, 'wgst': None, 'vis_m': 10000, 'ceil_ft': None, 'sky': '晴れ'}]}, 'flights': None}
        await c.route('https://fake.supabase.co/functions/v1/airport-now**', lambda r: r.fulfill(status=200, body=json.dumps(NOW), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(2000)
        t = await pg.inner_text('#opsGa'); print('BOX', t.replace('\n', ' | '))
        check('運用タブに今日のゴーアラウンド:', 'JL123' in t and '450ft' in t and '24時間で1機' in t)
        await pg.click('#opsGa [data-ga-ev="12"]'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#dGa'); print('EV', t[:300].replace('\n', ' | '))
        check('くわしく：便・いちばん低く・もう一度進入・そのときの天気:', 'JL123' in t and '450ft' in t and 'もう一度進入' in t and '突風 38kt' in t and '雲底 3,000ft' in t)
        check('高さの図:', await pg.locator('#dGa svg.gachart path').count() == 2)
        await pg.screenshot(path=os.path.join(WORK, 't65_ev.png'), full_page=True)
        await pg.evaluate("$('dGa').close()")
        await pg.click('#opsGa [data-ga-open="wx"]'); await pg.wait_for_timeout(800)
        t = await pg.inner_text('#dGa'); print('WX', t[:400].replace('\n', ' | '))
        check('着陸の天気：突風で起きやすい・横風の数字・この先:', '起きやすい' in t and '突風 38kt' in t and '横風' in t and await pg.locator('#dGa .gafc span').count() == 2)
        await pg.evaluate("$('dGa').close()")
        # 知らせの設定（端末の申し込みは置き換えて、送る中身だけ確かめる）
        await pg.evaluate("window.pushOK = () => true; syncPush = async (a, f, s, spot, ga) => { window.__ga = ga; localStorage.setItem('soramemo.pushGa', JSON.stringify(ga)); return true; }")
        await pg.click('#opsGa [data-ga-open="set"]'); await pg.wait_for_timeout(300)
        await pg.click('[data-ga-ap="NRT"]'); await pg.click('[data-ga-kind="ts"]'); await pg.click('[data-sg-set="gaquiet"][data-v="1"]'); await pg.click('[data-ga-save]'); await pg.wait_for_timeout(300)
        ga = await pg.evaluate('window.__ga'); print('GA', ga)
        check('設定の中身:', ga and ga['airports'] == ['HND', 'NRT'] and 'ts' in ga['kinds'] and 'plane' in ga['kinds'] and ga['quiet'] is True and ga['gap'] == 3)
        check('閉じて知らせを出す:', not await pg.evaluate("$('dGa').open") and '知らせます' in await pg.inner_text('#opsMsg'))
        # 通知から開く（#ops-HND/ga/12）
        await pg.evaluate("gaFromHash('/ga/12')"); await pg.wait_for_timeout(900)
        check('通知のリンクから1件が開く:', await pg.evaluate("$('dGa').open") and 'JL123' in await pg.inner_text('#dGa'))
        print('errors', errs, 'fails', fails); await b.close()
asyncio.run(main())
