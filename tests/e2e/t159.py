import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 改善担当の見回り（11/21・kaizen/sweep-1121）の直し（チェックイン担当・checkin/sweep-1121）
#   1 運用の一覧の「遅れ」：カードの数と専用ページの大きな数が同じ。カードが1以上ならページに1行以上。0なら「いま遅れ・欠航の便はありません」の1枚。
#     便ごとのお知らせはログインした人だけなので、ログインしていないときは「ログインすると見られます」の1行
#   3 ホームの上の段の「マイページ」は1行（390・375）
#   4 地図カード：機体の位置が届くまでは「0機」でなく「—」。前に開いたときの数があれば「約○分前」。地図の専用ページの数は「この範囲に ○機」の1つだけ
#   5 特別塗装機のカードから開いたページで、いま飛んでいる特別塗装機の欄は畳まない
#   8 空港の3D：全体の視点は前（約24.6km 先）より寄せて約12km（t142 で名札と模型が見えるかも確かめる）
#   9 押せる所：運用の地図の ＋− と空の道すじの ◀ ▶・日を選ぶは 44px
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, math, shutil
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-sweep-1121')); os.makedirs(SHOTS, exist_ok=True)
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat(); NOW = at(15, 0)
LATE = [0,0,0,0,0,0,1,2,3,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0]
def board(late, cancel=None):
    cancel = cancel or [0] * 24
    return {'iata': 'HND', 'next_arr': [{'flight': 'JL110', 'other': 'ITM', 'sched': iso(15, 18), 't': iso(15, 18), 'est': None, 'actual': None, 'aircraft': 'B767'}], 'next_dep': [],
            'hours': [{'h': h, 'flights': 10, 'late': late[h], 'cancel': cancel[h]} for h in range(24)]}
