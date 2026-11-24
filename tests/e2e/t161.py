import os, sys, json, gzip, shutil, asyncio, threading, functools, http.server, math
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D をもっとリアルに（PM 11/21 17時15分・checkin/a3-real）
#   建物：PLATEAU（大田区 2025・川崎市 2022。外形と計測高さ）で空港の建物と海沿いの街を立体に。屋根と壁の色を分ける（用途ごと）
#   地面：舗装の色むら・タイヤの跡・芝と陸の色むら・海の照り返し。三角の表の向きをそろえる（裏向きで黒く見えていた）
#   機体：機種ごとの形（787・777・A350・737・A320 など）・窓の帯・翼の先・脚（地上と着陸の前だけ）。会社の色やロゴなし
#   空：薄い雲（空港の上は空ける）・夜の星・街の灯り・駐機場の照明・夜のターミナルは壁（窓）だけ灯す
#   地上の機体：答えに ground があれば出す（データ担当への依頼の先取り）
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'a3srv')
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-a3-real')); os.makedirs(SHOTS, exist_ok=True)
THREE = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'three-0.160.0.module.min.js')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)


# ---- 形のファイル ----
shape_path = os.path.join(WEB, '3d', 'hnd.json')
S = json.load(open(shape_path, encoding='utf-8'))
check('形のファイル：PLATEAU の出典（大田区・川崎市・国土交通省・加工して作成）と利用条件', 'PLATEAU' in S.get('attribution', '') and '大田区' in S['attribution'] and '川崎市' in S['attribution'] and '加工して作成' in S['attribution'] and 'PDL1.0' in S.get('plateau', ''))
check('形のファイル：街の建物2万棟以上（用途 0・1・2）・空港の建物はターミナル3つ以上', len(S.get('city', [])) >= 20000 and {c[0] for c in S['city']} == {0, 1, 2} and sum(1 for b in S['bld'] if b[0] == 't') >= 3, (len(S.get('city', [])), len(S['bld'])))
check('形のファイル：ターミナルの高さは PLATEAU の計測高さ（30m 以上のものがある）', any(b[0] == 't' and b[1] >= 30 for b in S['bld']))
# ---- 画面 ----
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
     pl('a4', 'ANA241', 35.5521, 139.7903, 0, 0, 45, 0, 'other', 1, 'B788', 'JA801A'),
     pl('a8', 'ANA12', 35.470, 139.900, 4200, 220, 320, -900, 'arr', 15, 'B77W', 'JA781A')]
def mv(p, s):
    if p['alt_ft'] < 300: return dict(p)
    m = p['kt'] * 0.5144 * s; h = math.radians(p['hdg']); q = dict(p)
    q['lat'] += math.cos(h) * m / 110574; q['lon'] += math.sin(h) * m / (111320 * math.cos(math.radians(p['lat']))); q['alt_ft'] = max(0, p['alt_ft'] + p['fpm'] * s / 60); return q
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [{'no': 'JL318', 'place': 'FUK', 'time': '15:40', 'kind': 'ok'}], 'dep': []}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def open3d(b, sky, h=844, noshape=False):
    c = await b.new_context(viewport={'width': 390, 'height': h}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")   # ふつうの端末として開く（試す機械は CPU が2つで、古い端末の軽い形になるため）
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
    n = {'t': 0}
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        if name == 'airport-traffic':
            n['t'] += 1; body = {'iata': 'HND', 'at': iso(-90 if n['t'] == 1 else -30), 'source': 'adsb.lol', 'planes': [mv(x, -60) for x in P] if n['t'] == 1 else P}
        elif name == 'airport-now': body = NOWD
        else: body = {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    if noshape: await c.route('**/3d/hnd.json', lambda r: r.abort())
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{PORT}/index.html')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    if sky == 'night': await pg.evaluate("document.documentElement.dataset.night = 'on'")
    await pg.evaluate("s => { a3Night = () => s; }", sky)
    await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(600)
    await pg.click('#dAirport .a3pill [data-ap3d]')
    await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=30000)
    await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1800)
    return c, pg, errs
GREEN = "document.getElementById('dAp3d').style.background = '#00ff00'"
async def green_px(pg, y0, y1):
    from PIL import Image; import io
    im = Image.open(io.BytesIO(await pg.screenshot(clip={'x': 0, 'y': y0, 'width': 390, 'height': y1 - y0}))).convert('RGB')
    d = im.tobytes(); return sum(1 for i in range(0, len(d), 3) if d[i + 1] > 200 and d[i] < 60 and d[i + 2] < 60)

