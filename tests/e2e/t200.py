<<<<<<< HEAD
# 送り直しても二重にならない（11/26 checkin/idem-cid・データ担当の data/idem・移行200 の画面の側）
#   1 印を押すたびに ID（cid・UUID）を1つ作って関数 checkin に送る。押すたびに別の ID
#   2 記録できたのに返事だけ届かない → 保留に同じ ID で積む → 送り直すと「もう記録済み」（again）が返り、印は1つのまま・保留は空・確定の札
#   3 前の版で積んだ保留（ID なし）にも、送る前に ID を付けて保存する（次の送り直しから同じ ID）
#   4 前の関数（cid を無視する）でも今までどおり押せる
#   5 記録帳・国際線の「足す」：返事が届かず押し直しても1行（同じ ID の upsert）。列がまだないサーバーでは ID なしの insert で保存できる
import os, sys, re, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
HND = (35.5494, 139.7798); CTS = (42.7752, 141.6923); ITM = (34.7855, 135.4382)
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
GEO = """window.__geo = {delay:100, acc:20, lat:35.5494, lon:139.7798};
(() => { const W = new Map(); let n = 0;
  const pos = () => ({coords:{latitude:__geo.lat, longitude:__geo.lon, accuracy:__geo.acc}, timestamp:Date.now()});
  const g = { watchPosition(ok){ const id = ++n; W.set(id, setTimeout(() => { if(W.has(id)) ok(pos()); }, __geo.delay)); return id; },
    clearWatch(id){ clearTimeout(W.get(id)); W.delete(id); }, getCurrentPosition(ok){ setTimeout(() => ok(pos()), __geo.delay); } };
  Object.defineProperty(navigator, 'geolocation', {configurable:true, get(){ return g; }}); })();"""
fails = []
def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)
async def waitjs(pg, expr, timeout=15000):
    for _ in range(timeout // 100):
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(100)
    return False
async def page(p):
    b = await p.chromium.launch()
    c = await b.new_context(viewport={'width':390,'height':844}, permissions=['geolocation'])
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await waitjs(pg, 'S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); __fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); S.checkins.forEach(x => x.t -= 3*36e5)")
    return b, pg, errs
async def at(pg, ll):
    await pg.evaluate(f'__geo.lat = {ll[0]}; __geo.lon = {ll[1]}; HOME_POS = null; POS_LAST = null; GEO_WARM = null')
async def press(pg, wait=1500):
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true}))")
    await pg.wait_for_timeout(wait)
async def older(pg):   # 次の印が「間を置いて」「同じ空港」にならないよう、記録を3時間前へ
    await pg.evaluate("__fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); S.checkins.forEach(x => x.t -= 3*36e5)")
