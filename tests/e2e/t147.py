import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 半券を指で切る（11/19 本人の iPhone「指で右へ引いても切れない」・PM 11/19 14時05分・ブランチ checkin/tear-finger）
#   指の操作は CDP の Input.dispatchTouchEvent で出す（マウスではない）
#   1 半券の右寄り（右端から20px）をつかんで画面の端まで引くと切れる（端までの残りの半分・28〜56px）
#   2 速く右へはじくと、切れる長さに届かなくても切れる（0.5px/ms 以上・20px 以上）。ゆっくりなら切れない
#   3 縦に動かすと切れない（確かめのシートも出ない）
#   4 先に縦へ少し揺れてから右へ引いても切れる（縦と横は 10px 動いてから決める・横が縦の 0.6 倍以上なら横）
#   5 ゆっくり少しだけ引いた（切れる長さに届かない）ときは切れずに戻る
#   6 押すだけのときは今までどおり確かめてから切る（確かめのシートが出る）
#   iPhone SE（375）・15（390）・Pro Max（430）の幅で
import asyncio, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright
fails = []
def check(label, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + label + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WEB)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
async def touch(cdp, pg, pts, gap_ms):
    # pts：[(x, y), ...]。最初で指を置き、間を gap_ms ごとに動かし、最後で離す
    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': pts[0][0], 'y': pts[0][1]}]})
    for x, y in pts[1:]:
        if gap_ms: await pg.wait_for_timeout(gap_ms)
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y}]})
    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    await pg.wait_for_timeout(250)
def line(x0, y0, x1, y1, n):
    return [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n + 1)]
async def torn(pg):
    v = await pg.evaluate("(() => { const n = window.__torn || 0; window.__torn = 0; return n; })()")
    await pg.evaluate("(() => { const d = $('dCkConfirm'); if(d.open){ d.onclose = null; d.close(); } $('checkin').style.transform = ''; })()")
    return v
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        for w, h in [(375, 667), (390, 844), (430, 932)]:
            c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', has_touch=True, is_mobile=True, device_scale_factor=1)
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
            pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(1500)
            if not await pg.evaluate("demo"): await pg.evaluate("$('toggleDemo').click(); 0"); await pg.wait_for_timeout(800)
            # 切れたかどうかだけを見る：印を押す処理（checkin）は数えるだけにする（印の流れは t7・t144 で確かめる）
            await pg.evaluate("goTab('home'); window.checkin = async () => { window.__torn = (window.__torn || 0) + 1; }; 0"); await pg.wait_for_timeout(700)
            cdp = await c.new_cdp_session(pg)
            r = await pg.evaluate("(() => { const b = $('checkin').getBoundingClientRect(); return { l: b.left, r: b.right, t: b.top, h: b.height, W: document.documentElement.clientWidth, st: $('bpass').dataset.state }; })()")
            y = r['t'] + r['h'] / 2; W = r['W']; mid = (r['l'] + r['r']) / 2; grip = r['r'] - 20
            check(f'{w} 半券は判定範囲の中（デモ）', r['st'] == 'in', r)
            # 1 右寄りをつかんで端まで（ゆっくり：16ms ごとに 10 回）
            await touch(cdp, pg, line(grip, y, W - 1, y, 10), 16)
            n = await torn(pg); check(f'{w} 1 右端から20pxをつかんで画面の端まで引くと切れる（{round(W - 1 - grip)}px）', n == 1, n)
            # 2 はじく：左寄り（切れる長さ 53px）をつかんで 48px を 3 回で（ヘッドレスでは1回が約30ms・約0.75px/ms）
            left = r['l'] + 10
            await touch(cdp, pg, line(left, y, left + 48, y, 3), 0)
            n = await torn(pg); check(f'{w} 2 速く右へはじくと、切れる長さ（53px）より短くても切れる（48px）', n == 1, n)
            # 2b 同じ 48px でも、ゆっくり（320ms）なら切れない（はじいたときだけ）
            await touch(cdp, pg, line(left, y, left + 48, y, 8), 40)
            n = await torn(pg); check(f'{w} 2 同じ 48px でもゆっくりなら切れない', n == 0, n)
            # 3 縦に動かす
            await touch(cdp, pg, line(mid, y, mid + 5, y - 40, 8), 16)
            n = await torn(pg); dlg = await pg.evaluate("$('dCkConfirm').open")
            check(f'{w} 3 縦に動かすと切れない（確かめのシートも出ない）', n == 0 and not dlg, (n, dlg))
            # 4 先に縦へ 6px 揺れてから右へ
            pts = [(grip, y), (grip, y - 3), (grip + 1, y - 6)] + line(grip + 1, y - 6, W - 1, y - 6, 8)[1:]
            await touch(cdp, pg, pts, 16)
            n = await torn(pg); check(f'{w} 4 先に縦へ少し揺れてから右へ引いても切れる', n == 1, n)
            # 5 ゆっくり少しだけ（真ん中から 20px を 200ms かけて）
            await touch(cdp, pg, line(mid, y, mid + 20, y, 10), 25)
            n = await torn(pg); tf = await pg.evaluate("$('checkin').style.transform")
            check(f'{w} 5 ゆっくり少しだけ引いたときは切れずに戻る', n == 0 and tf == '', (n, tf))
            # 6 押すだけ
            await touch(cdp, pg, [(mid, y)], 0)
            dlg = await pg.evaluate("$('dCkConfirm').open")
            check(f'{w} 6 押すだけのときは確かめのシートが出る', dlg is True, dlg)
            await pg.evaluate("(() => { const d = $('dCkConfirm'); d.returnValue = 'yes'; d.close(); })()"); await pg.wait_for_timeout(300)
            n = await torn(pg); check(f'{w} 6 確かめて「はい」で切れる', n == 1, n)
            # 切れる長さの決め方（関数）
            if w == 390:
                v = await pg.evaluate("[tearAt(20), tearAt(66), tearAt(80), tearAt(200)]")
                check('切れる長さは残りの半分で 28〜56px', v == [28, 33, 40, 56], v)
            await c.close()
        await b.close()
        print('errors', errs + fails)
        if errs or fails: sys.exit(1)
asyncio.run(main())
