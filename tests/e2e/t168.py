import os, sys, json, shutil, asyncio, threading, functools, http.server, math, subprocess, io
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D の機体を細かい3Dモデルに（PM 11/23 14時20分・checkin/a3-models。本人「３Dモデルをリアルなものにして」）
#   7機種（787・777・767・737・A350・A321neo・A320）は近いとき細かい形（a3HdMesh）。遠くは前の形、もっと遠い地上の機体は平らな形。「軽い」と質0は前の形のまま
#   色は白い胴と尾翼の大まかな色だけ（夜は会社の色を使わない）。材質は PBR で空を映す。夜は窓が灯る
#   比べ写真：今の本番（origin/main の web）と同じ視点（全体・駐機場・寄り・夜）で撮る（docs/pm/shots-a3-models/）
#   以下の地上の機体の位置と作り物の空の機体は t166 と同じ（もとの説明）：
#   地上の機体：airport-traffic の答えの ground を、向き（hdg）どおりに置く。動いている機体（5ノット以上）は機首の先に小さな矢印。「まだ出ません」は消す
#   見やすく：1 遠いほど少し大きく（最小の見た目の大きさ。空 22px・地上 9px） 2 札は近い順・重ねない・押すとその機体を選ぶ・13px 以上
#             3 地上の機体は札を出さず、押した時だけ便名 4 夜は機体を少し自分で光らせる 5 下の一覧に「地上 ○機」を分ける
#   重さ：遠い地上の機体（カメラから3km より先）は簡単な形。描く三角形の数を比べる
#   比べ写真：今の本番（git の origin/main の web。本番は ground を返していないので地上の機体はない）と並べる（全体・管制塔 × 昼・夜）
#   地上の機体の位置は、2026-11-22 19時（日本時間）の羽田の実際の位置（adsb.lol・ODbL。空港の車両は除いた20機）。空の機体は作り物
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3m-new'); OLD = os.path.join(BASE, 'a3m-old')
SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-a3-models'); os.makedirs(SHOTS, exist_ok=True)
THREE = os.path.join(BASE, 'three-0.160.0.module.min.js')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)