QL = "JSON.parse(localStorage.getItem('soramemo.queue.u1') || '[]')"
async def main():
    allerrs = []
    async with async_playwright() as p:
        # 1・2 印の ID と、返事だけ届かないときの送り直し
        b, pg, errs = await page(p)
        await pg.evaluate('window.__calls = []'); await at(pg, CTS); await press(pg)
        r = await pg.evaluate("({calls: __calls.map(x => x.cid), db: __fake.db.checkins.length, last: __fake.db.checkins[__fake.db.checkins.length-1].client_id})")
        ok(len(r['calls']) == 1 and bool(UUID.match(r['calls'][0] or '')) and r['last'] == r['calls'][0], f'1 押すと ID（UUID）を送る（{r["calls"]}）')
        await older(pg); await pg.evaluate('window.__calls = []'); await at(pg, HND); await press(pg)
        c2 = await pg.evaluate('__calls.map(x => x.cid)')
        ok(len(c2) == 1 and c2[0] and c2[0] not in r['calls'], f'1 押すたびに別の ID（{c2}）')
        # 2 記録できたのに返事だけ届かない
        await older(pg); n0 = await pg.evaluate('__fake.db.checkins.length')
        await pg.evaluate('window.__calls = []; window.__lostReply = 1'); await at(pg, ITM); await press(pg, 2000)
        q = await pg.evaluate(QL); sent = await pg.evaluate('__calls.map(x => x.cid)')
        ok(len(q) == 1 and q[0].get('cid') == sent[0], f'2 返事が届かない → 同じ ID で保留（保留 {len(q)}件・{q[0].get("cid") if q else None} / 送った {sent}）')
        ok(await pg.evaluate('__fake.db.checkins.length') == n0 + 1, '2 サーバーには1つ記録された（作り物）')
        await pg.evaluate("window.__toastLog = []; const t0 = toast; toast = (m, ...a) => { __toastLog.push(m); return t0(m, ...a); }")
        await pg.evaluate('flushQueue()'); await waitjs(pg, QL + '.length === 0', 8000); await pg.wait_for_timeout(800)
        r = await pg.evaluate("({db: __fake.db.checkins.length, calls: __calls.map(x => x.cid), q: " + QL + ".length, toast: __toastLog, itm: S.checkins.filter(c => c.a === __fake.db.checkins[__fake.db.checkins.length-1].airport_id && Date.now() - c.t < 36e5).length, msg: $('msg').textContent})")
        ok(r['q'] == 0 and len(r['calls']) == 2 and r['calls'][1] == r['calls'][0], f'2 送り直しは同じ ID（{r["calls"]}）・保留は空')
        ok(r['db'] == n0 + 1, f'2 送り直しても印は1つ（{r["db"] - n0}）')
        ok(r['itm'] == 1, f'2 画面の記録も1つ（{r["itm"]}）')
        ok(any('確定' in str(t) for t in r['toast']) and '送れませんでした' not in r['msg'], f'2 「もう記録済み」は成功として扱う（札 {r["toast"]}・{r["msg"][:40]}）')
        # 3 前の版で積んだ保留（ID なし）にも ID を付ける
        await pg.evaluate("localStorage.setItem('soramemo.queue.u1', JSON.stringify([{lat:35.5494, lon:139.7798, acc:20, ts:Date.now()-6e5, a:5, term:null}])); window.__offline = true")
        await pg.evaluate('flushQueue(true)'); await pg.wait_for_timeout(500)
        q = await pg.evaluate(QL)
        ok(len(q) == 1 and bool(UUID.match(q[0].get('cid') or '')), f'3 前の版の保留にも ID を付けて残す（{q[0].get("cid") if q else None}）')
        cid3 = q[0].get('cid') if q else None
        await pg.evaluate('window.__offline = false; window.__calls = []'); await pg.evaluate('flushQueue(true)'); await waitjs(pg, QL + '.length === 0', 8000)
        ok(await pg.evaluate('__calls.map(x => x.cid)') == [cid3], '3 つながったら、その ID で送る')
        allerrs += errs; await b.close()
        # 4 前の関数（cid を無視する）でも押せる
        b, pg, errs = await page(p)
        await pg.evaluate('window.__noIdem = true'); n0 = await pg.evaluate('__fake.db.checkins.length'); await at(pg, CTS); await press(pg)
        ok(await pg.evaluate('__fake.db.checkins.length') == n0 + 1 and await pg.evaluate("$('dStamp').open"), '4 前の関数でも印を押せる')
        allerrs += errs; await b.close()
        # 5 記録帳・国際線
        b, pg, errs = await page(p)
        await pg.evaluate("$('mFrom').value = '5'; $('mTo').value = '6'; $('mDate').value = '2025-05-03'")
        ok(await pg.evaluate("$('mFrom').value === '5' && $('mTo').value === '6'"), '5 記録帳の欄に入れられる（準備）')
        n0 = await pg.evaluate('__fake.db.manual_flights.length')
        await pg.evaluate('window.__upLost = 1'); await pg.evaluate("$('mAdd').onclick()"); await pg.wait_for_timeout(600)
        ok('保存できませんでした' in await pg.evaluate("$('mMsg').textContent"), '5 返事が届かないと「保存できませんでした」')
        await pg.evaluate("$('mAdd').onclick()"); await pg.wait_for_timeout(800)
        r = await pg.evaluate(f"({{n: __fake.db.manual_flights.length - {n0}, cid: __fake.db.manual_flights.slice(-1)[0].client_id, msg: $('mMsg').textContent}})")
        ok(r['n'] == 1 and bool(UUID.match(r['cid'] or '')) and '追加しました' in r['msg'], f'5 押し直しても記録帳は1行（{r["n"]}行・{r["msg"][:30]}）')
        await pg.evaluate("$('mAdd').onclick()"); await pg.wait_for_timeout(800)
        ok(await pg.evaluate(f'__fake.db.manual_flights.length - {n0}') == 2, '5 保存できたあとにもう一度足すのは別の記録（同じ日の往復など）')
        # 国際線
        i0 = await pg.evaluate('(__fake.db.intl_flights = __fake.db.intl_flights || []).length')
        g = "{d:'2025-06-01', dep:'HND', arr:'LAX', no:'JL62', km:8800}"
        await pg.evaluate('window.__upLost = 1'); e1 = await pg.evaluate(f'addIntl({g})'); e2 = await pg.evaluate(f'addIntl({g})')
        ok(e1 and e2 is None and await pg.evaluate(f'__fake.db.intl_flights.length - {i0}') == 1, f'5 国際線も押し直して1行（{e1} → {e2}）')
        # 列がまだないサーバー（移行200 の前）
        await pg.evaluate("window.__noCidCol = true; $('mDate').value = '2025-05-04'"); await pg.evaluate("$('mAdd').onclick()"); await pg.wait_for_timeout(800)
        r = await pg.evaluate(f"({{n: __fake.db.manual_flights.length - {n0}, row: __fake.db.manual_flights.slice(-1)[0], msg: $('mMsg').textContent}})")
        ok(r['n'] == 3 and 'client_id' not in r['row'] and '追加しました' in r['msg'], f'5 移行200 の前のサーバーでも保存できる（ID なしの insert・{r["msg"][:30]}）')
        allerrs += errs; await b.close()
    allerrs = [e for e in allerrs if 'ResizeObserver' not in e]
    ok(not allerrs, f'ページのエラーなし（{allerrs[:3]}）')
    print('\n' + ('全部成功' if not fails else f'失敗 {len(fails)}件'))
    sys.exit(1 if fails else 0)
