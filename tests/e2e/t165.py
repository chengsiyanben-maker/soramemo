import os, sys, json, shutil, asyncio, threading, functools, http.server, math, random
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D に地上の機体・見やすく（PM 11/22 18時55分・checkin/a3-ground）
#   地上の機体：答えの ground（駐機場・誘導路・滑走路の上）を向きどおりに置く。動いている機体は前に琥珀の矢印・夜は航空灯。止まっている機体は灯りなし
#   見やすく：見た目の大きさの下限（空 約22px・地上 約8px）／札は近い順に重ならないように・押すと選ぶ・13px 以上／地上は札なし（押した機体だけ）
#             夜は胴を少し光らせる／下の一覧に「地上 ○機」を分ける／地上が多いとき全体の視点の地上機は胴だけ
#   A3_WEB に別の web（本番の写し）を渡すと、同じ場面の比べ写真だけ撮る（その web には ground を返さない＝今の本番の関数）
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.abspath(os.environ.get('A3_WEB') or os.path.join(HERE, '..', '..', 'web')); COMPARE = bool(os.environ.get('A3_WEB'))
WORK = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'a3ground' + ('-old' if COMPARE else ''))
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-a3-ground')); os.makedirs(SHOTS, exist_ok=True)
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
now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
def pl(i, cs, lat, lon, alt, kt, hdg, fpm, ph, dist, typ, reg): return {'id': i, 'callsign': cs, 'lat': lat, 'lon': lon, 'alt_ft': alt, 'kt': kt, 'hdg': hdg, 'fpm': fpm, 'phase': ph, 'dist_km': dist, 'type': typ, 'reg': reg, 'trail': []}
P = [pl('a1', 'JAL318', 35.512, 139.8340, 1300, 145, 337, -700, 'arr', 6, 'A359', 'JA01XJ'),
     pl('a2', 'ANA59', 35.585, 139.7560, 2600, 190, 337, 2200, 'dep', 4, 'B789', 'JA871A'),
     pl('a3', 'SKY12', 35.505, 139.8420, 1700, 150, 337, -700, 'arr', 7, 'B738', 'JA73NG'),
     pl('a8', 'ANA12', 35.470, 139.900, 4200, 220, 320, -900, 'arr', 15, 'B77W', 'JA781A')]
# 地上：形のファイル（3d/hnd.json）の駐機場の中で、建物にかからない所に80m おきに止まっている機体と、動いている3機
random.seed(7); TYPES = ['B788', 'B789', 'B763', 'B738', 'A359', 'B772', 'A321', 'B38M', 'B77W', 'A320']
SH = json.load(open(os.path.join(WEB, '3d', 'hnd.json')))
def inside(x, z, poly):
    c = False; n = len(poly) // 2
    for i in range(n):
        x1, z1, x2, z2 = poly[2 * i], poly[2 * i + 1], poly[2 * ((i + 1) % n)], poly[2 * ((i + 1) % n) + 1]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1: c = not c
    return c
BLD = [b[2:] for b in SH['bld']]
def ll(x, z): return round(35.5533 - z / 110574, 5), round(139.7811 + x / (111320 * math.cos(math.radians(35.5533))), 5)
spots = []
for poly in SH['apron']:
    xs, zs = poly[0::2], poly[1::2]
    for x in range(int(min(xs)) + 40, int(max(xs)), 110):
        for z in range(int(min(zs)) + 40, int(max(zs)), 110):
            if inside(x, z, poly) and not any(inside(x + dx, z + dz, b) for b in BLD for dx, dz in ((0, 0), (30, 0), (-30, 0), (0, 30), (0, -30))): spots.append((x, z))
random.shuffle(spots); spots = sorted(spots[:38])
G = []
for j, (x, z) in enumerate(spots):
    lat, lon = ll(x, z)
    G.append({'id': f'g{j:02d}', 'callsign': f"{['JAL', 'ANA', 'SKY', 'SFJ'][j % 4]}{100 + j}", 'lat': lat, 'lon': lon, 'hdg': [120, 300, 210, 30][j % 4], 'kt': 0,
              'type': TYPES[j % len(TYPES)], 'reg': f'JA{800 + j}A', 'dist_km': round(math.hypot(x, z) / 1000, 1)})