GROUND = [{'id': 'g1', 'callsign': 'JAL501', 'lat': 35.5490, 'lon': 139.7845, 'alt_ft': None, 'kt': 0, 'hdg': 120, 'fpm': 0, 'phase': 'other', 'dist_km': 1, 'type': 'B763', 'reg': 'JA602J', 'trail': []}]
async def main():
    if not os.path.exists(THREE): print('three.js がないので画面の確かめは飛ばす（t142 を先に流すと置かれる）'); return
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        c, pg, errs = await open3d(b, 'day')
        r = await pg.evaluate("""(() => { const big = A3.scene.getObjectByName('cityBig'), sm = A3.scene.getObjectByName('citySmall');
          const cols = new Set(); const ca = big.geometry.attributes.color.array; for(let i = 0; i < Math.min(ca.length, 30000); i += 9) cols.add([ca[i], ca[i + 1], ca[i + 2]].map(v => Math.round(v * 255)).join(','));
          return { big: !!big, small: !!sm, tri: (big.geometry.attributes.position.count + sm.geometry.attributes.position.count) / 3, cols: cols.size, clouds: !!A3.scene.getObjectByName('clouds') }; })()""")
        check('街の建物（大きい・小さい）を立てる・屋根と壁の色がいろいろ・雲がある', r['big'] and r['small'] and r['tri'] > 200000 and r['cols'] >= 10 and r['clouds'], r)
        # 三角の表の向き：屋根と誘導路は上向き（両面で描いて黒く見えていた不具合の直し）
        r = await pg.evaluate("""(() => { const bad = (g, onlyUp) => { const P = g.attributes.position.array, N = g.attributes.normal.array; let n = 0, b = 0;
            for(let t = 0; t < P.length; t += 9){ if(onlyUp && N[t + 1] < 0.9) continue; const ax = P[t + 3] - P[t], ay = P[t + 4] - P[t + 1], az = P[t + 5] - P[t + 2], bx = P[t + 6] - P[t], by = P[t + 7] - P[t + 1], bz = P[t + 8] - P[t + 2];
              const cx = ay * bz - az * by, cy = az * bx - ax * bz, cz = ax * by - ay * bx; n++; if(cx * N[t] + cy * N[t + 1] + cz * N[t + 2] < 0) b++; } return [n, b]; };
          const twy = A3.scene.children.find(o => o.isMesh && o.material && o.material.side === A3.THREE.DoubleSide && o.position.y === 1);
          return { city: bad(A3.scene.getObjectByName('cityBig').geometry, false), twy: twy ? bad(twy.geometry, true) : null, plane: bad(a3Geo('787').body, false) }; })()""")
        check('三角の表の向きが法線とそろう（街・誘導路・機体の左右の翼）', r['city'][0] > 0 and r['city'][1] == 0 and r['twy'] and r['twy'][1] == 0 and r['plane'][1] == 0, r)
        r = await pg.evaluate("['B789','B77W','A359','B738','A20N','B763','B744','A388','B39M','A321','E190','DH8D'].map(a3Model).join(' ')")
        check('機種ごとの形（787・777・A350・737・A320・767・747・A380・E170/E190・Q400）', r == '787 777 350 737 320 767 747 380 737 320 e q4', r)
        r = await pg.evaluate("""(() => { const g = a3Geo('320'); const vis = id => { const o = A3.objs.get(id); if(!o) return false; const h = o.g.getObjectByName('gearHD'); return o.hd && h ? h.visible : o.g.getObjectByName('gear').visible; };   /* 11/23：細かい形のときはその脚（11/24 a3-hq：最高の質では近くなくても細かい形） */
          return { win: g.win.attributes.position.count, gearGround: vis('a4') || !!(A3.objs.get('a4').lo && A3.objs.get('a4').lo.visible),   /* 11/22：遠い地上の機体は平らな簡単な形（脚なし） */ gearClimb: vis('a2'), gearArr: vis('a1') }; })()""")
        check('窓の帯がある・脚は地上と着陸の前だけ（上昇中はしまう）', r['win'] > 30 and r['gearGround'] and r['gearArr'] and not r['gearClimb'], r)
        r = await pg.evaluate("""(() => { const rw = A3.scene.children.find(o => o.isMesh && o.geometry.type === 'PlaneGeometry' && o.name !== 'clouds' && o.material.map); const c = rw.material.map.image, g = c.getContext('2d'), d = g.getImageData(0, Math.floor(c.height * .5), 20, 200).data;
          let s = 0, s2 = 0, n = 0; for(let i = 0; i < d.length; i += 4){ s += d[i]; s2 += d[i] * d[i]; n++; } const m = s / n; return Math.sqrt(s2 / n - m * m); })()""")
        check('滑走路の舗装に色むら（色の散らばりがある）', r > 2.5, round(r, 2))
        await pg.evaluate("a3Quality(0)"); r = await pg.evaluate("[A3.scene.getObjectByName('citySmall').visible, A3.scene.getObjectByName('clouds').visible, A3.scene.getObjectByName('cityBig').visible]")
        check('いちばん軽い質では街の小さな建物と雲を隠す（大きな建物は残す）', r == [False, False, True], r)
        await pg.evaluate("a3Quality(2)")
        await pg.evaluate("id => a3Select(id, true)", 'a4'); await pg.wait_for_timeout(700)
        r = await pg.evaluate("Math.round(A3.cam.position.y - A3.objs.get('a4').g.position.y)")
        check('地上の機体の視点は屋根（約40m）より上から見下ろす', r >= 60, r)
        await pg.click('#a3Credit'); await pg.wait_for_timeout(300); src = await pg.inner_text('#a3Sheet')
        check('出典のシートに PLATEAU の利用条件のリンク・灯りは AIP JAPAN（AD 2.14）', await pg.locator('#a3Sheet a[href="https://www.mlit.go.jp/plateau/site-policy/"]').count() == 1 and '雲・星' in src and 'AD 2.14' in src)
        allerr += errs; await c.close()
        # 夜：街の灯り・星・駐機場の照明・ターミナルは壁だけ灯す
        c, pg, errs = await open3d(b, 'night')
        r = await pg.evaluate("""(() => { const cl = A3.scene.getObjectByName('cityLights'), st = A3.sky.getObjectByName('stars');
          const t = A3.scene.children.find(o => o.isMesh && Array.isArray(o.material) && o.material[1].emissive && o.material[1].emissive.getHex() !== 0);
          return { lights: cl ? cl.geometry.attributes.position.count : 0, stars: st ? st.geometry.attributes.position.count : 0, termRoof: t ? t.material[0].emissive.getHex() : -1, termWall: t ? t.material[1].emissive.getHex() : -1 }; })()""")
        check('夜：街の灯り（千以上）・星・ターミナルは壁（窓）だけ灯す', r['lights'] > 1000 and r['stars'] > 100 and r['termRoof'] == 0 and r['termWall'] > 0, r)
        await pg.screenshot(path=os.path.join(SHOTS, 't161-all-night.png'))
        allerr += errs; await c.close()
        # 地上の機体（答えに ground があるとき）
        c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
        await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")   # ふつうの端末として開く（試す機械は CPU が2つで、古い端末の軽い形になるため）
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
        async def fn(r):
            name = r.request.url.split('/functions/v1/')[1].split('?')[0]
            body = {'iata': 'HND', 'at': iso(-30), 'source': 'adsb.lol', 'planes': P[:2], 'ground': GROUND} if name == 'airport-traffic' else NOWD if name == 'airport-now' else {}
            await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        await c.route('https://fake.supabase.co/functions/v1/**', fn)
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(500); await pg.click('#dAirport .a3pill [data-ap3d]')
        await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=30000)
        await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ g: A3.objs.has('g1'), air: A3.objs.has('g1') && a3Air(A3.objs.get('g1').p), txt: document.querySelector('#a3Sheet .a3range').textContent, row: !!document.querySelector('[data-a3-pick=\"g1\"]') })")
        check('答えに ground があれば地上の機体を出し、一覧にも出す', r['g'] and not r['air'] and r['row'] and '地上 1機' in r['txt'] and 'まだ出ません' not in r['txt'], r)
        allerr += errs; await c.close()
        await b.close()
    check('JS のエラーなし', not allerr, allerr[:3])
asyncio.run(main())
srv.shutdown()
print('fails', fails)
print('errors', fails)
