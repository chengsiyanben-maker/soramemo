import os, sys, json, shutil, asyncio, threading, functools, http.server
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 改善担当の見回り sweep-1124 の直し（PM 11/24 4時15分・checkin/sweep-1124）のうち、羽田の3D の所
#   2 管制塔の視点：目は塔の上（約118m）・管制室の外へ。建物だけカメラの前 A3_TOWER_CUT より手前を切る（地面・機体は切らない）。ほかの視点では切らない。夜のターミナルの壁は暗い灰色
#   3 375×667 で機体を選ぶと「この機体から見る」が画面の中（札の上）
#   4 「機体」を押して選ぶ途中：ピルは「機体」を押した形・数は × に重ならない。× で閉じたら前の視点のピル
#   7 視点のピルの高さ 44・「出典」の押せる所 44×44・題の補足 13px
#   偽のサーバーを使う。本物の Supabase には接続しない（three.js は t142 が作業用フォルダに置いたもの）
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3-sweep1124')
THREE = os.path.join(BASE, 'three-0.160.0.module.min.js')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
def serve():
    shutil.rmtree(WORK, ignore_errors=True); shutil.copytree(WEB, WORK)
    open(os.path.join(WORK, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=WORK))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv.server_address[1]
now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
def pl(i, cs, lat, lon, alt, kt, hdg, fpm, ph, dist, typ, reg): return {'id': i, 'callsign': cs, 'lat': lat, 'lon': lon, 'alt_ft': alt, 'kt': kt, 'hdg': hdg, 'fpm': fpm, 'phase': ph, 'dist_km': dist, 'type': typ, 'reg': reg, 'trail': []}
AIR = [pl('a1', 'JAL318', 35.512, 139.8340, 1300, 145, 337, -700, 'arr', 6, 'A359', 'JA01XJ'), pl('a2', 'ANA59', 35.585, 139.7560, 2600, 190, 337, 2200, 'dep', 4, 'B789', 'JA871A'),
       pl('a3', 'ANA36', 35.470, 139.880, 3500, 200, 320, -800, 'arr', 13, 'B78X', 'JA933A'), pl('a8', 'ANA12', 35.430, 139.950, 5200, 220, 320, -900, 'arr', 20, 'B77W', 'JA781A')]
GROUND = [{'id': 'g0', 'callsign': 'JAL98', 'lat': 35.54807, 'lon': 139.77256, 'hdg': 240, 'kt': 10, 'type': 'B789', 'reg': 'JA877J', 'moving': True}]
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [], 'dep': []}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def open3d(b, port, sky='day', w=390, h=844):
    c = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        body = {'iata': 'HND', 'at': iso(-30), 'source': 'adsb.lol', 'planes': AIR, 'ground': GROUND} if name == 'airport-traffic' else NOWD if name == 'airport-now' else {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{port}/index.html')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    if sky == 'night': await pg.evaluate("document.documentElement.dataset.night = 'on'")
    await pg.evaluate("s => { a3Night = () => s; }", sky)
    await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(600)
    await pg.click('#dAirport .a3pill [data-ap3d]')
    await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=40000)
    await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1500)
    return c, pg, errs
