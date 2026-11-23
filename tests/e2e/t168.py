import os, sys, json, shutil, asyncio, threading, functools, http.server, math, subprocess
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D の機体を本物に近い形に（PM 11/23 14時20分・checkin/a3-models。本人「３Dモデルをリアルなものにして」）
#   1 7機種（787-8/9・777-300ER・767-300・737-800・A350-900・A321neo・A320）は、近い・選んだ機体を本物に近い形（a3MeshR）にする。ほかの機種は今の形のまま
#   2 遠い機体は今の形（mid）、遠い地上の機体は平らな形（lo）。「軽い」表示では今の簡単な形のまま（本物に近い形は作らない）
#   3 尾翼の色は便名の会社ごとの大まかな色（JAL・ANA など）。特別塗装機は昼だけ金。ロゴや文字は描かない
#   4 金属っぽい材質（MeshStandardMaterial）と空の映り込み・夜は窓が灯る
#   5 増える量（アプリ本体の圧縮した大きさ）は 3MB よりずっと小さい・機種ごとの三角形の数
#   比べ写真：今の本番（origin/main の web）と並べる（全体・駐機場・寄り・夜）→ docs/pm/shots-a3-models/
#   地上の機体の位置は t166 と同じ（2026-11-22 19時の羽田。adsb.lol・ODbL）。偽のサーバーを使い、本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3m-new'); OLD = os.path.join(BASE, 'a3m-old')
SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-a3-models') if os.environ.get('A3M_SHOTS') == '1' else os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'shots-a3-models'); os.makedirs(SHOTS, exist_ok=True)
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
PORT_OLD = None
SHOOT = os.environ.get('A3M_SHOTS') == '1'   # 比べ写真（今の本番と並べる・画素の密度 2）は A3M_SHOTS=1 のときだけ。ふだんは速く確かめるだけ（run_all の 240秒に収める）
try:
    if not SHOOT: raise RuntimeError('A3M_SHOTS=1 ではない')
    tmp = OLD + '-src'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    tar = subprocess.run(['git', '-C', ROOT, 'archive', 'origin/main', 'web'], capture_output=True, check=True).stdout
    subprocess.run(['tar', '-x', '-C', tmp], input=tar, check=True); PORT_OLD = serve(OLD, os.path.join(tmp, 'web'))
except Exception as e: print('今の本番の web が取れないので比べ写真は飛ばす', e)

now = datetime.now(timezone.utc); iso = lambda s: (now + timedelta(seconds=s)).isoformat()
def pl(i, cs, lat, lon, alt, kt, hdg, fpm, ph, dist, typ, reg): return {'id': i, 'callsign': cs, 'lat': lat, 'lon': lon, 'alt_ft': alt, 'kt': kt, 'hdg': hdg, 'fpm': fpm, 'phase': ph, 'dist_km': dist, 'type': typ, 'reg': reg, 'trail': []}
AIR = [pl('a1', 'JAL318', 35.512, 139.8340, 1300, 145, 337, -700, 'arr', 6, 'A359', 'JA01XJ'),
       pl('a2', 'ANA59', 35.585, 139.7560, 2600, 190, 337, 2200, 'dep', 4, 'B789', 'JA871A'),
       pl('a3', 'ANA36', 35.470, 139.880, 3500, 200, 320, -800, 'arr', 13, 'B78X', 'JA933A'),
       pl('a8', 'ANA12', 35.430, 139.950, 5200, 220, 320, -900, 'arr', 20, 'B77W', 'JA781A'),
       pl('a9', 'ANA1', 35.45, 139.91, 4500, 210, 320, -800, 'arr', 18, 'A320', 'JA8946')]