=======
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用予想の小さな足し（11/26 PM の指示・Gemini 22往復目の考え方を機体の運用予想に当てはめたもの。docs/pm/yosoku-gemini-1126.md）
#   1 確からしさの回数：数字を太く。データ担当が seen_of（分母・重みなし）を返したら「12回中11回」、返さないうちは「11回見た」。時刻表の予想は回数を出さない
#   3・8 根拠の1行：どの便から（記録の最後の時刻）・前の何日の記録から（learn_hi は42日、ほかは60日）・先の便ほど外れやすい
#   4 外れたとき：いま飛んでいる便が予想の1便目と違う（同じころ・前後90分）ときは、隠さず「当時の予想」と並べ、この先は外れやすいと書く
#   どれも「予想です。保証しません」は今のまま。偽のサーバー（fake_sb.js）を使い、本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc)
JST = timezone(timedelta(hours=9))
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat()
ms = lambda h, m: int(at(h, m).timestamp() * 1000)
today = base.strftime('%Y-%m-%d')
V2 = {'reg': 'JA339J', 'src': 'reg', 'method': 'learn_hi', 'estimate': True, 'type': 'B738',
      'known': {'callsign': 'JAL148', 'dep': 'AOJ', 'arr': 'HND', 'first': iso(18, 35), 'last': iso(19, 36)}, 'next': [
    {'callsign': 'JAL599', 'dep': 'HND', 'arr': 'CTS', 'time': '20:30', 'seen': 12, 'share': 0.92, 'src': 'learn'},
    {'callsign': 'JAL502', 'dep': 'CTS', 'arr': 'HND', 'time': '07:30', 'seen': 5, 'share': 0.62, 'src': 'learn'}]}