def serve(dirpath, web):
    shutil.rmtree(dirpath, ignore_errors=True); shutil.copytree(web, dirpath)
    open(os.path.join(dirpath, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=dirpath))
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv.server_address[1]
PORT = serve(WORK, WEB)
# 今の本番：origin/main の web を取り出す（取れなければ比べ写真は飛ばす）
PORT_OLD = None
try:
    tmp = OLD + '-src'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    tar = subprocess.run(['git', '-C', ROOT, 'archive', 'origin/main', 'web'], capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', tmp], input=tar, check=True); PORT_OLD = serve(OLD, os.path.join(tmp, 'web'))
except Exception as e: print('今の本番の web が取れないので比べ写真は飛ばす', e)

now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
def pl(i, cs, lat, lon, alt, kt, hdg, fpm, ph, dist, typ, reg): return {'id': i, 'callsign': cs, 'lat': lat, 'lon': lon, 'alt_ft': alt, 'kt': kt, 'hdg': hdg, 'fpm': fpm, 'phase': ph, 'dist_km': dist, 'type': typ, 'reg': reg, 'trail': []}
AIR = [pl('a1', 'JAL318', 35.512, 139.8340, 1300, 145, 337, -700, 'arr', 6, 'A359', 'JA01XJ'),
       pl('a2', 'ANA59', 35.585, 139.7560, 2600, 190, 337, 2200, 'dep', 4, 'B789', 'JA871A'),
       pl('a3', 'ANA36', 35.470, 139.880, 3500, 200, 320, -800, 'arr', 13, 'B78X', 'JA933A'),
       pl('a8', 'ANA12', 35.430, 139.950, 5200, 220, 320, -900, 'arr', 20, 'B77W', 'JA781A')]
# [便名, 緯度, 経度, 向き, ノット, 機種, 登録記号]（2026-11-22 19時の羽田。adsb.lol）
G = [["JAL98", 35.54807, 139.77256, 240, 10, "B789", "JA877J"], ["ANA860", 35.55029, 139.77593, 330, 48, "B763", "JA626A"], ["JAL333", 35.5497, 139.78017, 149, 0, "A359", "JA10XJ"],
     ["JAL137", 35.54874, 139.78106, 355, 3, "B788", "JA846J"], ["JAL264", 35.54663, 139.78108, 149, 26, "B738", "JA301J"], [None, 35.5459, 139.78313, 93, 7, "B738", "JA343J"],
     [None, 35.55878, 139.78405, None, 2, "B738", "JA66AN"], ["JAL520", 35.56459, 139.78415, 248, 10, "B738", "JA342J"], ["JAL377", 35.54202, 139.78436, 149, 22, "B738", "JA305J"],
     ["ACA2", 35.54659, 139.79326, 59, 15, "B77W", "C-FITU"], ["ANA264", 35.55473, 139.79447, 338, 58, "B78X", "JA984A"], ["SKY523", 35.53522, 139.79571, 59, 26, "B738", "JA73NL"],
     ["ANA649", 35.54727, 139.79595, 149, 24, "A21N", "JA146A"], ["ANA699", 35.54131, 139.80018, 149, 22, "A21N", "JA137A"], ["SNJ25", 35.53758, 139.80178, 174, 18, "B738", "JA808X"],
     ["ANA39", 35.53615, 139.80217, 152, 16, "B788", "JA821A"], ["JAL499", 35.52788, 139.80332, 222, 22, "B738", "JA335J"], ["ANA617", 35.52666, 139.80346, 222, 20, "B738", "JA84AN"],
     ["UAL882", 35.53947, 139.80433, 60, 7, "B78X", "N14016"], ["JAL485", 35.53034, 139.8106, 42, 118, "B738", "JA319J"]]
GROUND = [{'id': 'g%d' % i, 'callsign': g[0], 'lat': g[1], 'lon': g[2], 'hdg': g[3], 'kt': g[4], 'type': g[5], 'reg': g[6], 'moving': (g[4] or 0) >= 5} for i, g in enumerate(G)]
N_MOVE = sum(1 for g in GROUND if g['moving'])
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [], 'dep': []}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def open3d(b, sky, port, ground=True):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
    await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        if name == 'airport-traffic':
            body = {'iata': 'HND', 'at': iso(-30), 'source': 'adsb.lol', 'planes': AIR}
            if ground: body['ground'] = GROUND
        elif name == 'airport-now': body = NOWD
        else: body = {}
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
    await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(2000)
    return c, pg, errs
async def view(pg, v, yaw=0):
    await pg.evaluate("([v, y]) => { A3.view = v; A3.yaw = y; A3.card = false; a3Pills(); a3Sheet(); A3.dirty = true; }", [v, yaw]); await pg.wait_for_timeout(1200)
SE = 1.25 * math.pi   # 管制塔から南東（第2ターミナルの駐機場と誘導路。この時間の地上の機体が多い側）
INFO = "(() => { A3.r.render(A3.scene, A3.cam); const i = A3.r.info.render; return { tri: i.triangles, calls: i.calls }; })()"

