import os, sys, json, gzip, shutil, asyncio, threading, functools, http.server, math
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 滑走路の灯りと機体をもっと現実的に（PM 11/21 21時35分・checkin/a3-lights）
#   灯り：AIP JAPAN RJTT AD 2.14 の種類と長さ（縁の白と黄・中心線の白と赤・末端の緑と翼の形の列・終わりの赤・接地帯・PALS と順に流れる閃光・PAPI 4灯・誘導路の縁の青と中心線の緑）。にじむ光の輪
#   機体：機種ごとの形（787 の反った翼・777 の大きな発動機・A350 の曲がる翼の先・E170/E190・Q400 と ATR のプロペラと T 字の尾翼）。航空灯・衝突防止灯・白い閃光・着陸灯
#   （以下は t161 の説明）
#   建物：PLATEAU（大田区 2025・川崎市 2022。外形と計測高さ）で空港の建物と海沿いの街を立体に。屋根と壁の色を分ける（用途ごと）
#   地面：舗装の色むら・タイヤの跡・芝と陸の色むら・海の照り返し。三角の表の向きをそろえる（裏向きで黒く見えていた）
#   機体：機種ごとの形（787・777・A350・737・A320 など）・窓の帯・翼の先・脚（地上と着陸の前だけ）。会社の色やロゴなし
#   空：薄い雲（空港の上は空ける）・夜の星・街の灯り・駐機場の照明・夜のターミナルは壁（窓）だけ灯す
#   地上の機体：答えに ground があれば出す（データ担当への依頼の先取り）
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'a3srv')
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-a3-lights')); os.makedirs(SHOTS, exist_ok=True)
THREE = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'three-0.160.0.module.min.js')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)


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
async def open3d(b, sky, h=844, noshape=False, weak=False):
    c = await b.new_context(viewport={'width': 390, 'height': h}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW + ("" if weak else "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });"))   # ふつうの端末として開く（試す機械は CPU が2つで、古い端末の軽い形になるため）
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


