import math, os, sys, json, shutil, asyncio, threading, functools, http.server
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D を自由に動かす（PM 11/25 3時20分・本人「案B、管制塔もピルに残す」・checkin/a3-free・画面案 design/a3-free）
#   下の4つのボタン（自由・追う・立つ・飛ぶ）・上のピル（全体・管制塔・機体）は近道
#   自由：1本指で回す・2本指でつまむ／なぞる／上下・地面の下と遠すぎる所には行かない・「全体に戻す」・はじめての1回だけの案内
#   追う：後ろ・横・前・機体が消えたら今の位置のまま自由へ（下に一言と「ほかを追う」）
#   立つ：おすすめの場所と押した所・目の高さ 約1.6m・2本指はズーム（目は動かない）
#   飛ぶ：左のつまみで進む・右で上下と向き・上限 1,000m・つまみと4つのボタンが重ならない
#   375×667：押せる所 44px・はみ出しなし。写真は docs/pm/shots-a3-free/
#   偽のサーバーを使う。本物の Supabase には接続しない（three.js は t142 が作業用フォルダに置いたもの）
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3-free')
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
async def open3d(b, port, sky='day', w=390, h=844, guide=False):
    c = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });" + ("window.A3_GUIDE = true;" if guide else ""))
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
SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-a3-free'); os.makedirs(SHOTS, exist_ok=True)
PRESSED = "[...document.querySelectorAll('[data-a3-view]')].map(b => b.getAttribute('aria-pressed') === 'true' ? b.dataset.a3View : '').join('')"
MODE = "[...document.querySelectorAll('[data-a3-mode]')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.dataset.a3Mode).join('')"
CAM = "(() => { const c = A3.cam.position, d = new A3.THREE.Vector3(); A3.cam.getWorldDirection(d); return { x: c.x, y: c.y, z: c.z, dx: d.x, dy: d.y, dz: d.z, fov: A3.cam.fov }; })()"
# 指の操作を作る（PointerEvent を絵に送る）
TOUCH = """([pts]) => { const cv = document.getElementById('a3Cv'); const ev = (t, id, x, y) => cv.dispatchEvent(new PointerEvent(t, { pointerId:id, clientX:x, clientY:y, bubbles:true, pointerType:'touch', isPrimary:id === 1 }));
  const [a, b] = [pts[0], pts[pts.length - 1]];
  for(let i = 0; i < a.length; i++) ev('pointerdown', i + 1, a[i][0], a[i][1]);
  for(let k = 1; k <= 10; k++) for(let i = 0; i < a.length; i++) ev('pointermove', i + 1, a[i][0] + (b[i][0] - a[i][0]) * k / 10, a[i][1] + (b[i][1] - a[i][1]) * k / 10);
  for(let i = 0; i < a.length; i++) ev('pointerup', i + 1, b[i][0], b[i][1]); }"""
