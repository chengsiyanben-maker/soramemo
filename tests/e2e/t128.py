import os, sys, json, asyncio, threading, functools, http.server, socketserver, shutil, tempfile
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 全体の見回り（11/13 改善担当 report-sweep-1113・データ担当 report-speed-1113）の直し
#   1 図鑑でデモの「終了」が押せる（ツメがかぶらない）・ツメが下のタブ帯にかからない（844・667）
#   2 ホームの地図の「＋」「−」が押せる（667 でも MAIN.wrap がかぶらない）
#   4 フライトの地図の下に国土地理院の淡色地図
#   5 高さ 667 のログイン画面で「デモで試す」が画面の中・高さ 44px 以上
#   6 図鑑の「図鑑の上へ」を下の端へ送ってもタブ帯にもぐらない
#   7 見方の帯のピル・上の段のボタン・デモの「終了」・シートのつまみは、押せる範囲が 44px 以上（見た目の大きさは変えない）
#   8 サービスワーカーは保存した版を先に出す（網が遅くても待たない）・supabase-js を head で先読み
#   9 デモの便の時刻は開き直しても同じ・デモでは push-subscribe を呼ばない・ログインの箱を閉じると Turnstile を片付ける
#   運用の見方の帯は、選んだ見方が見えているなら左端から（先頭の「案内板」を隠さない）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
from playwright.async_api import async_playwright
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
HANEDA = (35.5494, 139.7798)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
async def openp(b, h=844, mode='demo', extra='', reqs=None):
    c = await b.new_context(viewport={'width':390,'height':h}, geolocation={'latitude':HANEDA[0],'longitude':HANEDA[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo', has_touch=True)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://challenges.cloudflare.com/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_turnstile.js'), content_type='application/javascript'))
    await c.add_init_script(INIT + extra)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    if reqs is not None: pg.on('request', lambda r: reqs.append(r.url))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(600)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    if mode == 'demo': await pg.evaluate("$('gateDemo').click()"); await pg.wait_for_timeout(1200)
    if mode == 'login': await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1500)
    return c, pg, errs
# 真ん中を押したときにいちばん上にあるのがその要素（か中身）か
HIT = """(sel => { const e = document.querySelector(sel); if(!e) return { ok:false, why:'none' }; const r = e.getBoundingClientRect(); const t = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
  return { ok: !!t && (t === e || e.contains(t)), top: t ? t.tagName + '.' + String(t.className).slice(0, 30) : null, r:[Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })"""
# 押せる範囲（要素の中心から上下・左右に、要素に当たる所を数える）
AREA = """(sel => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), box = e.closest('.viewsw') ? e.closest('.viewsw').getBoundingClientRect() : { left:0, right:innerWidth }; return r.width && r.left >= box.left && r.right <= box.right && r.top >= 0 && r.bottom <= innerHeight; }).map(e => { const r = e.getBoundingClientRect(), cx = r.left + r.width/2, cy = r.top + r.height/2;
  const on = (x, y) => { const t = document.elementFromPoint(x, y); return !!t && (t === e || e.contains(t)); };
  let t = cy, b = cy, l = cx, rr = cx; while(t > 0 && on(cx, t - 1)) t--; while(b < innerHeight - 1 && on(cx, b + 1)) b++; while(l > 0 && on(l - 1, cy)) l--; while(rr < innerWidth - 1 && on(rr + 1, cy)) rr++;
  return [(e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 8), Math.round(r.width), Math.round(r.height), Math.round(rr - l + 1), Math.round(b - t + 1)]; }))"""