SE = 1.25 * math.pi
HD = """(() => { const out = {}; for(const [id, o] of A3.objs){ const hd = o.g.getObjectByName('hd'); out[id] = { type: o.p.type, has: !!hd, vis: !!(hd && hd.visible), tri: hd ? hd.userData.tri : 0, cd: Math.round(o.cd) }; } return out; })()"""
async def shots(b, port, tag, ground=True):
    out = {}
    for sky in ('day', 'night'):
        c, pg, errs = await open3d(b, sky, port, ground)
        views = (('all', 'all', 0, None), ('apron', 'tower', SE, None), ('close', 'plane', 0, 'g3'), ('close2', 'plane', 0, 'g10'))
        for k, v, y, sel in views:
            if sel:
                if not await pg.evaluate("id => !!A3.objs.get(id)", sel): continue
                await pg.evaluate("id => { a3Select(id, true); A3.card = false; a3Sheet(); }", sel); await pg.wait_for_timeout(300)
                await pg.evaluate("y => { A3.view = 'plane'; A3.yaw = y; A3.dirty = true; }", 2.4); await pg.wait_for_timeout(1500)
            else: await view(pg, v, y)
            out[f'{k}_{sky}'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, f'{tag}_{k}_{sky}.png'))
        await c.close()
    return out