SPECIAL = [{'reg': 'JA01XJ', 'name': 'A350 1号機', 'airline': 'JAL', 'callsign': 'JAL5', 'kind': 'livery', 'lat': 34.0, 'lon': 135.0, 'alt_ft': 30000, 'iata': None, 'phase': None}]
PLANES = [{'id': 't%d' % i, 'callsign': 'TST%d' % i, 'lat': 35.515 + i * .006, 'lon': 139.80, 'alt_ft': 2000, 'kt': 150, 'hdg': 340, 'fpm': -700, 'phase': 'arr', 'dist_km': 7, 'type': 'B738', 'reg': 'JA%03dA' % i} for i in range(3)]
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, w=390, h=844, login=True, bd=None, traffic_delay=0, extra=''):
    c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', has_touch=True)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    hold = {'v': traffic_delay}
    async def hd(r):
        u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
        if name == 'airport-traffic' and hold['v']: await asyncio.sleep(hold['v'])
        body = {'airport_board': bd or board(LATE), 'special_now': SPECIAL, 'airport-traffic': {'iata': 'HND', 'at': NOW.isoformat(), 'source': 'adsb.lol', 'planes': PLANES},
                'metar': {'id': 'RJTT', 'time': NOW.isoformat(), 'raw': 'TEST', 'wdir': 340, 'wspd': 7, 'wgst': None, 'vis_m': 10000, 'vis_plus': True},
                'push-subscribe': {'key': None}}.get(name, {} if '/functions/' in u else [])
        try: await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        except Exception: pass
    await c.route('https://fake.supabase.co/rest/**', hd); await c.route('https://fake.supabase.co/functions/**', hd)
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
                            "localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND');" + extra)
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    if login: await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return c, pg, errs
async def open_ops(pg, wait=2500):
    await pg.evaluate("OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(wait)
async def late_card(pg):
    return await pg.evaluate("(document.querySelector('[data-ohub=\"late\"] .ohv b') || {}).textContent || ''")
async def main():
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs_all = []
        # ---- 1 遅れ：ログインした人
        c, pg, errs = await page(b); await open_ops(pg)
        card = await late_card(pg)
        check('1 カードは今日の遅れ・欠航の合計（8便）', card == '8', card)
        await pg.evaluate("document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ page: $('v-ops').dataset.page, big: (document.querySelector('#opsLate .ltbig b') || {}).textContent, rows: document.querySelectorAll('#opsLate .lthrs li').length, txt: $('opsLate').innerText, h: $('opsLate').getBoundingClientRect().height })")
        check('1 専用ページの大きな数はカードと同じ', r['page'] == 'late' and r['big'] == card, r)
        check('1 カードが1以上なら、ページに1行以上（時間ごとの内訳 5つ）', r['rows'] == 5 and r['h'] > 100, r['rows'])
        check('1 「6時台 1便」のように時間と便', '6時台 1便' in r['txt'].replace('\n', ' ') or '6時台 1 便' in r['txt'], r['txt'][:120])
        check('1 ログインした人には「ログインすると」は出さない', 'ログインすると' not in r['txt'])
        await pg.screenshot(path=os.path.join(SHOTS, '01_late_login_390.png'))
        await pg.evaluate("$('opsHubBack').click()"); await pg.wait_for_timeout(700)
        r = await pg.evaluate("$('opsLate').hidden || getComputedStyle($('opsLate')).display === 'none'")
        check('1 一覧に戻ると、遅れの頭は出さない', r)
        await pg.evaluate("document.querySelector('[data-ohub=\"board\"]').click()"); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("(() => { const e = $('opsLate'); const r = e.getBoundingClientRect(); return r.height; })()")
        check('1 案内板のページには遅れの頭を出さない', r == 0, r)
        errs_all += errs; await c.close()
        # ---- 1 遅れ：ログインしていない人
        c, pg, errs = await page(b, login=False); await open_ops(pg)
        card = await late_card(pg)
        await pg.evaluate("document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ big: (document.querySelector('#opsLate .ltbig b') || {}).textContent, txt: $('opsLate').innerText, alerts: $('opsAlerts').hidden })")
        check('1 ログインしていなくても白紙にならない（カードと同じ数）', r['big'] == card == '8', (card, r['big']))
        check('1 ログインしていない人には「便ごとのお知らせ…ログインすると見られます」', 'ログインすると見られます' in r['txt'], r['txt'][-120:])
        await pg.screenshot(path=os.path.join(SHOTS, '02_late_logout_390.png'))
        errs_all += errs; await c.close()
        # ---- 1 遅れ：0便
        c, pg, errs = await page(b, bd=board([0] * 24)); await open_ops(pg)
        card = await late_card(pg)
        await pg.evaluate("document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ none: (document.querySelector('#opsLate .ltnone') || {}).textContent, rows: document.querySelectorAll('#opsLate .lthrs li').length })")
        check('1 0便のときのカードは「0」', card == '0', card)
        check('1 0便のときは「いま遅れ・欠航の便はありません」の1枚', r['none'] == 'いま遅れ・欠航の便はありません' and r['rows'] == 0, r)
        await pg.screenshot(path=os.path.join(SHOTS, '03_late_none_390.png'))
        # 欠航も数える
        errs_all += errs; await c.close()
        c, pg, errs = await page(b, bd=board(LATE, [0] * 20 + [2, 0, 0, 0])); await open_ops(pg)
        card = await late_card(pg)
        await pg.evaluate("document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("$('opsLate').innerText")
        check('1 欠航も数える（カード10・「遅れ 8便・欠航 2便」）', card == '10' and '遅れ 8便・欠航 2便' in r, (card, r[:100]))
        errs_all += errs; await c.close()
        # ---- 3 ホームの「マイページ」は1行
        for w, h in ((390, 844), (375, 667)):
            c, pg, errs = await page(b, w, h)
            await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(900)
            r = await pg.evaluate("(() => { const b = $('openSettings').getBoundingClientRect(), s = $('mpLabel'); const lh = parseFloat(getComputedStyle(s).fontSize) * 1.8; return { h: Math.round(b.height), lab: Math.round(s.getBoundingClientRect().height), lh, right: Math.round(b.right), W: document.documentElement.clientWidth, txt: s.textContent }; })()")
            check(f'3 ホームの「マイページ」は1行（{w}）', r['txt'] == 'マイページ' and r['lab'] < r['lh'] and r['h'] >= 44 and r['right'] <= r['W'], r)
            r = await pg.evaluate("[...document.querySelectorAll('#modeSw button')].map(b => Math.round(b.getBoundingClientRect().height))")
            check(f'3 切り替えのピルは1行のまま（{w}）', all(x <= 40 for x in r), r)
            await pg.screenshot(path=os.path.join(SHOTS, f'04_home_top_{w}.png'), clip={'x': 0, 'y': 0, 'width': w, 'height': 130})
            errs_all += errs; await c.close()
        # ---- 4 地図カード：届くまで「—」
        c, pg, errs = await page(b, traffic_delay=4); await open_ops(pg, 1200)
        r = await pg.evaluate("document.querySelector('[data-ohub=\"map\"] .ohv').innerText")
        check('4 機体の位置が届くまでは「—」（「0機」と言い切らない）', r.strip() == '—', r)
        await pg.screenshot(path=os.path.join(SHOTS, '05_map_card_loading_390.png'))
        await pg.wait_for_timeout(4500)
        r = await pg.evaluate("document.querySelector('[data-ohub=\"map\"] .ohv').innerText.replace(/\\s/g, '')")
        check('4 届いたら数（3機）', r == '3機', r)
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300)
        await pg.evaluate("TRAFFIC_GOT = null; OPS_PLANES = []"); await pg.clock.set_fixed_time(at(15, 3))
        await pg.evaluate("opsHubRender()")
        r = await pg.evaluate("document.querySelector('[data-ohub=\"map\"] .ohv').innerText.replace(/\\s/g, '')")
        check('4 次に開いて届くまでは、前の数を「約○分前」と添えて出す', r == '3機・約3分前', r)
        await pg.clock.set_fixed_time(at(15, 20)); await pg.evaluate("opsHubRender()")
        r = await pg.evaluate("document.querySelector('[data-ohub=\"map\"] .ohv').innerText.trim()")
        check('4 10分より前の数は出さない（「—」）', r == '—', r)
        errs_all += errs; await c.close()
        c, pg, errs = await page(b); await open_ops(pg)
        await pg.evaluate("document.querySelector('[data-ohub=\"map\"]').click()"); await pg.wait_for_timeout(2000)
        r = await pg.evaluate("({ txt: $('trafficNote').innerText, n: ($('trafficNote').innerText.match(/\\d+機/g) || []) })")
        check('4 地図の専用ページの数は「この範囲に ○機」の1つだけ', r['n'] == ['3機'] and 'この範囲に' in r['txt'], r)
        r = await pg.evaluate("[...document.querySelectorAll('#opsMap .leaflet-control-zoom a')].map(a => { const r = a.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })")
        check('9 運用の地図の ＋− は 44px', len(r) == 2 and all(w >= 44 and h >= 44 for w, h in r), r)
        await pg.screenshot(path=os.path.join(SHOTS, '06_map_page_390.png'))
        await pg.evaluate("$('opsHubBack').click()"); await pg.wait_for_timeout(700)
        # ---- 5 特別塗装機
        n = await pg.evaluate("(document.querySelector('[data-ohub=\"special\"] .ohv b') || {}).textContent")
        await pg.evaluate("document.querySelector('[data-ohub=\"special\"]').click()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("[...document.querySelectorAll('#opsPSpecial details.spnow')].map(d => d.open)")
        check('5 特別塗装機のカード（1機）から開くと、いま飛んでいる特別塗装機の欄は開いている', n == '1' and r == [True], (n, r))
        await pg.screenshot(path=os.path.join(SHOTS, '07_special_390.png'))
        errs_all += errs; await c.close()
        # ---- 8 空港の3D の全体の視点
        c, pg, errs = await page(b)
        r = await pg.evaluate("""(() => { const pos = {}, at = {}; const cam = { position:{ set(x, y, z){ pos.x = x; pos.y = y; pos.z = z; } }, lookAt(x, y, z){ at.x = x; at.y = y; at.z = z; }, userData:{} };
          const keep = typeof A3 === 'undefined' ? undefined : A3; A3 = { THREE:{}, cam, yaw:0, view:'all' }; a3Camera([]); A3 = keep === undefined ? null : keep;
          return { d: Math.hypot(pos.x - at.x, pos.y - at.y, pos.z - at.z), y: pos.y }; })()""")
        check('8 全体の視点は約12km（前の約24.6km より寄せた）', 11500 < r['d'] < 13000 and r['y'] < 11000, r)
        errs_all += errs; await c.close()
        # ---- 9 空の道すじの ◀ ▶・日を選ぶ
        c, pg, errs = await page(b, extra="localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.view.ops','art');")
        await c.route('https://fake.supabase.co/rest/v1/rpc/airport_tracks', lambda r: r.fulfill(status=200, body=json.dumps([{'d': 1, 'h': 9, 'p': '_p~iF~ps|U_ulL'}]), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}))
        await open_ops(pg)
        r = await pg.evaluate("[...document.querySelectorAll('#opsArt .artnav button, #opsArt .artdate')].map(e => Math.round(e.getBoundingClientRect().height))")
        check('9 空の道すじの ◀ ▶ と日を選ぶは高さ44', len(r) == 3 and all(x >= 44 for x in r), r)
        errs_all += errs; await c.close()
        await b.close()
    check('JS のエラーなし', not errs_all, errs_all[:3])
    print('errors', fails)
asyncio.run(main())