G[0]['hdg'] = 120
G += [{'id': 'm1', 'callsign': 'JAL501', 'lat': 35.5440, 'lon': 139.7895, 'hdg': 340, 'kt': 15, 'type': 'B763', 'reg': 'JA602J', 'dist_km': 1.1},
      {'id': 'm2', 'callsign': 'ANA265', 'lat': 35.5575, 'lon': 139.7750, 'hdg': 160, 'kt': 22, 'type': 'B788', 'reg': 'JA801A', 'dist_km': 0.6},
      {'id': 'm3', 'callsign': 'APJ801', 'lat': 35.5380, 'lon': 139.7740, 'hdg': 50, 'kt': 9, 'type': 'A320', 'reg': 'JA01VA', 'dist_km': 2.0}]
MOVING = {'m1', 'm2', 'm3'}
def mv(p, s):
    if p['alt_ft'] < 300: return dict(p)
    m = p['kt'] * 0.5144 * s; h = math.radians(p['hdg']); q = dict(p)
    q['lat'] += math.cos(h) * m / 110574; q['lon'] += math.sin(h) * m / (111320 * math.cos(math.radians(p['lat']))); q['alt_ft'] = max(0, p['alt_ft'] + p['fpm'] * s / 60); return q
def gmv(g, s):
    q = dict(g); m = g['kt'] * 0.5144 * s; h = math.radians(g['hdg'])
    q['lat'] = g['lat'] + math.cos(h) * m / 110574; q['lon'] = g['lon'] + math.sin(h) * m / (111320 * math.cos(math.radians(g['lat']))); return q
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [{'no': 'JL318', 'place': 'FUK', 'time': '15:40', 'kind': 'ok'}], 'dep': [{'no': 'JL501', 'place': 'CTS', 'time': '15:50', 'kind': 'ok'}]}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def open3d(b, sky, ground=True):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
    n = {'t': 0}
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        if name == 'airport-traffic':
            n['t'] += 1; first = n['t'] == 1
            body = {'iata': 'HND', 'at': iso(-90 if first else -30), 'source': 'adsb.lol', 'planes': [mv(x, -60) for x in P] if first else P}
            if ground: body['ground'] = [gmv(g, -60) for g in G] if first else G
        elif name == 'airport-now': body = NOWD
        else: body = {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    if sky == 'night': await pg.evaluate("document.documentElement.dataset.night = 'on'")
    await pg.evaluate("s => { a3Night = () => s; }", sky)
    await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(600)
    await pg.click('#dAirport .a3pill [data-ap3d]')
    await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=30000)
    await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(500); await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1800)
    return c, pg, errs

async def shots(b, tag, ground):
    for sky in ('day', 'night'):
        c, pg, errs = await open3d(b, sky, ground)
        await pg.evaluate("A3.yaw = 0; A3.view = 'all'; A3.dirty = true"); await pg.wait_for_timeout(600)
        await pg.screenshot(path=os.path.join(SHOTS, f'{tag}-all-{sky}.png'))
        await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(700)
        await pg.screenshot(path=os.path.join(SHOTS, f'{tag}-tower-{sky}.png'))
        await c.close()