async def main():
    if not os.path.exists(THREE): print('three.js がないので飛ばす（t142 を先に流すと置かれる）'); sys.exit(1)
    allerr = []; info = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        c, pg, errs = await open3d(b, 'day', PORT)
        r = await pg.evaluate("['B788','B789','B78X','B77W','B763','B738','B38M','A359','A21N','A321','A320','A20N','E190','DH8D','B744'].map(t => a3HdKey(t) || '-').join(' ')")
        check('細かい形の機種（787・777・767・737・A350・A321・A320。ほかは前の形）', r == '787 787 787 777 767 737 737 350 a321 a321 320 320 - - -', r)
        r = await pg.evaluate("Object.fromEntries(Object.keys(A3_HD).map(k => [k, a3HdGeo(k).tri]))")
        check('細かい形の三角形は1機種 3万以下（1機種で1回作り、同じ機種で使い回す）', all(5000 < v < 30000 for v in r.values()), r)
        # 寸法：翼幅と長さの割合（FAA の表）。形の外側の箱で測る
        r = await pg.evaluate("""Object.fromEntries(Object.keys(A3_HD).map(k => { const g = a3HdGeo(k), T = A3.THREE, bb = new T.Box3(); for(const v of Object.values(g)) if(v && v.isBufferGeometry){ v.computeBoundingBox(); bb.union(v.boundingBox); }
            return [k, [+(bb.max.x - bb.min.x).toFixed(3), +(bb.max.z - bb.min.z).toFixed(3), A3_HD[k].span]]; }))""")
        check('翼幅と長さは機種の寸法の割合どおり（±4%）', all(abs(v[0] - v[2]) / v[2] < .04 and abs(v[1] - 1) < .04 for v in r.values()), r)
        await view(pg, 'tower', SE)
        h = await pg.evaluate(HD)
        near = [k for k, v in h.items() if v['has'] and v['cd'] < 1600]
        check('管制塔の視点：近い7機種の機体は細かい形を出す', near and all(h[k]['vis'] for k in near), {k: h[k] for k in near})
        far = [k for k, v in h.items() if v['has'] and v['cd'] > 1700 and k != await pg.evaluate("A3.sel || ''")]
        check('遠い機体は細かい形を出さない（前の形か平らな形）', all(not h[k]['vis'] for k in far), len(far))
        r = await pg.evaluate("(() => { const o = A3.objs.get('g9'), hd = o.g.getObjectByName('hd'); const mid = o.g.userData.mid.filter(c => c.visible).length; return { hd: !!hd, mid }; })()")
        await pg.evaluate("id => { a3Select(id, true); }", 'g3'); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("(() => { const o = A3.objs.get('g3'), hd = o.g.getObjectByName('hd'); return { vis: hd.visible, mid: o.g.userData.mid.filter(c => c.visible).length, gear: o.g.getObjectByName('gearHD').visible }; })()")
        check('追っている機体は細かい形・前の形は隠す・地上なので脚を出す', r['vis'] and r['mid'] == 0 and r['gear'], r)
        # 色：白い胴・尾翼の色は会社ごとの大まかな色（JAL 赤・ANA 紺）。特別塗装機は昼だけ金。ロゴや字の絵はない（胴の絵は窓・扉・操縦室・継ぎ目だけ）
        r = await pg.evaluate("""(() => { const fin = id => { const o = A3.objs.get(id), hd = o.g.getObjectByName('hd'); const m = hd.children.find(c => c.isMesh && c.geometry === a3HdGeo(a3HdKey(o.p.type)).fin); return m.material.color.getHexString(); };
            return { jal: fin('g3'), ana: fin('g10'), aca: fin('g9') }; })()""")
        check('尾翼の色：JAL は赤・ANA は紺・海外の会社は白に近い灰色', r == {'jal': 'c8102e', 'ana': '13317d', 'aca': 'e9ecef'}, r)
        r = await pg.evaluate("(() => { const m = A3.hdm['787']; return { std: m.type, env: !!m.envMap, map: !!m.map, em: m.emissiveIntensity, shadow: A3.objs.get('g3').g.getObjectByName('hd').children[0].castShadow }; })()")
        check('材質は PBR（MeshStandardMaterial）・空を映す・昼は窓を灯さない・影を落とす', r['std'] == 'MeshStandardMaterial' and r['env'] and r['map'] and r['em'] == 0 and r['shadow'], r)
        info['hd_tower_day'] = await pg.evaluate(INFO)
        # 軽い表示と質0は前の形のまま
        await pg.evaluate("a3SetLite(true)"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("[...A3.objs.values()].some(o => o.g.getObjectByName('hd'))")
        check('「軽い」表示では細かい形を作らない（前の簡単な形のまま）', r is False, r)
        allerr += errs; await c.close()
        # 夜：窓が灯る・尾翼に会社の色を使わない
        c, pg, errs = await open3d(b, 'night', PORT)
        await view(pg, 'tower', SE); await pg.evaluate("id => { a3Select(id, true); }", 'g3'); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("""(() => { const o = A3.objs.get('g3'), hd = o.g.getObjectByName('hd'), g = a3HdGeo('787'); const fin = hd.children.find(c => c.geometry === g.fin), body = hd.children.find(c => c.geometry === g.body);
            return { fin: fin.material.color.getHexString(), em: body.material.emissiveIntensity, emMap: !!body.material.emissiveMap }; })()""")
        check('夜は窓が灯る・尾翼に会社の色を使わない', r['em'] == 1 and r['emMap'] and r['fin'] == 'f0f2f5', r)
        allerr += errs; await c.close()
        # 比べ写真：同じ視点（全体・駐機場・寄り・夜）
        info['new'] = await shots(b, PORT, 'new')
        if PORT_OLD: info['old'] = await shots(b, PORT_OLD, 'old')
        try:
            from PIL import Image
            for k in ('all_day', 'apron_day', 'close_day', 'close2_day', 'all_night', 'apron_night', 'close_night', 'close2_night'):
                a, n = os.path.join(SHOTS, f'old_{k}.png'), os.path.join(SHOTS, f'new_{k}.png')
                if not (os.path.exists(a) and os.path.exists(n)): continue
                A, N = Image.open(a), Image.open(n); im = Image.new('RGB', (A.width + N.width + 12, max(A.height, N.height)), 'white'); im.paste(A, (0, 0)); im.paste(N, (A.width + 12, 0))
                im.save(os.path.join(SHOTS, f'cmp_{k}.png'))
        except Exception as e: print('並べた写真を作れない', e)
        print('描く量（三角形・呼び出し）', json.dumps(info))
        json.dump(info, open(os.path.join(SHOTS, 'render_info.json'), 'w'), indent=1)
        check('ページのエラーなし', not allerr, allerr[:3])
        await b.close()
    print('\n' + ('全部成功' if not fails else f'失敗 {len(fails)}件：' + ' / '.join(fails)))
    sys.exit(1 if fails else 0)
asyncio.run(main())
