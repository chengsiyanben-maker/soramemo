import os, sys, json, shutil, asyncio, threading, functools, http.server
from playwright.async_api import async_playwright
# 閉じるはいつでも押せる（PM 11/21 22時・本人「閉じるの機能は、いつでも触れるように」・checkin/close-always）
#   1 読み込み中・3D を回している最中・シートを上まで引いた時・中身を下まで送った時でも、× と ‹ が見えていて押せる（重なりの順・指の取り合い）
#   2 上に固定・押せる大きさ44px以上
#   3 3D は × のほかに左の端から引いても閉じる。戻る操作（history.back＝iPhone の左端から引く戻る・ホーム画面のアプリ）でも閉じる
#   4 読み込みに失敗した時も × が残る
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'cxsrv')
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-close-always')); os.makedirs(SHOTS, exist_ok=True)
THREE = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'three-0.160.0.module.min.js')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
shutil.rmtree(WORK, ignore_errors=True); os.makedirs(WORK)
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index.html')); shutil.copytree(os.path.join(WEB, '3d'), os.path.join(WORK, '3d'))
open(os.path.join(WORK, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=WORK)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
# 押せるか：ボタンの真ん中で一番上にあるのがそのボタン（か中身）・大きさ44px以上・画面の中
HIT = """(sel) => { const b = typeof sel === 'string' ? document.querySelector(sel) : sel; if(!b) return { none:true };
  const r = b.getBoundingClientRect(), h = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  return { hit: !!h && (h === b || b.contains(h)), w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.y), x: Math.round(r.x), inview: r.top >= 0 && r.bottom <= innerHeight }; }"""
def ok_hit(r): return r.get('hit') and r.get('w', 0) >= 44 and r.get('h', 0) >= 44 and r.get('inview')
async def page(b, three='ok'):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    hold = []
    async def th(r):
        if three == 'hang': hold.append(r); return          # 読み込みを止めた状態（返さない）
        if three == 'fail' or not os.path.exists(THREE): await r.abort(); return
        await r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://cdn.jsdelivr.net/npm/three@**', th)
    await c.route('https://fake.supabase.co/**', lambda r: r.fulfill(body='{"planes":[],"at":null}' if 'airport-traffic' in r.request.url else '[]', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    pg.hold = hold
    return c, pg, errs
async def open3d(pg):
    await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(500)
    await pg.click('#dAirport [data-ap3d]'); await pg.wait_for_timeout(500)
OPEN = "(id) => document.getElementById(id).open"
async def main():
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        # ---- 空港のページ：上の × は中身を送っても残る ----
        c, pg, errs = await page(b)
        await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(500)
        r = await pg.evaluate(HIT, '#dAirport .cx')
        check('空港：上の × が見えて押せる（44px以上）', ok_hit(r), r)
        await pg.screenshot(path=os.path.join(SHOTS, '01-airport-top.png'))
        await pg.evaluate("document.getElementById('dAirportBody').scrollTop = 99999"); await pg.wait_for_timeout(200)
        r2 = await pg.evaluate(HIT, '#dAirport .cx')
        check('空港：下まで送っても × は同じ所に残って押せる', ok_hit(r2) and abs(r2['y'] - r['y']) <= 2, r2)
        await pg.click('#dAirport .cx'); await pg.wait_for_timeout(200)
        check('空港：× で閉じる', not await pg.evaluate(OPEN, 'dAirport'))
        check('閉じたら足した履歴も戻る（戻るが空回りしない）', await pg.evaluate("!(history.state && history.state.cx)"))
        # 戻る操作で閉じる・重なった画面は上から1枚ずつ
        await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(300)
        await pg.evaluate("history.back()"); await pg.wait_for_timeout(400)
        check('空港：戻る操作で閉じる（ページは出ない）', not await pg.evaluate(OPEN, 'dAirport') and await pg.evaluate("typeof render === 'function'"))
        # ---- 機体のくわしく（全画面）：中身を下まで送っても ‹ が残る ----
        await pg.evaluate("openPlane('JA01XJ')"); await pg.wait_for_timeout(500)
        await pg.evaluate("document.getElementById('dPlaneBody').insertAdjacentHTML('beforeend', '<div style=\"height:3000px\"></div>'); document.getElementById('dPlane').scrollTop = 99999"); await pg.wait_for_timeout(200)
        r = await pg.evaluate(HIT, '#dPlane .mp-back')
        check('機体のくわしく：下まで送っても ‹ 戻る が上に残って押せる（44px以上）', ok_hit(r) and r['y'] < 80, r)
        await pg.screenshot(path=os.path.join(SHOTS, '02-plane-scrolled.png'))
        await pg.click('#dPlane .mp-back'); await pg.wait_for_timeout(200)
        check('機体のくわしく：‹ で閉じる', not await pg.evaluate(OPEN, 'dPlane'))
        # ---- シートを上まで引いた時（中身が長いシートを下まで送る） ----
        await pg.evaluate("document.getElementById('dOpsAp').showModal(); document.querySelector('#dOpsAp .dlg').insertAdjacentHTML('beforeend', '<div style=\"height:3000px\"></div>'); document.querySelector('#dOpsAp .dlg').scrollTop = 99999"); await pg.wait_for_timeout(200)
        r = await pg.evaluate(HIT, '#dOpsAp .spx')
        check('シート：下まで送っても × が上に残って押せる（押せる所44px以上）', ok_hit(r), r)
        await pg.screenshot(path=os.path.join(SHOTS, '03-sheet-scrolled.png'))
        await pg.click('#dOpsAp .spx'); await pg.wait_for_timeout(200)
        check('シート：× で閉じる', not await pg.evaluate(OPEN, 'dOpsAp'))
        # ---- 運用の専用ページ：送っても ‹ 運用 が上に残る・開く途中でも戻れる・戻る操作でも戻る ----
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(800)
        await pg.evaluate("opsHubOpen('board')"); await pg.wait_for_timeout(700)
        await pg.evaluate("window.scrollTo(0, 3000)"); await pg.wait_for_timeout(200)
        r = await pg.evaluate(HIT, '#opsHubBack')
        check('運用の専用ページ：下へ送っても ‹ 運用 が上に残って押せる', ok_hit(r) and r['y'] < 80, r)
        await pg.screenshot(path=os.path.join(SHOTS, '04-ops-page-scrolled.png'))
        await pg.click('#opsHubBack'); await pg.wait_for_timeout(600)
        check('運用の専用ページ：‹ で一覧に戻る', await pg.evaluate("document.getElementById('v-ops').dataset.hub") == 'list')
        await pg.evaluate("(() => { const c = document.querySelector('[data-ohub=\"board\"]'); opsHubOpen('board', c); })()"); await pg.wait_for_timeout(80)
        busy = await pg.evaluate("OH_BUSY")
        await pg.evaluate("opsHubBack()"); await pg.wait_for_timeout(700)
        check('運用の専用ページ：開く動きの途中でも戻れる', busy and await pg.evaluate("document.getElementById('v-ops').dataset.hub") == 'list' and await pg.evaluate("!OPS_PAGE && !document.getElementById('v-ops').style.clipPath"), busy)
        await pg.evaluate("opsHubOpen('board')"); await pg.wait_for_timeout(700)
        await pg.evaluate("history.back()"); await pg.wait_for_timeout(700)
        check('運用の専用ページ：戻る操作で一覧に戻る', await pg.evaluate("document.getElementById('v-ops').dataset.hub") == 'list')
        allerr += errs; await c.close()

        # ---- 3D：読み込みを止めた状態 ----
        c, pg, errs = await page(b, 'hang')
        await open3d(pg)
        r = await pg.evaluate(HIT, '#dAp3d .a3top [data-a3-close]')
        load = await pg.evaluate("!document.getElementById('a3Load').hidden")
        check('3D：読み込み中も左上の × が幕の上に見えて押せる', load and ok_hit(r), r)
        await pg.screenshot(path=os.path.join(SHOTS, '05-3d-loading.png'))
        await pg.click('#dAp3d .a3top [data-a3-close]'); await pg.wait_for_timeout(200)
        check('3D：読み込み中に × で閉じる（描くのも止まる）', not await pg.evaluate(OPEN, 'dAp3d') and await pg.evaluate("A3 === null"))
        check('3D を閉じたあと空港のページは開いたまま', await pg.evaluate(OPEN, 'dAirport'))
        # 重なった画面：戻るで 3D → 空港 の順に1枚ずつ
        await pg.click('#dAirport [data-ap3d]'); await pg.wait_for_timeout(300)
        await pg.evaluate("history.back()"); await pg.wait_for_timeout(400)
        s1 = await pg.evaluate("[document.getElementById('dAp3d').open, document.getElementById('dAirport').open, A3 === null]")
        await pg.evaluate("history.back()"); await pg.wait_for_timeout(400)
        s2 = await pg.evaluate("[document.getElementById('dAp3d').open, document.getElementById('dAirport').open]")
        check('戻る操作：3D、空港の順に1枚ずつ閉じる', s1 == [False, True, True] and s2 == [False, False], [s1, s2])
        for r in pg.hold:
            try: await r.abort()
            except Exception: pass
        allerr += errs; await c.close()

        # ---- 3D：読み込みに失敗した時 ----
        c, pg, errs = await page(b, 'fail')
        await open3d(pg); await pg.wait_for_timeout(500)
        txt = await pg.evaluate("document.getElementById('a3Load').textContent")
        r = await pg.evaluate(HIT, '#dAp3d .a3top [data-a3-close]')
        check('3D：読み込めなかった時も左上の × が残って押せる', '読み込めませんでした' in txt and ok_hit(r), [txt[:20], r])
        await pg.screenshot(path=os.path.join(SHOTS, '06-3d-failed.png'))
        await pg.click('#dAp3d .a3top [data-a3-close]'); await pg.wait_for_timeout(200)
        check('3D：失敗のあと × で閉じる', not await pg.evaluate(OPEN, 'dAp3d'))
        allerr += errs; await c.close()

        # ---- 3D：回している途中・左の端から引く ----
        if os.path.exists(THREE):
            c, pg, errs = await page(b)
            await open3d(pg)
            await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=30000)
            # 指で回している途中（絵の上で押したまま動かしている）
            await pg.mouse.move(150, 300)   # 押したままの指は、ほんとうにある指（マウスの pointerId 1）で作る（setPointerCapture が通るように）
            y0 = await pg.evaluate("""(() => { const cv = document.getElementById('a3Cv'), o = { bubbles:true, pointerId:1, pointerType:'mouse', isPrimary:true, buttons:1, clientY:300 };
              cv.dispatchEvent(new PointerEvent('pointerdown', { ...o, clientX:150 })); cv.dispatchEvent(new PointerEvent('pointermove', { ...o, clientX:220 })); return A3.yaw; })()""")
            r = await pg.evaluate(HIT, '#dAp3d .a3top [data-a3-close]')
            check('3D：回している途中も × が押せる', y0 != 0 and ok_hit(r), [y0, r])
            await pg.click('#dAp3d .a3top [data-a3-close]'); await pg.wait_for_timeout(200)
            check('3D：回している途中に × で閉じる', not await pg.evaluate(OPEN, 'dAp3d') and await pg.evaluate("A3 === null"))
            # 左の端から引く（3割より短いと戻る・長いと閉じる）
            await pg.click('#dAirport [data-ap3d]')
            await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=30000)
            yaw = await pg.evaluate("A3.yaw")
            await pg.mouse.move(6, 420); await pg.mouse.down(); await pg.mouse.move(40, 422, steps=4); await pg.mouse.move(70, 424, steps=4); await pg.mouse.up(); await pg.wait_for_timeout(300)
            short = await pg.evaluate("[document.getElementById('dAp3d').open, A3 && A3.yaw, document.getElementById('a3Wrap').style.transform]")
            check('3D：左の端から少し引いただけなら閉じない（3D も回らない）', short[0] and short[1] == yaw and short[2] in ('', 'none'), short)
            await pg.mouse.move(6, 420); await pg.mouse.down(); await pg.mouse.move(80, 422, steps=5)
            await pg.screenshot(path=os.path.join(SHOTS, '07-3d-edge-swipe.png'))
            await pg.mouse.move(260, 424, steps=6); await pg.mouse.up(); await pg.wait_for_timeout(300)
            check('3D：左の端から3割より長く引くと閉じる', not await pg.evaluate(OPEN, 'dAp3d') and await pg.evaluate("A3 === null"))
            # 戻る操作
            await pg.click('#dAirport [data-ap3d]'); await pg.wait_for_timeout(800)
            await pg.evaluate("history.back()"); await pg.wait_for_timeout(400)
            check('3D：戻る操作で閉じる', not await pg.evaluate(OPEN, 'dAp3d') and await pg.evaluate("A3 === null"))
            allerr += errs; await c.close()
        else:
            print('three.js がないので、3D を回している途中・左の端の確かめは飛ばす（t142 を先に流すと置かれる）')

        # ---- 閉じさせない画面（cancel を止めている）は戻る操作でも閉じない ----
        c, pg, errs = await page(b)
        await pg.evaluate("(() => { const d = document.getElementById('dGuide'); d.addEventListener('cancel', e => e.preventDefault()); d.showModal(); })()"); await pg.wait_for_timeout(200)
        await pg.evaluate("history.back()"); await pg.wait_for_timeout(400)
        st = await pg.evaluate("[document.getElementById('dGuide').open, !!(history.state && history.state.cx)]")
        check('cancel を止めた画面は戻る操作で閉じず、履歴を足し直す', st == [True, True], st)
        allerr += errs; await c.close()
        await b.close()
    check('画面のエラーなし', allerr == [], allerr)
    print('errors', fails)
asyncio.run(main())