HIST = [{'day': today, 'callsign': cs, 'dep': d, 'arr': a, 'first': iso(*f), 'last': iso(*l), 'type': 'B738'} for cs, d, a, f, l in [
    ('JAL147', 'HND', 'AOJ', (16, 15), (17, 30)), ('JAL148', 'AOJ', 'HND', (18, 35), (19, 36)), ('JAL517', 'HND', 'CTS', (20, 40), (20, 49))]]
fails = []
def check(label, ok, detail=''):
    print(label, ok, detail if not ok else '')
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for H in (844, 667):
            c = await b.new_context(viewport={'width': 390, 'height': H}, timezone_id='Asia/Tokyo')
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
            await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
            mode = {'v2': V2, 'hist': HIST}
            async def rpc(r):
                name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
                out = {'reg_history': mode['hist'], 'predict_rotation': {'reg': body.get('p_reg'), 'known': None, 'next': []},
                       'predict_rotation_v2': mode['v2'], 'predict_rotation_reg': {'reg': body.get('p_reg'), 'known': None, 'next': [], 'src': 'reg'},
                       'livery_board': []}.get(name, [])
                await r.fulfill(status=200, body=json.dumps(out), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
            await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
            await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}))
            await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
            pg = await c.new_page(); await pg.clock.set_fixed_time(at(19, 50)); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
            await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
            tag = f'[{H}]'

            # 1 回数：数字は太く、分母がないうちは「12回見た」、seen_of があれば「14回中12回」
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", V2)
            check(tag + ' 回数の数字は太い:', '<b>12</b>回見た' in h, h[:300])
            v = json.loads(json.dumps(V2)); v['next'][0]['seen_of'] = 14; v['next'][1]['seen_of'] = 3
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", v)
            check(tag + ' 分母があれば「14回中12回」:', '14回中<b>12</b>回' in h and 'aria-label="確からしさ 高い・14回中12回"' in h)
            check(tag + ' 分母が回数より小さいときは使わない:', '<b>5</b>回見た' in h and '3回中' not in h)
            tt = {'reg': 'JA1', 'src': 'odpt', 'known': {'flight': 'JL148', 'dep': 'AOJ', 'arr': 'HND', 'std': iso(18, 35), 'sta': iso(19, 36), 'phase': 'landed'},
                  'next': [{'flight': 'JL599', 'dep': 'HND', 'arr': 'CTS', 'std': iso(20, 30), 'seen': 20, 'of': 22, 'share': 0.9, 'seen_of': 30}]}
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", tt)
            check(tag + ' 時刻表の予想は回数を出さない:', '回見た' not in h and '回中' not in h and '高い' in h)

            # 3・8 根拠の1行
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", V2)
            check(tag + ' 根拠は便と時刻と42日:', 'class="rbasis"' in h and 'JL148（19:36 着）から、前の42日の記録で続いた便をたどっています' in h)
            check(tag + ' 先の便ほど外れやすい:', '先の便ほど外れやすくなります' in h)
            check(tag + ' 保証しないは今のまま:', '予想です。保証しません' in h)
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", tt)
            check(tag + ' 時刻表の予想は60日:', '前の60日の記録' in h)
            v = json.loads(json.dumps(V2)); v['next'] = [{'callsign': 'JAL599', 'dep': 'HND', 'arr': 'CTS', 'time': '20:30', 'seen': None, 'share': None, 'src': 'livery'}]
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", v)
            check(tag + ' 運航情報の便だけなら航空会社の予定から:', '運航情報の便は、航空会社の予定から' in h and '日の記録' not in h)
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", dict(V2, next=[]))
            check(tag + ' 予想がないときは根拠を出さない:', 'rbasis' not in h)

            # 4 外れたとき：予想は 20:30 の JL599、いま 20:40 発の JL517 で飛んでいる
            await pg.clock.set_fixed_time(at(20, 50))
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL517', dep:'HND', arr:'CTS', t:%d } }, {})" % ms(20, 40), V2)
            check(tag + ' いま実際は・当時の予想と並べる:', 'class="skip miss"' in h and 'いま実際は <b>JL517</b>' in h and '当時の予想：20:30 JL599</small>' in h)
            check(tag + ' 機体の入れ替えなどで変わる:', '機体の入れ替えなどで変わることがあります' in h)
            check(tag + ' この先は外れやすいと書く:', 'いま飛んでいる JL517 は予想と違いました' in h and 'この先は外れやすくなっています' in h)
            check(tag + ' いま飛んでいるので…の行は重ねない:', 'いま飛んでいるので予想に出しません' not in h)
            check(tag + ' 予想の便そのものは出さない（過ぎた）:', h.count('JL599') == 1 and 'JL502' in h)
            # 時刻が離れている（前後90分より外）・時刻が分からないときは外れと言わない
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL517', dep:'HND', arr:'CTS', t:%d } }, {})" % ms(22, 30), V2)
            check(tag + ' 時刻が離れていれば外れと言わない:', 'miss' not in h and 'いま飛んでいるので予想に出しません' in h)
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL517', dep:'HND', arr:'CTS' } }, {})", V2)
            check(tag + ' 出発の時刻が分からなければ外れと言わない:', 'miss' not in h)
            # 当たっているときは今までどおり
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL599', dep:'HND', arr:'CTS', t:%d } }, {})" % ms(20, 32), V2)
            check(tag + ' 当たっているときは外れの行なし:', 'miss' not in h and 'いま飛んでいるので予想に出しません' in h)

            # 機体の1日：記録（reg_history）で JL517 が飛んでいる → 外れの行・根拠・この先は外れやすい
            await pg.evaluate("openPlane('JA339J')"); await pg.wait_for_timeout(900)
            t = (await pg.inner_text('#dPlane')).replace('\n', ' ')
            check(tag + ' 機体の1日に外れの行:', await pg.locator('#dPlane li.skip.miss').count() == 1 and '当時の予想：20:30 JL599' in t, t[:400])
            check(tag + ' 機体の1日に根拠:', '根拠' in t and 'から、前の42日の記録で続いた便をたどっています' in t)
            box = await pg.locator('#dPlane li.p').first.bounding_box()
            check(tag + ' 予想の1便目が画面の中:', box is not None and box['y'] + box['height'] <= H, box)
            await pg.screenshot(path=os.path.join(WORK, f't200_plane_miss_{H}.png'))
            # シートの説明
            await pg.click('#dPlane [data-rot-conf]'); await pg.wait_for_timeout(150)
            s = await pg.inner_text('#dRotConf')
            check(tag + ' シートに根拠と外れたとき:', '根拠と外れたとき' in s and '当時の予想' in s and '先の便ほど外れやすくなります' in s)
            await pg.click('#dRotConf .btn1'); await pg.evaluate("$('dPlane').close()")
            # 夜の画面でも読める（色は変数）
            await pg.evaluate("document.documentElement.dataset.night = 'on'; openPlane('JA339J')"); await pg.wait_for_timeout(900)
            col = await pg.evaluate("getComputedStyle(document.querySelector('#dPlane .rbasis')).color")
            check(tag + ' 夜は根拠の字が明るい:', col in ('rgb(167, 176, 188)',), col)
            if H == 844: await pg.screenshot(path=os.path.join(WORK, 't200_plane_night.png'))
            await c.close()
            check(tag + ' ページのエラーなし:', not errs, errs)
        await b.close()
    print('errors', fails)
>>>>>>> origin/yosoku/gemini-small
asyncio.run(main())
