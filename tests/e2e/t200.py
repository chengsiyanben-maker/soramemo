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
asyncio.run(main())