async def main():
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for h in (844, 667):
            # 1・6・7 図鑑（デモ）
            c, pg, errs = await openp(b, h, 'demo')
            await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(900)
            r = await pg.evaluate(HIT + "('#demoEnd')")
            check(f'{h} 図鑑：デモの「終了」が押せる（ツメがかぶらない）', r['ok'], r)
            r = await pg.evaluate("(() => { const bs = [...document.querySelectorAll('#zkTsume button')], l = bs[bs.length - 1].getBoundingClientRect(), e = $('demoEnd').getBoundingClientRect(); return { first: Math.round(bs[0].getBoundingClientRect().top), last: Math.round(l.bottom), end: Math.round(e.bottom), tabs: Math.round(document.querySelector('nav.tabs').getBoundingClientRect().top), h: Math.round(l.height) }; })()")
            check(f'{h} 図鑑：ツメはデモの帯の下から・タブ帯にかからない・高さ 44', r['first'] > r['end'] and r['last'] <= r['tabs'] and r['h'] >= 44, r)
            await pg.click('#demoEnd'); await pg.wait_for_timeout(900)
            check(f'{h} 図鑑：「終了」を押すとデモが終わる', await pg.evaluate('demo === false'))
            allerr += errs; await c.close()
            c, pg, errs = await openp(b, h, 'login')
            await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(900)
            r = await pg.evaluate("(() => { const bs = [...document.querySelectorAll('#zkTsume button')]; return [Math.round(bs[0].getBoundingClientRect().top), $('zkTsume').classList.contains('tight')]; })()")
            check(f'{h} 図鑑：デモでないときツメの位置とすき間は前のまま（140）', r == [140, False], r)
            await pg.evaluate("document.querySelector('#zkrg-九州 [data-zk-up]').scrollIntoView({block:'end'})"); await pg.wait_for_timeout(300)
            r = await pg.evaluate(HIT + "('#zkrg-九州 [data-zk-up]')")
            check(f'{h} 図鑑：「図鑑の上へ」を下の端へ送ってもタブ帯にもぐらない', r['ok'], r)
            allerr += errs; await c.close()
            # 2・7 ホーム（ログインしない人・ログインした人）
            for mode in ('none', 'login'):
                c, pg, errs = await openp(b, h, mode)
                try: await pg.wait_for_selector('.leaflet-control-zoom-in', timeout=8000)
                except Exception: pass
                await pg.wait_for_timeout(500)
                r1 = await pg.evaluate(HIT + "('.leaflet-control-zoom-in')"); r2 = await pg.evaluate(HIT + "('.leaflet-control-zoom-out')")
                check(f'{h} ホーム（{mode}）：地図の「＋」「−」が押せる', r1['ok'] and r2['ok'], [r1, r2])
                z0 = await pg.evaluate('HOME_MAP.getZoom()'); await pg.click('.leaflet-control-zoom-in'); await pg.wait_for_timeout(600); z1 = await pg.evaluate('HOME_MAP.getZoom()')
                check(f'{h} ホーム（{mode}）：「＋」で地図が寄る', z1 > z0, [z0, z1])
                r = await pg.evaluate(HIT + "('#openSettings, #gateLogin')")
                check(f'{h} ホーム（{mode}）：上の段のボタンは押せる（地図へ通すのは透明な所だけ）', r['ok'], r)
                ar = await pg.evaluate(AREA + "('#homeSheet .grab')")
                check(f'{h} ホーム（{mode}）：シートのつまみの押せる高さ 44 以上・見た目は 24 のまま', ar and ar[0][2] == 24 and ar[0][4] >= 44, ar)
                allerr += errs; await c.close()
            # 5 ログイン画面
            c, pg, errs = await openp(b, h, 'none')
            await pg.evaluate("$('gateLogin').click()"); await pg.wait_for_timeout(800)
            r = await pg.evaluate("(() => { const e = document.querySelector('#auFoot [data-au=demo]'), s = document.querySelector('#auFoot [data-au=to-signup]'); const a = e.getBoundingClientRect(), b = s.getBoundingClientRect(); return { top: Math.round(a.top), bottom: Math.round(a.bottom), h: Math.round(a.height), below: a.top >= b.bottom, ih: innerHeight }; })()")
            check(f'{h} ログイン：「デモで試す」は新規登録の下・画面の中・高さ 44 以上', r['below'] and r['bottom'] <= r['ih'] and r['h'] >= 44, r)
            r = await pg.evaluate(HIT + "('#auFoot [data-au=demo]')")
            check(f'{h} ログイン：「デモで試す」が押せる', r['ok'], r)
            await pg.click('#auFoot [data-au=demo]'); await pg.wait_for_timeout(1200)
            check(f'{h} ログイン：押すとデモが始まる', await pg.evaluate('demo === true'))
            allerr += errs; await c.close()
            # 7 見方の帯・上の段・デモの「終了」の押せる範囲
            c, pg, errs = await openp(b, h, 'demo')
            for v in ('log', 'ops'):
                await pg.evaluate(f"goTab('{v}')"); await pg.wait_for_timeout(900)
                ar = await pg.evaluate(AREA + "('.view.on .viewsw button')")
                check(f'{h} {v}：見方の帯のピルは押せる範囲 44×44 以上（見た目は高さ 40 のまま）', ar and all(x[3] >= 44 and x[4] >= 44 and x[2] == 40 for x in ar), ar)
                ar = await pg.evaluate(AREA + "('.topzone .iconbtn, .modesw button, #demoEnd')")
                check(f'{h} {v}：上の段のマイページ・切り替え・デモの「終了」は押せる高さ 44 以上', len(ar) >= 3 and all(x[4] >= 44 for x in ar), ar)
            r = await pg.evaluate("[$('opsViews').scrollLeft, VIEW.ops]")
            check(f'{h} 運用：選んだ見方が見えているので帯は左端から（案内板を隠さない）', r[0] == 0, r)
            await pg.evaluate("VIEW.ops = 'photo'; setViewsw('opsViews', 'ops')")
            r = await pg.evaluate("(() => { const e = $('opsViews'), b = e.querySelector('[aria-selected=true]'); if(!b) return [true, 'なし']; const x = b.getBoundingClientRect(), y = e.getBoundingClientRect(); return [x.right <= y.right + 1 && x.left >= y.left - 1, e.scrollLeft]; })()")
            check(f'{h} 運用：右の外の見方を選んでいるときは、それが見えるまで送る', r[0], r)
            allerr += errs; await c.close()
        # 4 フライトの地図の下に淡色地図
        c, pg, errs = await openp(b, 844, 'demo')
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(500); await pg.evaluate("VIEW.log = 'map'; renderLog()")
        try: await pg.wait_for_selector('#fbLeaf .leaflet-tile', timeout=8000)
        except Exception: pass
        r = await pg.evaluate("[...document.querySelectorAll('#fbLeaf img.leaflet-tile')].map(i => i.src).filter(s => s.includes('/xyz/pale/')).length")
        check('フライトの地図：下に国土地理院の淡色地図（画像）を敷く', r > 0, r)
        await pg.locator('.fbmapc').screenshot(path=os.path.join(WORK, 't128_flight_map.png'))
        # 9 デモの便の時刻は開き直しても同じ
        d1 = await pg.evaluate("S.flights.slice(0, 3).map(f => f.dep)")
        allerr += errs; await c.close()
        reqs = []
        c, pg, errs = await openp(b, 844, 'demo', reqs=reqs)
        await pg.wait_for_timeout(1500)
        d2 = await pg.evaluate("S.flights.slice(0, 3).map(f => f.dep)")
        check('デモ：見本の便の時刻は開き直しても同じ', d1 == d2 and len(d1) == 3, [d1, d2])
        r = await pg.evaluate("S.flights.slice(0, 1).map(f => new Date(f.dep).toLocaleTimeString('ja-JP', { timeZone:'Asia/Tokyo', hour:'2-digit', minute:'2-digit' }))")
        check('デモ：最初の便は朝8時（日本時間）', r == ['08:00'], r)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1500)
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(500)
        check('デモ：push-subscribe を呼ばない', not any('push-subscribe' in u for u in reqs), [u for u in reqs if 'push-subscribe' in u])
        allerr += errs; await c.close()
        # 9 Turnstile：ログインの箱を閉じると片付ける（開き直しで二重に作らない）
        cfg = "window.SORAMEMO_CONFIG = Object.assign(window.SORAMEMO_CONFIG || {}, { turnstileSiteKey:'test' });"
        c, pg, errs = await openp(b, 844, 'none')
        await pg.evaluate(cfg)
        await pg.evaluate("$('gateLogin').click()"); await pg.wait_for_timeout(900)
        w1 = await pg.evaluate('AU_CAP.widget')
        await pg.evaluate("document.querySelector('[data-au=close]').click()"); await pg.wait_for_timeout(300)
        rm = await pg.evaluate('window.__tsRemoved || []')
        await pg.evaluate("$('gateLogin').click()"); await pg.wait_for_timeout(900)
        w2 = await pg.evaluate('AU_CAP.widget')
        check('Turnstile：閉じると turnstile.remove() で片付け、開き直すと新しく作る', w1 is not None and rm == [w1] and w2 is not None and w2 != w1, [w1, rm, w2])
        allerr += errs; await c.close()
        # 8 head の先読み：URL は SUPABASE_JS と同じ
        c, pg, errs = await openp(b, 844, 'none')
        r = await pg.evaluate("[document.getElementById('sbPreload') && document.getElementById('sbPreload').href, SUPABASE_JS]")
        check('supabase-js を head で先読み（URL は SUPABASE_JS と同じ）', r[0] == r[1], r)
        allerr += errs; await c.close()
        # 8 サービスワーカー：保存した版を先に出す（localhost で配る）
        tmp = tempfile.mkdtemp(prefix='t128sw'); site = os.path.join(tmp, 'site'); shutil.copytree(WEB, site)
        open(os.path.join(site, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = {};')
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
        Hd = functools.partial(Quiet, directory=site)
        srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), Hd); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', service_workers='allow')
            await c.add_init_script(INIT)
            pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            url = f'http://127.0.0.1:{port}/'
            await pg.goto(url); await pg.wait_for_function('navigator.serviceWorker && navigator.serviceWorker.controller', timeout=15000)
            await pg.wait_for_timeout(500)
            slow = {'n': 0}
            async def delay(route):
                slow['n'] += 1; await asyncio.sleep(4); await route.continue_()
            await c.route('**/127.0.0.1:*/', delay); await c.route('**/index.html', delay)
            t0 = asyncio.get_event_loop().time()
            await pg.reload(wait_until='domcontentloaded'); dt = asyncio.get_event_loop().time() - t0
            check('サービスワーカー：網が遅くても保存した版をすぐ出す（4 秒待たない）', dt < 3, round(dt, 2))
            await pg.wait_for_timeout(4800)
            check('サービスワーカー：裏で新しい版を取りに行く', slow['n'] >= 1, slow['n'])
            await c.unroute('**/127.0.0.1:*/'); await c.unroute('**/index.html')
            await c.set_offline(True)
            await pg.reload(wait_until='domcontentloaded'); await pg.wait_for_function('typeof render === "function"', timeout=8000)
            check('サービスワーカー：圏外でも開ける', await pg.evaluate("!!document.querySelector('nav.tabs')"))
            await c.set_offline(False)
            allerr += errs; await c.close()
        finally:
            srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
        await b.close()
    check('エラーなし', not allerr, allerr)
    print('errors', fails)
asyncio.run(main())