PRESSED = "[...document.querySelectorAll('[data-a3-view]')].map(b => b.getAttribute('aria-pressed') === 'true' ? b.dataset.a3View : '').join('')"
async def main():
    if not os.path.exists(THREE): print('three.js がないので飛ばす（t142 を先に流すと置かれる）'); sys.exit(1)
    port = serve(); allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        # ---- 2 管制塔
        c, pg, errs = await open3d(b, port)
        INERT = "A3.clip.distanceToPoint(new A3.THREE.Vector3(A3.cam.position.x, 0, A3.cam.position.z)) > 0 && A3.clip.distanceToPoint(A3.cam.position) > 0"
        r = await pg.evaluate("({ clip: !!A3.clipOn, mats: A3.bldMats.length, hasClip: A3.bldMats.every(m => m.clippingPlanes && m.clippingPlanes[0] === A3.clip) && (%s) })" % INERT)
        check('2 全体の視点では建物を切らない', not r['clip'] and r['mats'] >= 3 and r['hasClip'], r)
        await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("""(() => { const T = A3.THREE, d = new T.Vector3(); A3.cam.getWorldDirection(d); const [tx, tz] = A3.towerXZ, c = A3.cam.position;
          const near = new T.Vector3(c.x + d.x / Math.hypot(d.x, d.z) * 200, 30, c.z + d.z / Math.hypot(d.x, d.z) * 200), far = new T.Vector3(c.x + d.x / Math.hypot(d.x, d.z) * 900, 30, c.z + d.z / Math.hypot(d.x, d.z) * 900);
          return { y: Math.round(c.y), out: Math.round(Math.hypot(c.x - tx, c.z - tz)), pitch: Math.asin(d.y) * 180 / Math.PI, clip: !!A3.clipOn, every: A3.bldMats.every(m => m.clippingPlanes && m.clippingPlanes[0] === A3.clip),
            nearCut: A3.clip.distanceToPoint(near) < 0, farKeep: A3.clip.distanceToPoint(far) > 0, cut: A3_TOWER_CUT }; })()""")
        check('2 管制塔：目は塔の上（約118m）・管制室の外（約40m 滑走路側）・少し見下ろす', r['y'] == 118 and 35 <= r['out'] <= 45 and -10 < r['pitch'] < -2, r)
        check('2 管制塔：建物の材質だけに切る面（前 200m の建物は切り、900m 先は残す）', r['clip'] and r['every'] and r['nearCut'] and r['farKeep'], r)
        await pg.evaluate("A3.yaw = Math.PI * 0.75; A3.dirty = true"); await pg.wait_for_timeout(900)
        r2 = await pg.evaluate("(() => { const d = new A3.THREE.Vector3(); A3.cam.getWorldDirection(d); const n = A3.clip.normal; return Math.abs(n.x * d.x + n.z * d.z) / Math.hypot(d.x, d.z); })()")
        check('2 指で回しても切る面はいつも前（向きと同じ）', r2 > 0.99, r2)
        await pg.click('[data-a3-view="all"]'); await pg.wait_for_timeout(900)
        check('2 全体に戻すと何も切らない', await pg.evaluate("!A3.clipOn && (%s)" % INERT))
        await pg.evaluate("a3Select('a1', true)"); await pg.wait_for_timeout(900)
        check('2 機体の視点でも切らない', await pg.evaluate("!A3.clipOn && (%s)" % INERT))
        # ---- 7 大きさ
        r = await pg.evaluate("({ pills: [...document.querySelectorAll('.a3pills button')].map(b => Math.round(b.getBoundingClientRect().height)), cr: (r => [Math.round(r.width), Math.round(r.height)])($('a3Credit').getBoundingClientRect()), crf: getComputedStyle($('a3Credit')).fontSize, sub: getComputedStyle($('a3Sub')).fontSize })")
        check('7 視点のピルの高さ 44・出典の押せる所 44×44 以上・字 13px・題の補足 13px', all(h >= 44 for h in r['pills']) and r['cr'][0] >= 44 and r['cr'][1] >= 44 and r['crf'] == '13px' and r['sub'] == '13px', r)
        allerr += errs; await c.close()
        # 夜：ターミナルの壁は暗い灰色（明るい灯りの色でない）
        c, pg, errs = await open3d(b, port, 'night')
        r = await pg.evaluate("(() => { const c = new A3.THREE.Color(A3.col.tWall); return Math.max(c.r, c.g, c.b); })()")
        check('2 夜のターミナルの壁は暗い灰色', r < 0.35, r)
        allerr += errs; await c.close()
        # ---- 3・4 375×667
        c, pg, errs = await open3d(b, port, 'day', 375, 667)
        await pg.evaluate("a3Select('a1')"); await pg.wait_for_timeout(700)
        r = await pg.evaluate("(() => { const b = document.querySelector('[data-a3-follow]').getBoundingClientRect(), g = document.querySelector('.a3grid').getBoundingClientRect(); return { bottom: Math.round(b.bottom), above: b.bottom <= g.top, h: innerHeight }; })()")
        check('3 375×667：「この機体から見る」が画面の中（札の上）', r['bottom'] <= r['h'] and r['above'], r)
        await pg.click('[data-a3-uncard]'); await pg.wait_for_timeout(500)
        await pg.click('[data-a3-view="plane"]'); await pg.wait_for_timeout(700)
        r = await pg.evaluate("(() => { const n = document.querySelector('.a3sh .n').getBoundingClientRect(), x = document.querySelector('.a3x').getBoundingClientRect(); return { gap: Math.round(x.left - n.right), txt: $('a3Sheet').innerText.slice(0, 40) }; })()")
        check('4 選ぶ途中：数は × に重ならない', r['gap'] >= 8 and '見たい機体を押してください' in r['txt'], r)
        check('4 選ぶ途中：ピルは「機体」を押した形', await pg.evaluate(PRESSED) == 'plane')
        await pg.click('[data-a3-unpick]'); await pg.wait_for_timeout(500)
        check('4 × で閉じたら前の視点（全体）のピルに戻る', await pg.evaluate(PRESSED) == 'all')
        allerr += errs; await c.close()
        await b.close()
    print('JS のエラー', allerr)
    if allerr: fails.append('JS のエラー')
    print('fails', fails)
    print('全部成功' if not fails else 'errors ' + str(fails))
    sys.exit(1 if fails else 0)
asyncio.run(main())
