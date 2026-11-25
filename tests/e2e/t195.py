# 印を押すときに待たない（11/25 stamp-fast・本人「印を押す時、ロードが長くて不安になるし、画面が固まる」）
#   1 遅い電波（1回 2秒）でも、ハンコは返事を待たずに出る（仮の印）。返事のあとで本物の記録に入れ替わる
#     （速さ「0.5 秒以内・長い処理 100ms 未満」は t203 で別に測る。同時に流すと速さが揺れて、決まりの確かめまで落ちていたため・11/26 test-steady）
#   2 便ができるとき、印の画面の「乗った便を記録する」は返事までは押せず、返事のあとサーバーの便の番号で押せる
#   3 二重に押しても、サーバーに送るのは1回・印は1つ
#   4 サーバーに届かない → 今の保留に入り、「あとで送ります」の札（2秒で消える）
#   5 サーバーが断る → 先に出したハンコを取り消し、理由を出す（記録は増えない）
#   6 直近の位置（30秒以内・誤差50m以内・範囲の中）があれば位置を待たない。なければ「位置を確かめています」を出し、10秒で区切る。誤差300m以内なら3秒で確定
#   7 範囲の外は今までどおりサーバーの判定を待つ（ハンコは出さない）
#   8 動きを減らす設定では、札は動かない
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, shutil
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
sys.path.insert(0, HERE); from stamp_perf import GEO, WATCH
HND = (35.5494, 139.7798); CTS = (42.7752, 141.6923); OUT = (35.70, 139.70)
fails = []
def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)
async def page(p, reduced=False):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':390,'height':844}, permissions=['geolocation'], reduced_motion='reduce' if reduced else 'no-preference')
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await waitjs(pg, 'S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); HOME_POS = null; POS_LAST = null; GEO_WARM = null; homeLocStop()")
    return b, c, pg, errs
async def waitjs(pg, expr, timeout=20000):   # wait_for_function は CSP で止まることがあるので、evaluate を繰り返す
    for _ in range(timeout // 100):
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(100)
    return False
async def at(pg, ll, delay=200, acc=20):
    await pg.evaluate(f'__geo.lat = {ll[0]}; __geo.lon = {ll[1]}; __geo.delay = {delay}; __geo.acc = {acc}')
async def press(pg):
    await pg.evaluate(WATCH)
async def main():
    allerrs = []
    async with async_playwright() as p:
        # 1・2 遅い電波：ハンコはすぐ・返事のあとで入れ替わる・便のボタン
        b, c, pg, errs = await page(p)
        await pg.evaluate('window.__netDelay = 2000; window.__mkFlight = true')
        await at(pg, CTS); n0 = await pg.evaluate('__fake.db.checkins.length')
        await press(pg); await pg.wait_for_timeout(700)
        r = await pg.evaluate("({ stamp: __stampAt == null ? null : __stampAt - __t0, lt: Math.max(0, ...__lt.filter(([s]) => s >= __t0 - 5).map(x => x[1])), pend: S.checkins.filter(x => x.pending).length })")
        print('  1:', json.dumps(r))
        ok(r['stamp'] is not None and r['stamp'] < 2000, f"1 遅い電波（返事に2秒）でも、ハンコは返事を待たずに出る（{r['stamp'] and round(r['stamp'])}ms。速さは t203）")
        ok(r['pend'] == 1, '1 返事の前は仮の印が1つ')
        fb = await pg.evaluate("(() => { const b = document.querySelector('#dStamp [data-flight]'); return b ? {dis: b.disabled, txt: b.textContent, id: b.dataset.flight} : null; })()")
        ok(fb and fb['dis'] and '記録しています' in fb['txt'], f'2 返事の前は「乗った便を記録する」を押せない（{fb}）')
        await waitjs(pg, '!S.checkins.some(x => x.pending)'); await pg.wait_for_timeout(600)
        fb = await pg.evaluate("(() => { const b = document.querySelector('#dStamp [data-flight]'); return b ? {dis: b.disabled, txt: b.textContent, id: b.dataset.flight} : null; })()")
        ok(fb and not fb['dis'] and fb['id'].isdigit() and fb['txt'] == '乗った便を記録する', f'2 返事のあとはサーバーの便の番号で押せる（{fb}）')
        ok(await pg.evaluate('__fake.db.checkins.length') == n0 + 1, '1 サーバーに印が1つ増えた')
        ok(await pg.evaluate("S.flights.some(f => String(f.id) === '%s')" % (fb or {}).get('id', 'x')), '2 読み直した便が記録にある')
        await pg.click('#dStamp [data-flight]'); await pg.wait_for_timeout(300)
        ok(await pg.evaluate("$('dFlight') ? $('dFlight').open : true"), '2 押すと便の記録の画面が開く')
        allerrs += errs; await b.close()
        # 3 二重に押す
        b, c, pg, errs = await page(p)
        await pg.evaluate('window.__netDelay = 600; window.__calls = []'); await at(pg, HND, delay=400); n0 = await pg.evaluate('__fake.db.checkins.length')
        await pg.evaluate("for(let i = 0; i < 3; i++) document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true}))")
        await pg.wait_for_timeout(150); await pg.evaluate("document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true}))")
        await pg.wait_for_timeout(900); await pg.evaluate("document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true}))")
        await pg.wait_for_timeout(3500)
        calls = await pg.evaluate('window.__calls.length'); added = await pg.evaluate('__fake.db.checkins.length') - n0
        ok(calls == 1 and added == 1, f'3 二重に押しても送るのは1回・印は1つ（送った {calls}回・増えた {added}）')
        m = await pg.inner_text('#msg'); ok(any(k in m for k in ('チェックインは完了しています', '少し時間をおいて', 'チェックインしました')), f'3 あとから押すと「チェックイン済み」か「少し時間をおいて」（{m}）')
        allerrs += errs; await b.close()
        # 4 サーバーに届かない → 保留と札
        b, c, pg, errs = await page(p)
        await pg.evaluate('window.__offline = true'); await at(pg, HND)
        await press(pg); await pg.wait_for_timeout(900)
        q = await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.queue.u1') || '[]').length")
        t = await pg.evaluate("(() => { const t = $('smToast'); return t ? {show: t.classList.contains('show'), txt: t.textContent} : null; })()")
        st = await pg.evaluate('__stampAt != null')
        ok(st and q == 1, f'4 届かないときもハンコは出て、保留に入る（保留 {q}）')
        ok(t and t['show'] and 'つながり次第送ります' in t['txt'], f'4 「つながり次第送ります」の札（{t}）')   # 11/25 stamp-edge で文をそろえた
        await pg.screenshot(path=os.path.join(WORK, 'stamp_queue_390.png'))
        await pg.wait_for_timeout(2300)
        ok(not await pg.evaluate("$('smToast').classList.contains('show')"), '4 札は2秒で消える')
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        ok(not await pg.is_hidden('#queueBar'), '4 送信待ちの帯が出る')
        await pg.evaluate('window.__offline = false; window.dispatchEvent(new Event("online"))'); await pg.wait_for_timeout(1200)
        ok(await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.queue.u1') || '[]').length") == 0, '4 電波が戻ったら送る（今の保留の仕組み）')
        allerrs += errs; await b.close()
        # 5 サーバーが断る
        b, c, pg, errs = await page(p)
        await pg.evaluate('window.__fnFail = true'); await at(pg, HND); n0 = await pg.evaluate('S.checkins.length')
        await press(pg); await pg.wait_for_timeout(1500)
        ok(await pg.evaluate('__stampAt != null') and not await pg.evaluate("$('dStamp').open"), '5 断られたら、先に出したハンコの画面を閉じる')
        ok(await pg.evaluate('S.checkins.length') == n0, '5 端末の記録も元のまま（仮の印を取り消す）')
        m = await pg.inner_text('#msg'); ok('印を記録できませんでした' in m and '建物の中のため' in m, f'5 理由を出す（{m}）')   # 11/25 stamp-edge：理由ごとにそろえた文
        allerrs += errs; await b.close()
        # 6 直近の位置を使う・位置を待つときの札・10秒で区切る
        b, c, pg, errs = await page(p)
        await at(pg, HND, delay=6000)
        await pg.evaluate(f"HOME_POS = {{lat:{HND[0]}, lon:{HND[1]}, acc:20, ts:Date.now() - 5000, at:Date.now()}}; __geo.calls = 0")
        await press(pg); await pg.wait_for_timeout(600)
        r = await pg.evaluate("({ stamp: __stampAt == null ? null : __stampAt - __t0, fresh: GEO_WARM != null })")
        ok(r['stamp'] is not None and r['stamp'] < 3000 and not r['fresh'], f"6 直近の位置があれば位置を待たない（位置は6秒かかる・3秒の確定より前にハンコ）（{r}）")
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); allerrs += errs; await b.close()
        b, c, pg, errs = await page(p)
        await at(pg, HND, delay=60000)
        await pg.evaluate("HOME_POS = {lat:35.5494, lon:139.7798, acc:20, ts:Date.now() - 60000}")   # 古い位置は使わない
        await press(pg); await pg.wait_for_timeout(1000)
        m1 = await pg.inner_text('#msg'); s1 = await pg.evaluate("$('stubMsg') ? $('stubMsg').textContent : ''")
        ok('位置を確かめています' in m1 and '位置を確かめています' in s1, f'6 待つときは「位置を確かめています」（{m1}／{s1}）')
        await pg.wait_for_timeout(7500)   # 押してから約8.5秒：まだ区切らない
        m15 = await pg.inner_text('#msg'); ok('現在地が少しずれているようです' not in m15, f'6 10秒より前には区切らない（{m15}）')
        await waitjs(pg, "document.getElementById('msg').textContent.includes('現在地が少しずれているようです')", 8000)   # 重いと時計が遅れるので、決まった時間でなく文が出るまで待つ
        m2 = await pg.inner_text('#msg'); ok('現在地が少しずれているようです' in m2 and await pg.evaluate('__stampAt == null'), f'6 10秒で区切る（{m2}）')
        allerrs += errs; await b.close()
        # 6 屋内で誤差 120m：3秒で確定する（10秒待たせない）
        b, c, pg, errs = await page(p)
        await at(pg, HND, acc=120); await press(pg); await pg.wait_for_timeout(2400)
        r0 = await pg.evaluate("__stampAt == null ? null : __stampAt - __t0")
        await waitjs(pg, "__stampAt != null || document.getElementById('msg').textContent.includes('現在地が少しずれているようです')", 9000)
        r = await pg.evaluate("__stampAt == null ? null : __stampAt - __t0"); m3 = await pg.inner_text('#msg')
        ok(r0 is None and r is not None and 2800 <= r < 9500 and 'ずれている' not in m3, f'6 誤差120mでも3秒で確定してハンコ（10秒の区切りを待たない・3秒より前には確定しない）（{r and round(r)}ms）')
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); allerrs += errs; await b.close()
        # 7 範囲の外は今までどおり
        b, c, pg, errs = await page(p)
        await pg.evaluate('window.__calls = []'); await at(pg, OUT); await press(pg); await pg.wait_for_timeout(1500)
        m = await pg.inner_text('#msg'); ok(await pg.evaluate('__stampAt == null && window.__calls.length == 1') and 'いちばん近い' in m and 'まであと' in m, f'7 範囲の外はサーバーの判定を待つ（{m}）')
        allerrs += errs; await b.close()
        # 8 動きを減らす設定
        b, c, pg, errs = await page(p, reduced=True)
        await pg.evaluate("toast('テスト')"); await pg.wait_for_timeout(50)
        tr = await pg.evaluate("getComputedStyle($('smToast')).transitionDuration")
        ok(all(x.strip() in ('0s', '') for x in tr.split(',')), f'8 動きを減らす設定では札は動かない（{tr}）')
        allerrs += errs; await b.close()
    print('errors', allerrs if not fails else fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