async def main():
    if not os.path.exists(THREE): print('three.js がないので画面の確かめは飛ばす（t142 を先に流すと置かれる）'); return
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        # 昼：灯りは出さない（目立たないように消す）
        c, pg, errs = await open3d(b, 'day')
        r = await pg.evaluate("({ main: !!A3.scene.getObjectByName('lightsMain'), acl: !!A3.objs.get('a1').g.getObjectByName('acl') })")
        check('昼：滑走路の灯りと機体の灯りは出さない', not r['main'] and not r['acl'], r)
        r = await pg.evaluate("""(() => { const t = id => { const p = a3Geo(id).pts.nav; return +p[0][1].toFixed(4); }; const dk = id => a3Geo(id).dark.attributes.position.count;
          return { m: ['E190','E170','CRJ7','DH8D','AT76'].map(a3Model).join(' '), flex: t('787') > t('777'), q4: dk('q4') > dk('crj'), wing: a3Geo('q4').pts.nav[1][1] > 0, low: a3Geo('320').pts.nav[1][1] < a3Geo('q4').pts.nav[1][1] - .03 }; })()""")
        check('機種ごとの形：E170/E190・CRJ・Q400・ATR を分ける／787 の翼の先は 777 より反る／Q400 は高い翼とプロペラ・A320 は低い翼', r['m'] == 'e e crj q4 atr' and r['flex'] and r['q4'] and r['wing'] and r['low'], r)
        r = await pg.evaluate("(() => { const o = A3.objs.get('a4'), b = new A3.THREE.Box3().setFromObject(o.g); return Math.round(b.min.y * 10) / 10; })()")
        check('地上の機体は車輪が地面に着く高さ（めり込まない・浮かない）', -0.5 <= r <= 1.5, r)
        allerr += errs; await c.close()
        for sky in ('dusk', 'night'):
            c, pg, errs = await open3d(b, sky)
            r = await pg.evaluate("""(() => { const m = A3.scene.getObjectByName('lightsMain'), f = A3.scene.getObjectByName('lightsFine'), pa = A3.scene.getObjectByName('papi');
              const C = m.geometry.attributes.aCol.array, F = m.geometry.attributes.aFx.array, key = (a, i) => [a[i], a[i + 1], a[i + 2]].map(v => v.toFixed(2)).join(',');
              const cols = {}; for(let i = 0; i < C.length; i += 3){ const k = key(C, i); cols[k] = (cols[k] || 0) + 1; }
              let fl = 0; for(let i = 0; i < F.length; i += 2) if(F[i] === 1) fl++;
              const fc = {}; const FC = f.geometry.attributes.aCol.array; for(let i = 0; i < FC.length; i += 3){ const k = key(FC, i); fc[k] = (fc[k] || 0) + 1; }
              return { n: m.geometry.attributes.position.count, fine: f.geometry.attributes.position.count, fineVis: f.visible, papi: pa.geometry.attributes.position.count, flash: fl, cols, fc, add: m.material.blending === A3.THREE.AdditiveBlending }; })()""")
            L = lambda c: '%.2f,%.2f,%.2f' % tuple(c)
            cols = r['cols']
            check(f'{sky}：滑走路の灯り（縁の白と黄・中心線と終わりの赤・末端の緑・誘導路の縁の青）', r['n'] > 2000 and all(cols.get(L(x), 0) > 50 for x in ([1, .94, .82], [1, .78, .28], [1, .24, .2], [.28, .9, .5], [.32, .5, 1])), {k: v for k, v in cols.items()})
            check(f'{sky}：接地帯と誘導路の中心線の緑（細かい灯り）・PAPI 7か所×4灯', r['fine'] > 500 and r['fineVis'] and r['papi'] == 28 and r['fc'].get(L([.22, .86, .5]), 0) > 100, (r['fine'], r['papi']))
            check(f'{sky}：進入灯の順に流れる閃光（PALS の6か所。16L・34R・16R・34L・22 は900m・23 は870m）・光は足し合わせてにじむ', r['flash'] == 20 * 5 + 19 and r['add'], r['flash'])
            r = await pg.evaluate("""(() => { const u = A3.papi.u.slice(20, 24), m = A3.papi.m; const want = [3.5, 3 + 1/6, 2 + 5/6, 2.5];
              const at = deg => { const x = u[0].x, z = u[0].z, d = 2500; A3.cam.position.set(x + 400, Math.tan(deg * D2R) * d + 2, z + Math.sqrt(d * d - 400 * 400)); a3Papi(); return u.map((_, i) => m.geometry.attributes.aCol.array[(20 + i) * 3 + 1] > .5 ? 'W' : 'R').join(''); };
              return { tr: u.map(x => +x.tr.toFixed(2)).join(','), hi: at(6), on: at(3), lo: at(1) }; })()""")
            check(f'{sky}：PAPI は見上げる角度で色が変わる（高い＝白4・正しい＝赤2白2・低い＝赤4）', r['hi'] == 'WWWW' and r['on'] == 'RRWW' and r['lo'] == 'RRRR', r)
            r = await pg.evaluate("""(() => { const v = (id, n) => { const o = A3.objs.get(id).g.getObjectByName(n); return !!o && o.visible; };
              const a = A3.objs.get('a1').g.getObjectByName('acl'), C = a.geometry.attributes.aCol.array, F = a.geometry.attributes.aFx.array;
              return { acl: v('a1', 'acl'), landArr: v('a1', 'land'), landClimb: v('a2', 'land'), landGround: v('a4', 'land'), red: C[0] > .9 && C[1] < .3, green: C[4] > .9 && C[3] < .3, beacon: [...F].filter((x, i) => i % 2 === 0 && x === 2).length, strobe: [...F].filter((x, i) => i % 2 === 0 && x === 3).length }; })()""")
            check(f'{sky}：機体の灯り（左の赤・右の緑・尾の白・衝突防止灯2つ・白い閃光2つ）・着陸灯は着陸の手前だけ', r['acl'] and r['red'] and r['green'] and r['beacon'] == 2 and r['strobe'] == 2 and r['landArr'] and not r['landClimb'] and not r['landGround'], r)
            # 写真：全体・管制塔・機体（進入中の a1 の後ろ）・地上
            await pg.evaluate("A3.yaw = 0; A3.view = 'all'; A3.dirty = true"); await pg.wait_for_timeout(500)
            await pg.screenshot(path=os.path.join(SHOTS, f't162-all-{sky}.png'))
            await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(600)
            await pg.screenshot(path=os.path.join(SHOTS, f't162-tower-{sky}.png'))
            await pg.evaluate("id => a3Select(id, true)", 'a1'); await pg.wait_for_timeout(800)
            await pg.screenshot(path=os.path.join(SHOTS, f't162-plane-{sky}.png'))
            if sky == 'dusk':
                await pg.evaluate("a3Quality(0)"); r = await pg.evaluate("[A3.scene.getObjectByName('lightsFine').visible, A3.scene.getObjectByName('lightsMain').visible, A3.lmats.every(m => m.uniforms.uPr.value === 1)]")
                check('いちばん軽い質では細かい灯り（接地帯・誘導路の中心線）を隠す・滑走路の灯りは残す', r == [False, True, True], r)
            allerr += errs; await c.close()
        # 古い端末（CPU 2つ）：はじめから影なし・機体の丸を粗く・細かい灯りなし
        c, pg, errs = await open3d(b, 'night', weak=True)
        r = await pg.evaluate("({ q: A3.q, seg: A3.seg, sh: A3.r.shadowMap.enabled, fine: A3.scene.getObjectByName('lightsFine').visible })")
        check('古い端末：はじめから影なし・機体の丸を粗く・細かい灯りを出さない', r == {'q': 1, 'seg': 10, 'sh': False, 'fine': False}, r)
        allerr += errs; await c.close()
        await b.close()
    check('JS のエラーなし', not allerr, allerr[:3])
asyncio.run(main())
srv.shutdown()
print('fails', fails)
print('errors', fails)