G = [["JAL98", 35.54807, 139.77256, 240, 10, "B789", "JA877J"], ["ANA860", 35.55029, 139.77593, 330, 48, "B763", "JA626A"], ["JAL333", 35.5497, 139.78017, 149, 0, "A359", "JA10XJ"],
     ["JAL137", 35.54874, 139.78106, 355, 3, "B788", "JA846J"], ["JAL264", 35.54663, 139.78108, 149, 26, "B738", "JA301J"], [None, 35.5459, 139.78313, 93, 7, "B738", "JA343J"],
     [None, 35.55878, 139.78405, None, 2, "B738", "JA66AN"], ["JAL520", 35.56459, 139.78415, 248, 10, "B738", "JA342J"], ["JAL377", 35.54202, 139.78436, 149, 22, "B738", "JA305J"],
     ["ACA2", 35.54659, 139.79326, 59, 15, "B77W", "C-FITU"], ["ANA264", 35.55473, 139.79447, 338, 58, "B78X", "JA984A"], ["SKY523", 35.53522, 139.79571, 59, 26, "B738", "JA73NL"],
     ["ANA649", 35.54727, 139.79595, 149, 24, "A21N", "JA146A"], ["ANA699", 35.54131, 139.80018, 149, 22, "A21N", "JA137A"], ["SNJ25", 35.53758, 139.80178, 174, 18, "B738", "JA808X"],
     ["ANA39", 35.53615, 139.80217, 152, 16, "B788", "JA821A"], ["JAL499", 35.52788, 139.80332, 222, 22, "B738", "JA335J"], ["ANA617", 35.52666, 139.80346, 222, 20, "B738", "JA84AN"],
     ["UAL882", 35.53947, 139.80433, 60, 7, "B78X", "N14016"], ["JAL485", 35.53034, 139.8106, 42, 118, "B738", "JA319J"],
     ["ADO15", 35.5440, 139.7900, 150, 0, "B38M", "JA15AN"], ["DAL7", 35.5470, 139.7870, 150, 0, "B752", "N555XX"]]
GROUND = [{'id': 'g%d' % i, 'callsign': g[0], 'lat': g[1], 'lon': g[2], 'hdg': g[3], 'kt': g[4], 'type': g[5], 'reg': g[6], 'moving': (g[4] or 0) >= 5} for i, g in enumerate(G)]
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [], 'dep': []}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def open3d(b, sky, port, dsf=None):
    dsf = dsf or (2 if SHOOT else 1)
    c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=dsf, timezone_id='Asia/Tokyo', bypass_csp=True)
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
    await pg.evaluate("A3.qAt = Date.now() + 1e9")   # 写真の機械（swiftshader）は遅いので、質が自動で下がらないようにする（iPhone では下がる）
    await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(2000)
    return c, pg, errs
async def view(pg, v, yaw=0, sel=None):
    await pg.evaluate("([v, y, s]) => { A3.view = v; A3.yaw = y; A3.sel = s; A3.card = false; a3Pills(); a3Sheet(); A3.dirty = true; }", [v, yaw, sel]); await pg.wait_for_timeout(1500)
# 寄り：選んだ機体の斜め前・少し上から（写真だけのためにカメラを置く。アプリの視点は変えない）
CLOSE = """([id, az, dist, up]) => { A3.sel = id; A3.view = 'all'; const o = A3.objs.get(id); window.__cam = window.__cam || a3Camera;
  a3Camera = () => { const p = o.g.position, L = o.g.scale.x, h = -o.g.rotation.y + az; A3.cam.near = 1; A3.cam.fov = 40; A3.cam.clearViewOffset(); A3.vo = -1; A3.cam.updateProjectionMatrix();
    A3.cam.position.set(p.x + Math.sin(h) * L * dist, p.y + L * up, p.z - Math.cos(h) * L * dist); A3.cam.lookAt(p.x, p.y - L * .02, p.z); }; const lb = document.getElementById('a3Labels'); if(lb) lb.style.visibility = 'hidden'; a3Pills(); A3.dirty = true; }"""