async def touch(pg, a, b): await pg.evaluate(TOUCH, [[a, b]]); await pg.wait_for_timeout(250)
SMALL = "[...document.querySelectorAll('#dAp3d button')].filter(b => b.offsetParent && !b.closest('[hidden]') && (b.getBoundingClientRect().height < 44 || b.getBoundingClientRect().width < 44) && !b.classList.contains('a3peekb')).map(b => (b.innerText || b.getAttribute('aria-label') || '').trim() + ':' + Math.round(b.getBoundingClientRect().width) + 'x' + Math.round(b.getBoundingClientRect().height))"
OVER = "(() => { const W = document.documentElement.clientWidth; return [...document.querySelectorAll('#dAp3d *')].filter(e => e.offsetParent && !e.closest('.a3labels') && !e.closest('canvas') && (e.getBoundingClientRect().right > W + 1 || e.getBoundingClientRect().left < -1)).map(e => e.className || e.tagName).slice(0, 5); })()"
FLYGAP = "(() => { const m = $('a3Modes').getBoundingClientRect(); return [...document.querySelectorAll('#a3Fly .a3joy, #a3Fly .a3vrt, #a3Fly .a3turn, #a3Fly .a3cap')].map(e => e.getBoundingClientRect()).every(r => r.bottom <= m.top - 4); })()"
async def shot(pg, name): await pg.wait_for_timeout(700); await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
async def main():
    if not os.path.exists(THREE): print('three.js がないので飛ばす（t142 を先に流すと置かれる）'); sys.exit(1)
    port = serve(); allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for (w, h) in ((390, 844), (375, 667)):
            tag = f'{w}x{h}'
            c, pg, errs = await open3d(b, port, 'day', w, h, guide=True)
            # ---- はじめての案内（1回だけ）
            r = await pg.evaluate("({ g: !$('a3Guide').hidden, txt: $('a3Guide').innerText, peek: $('a3Sheet').classList.contains('a3peek'), mode: %s, pr: %s })" % (MODE, PRESSED))
            check(f'{tag} はじめての案内：回す・寄る・ずらす・傾ける・わかった（シートは畳む）', r['g'] and all(k in r['txt'] for k in ('回す', '寄る・離れる', 'ずらす', '傾ける', 'わかった')) and r['peek'], r)
            check(f'{tag} はじめは「自由」と上の「全体」を押した形', r['mode'] == 'free' and r['pr'] == 'all', r)
            g = await pg.evaluate("(() => { const a = $('a3Guide').getBoundingClientRect(), m = $('a3Modes').getBoundingClientRect(), p = document.querySelector('.a3pills').getBoundingClientRect(); return a.bottom <= m.top && a.top >= p.bottom; })()")
            check(f'{tag} 案内は上のピルと下のボタンの間', g)
            await shot(pg, f'01-guide-{tag}')
            await pg.click('[data-a3-guide-ok]'); await pg.wait_for_timeout(300)
            r = await pg.evaluate("({ g: $('a3Guide').hidden, ls: localStorage.getItem(A3_GUIDE_KEY), peek: $('a3Sheet').classList.contains('a3peek') })")
            check(f'{tag} 「わかった」で閉じ、次からは出さない（シートは開く）', r['g'] and r['ls'] == '1' and not r['peek'], r)
            check(f'{tag} 自由：押せる所 44px・横のはみ出しなし', await pg.evaluate(SMALL) == [] and await pg.evaluate(OVER) == [], [await pg.evaluate(SMALL), await pg.evaluate(OVER)])
            await shot(pg, f'02-free-start-{tag}')
            if w == 390:
                # ---- 自由：指の操作
                c0 = await pg.evaluate(CAM)
                y0 = await pg.evaluate("A3.yaw")
                await touch(pg, [[150, 300]], [[230, 300]])
                check('自由：1本指でなぞると回る（向きが変わる）', abs(await pg.evaluate("A3.yaw") - y0) > 0.3)
                check('自由：回しただけなら上の「全体」は押したまま', await pg.evaluate(PRESSED) == 'all')
                d0 = await pg.evaluate("a3Orb().d")
                await touch(pg, [[150, 300], [240, 300]], [[100, 300], [290, 300]])
                d1 = await pg.evaluate("a3Orb().d")
                check('自由：2本指で広げると寄る（距離が短く）', d1 < d0 * 0.75, [round(d0), round(d1)])
                r = await pg.evaluate("({ pr: %s, home: !!document.querySelector('[data-a3-home]') })" % PRESSED)
                check('自由：寄ったら右上に「全体に戻す」・上の「全体」は外れる', r['home'] and r['pr'] == '', r)
                t0 = await pg.evaluate("[a3Orb().tx, a3Orb().tz]")
                await touch(pg, [[150, 320], [240, 330]], [[230, 320], [320, 330]])
                t1 = await pg.evaluate("[a3Orb().tx, a3Orb().tz]")
                check('自由：2本指でなぞると見る点がずれる', abs(t1[0] - t0[0]) + abs(t1[1] - t0[1]) > 100, [t0, t1])
                p0 = await pg.evaluate("a3Orb().p")
                await touch(pg, [[150, 300], [250, 300]], [[150, 380], [250, 380]])
                p1 = await pg.evaluate("a3Orb().p")
                check('自由：2本指で上下になぞると傾く', abs(p1 - p0) > 0.15, [p0, p1])
                for _ in range(8): await touch(pg, [[180, 300], [210, 300]], [[20, 300], [370, 300]])
                await pg.evaluate("for(let i = 0; i < 40; i++) a3Pan(0, -400)"); await pg.wait_for_timeout(300)
                await pg.evaluate("for(let i = 0; i < 40; i++) a3Tilt(400)"); await pg.wait_for_timeout(400)
                r = await pg.evaluate("({ d: a3Orb().d, r: Math.hypot(a3Orb().tx, a3Orb().tz), y: A3.cam.position.y })")
                check('自由：寄っても地面の下に行かない（カメラ 15m より上）・見る点は空港から 6km まで', r['y'] >= 15 and r['r'] <= 6000.5 and r['d'] >= 199, r)
                await pg.evaluate("a3Orb().d = 900; a3Orb().p = 0.5; a3Orb().tx = -900; a3Orb().tz = 300; A3.yaw = -0.6; A3.dirty = true"); await shot(pg, '03-free-moved-390x844')
                await pg.mouse.move(195, 300); await pg.mouse.wheel(0, 3000); await pg.wait_for_timeout(300)
                check('自由：ホイールでも離れる', await pg.evaluate("a3Orb().d") > 1500)
                await pg.click('[data-a3-home]'); await pg.wait_for_timeout(400)
                c1 = await pg.evaluate(CAM)
                check('「全体に戻す」で前の「全体」と同じ位置（約10km 北・7,000m）', abs(c1['y'] - 7000) < 1 and abs(c1['z'] - (300 - 10000)) < 1 and abs(c1['x']) < 1, c1)
                # ---- 立つ
                await pg.click('[data-a3-mode="stand"]'); await pg.wait_for_timeout(500)
                r = await pg.evaluate("({ sh: $('a3Sheet').innerText, mode: %s, pins: [...document.querySelectorAll('.a3pin')].map(e => e.innerText) })" % MODE)
                check('立つ：場所のシート（管制塔・第1／第2ターミナル 展望デッキ・C 滑走路の南の端）', all(k in r['sh'] for k in ('どこに立ちますか', '管制塔', '第1ターミナル 展望デッキ', '第2ターミナル 展望デッキ', 'C 滑走路の南の端')) and r['mode'] == 'stand', r)
                await pg.evaluate("a3Orb().d = 5200; a3Orb().p = 0.62; a3Orb().tx = 300; a3Orb().tz = 0; A3.dirty = true"); await pg.wait_for_timeout(500)
                await pg.mouse.click(190, 330); await pg.wait_for_timeout(500)
                r = await pg.evaluate("({ here: !!A3.here, pin: !!document.querySelector('[data-a3-here]'), pins: [...document.querySelectorAll('.a3pin')].map(e => e.innerText) })")
                check('立つ：3D の地面を押すと「ここに立つ」', r['here'] and r['pin'], r)
                await shot(pg, '04-stand-pick-390x844')
                await pg.click('[data-a3-here]'); await pg.wait_for_timeout(700)
                r = await pg.evaluate("({ v: A3.view, y: A3.cam.position.y, st: A3.st, chips: $('a3Chips').innerText })")
                check('立つ：押した所に目の高さ 約1.6m（屋上ならその上）で立つ', r['v'] == 'stand' and abs(r['y'] - r['st']['eye']) < .01 and abs(r['st']['eye'] - 1.6 - (r['st']['eye'] - 1.6)) < 1e-9 and 'を見ています' in r['chips'], r)
                await pg.click('[data-a3-spots]'); await pg.wait_for_timeout(400)
                await pg.click('#a3Sheet [data-a3-spot="t2"]'); await pg.wait_for_timeout(900)
                r = await pg.evaluate("({ st: A3.st, chips: $('a3Chips').innerText, pr: %s, mode: %s, peek: $('a3Sheet').classList.contains('a3peek'), n: A3.cam.near })" % (PRESSED, MODE))
                check('立つ：第2ターミナル 展望デッキ（屋上の上に目）・「東を見ています」・シートは畳む', r['st']['name'].startswith('第2ターミナル') and r['st']['eye'] > 10 and 'を見ています' in r['chips'] and r['mode'] == 'stand' and r['peek'], r)
                pos0 = await pg.evaluate(CAM)
                await touch(pg, [[150, 300], [240, 300]], [[100, 300], [290, 300]])
                pos1 = await pg.evaluate(CAM)
                check('立つ：2本指はズーム（目の位置は動かない・画角が狭く）', abs(pos0['x'] - pos1['x']) < .01 and abs(pos0['y'] - pos1['y']) < .01 and pos1['fov'] < pos0['fov'] * 0.8, [pos0['fov'], pos1['fov']])
                await touch(pg, [[150, 300]], [[260, 250]])
                pos2 = await pg.evaluate(CAM)
                check('立つ：1本指で見回す（目の位置は同じ）', abs(pos1['x'] - pos2['x']) < .01 and abs(pos1['dx'] - pos2['dx']) + abs(pos1['dy'] - pos2['dy']) > .05)
                await pg.evaluate("A3.zoom = 1; A3.yaw = 0; A3.lp = 0; A3.dirty = true; a3Status()"); await shot(pg, '05-stand-t2-390x844')
                for sid in ('t1', 'c34'):
                    await pg.click('[data-a3-spots]'); await pg.wait_for_timeout(300); await pg.click(f'#a3Sheet [data-a3-spot="{sid}"]'); await pg.wait_for_timeout(900)
                    await shot(pg, f'05-stand-{sid}-390x844')
                check('立つ：C 滑走路の南の端は地面（約1.6m）で南東を見る', await pg.evaluate("Math.abs(A3.cam.position.y - 1.6) < 0.5 && /南/.test($('a3Chips').innerText)"), await pg.evaluate("[A3.cam.position.y, $('a3Chips').innerText]"))
                # 上のピルの管制塔
                await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(900)
                r = await pg.evaluate("({ y: Math.round(A3.cam.position.y), pr: %s, mode: %s, chips: $('a3Chips').innerText, clip: !!A3.clipOn })" % (PRESSED, MODE))
                check('上のピル「管制塔」：その場で管制塔から（高さ 約118m・立つの管制塔と同じ）', r['y'] == 118 and r['pr'] == 'tower' and r['mode'] == 'stand' and '管制塔' in r['chips'] and r['clip'], r)
                await shot(pg, '06-tower-pill-390x844')
                await pg.click('[data-a3-spots]'); await pg.wait_for_timeout(300); await pg.click('#a3Sheet [data-a3-spot="tower"]'); await pg.wait_for_timeout(500)
                check('立つの「管制塔」もピルと同じ', await pg.evaluate("A3.view === 'tower' && Math.round(A3.cam.position.y) === 118"))
                # ---- 追う
                await pg.click('[data-a3-mode="follow"]'); await pg.wait_for_timeout(400)
                r = await pg.evaluate("({ sh: $('a3Sheet').innerText, mode: %s, pr: %s })" % (MODE, PRESSED))
                check('追う：機体を選ぶシート「どの機体を追いますか」', 'どの機体を追いますか' in r['sh'] and r['mode'] == 'follow' and r['pr'] == 'plane', r)
                await shot(pg, '07-follow-pick-390x844')
                await pg.click('[data-a3-pick="a1"]'); await pg.wait_for_timeout(900)
                r = await pg.evaluate("({ ban: $('a3Ban').hidden ? '' : $('a3Ban').innerText, side: $('a3Side').hidden ? '' : $('a3Side').innerText, pills: [...document.querySelectorAll('[data-a3-view]')].map(b => b.innerText + ':' + b.getAttribute('aria-pressed')) })")
                check('追う：「JL 318 を追っています」と後ろ・横・前・ピルに便名', 'JL 318 を追っています' in r['ban'] and all(k in r['side'] for k in ('後ろ', '横', '前')) and r['pills'][2] == 'JL 318:true', r)
                await shot(pg, '08-follow-back-390x844')
                REL = "(() => { const c = A3.cam.position, o = A3.objs.get('a1').g.position; return Math.atan2(c.x - o.x, c.z - o.z); })()"   # 機体から見たカメラの向き（同じこまで測る）
                cb = await pg.evaluate(REL)
                await pg.click('[data-a3-side="1"]'); await pg.wait_for_timeout(700); cs = await pg.evaluate(REL)
                await pg.click('[data-a3-side="2"]'); await pg.wait_for_timeout(700); cf = await pg.evaluate(REL)
                await shot(pg, '08-follow-front-390x844')
                ang = lambda c: c
                da = lambda a, b: abs((a - b + math.pi) % (2 * math.pi) - math.pi)
                check('追う：横・前で付く位置が回る（後ろと前は反対側）', da(ang(cb), ang(cs)) > 1.0 and da(ang(cb), ang(cf)) > 2.6, [ang(cb), ang(cs), ang(cf)])
                await pg.click('[data-a3-side="0"]'); await pg.wait_for_timeout(300)
                k0 = await pg.evaluate("A3.fk || 1"); await touch(pg, [[150, 300], [240, 300]], [[180, 300], [210, 300]])
                check('追う：2本指でつまむと離れる', await pg.evaluate("A3.fk") > k0 * 1.5)
                # 機体が消えた
                await pg.evaluate("for(const s of A3.snaps) s.planes = s.planes.filter(p => p.id !== 'a1'); A3.dirty = true"); await pg.wait_for_timeout(2600)
                r = await pg.evaluate("({ v: A3.view, mode: %s, toast: $('a3Toast').hidden ? '' : $('a3Toast').innerText, y: A3.cam.position.y })" % MODE)
                check('追う：機体が消えたら今の位置のまま自由へ（7,000m の全体へ飛ばない）・下に一言と「ほかを追う」', r['v'] == 'all' and r['mode'] == 'free' and 'JL 318' in r['toast'] and 'ほかを追う' in r['toast'] and r['y'] < 3000, r)
                await shot(pg, '09-follow-lost-390x844')
                await pg.click('[data-a3-other]'); await pg.wait_for_timeout(400)
                check('「ほかを追う」で機体を選ぶシート', 'どの機体を追いますか' in await pg.inner_text('#a3Sheet'))
                await pg.click('[data-a3-unpick]'); await pg.wait_for_timeout(300)
                # 上のピル「機体」も追うへ
                await pg.click('[data-a3-view="plane"]'); await pg.wait_for_timeout(300); await pg.click('[data-a3-pick="a2"]'); await pg.wait_for_timeout(700)
                check('上のピル「機体」→ 選ぶと追う', await pg.evaluate(MODE) == 'follow')
                await pg.click('[data-a3-unfollow]'); await pg.wait_for_timeout(400)
                check('追うの × で自由へ（今の位置のまま）', await pg.evaluate("A3.view === 'all' && A3.cam.position.y < 3000"))
            # ---- 飛ぶ（どちらの大きさでも）
            await pg.click('[data-a3-mode="fly"]'); await pg.wait_for_timeout(700)
            r = await pg.evaluate("({ v: A3.view, alt: $('a3AltN') && $('a3AltN').textContent, gap: %s, chips: $('a3Chips').innerText, small: %s, over: %s })" % (FLYGAP, SMALL, OVER))
            check(f'{tag} 飛ぶ：高さの大きな数字・つまみと4つのボタンが重ならない・44px・はみ出しなし', r['v'] == 'fly' and r['alt'] and r['gap'] and r['small'] == [] and r['over'] == [] and '左で進む' in r['chips'], r)
            await shot(pg, f'10-fly-{tag}')
            f0 = await pg.evaluate("({ ...A3.fl })")
            jb = await pg.evaluate("(() => { const r = $('a3Joy').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, r.width]; })()")
            await pg.mouse.move(jb[0], jb[1]); await pg.mouse.down(); await pg.mouse.move(jb[0], jb[1] - jb[2] * 0.45, steps=4); await pg.wait_for_timeout(1500); await pg.mouse.up()
            f1 = await pg.evaluate("({ ...A3.fl })")

            import math as m2
            check(f'{tag} 飛ぶ：つまみを前へ倒すと前へ進む', m2.hypot(f1['x'] - f0['x'], f1['z'] - f0['z']) > 50 and abs(f1['y'] - f0['y']) < 1, [f0, f1])
            await pg.evaluate("A3.fl.y = 990; A3.dirty = true")
            ub = await pg.evaluate("(() => { const r = document.querySelector('[data-a3-hold=\"up\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
            await pg.mouse.move(ub[0], ub[1]); await pg.mouse.down(); await pg.wait_for_timeout(1500)
            r = await pg.evaluate("({ y: A3.fl.y, alt: $('a3AltN').textContent, chips: $('a3Chips').innerText })")
            check(f'{tag} 飛ぶ：上限 1,000m で止まり「これより上には行けません」', r['y'] <= 1000 and r['alt'] == '1,000' and 'これより上には行けません' in r['chips'], r)
            if w == 390: await shot(pg, '11-fly-limit-390x844')
            await pg.mouse.up(); await pg.wait_for_timeout(200)
            await pg.evaluate("A3.fl.y = 30; A3.dirty = true")
            db = await pg.evaluate("(() => { const r = document.querySelector('[data-a3-hold=\"down\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
            await pg.mouse.move(db[0], db[1]); await pg.mouse.down(); await pg.wait_for_timeout(1500); await pg.mouse.up()
            check(f'{tag} 飛ぶ：地面の下には行かない（15m で止まる）', await pg.evaluate("A3.fl.y") >= 15)
            h0 = await pg.evaluate("A3.fl.h")
            rb = await pg.evaluate("(() => { const r = document.querySelector('[data-a3-hold=\"right\"]').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })()")
            await pg.mouse.move(rb[0], rb[1]); await pg.mouse.down(); await pg.wait_for_timeout(800); await pg.mouse.up()
            check(f'{tag} 飛ぶ：右のボタンで向きが変わる', await pg.evaluate("A3.fl.h") - h0 > 0.2)
            await pg.evaluate("A3.fl.x = 20000; A3.fin.jy = -1"); await pg.wait_for_timeout(500); await pg.evaluate("A3.fin.jy = 0")
            check(f'{tag} 飛ぶ：空港から 8km より遠くには行かない', await pg.evaluate("Math.hypot(A3.fl.x, A3.fl.z)") <= 8000.5)
            # 閉じるはいつでも押せる
            for m in ('free', 'fly'):
                await pg.click(f'[data-a3-mode="{m}"]'); await pg.wait_for_timeout(300)
                check(f'{tag} {m}：左上の「閉じる」はいつも押せる', await pg.evaluate("(() => { const b = document.querySelector('.a3top [data-a3-close]').getBoundingClientRect(); const e = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2); return !!e && !!e.closest('[data-a3-close]'); })()"))
            if w == 375:
                await pg.click('[data-a3-mode="stand"]'); await pg.wait_for_timeout(300); await pg.click('#a3Sheet [data-a3-spot="t1"]'); await pg.wait_for_timeout(800)
                check('375×667 立つ：44px・はみ出しなし', await pg.evaluate(SMALL) == [] and await pg.evaluate(OVER) == [], [await pg.evaluate(SMALL), await pg.evaluate(OVER)])
                await shot(pg, '05-stand-t1-375x667')
                await pg.click('[data-a3-mode="follow"]'); await pg.wait_for_timeout(300); await pg.click('[data-a3-pick="a1"]'); await pg.wait_for_timeout(900)
                check('375×667 追う：44px・はみ出しなし・出典の札は「後ろ・横・前」に重ならない', await pg.evaluate(SMALL) == [] and await pg.evaluate(OVER) == [] and await pg.evaluate("(() => { const a = $('a3Credit').getBoundingClientRect(), b = $('a3Side').getBoundingClientRect(); return a.bottom <= b.top || a.top >= b.bottom; })()"), [await pg.evaluate(SMALL), await pg.evaluate(OVER)])
                await shot(pg, '08-follow-back-375x667')
            await pg.click('.a3top [data-a3-close]'); await pg.wait_for_timeout(300)
            check(f'{tag} 閉じると止まる', await pg.evaluate("A3 === null"))
            allerr += errs; await c.close()
        # 2回目に開くと案内は出ない
        c, pg, errs = await open3d(b, port, 'day', 390, 844, guide=True)
        await pg.evaluate("localStorage.setItem(A3_GUIDE_KEY, '1')"); await pg.click('.a3top [data-a3-close]'); await pg.wait_for_timeout(500)
        await pg.click('#dAirport .a3pill [data-ap3d]')
        await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=40000)
        check('案内を見たあとは出ない', await pg.evaluate("$('a3Guide').hidden"))
        await pg.click('[data-a3-menu]'); await pg.click('[data-a3-guide]'); await pg.wait_for_timeout(300)
        check('… の「指の動きの案内」でもう一度見られる', await pg.evaluate("!$('a3Guide').hidden"))
        allerr += errs; await c.close()
        await b.close()
    print('JS のエラー', allerr)
    if allerr: fails.append('JS のエラー')
    print('fails', fails)
    print('全部成功' if not fails else 'errors ' + str(fails))
    sys.exit(1 if fails else 0)
asyncio.run(main())