async def main():
    if not os.path.exists(THREE): print('three.js がないので画面の確かめは飛ばす（t142 を先に流すと置かれる）'); return
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        if COMPARE:   # 今の本番（ground を返さない関数）の比べ写真だけ
            await shots(b, 'old', False); await b.close(); return
        allerr = []
        c, pg, errs = await open3d(b, 'day')
        r = await pg.evaluate("""(() => { const gs = [...A3.objs.values()].filter(o => !a3Air(o.p));
          const o = A3.objs.get('g00'), m = A3.objs.get('m1');
          return { n: gs.length, rot: Math.round(-o.g.rotation.y / D2R), rotM: Math.round(((-m.g.rotation.y / D2R) % 360 + 360) % 360),
            arrowM: m.mv && m.mv.visible, arrowS: o.mv && o.mv.visible, txt: document.getElementById('a3Sheet').innerText }; })()""")
        check(f'地上の機体を全部置く（{len(G)}機）・向きは trk どおり', r['n'] == len(G) and r['rot'] == 120 and r['rotM'] == 340, (r['n'], r['rot'], r['rotM']))
        check('動いている機体だけ前に矢印（止まっている機体には出さない）', r['arrowM'] and not r['arrowS'], (r['arrowM'], r['arrowS']))
        check('「地上の機体はまだ出ません」の文は消えた', 'まだ出ません' not in r['txt'], '')
        hd = (await pg.evaluate("document.querySelector('#a3Sheet .a3sh .n').innerText")).replace('\n', ' ')
        check('下の一覧の頭に「空 ○機・地上 ○機」を分けて出す', hd.replace(' ', '') == f'空4機地上{len(G)}機', hd)
        r = await pg.evaluate("""(() => { const h = document.querySelector('.a3gh'); const rows = [...document.querySelectorAll('.a3glist [data-a3-pick]')].map(b => b.dataset.a3Pick);
          return { h: h && h.innerText.replace(/\\s+/g, ' '), first: rows.slice(0, 3), n: rows.length, air: document.querySelectorAll('.a3list:not(.a3glist) [data-a3-pick]').length }; })()""")
        check('地上の一覧は動いている機体が先（m2・m1・m3 の近い順）・6行まで・空の一覧は着陸と離陸の4機', r['first'] == ['m2', 'm1', 'm3'] and r['n'] == 6 and r['air'] == 4 and '動いている 3機' in (r['h'] or ''), r)
        r = await pg.evaluate("[...document.querySelectorAll('.a3glist .st b')].slice(0, 4).map(e => e.textContent)")
        check('地上の行の様子：「地上を移動中」と「止まっている」', r[:3] == ['地上を移動中'] * 3 and r[3] == '止まっている', r)
        # 見た目の大きさの下限（全体の視点）
        await pg.evaluate("A3.yaw = 0; A3.view = 'all'; A3.dirty = true"); await pg.wait_for_timeout(500)
        r = await pg.evaluate("""(() => { const T = A3.THREE, H = document.getElementById('a3Stage').clientHeight;
          const px = id => { const o = A3.objs.get(id), cam = A3.cam, d = cam.position.distanceTo(o.g.position); return o.g.scale.x / (2 * Math.tan(cam.fov * D2R / 2) * d / H); };
          return { air: Math.round(px('a8')), gnd: Math.round(px('g00') * 10) / 10, simple: !A3.objs.get('g00').g.getObjectByName('dark').visible, calls: A3.r.info.render.calls }; })()""")
        check('全体の視点：遠い空の機体は約22px・地上の機体は約8px より小さくしない', 21 <= r['air'] <= 40 and 7.5 <= r['gnd'] <= 12, r)
        check('地上が多いときは全体の視点の地上機を胴だけにする（描く数を減らす）', r['simple'], r['calls'])
        # 札：地上は出さない・13px 以上・重ならない・押すと選ぶ
        r = await pg.evaluate("""(() => { const t = [...document.querySelectorAll('#a3Labels .a3tag')]; const bx = t.map(e => e.getBoundingClientRect());
          let ov = 0; for(let i = 0; i < bx.length; i++) for(let j = i + 1; j < bx.length; j++){ const a = bx[i], b = bx[j]; if(a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top) ov++; }
          return { ids: t.map(e => e.dataset.a3Tag), fs: Math.min(...t.map(e => parseFloat(getComputedStyle(e).fontSize))), ov, pe: t.length ? getComputedStyle(t[0]).pointerEvents : '' }; })()""")
        check('札は空の機体だけ（地上の機体には出さない）・字は13px 以上・重ならない', r['ids'] and not any(i.startswith(('g', 'm')) for i in r['ids']) and r['fs'] >= 13 and r['ov'] == 0, r)
        tag = r['ids'][0]
        await pg.evaluate("id => document.querySelector(`#a3Labels [data-a3-tag=\"${id}\"]`).click()", tag); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ sel: A3.sel, card: A3.card, fl: (document.querySelector('#a3Sheet .a3fl') || {}).textContent })")
        check('札を押すとその機体を選び、下のシートも同じ機体のカードになる', r['sel'] == tag and r['card'] and r['fl'], r)
        await pg.click('[data-a3-uncard]'); await pg.wait_for_timeout(300)
        # 地上の機体を押すと便名の札が出る
        await pg.click('.a3glist [data-a3-pick="m2"]'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("({ tag: (document.querySelector('#a3Labels [data-a3-tag=\"m2\"]') || {}).textContent, now: [...document.querySelectorAll('#a3Sheet .a3grid b')].map(e => e.textContent).join('|') })")
        check('地上の機体は押した時だけ便名の札（「NH 265 地上」）・カードに移動中と速さ', r['tag'] and '265' in r['tag'] and '地上' in r['tag'] and '地上を移動中' in r['now'], r)
        await pg.screenshot(path=os.path.join(SHOTS, 'new-pick-ground-day.png'))
        # 管制塔の視点では細かい形に戻る
        await pg.click('[data-a3-uncard]'); await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(500)
        r = await pg.evaluate("A3.objs.get('g00').g.getObjectByName('dark').visible")
        check('管制塔の視点では地上機も細かい形', r, r)
        r = await pg.evaluate("(() => { const o = A3.objs.get('g00'), b = new A3.THREE.Box3().setFromObject(o.g); return Math.round(b.min.y * 10) / 10; })()")
        check('大きく見せても地上の機体は車輪が地面に着く高さ', -1 <= r <= 2, r)
        # はみ出しなし
        r = await pg.evaluate("document.querySelector('#a3Sheet').scrollWidth <= document.querySelector('#a3Sheet').clientWidth + 1")
        check('下のシートは横にはみ出さない', r, r)
        allerr += errs; await c.close()
        # 夜：胴を少し光らせる・止まっている機体は灯りなし・動いている機体は航空灯
        c, pg, errs = await open3d(b, 'night')
        r = await pg.evaluate("""(() => { const v = (id, n) => { const o = A3.objs.get(id).g.getObjectByName(n); return !!o && o.visible; };
          return { em: A3.pm.body.emissive.getHex(), stopped: v('g00', 'acl'), moving: v('m1', 'acl'), air: v('a1', 'acl'), arrowCol: A3.mvM.color.getHex() }; })()""")
        check('夜：胴を少し光らせる（輪郭が背景から浮く）', r['em'] > 0x202020, hex(r['em']))
        check('夜：止まっている地上機は灯りなし・動いている地上機と空の機体は航空灯', not r['stopped'] and r['moving'] and r['air'], r)
        allerr += errs; await c.close()
        # 写真（新しい版）
        await shots(b, 'new', True)
        # 重さの目安：全体の視点で地上の機体が多いときのとき、1こまにかかる時間（swiftshader なので実機より遅い。比べるための数）
        c, pg, errs = await open3d(b, 'day')
        r = await pg.evaluate("""(() => { const t0 = performance.now(); for(let i = 0; i < 20; i++){ const ps = a3Planes(); a3Sync(ps); A3.r.render(A3.scene, A3.cam); } return { ms: Math.round((performance.now() - t0) / 20), calls: A3.r.info.render.calls }; })()""")
        print('参考：全体の視点・地上の機体が多いときの1こま', r)
        allerr += errs; await c.close()
        await b.close()
    check('JS のエラーなし', not allerr, allerr[:3])
asyncio.run(main())
srv.shutdown()
print('fails', fails)