UNCLOSE = "(() => { if(window.__cam){ a3Camera = window.__cam; A3.cam.near = 30; A3.cam.updateProjectionMatrix(); } const lb = document.getElementById('a3Labels'); if(lb) lb.style.visibility = ''; A3.sel = null; A3.dirty = true; })()"
INFO = "(() => { A3.r.render(A3.scene, A3.cam); const i = A3.r.info.render; return { tri: i.triangles, calls: i.calls }; })()"
async def main():
    if not os.path.exists(THREE): print('three.js がないので飛ばす（t142 を先に流すと置かれる）'); sys.exit(1)
    allerr = []; info = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        c, pg, errs = await open3d(b, 'day', PORT)
        # 1 7機種の鍵
        keys = await pg.evaluate("['B788','B789','B78X','B77W','B763','B738','B38M','A359','A21N','A320','A20N','B752','E190','DH8D'].map(t => [t, a3RealKey(t)])")
        exp = {'B788': '788', 'B789': '789', 'B78X': '789', 'B77W': '77W', 'B763': '763', 'B738': '738', 'B38M': '38M', 'A359': '359', 'A21N': '21N', 'A320': '320', 'A20N': '320', 'B752': None, 'E190': None, 'DH8D': None}
        check('7機種（と MAX 8・787-10・A320neo）だけ本物に近い形の鍵がある', all(exp[t] == k for t, k in keys), keys)
        # 機種ごとの形：寸法の割合（翼幅／長さ）と三角形の数
        geo = await pg.evaluate("""Object.keys(A3_REAL).map(k => { const g = a3GeoR(k), T = A3.THREE, bb = new T.Box3();
            for(const n of ['body','wing','white','fin']) if(g[n]){ g[n].computeBoundingBox(); bb.union(g[n].boundingBox); }
            return { k, tri: Math.round(g.tri), span: +(bb.max.x - bb.min.x).toFixed(3), want: A3_REAL[k].span, len: +(bb.max.z - bb.min.z).toFixed(3) }; })""")
        check('翼幅と長さの割合が寸法の表どおり（±6%）', all(abs(g['span'] - g['want']) / g['want'] < .06 and abs(g['len'] - 1) < .06 for g in geo), [(g['k'], g['span'], g['want'], g['len']) for g in geo])
        check('1機の三角形は 2万5千 以内', all(g['tri'] < 25000 for g in geo), [(g['k'], g['tri']) for g in geo])
        info['geo'] = geo
        # 2 選んだ機体は本物に近い形・遠い地上の機体は平らな形
        await view(pg, 'all')
        r = await pg.evaluate("(() => { const g = [...A3.objs.values()].filter(o => !a3Air(o.p)); return { lo: g.filter(o => o.lo && o.lo.visible).length, real: g.filter(o => o.real && o.real.visible).length, n: g.length }; })()")
        check('全体の視点：遠い地上の機体は平らな形のまま（本物に近い形は出さない）', r['lo'] == r['n'] and r['real'] == 0, r)
        info['new_all_day'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_all_day.png'))
        await view(pg, 'tower', 1.25 * math.pi)
        r = await pg.evaluate("(() => { const g = [...A3.objs.values()].filter(o => !a3Air(o.p) && !(o.lo && o.lo.visible)); return { real: g.filter(o => o.real && o.real.visible).map(o => o.p.type), mid: g.filter(o => !(o.real && o.real.visible)).map(o => o.p.type) }; })()")
        check('駐機場（管制塔の視点）：画面で大きく見える7機種は本物に近い形', len(r['real']) > 0, r)
        info['new_tower_day'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_tower_day.png'))
        # 7機種それぞれを選ぶと本物に近い形・今の形は隠れる
        res = []
        for gid, t in (('g3', 'B788'), ('g0', 'B789'), ('g9', 'B77W'), ('g1', 'B763'), ('g4', 'B738'), ('g20', 'B38M'), ('g2', 'A359'), ('g12', 'A21N')):
            await view(pg, 'plane', 0, gid)
            res.append(await pg.evaluate("id => { const o = A3.objs.get(id); return [o.p.type, !!(o.real && o.real.visible), o.g.userData.hi.every(c => !c.visible)]; }", gid))
        check('7機種を選ぶと本物に近い形になり、今の形は隠れる', all(x[1] and x[2] for x in res), res)
        await view(pg, 'plane', 0, 'g21')
        r = await pg.evaluate("(() => { const o = A3.objs.get('g21'); return [!!o.real, o.g.userData.hi.some(c => c.visible)]; })()")
        check('ほかの機種（757）は今の形のまま', r == [False, True], r)
        # 3 尾翼の色・特別塗装機の金
        r = await pg.evaluate("""(() => { const fin = id => { const o = A3.objs.get(id); if(!o.real){ o.real = a3MeshR(o.p, a3RealKey(o.p.type)); o.g.add(o.real); o.real.visible = false; }
            return o; };
            const col = id => { const o = A3.objs.get(id); const m = o.real.children.filter(x => x.isMesh).map(x => x.material).find(x => Object.keys(A3.rm).some(k => k.startsWith('fin') && A3.rm[k] === x)); return m ? m.color.getHex() : null; };
            ['g3', 'g12', 'g18'].forEach(fin); return { jal: col('g3'), ana: col('g12'), ual: col('g18') }; })()""")
        check('尾翼の色：JAL は赤・ANA は青・知らない会社は白に近い灰色', r == {'jal': 0xC8102E, 'ana': 0x1A4C9C, 'ual': 0xE6E9EE}, r)
        sp = await pg.evaluate("(() => { const p = { callsign:'JAL1', reg:'JA8089', type:'B738', id:'sp' }; const reg = [...(window.SPECIAL ? SPECIAL.keys() : [])][0] || Object.keys(LIVERY_NAMES)[0]; p.reg = reg; const g = a3MeshR(p, '738'); return g.children.filter(m => m.isMesh).some(m => m.material.color && m.material.color.getHex() === 0xC9A23A); })()")
        check('特別塗装機の尾翼は昼は金', sp, sp)
        # 4 材質と映り込み
        r = await pg.evaluate("(() => { const o = A3.objs.get('g3'); const ms = o.real.children.filter(m => m.isMesh).map(m => m.material); return { std: ms.every(m => m.isMeshStandardMaterial), env: ms.every(m => !!m.envMap), metal: Math.max(...ms.map(m => m.metalness)), sh: o.real.children.filter(m => m.isMesh).every(m => m.castShadow === A3.r.shadowMap.enabled) }; })()")
        check('金属っぽい材質（PBR）・空の映り込み・影を落とす', r['std'] and r['env'] and r['metal'] >= .5 and r['sh'], r)
        # 寄りの写真（昼）
        for gid, nm, az, d, up in (('g3', 'close_788', 2.3, 1.9, .45), ('g12', 'close_21N', 2.3, 2.0, .5), ('g9', 'close_77W', 0.8, 1.8, .35), ('g2', 'close_359', 0.9, 1.9, .4), ('g20', 'close_38M', -0.9, 2.0, .45), ('g3', 'apron', 2.6, 4.5, 1.6)):
            await pg.evaluate(CLOSE, [gid, az, d, up]); await pg.wait_for_timeout(1200)
            await pg.screenshot(path=os.path.join(SHOTS, f'new_{nm}_day.png'))
        info['new_close_day'] = await pg.evaluate(INFO)
        await pg.evaluate(UNCLOSE)
        # 空の機体を追う（機体の視点）
        await view(pg, 'plane', 0, 'a2'); await pg.wait_for_timeout(800)
        r = await pg.evaluate("(() => { const o = A3.objs.get('a2'); return !!(o && o.real && o.real.visible); })()")
        check('空の機体の視点（787-9）も本物に近い形', r, r)
        await pg.screenshot(path=os.path.join(SHOTS, 'new_plane_air_day.png'))
        # 2 「軽い」表示では作らない
        await pg.evaluate("a3SetLite(true)"); await pg.wait_for_timeout(1500); await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("[...A3.objs.values()].filter(o => o.real).length")
        check('「軽い」表示では本物に近い形を作らない（今の簡単な形のまま）', r == 0, r)
        allerr += errs; await c.close()
        # 夜：窓が灯る・寄り
        c, pg, errs = await open3d(b, 'night', PORT)
        await view(pg, 'plane', 0, 'g3')
        r = await pg.evaluate("(() => { const o = A3.objs.get('g3'); const b = o.real.children.find(m => m.isMesh && m.material.map); return { em: !!b.material.emissiveMap, i: b.material.emissiveIntensity, pts: o.real.children.some(c => c.isPoints) }; })()")
        check('夜は窓が灯り、翼の先の灯りも本物に近い形に付く', r['em'] and r['i'] >= .9 and r['pts'], r)
        await view(pg, 'tower', 1.25 * math.pi); info['new_tower_night'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_tower_night.png'))
        await pg.evaluate(CLOSE, ['g3', 2.3, 1.9, .45]); await pg.wait_for_timeout(1200); await pg.screenshot(path=os.path.join(SHOTS, 'new_close_788_night.png'))
        await pg.evaluate(CLOSE, ['g12', 2.3, 2.0, .5]); await pg.wait_for_timeout(1200); await pg.screenshot(path=os.path.join(SHOTS, 'new_close_21N_night.png'))
        await pg.evaluate(CLOSE, ['g3', 2.6, 4.5, 1.6]); await pg.wait_for_timeout(1200); await pg.screenshot(path=os.path.join(SHOTS, 'new_apron_night.png'))
        await pg.evaluate(UNCLOSE)
        allerr += errs; await c.close()
        # 今の本番（比べ写真）
        if PORT_OLD:
            for sky in ('day', 'night'):
                c, pg, errs = await open3d(b, sky, PORT_OLD)
                if sky == 'day':
                    await view(pg, 'all'); info['old_all_day'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'old_all_day.png'))
                await view(pg, 'tower', 1.25 * math.pi); info[f'old_tower_{sky}'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, f'old_tower_{sky}.png'))
                for gid, nm, az, d, up in ((('g3', 'close_788', 2.3, 1.9, .45), ('g12', 'close_21N', 2.3, 2.0, .5), ('g9', 'close_77W', 0.8, 1.8, .35), ('g2', 'close_359', 0.9, 1.9, .4), ('g20', 'close_38M', -0.9, 2.0, .45), ('g3', 'apron', 2.6, 4.5, 1.6)) if sky == 'day' else (('g3', 'close_788', 2.3, 1.9, .45), ('g12', 'close_21N', 2.3, 2.0, .5), ('g3', 'apron', 2.6, 4.5, 1.6))):
                    await pg.evaluate(CLOSE, [gid, az, d, up]); await pg.wait_for_timeout(1200); await pg.screenshot(path=os.path.join(SHOTS, f'old_{nm}_{sky}.png'))
                if sky == 'day': info['old_close_day'] = await pg.evaluate(INFO)
                await c.close()
        try:
            from PIL import Image
            for f in sorted(os.listdir(SHOTS)):
                if not f.startswith('new_'): continue
                a, n = os.path.join(SHOTS, 'old_' + f[4:]), os.path.join(SHOTS, f)
                if not os.path.exists(a): continue
                A, N = Image.open(a), Image.open(n); im = Image.new('RGB', (A.width + N.width + 24, max(A.height, N.height)), 'white'); im.paste(A, (0, 0)); im.paste(N, (A.width + 24, 0))
                im.save(os.path.join(SHOTS, 'cmp_' + f[4:]))
        except Exception as e: print('並べた写真を作れない', e)
        print('描く量（三角形・呼び出し）', json.dumps({k: v for k, v in info.items() if k != 'geo'}))
        json.dump(info, open(os.path.join(SHOTS, 'render_info.json'), 'w'), indent=1, ensure_ascii=False)
        check('ページのエラーなし', not allerr, allerr[:3])
        await b.close()
    print('\n' + ('全部成功' if not fails else f'失敗 {len(fails)}件：' + ' / '.join(fails)))
    sys.exit(1 if fails else 0)
asyncio.run(main())
