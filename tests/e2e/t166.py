import os, sys, json, shutil, asyncio, threading, functools, http.server, math, subprocess, io
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D に地上の機体・見やすく（PM 11/22 18時55分・checkin/a3-ground。本人「地上の機体も写して、もっと見やすく、改善して」）
#   地上の機体：airport-traffic の答えの ground を、向き（hdg）どおりに置く。動いている機体（5ノット以上）は機首の先に小さな矢印。「まだ出ません」は消す
#   見やすく：1 遠いほど少し大きく（最小の見た目の大きさ。空 22px・地上 9px） 2 札は近い順・重ねない・押すとその機体を選ぶ・13px 以上
#             3 地上の機体は札を出さず、押した時だけ便名 4 夜は機体を少し自分で光らせる 5 下の一覧に「地上 ○機」を分ける
#   重さ：遠い地上の機体（カメラから3km より先）は簡単な形。描く三角形の数を比べる
#   比べ写真：今の本番（git の origin/main の web。本番は ground を返していないので地上の機体はない）と並べる（全体・管制塔 × 昼・夜）
#   地上の機体の位置は、2026-11-22 19時（日本時間）の羽田の実際の位置（adsb.lol・ODbL。空港の車両は除いた20機）。空の機体は作り物
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3g-new'); OLD = os.path.join(BASE, 'a3g-old')
SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-a3-ground'); os.makedirs(SHOTS, exist_ok=True)
THREE = os.path.join(BASE, 'three-0.160.0.module.min.js')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from three_local import ensure_three; ensure_three(THREE)   # 自分で用意する（t142 に頼らない・11/26 test-steady）
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
    t0 = await pg.evaluate("([v, y]) => { A3.view = v; A3.yaw = y; A3.card = false; a3Pills(); a3Sheet(); A3.dirty = true; return Date.now(); }", [v, yaw]); await pg.wait_for_timeout(1200)
    # 重いとき（同時に流す）は 1.2 秒でもまだ新しい視点で描いていないことがある（11/27 t166-fix：管制塔の近い機体が 0 機になった）。新しい視点で2こま描くまで待つ
    await pg.evaluate("t => new Promise(ok => { let n = 0; const f = () => { if(A3.drawn > t && ++n >= 2 && !A3.dirty) ok(); else { A3.dirty = true; setTimeout(f, 120); } }; f(); })", t0)
SE = 1.25 * math.pi   # 管制塔から南東（第2ターミナルの駐機場と誘導路。この時間の地上の機体が多い側）
INFO = "(() => { A3.r.render(A3.scene, A3.cam); const i = A3.r.info.render; return { tri: i.triangles, calls: i.calls }; })()"
# 機体の画面の上の長さ（px）：機首と尾を画面に写した距離
SIZE = """(() => { const T = A3.THREE, H = $('a3Stage').clientHeight, W = $('a3Stage').clientWidth, out = { air: [], gnd: [] };
  for(const [id, o] of A3.objs){ const L = o.g.scale.x, h = (o.p.hdg || 0) * Math.PI / 180, p = o.g.position;
    const a = new T.Vector3(p.x + Math.sin(h) * L / 2, p.y, p.z - Math.cos(h) * L / 2).project(A3.cam), b = new T.Vector3(p.x - Math.sin(h) * L / 2, p.y, p.z + Math.cos(h) * L / 2).project(A3.cam);
    const ap = [(a.x + 1) / 2 * W, (1 - a.y) / 2 * H], bp = [(b.x + 1) / 2 * W, (1 - b.y) / 2 * H];
    const ax = new T.Vector3(p.x - L / 2, p.y, p.z).project(A3.cam), bx = new T.Vector3(p.x + L / 2, p.y, p.z).project(A3.cam), ay = new T.Vector3(p.x, p.y - L / 2, p.z).project(A3.cam), by = new T.Vector3(p.x, p.y + L / 2, p.z).project(A3.cam);
    const s = Math.max(Math.hypot((ax.x - bx.x) / 2 * W, (ax.y - bx.y) / 2 * H), Math.hypot((ay.x - by.x) / 2 * W, (ay.y - by.y) / 2 * H));   // 向きによらない大きさ（長さ L の球の見かけ）
    (a3Air(o.p) ? out.air : out.gnd).push(Math.round(s)); }
  return out; })()"""
async def main():
    if not os.path.exists(THREE): print('three.js がないので飛ばす（CDN から取れなかった）'); sys.exit(1)
    allerr = []; info = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        # ---- 昼：数・置き方・矢印・一覧
        c, pg, errs = await open3d(b, 'day', PORT)
        r = await pg.evaluate("(() => { const g = [...A3.objs.values()].filter(o => !a3Air(o.p)); return { n: g.length, mv: g.filter(o => (o.g.getObjectByName('mv') || {}).visible).length,"
                              " rot: Object.fromEntries(g.map(o => [o.p.id, Math.round((-o.g.rotation.y * 180 / Math.PI + 360) % 360)])) }; })()")
        check('地上の機体を20機出す', r['n'] == 20, r['n'])
        check(f'動いている機体（{N_MOVE}機）だけ機首の先に矢印', r['mv'] == N_MOVE, r['mv'])
        check('向き（hdg）どおりに置く（JAL98 は 240°・ANA860 は 330°）', r['rot']['g0'] == 240 and r['rot']['g1'] == 330, (r['rot']['g0'], r['rot']['g1']))
        exp = await pg.evaluate("Math.round(a3NoseIn({ lat: 35.55878, lon: 139.78405 }))")
        check('向きが分からない機体は近いターミナルへ機首を向ける', r['rot']['g6'] == exp, (r['rot']['g6'], exp))
        sh = await pg.evaluate("({ txt: $('a3Sheet').innerText, ngnd: ($('a3NGnd') || {}).textContent, nair: ($('a3NAir') || {}).textContent, gh: (document.querySelector('.a3gh') || {}).textContent || '', rows: document.querySelectorAll('.a3gl li').length })")
        check('下の一覧に「地上 20機」を分けて出す（空 4機）', sh['ngnd'] == '20' and sh['nair'] == '4' and '地上' in sh['gh'] and sh['rows'] == 8, sh)
        check('「地上の機体はまだ出ません」は消した', 'まだ出ません' not in sh['txt'], sh['txt'][:80])
        check('地上は動いている機体を先に・様子（走行中・止まっている）', '走行中' in sh['txt'], sh['txt'][-200:])
        await pg.evaluate("document.querySelector('.a3gh').scrollIntoView({ block: 'start' })"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(SHOTS, 'new_sheet_ground.png'))
        await pg.evaluate("document.querySelector('#a3Sheet .a3body').scrollTop = 0"); await pg.wait_for_timeout(200)
        # 全体の視点：最小の見た目の大きさ・簡単な形
        await view(pg, 'all')
        sz = await pg.evaluate(SIZE)
        check('全体の視点：空の機体は 22px 以上', min(sz['air']) >= 21, sz['air'])
        check('全体の視点：地上の機体は 16px 以上（実寸だと約3px）', min(sz["gnd"]) >= 15, sz['gnd'])
        lo = await pg.evaluate("[...A3.objs.values()].filter(o => !a3Air(o.p)).filter(o => o.lo && o.lo.visible).length")
        check('全体の視点：遠い地上の機体は簡単な形', lo == 20, lo)
        tags = await pg.evaluate("[...document.querySelectorAll('#a3Labels .a3tag')].map(t => ({ t: t.innerText, fs: parseFloat(getComputedStyle(t).fontSize), id: t.dataset.a3Pick, r: t.getBoundingClientRect().toJSON() }))")
        check('地上の機体は札を出さない', not any(t['id'].startswith('g') for t in tags), [t['t'] for t in tags])
        check('札の字は13px以上', tags and all(t['fs'] >= 13 for t in tags), [t['fs'] for t in tags])
        ov = any(a['r']['left'] < b2['r']['right'] and a['r']['right'] > b2['r']['left'] and a['r']['top'] < b2['r']['bottom'] and a['r']['bottom'] > b2['r']['top'] for i, a in enumerate(tags) for b2 in tags[i + 1:])
        check('札は重ならない', not ov, [(t['t'], [round(t['r'][k]) for k in ('left', 'top', 'right', 'bottom')]) for t in tags])
        hs = await pg.evaluate("[...document.querySelectorAll('#a3Labels .a3tag')].map(t => t.getBoundingClientRect().height)")
        check('札の高さは置き方の見積もり（36px）に収まる（11/27：32px の見積もりで端の札が接して重なった）', hs and max(hs) <= 36, hs)
        info['new_all_day'] = await pg.evaluate(INFO)
        await pg.screenshot(path=os.path.join(SHOTS, 'new_all_day.png'))
        # 札を押すとその機体を選ぶ（下のシートもその機体のカード）
        tid = tags[0]['id'] if tags else None
        if tid:
            await pg.evaluate("id => document.querySelector(`#a3Labels .a3tag[data-a3-pick=\"${id}\"]`).click()", tid); await pg.wait_for_timeout(500)
            r = await pg.evaluate("({ sel: A3.sel, card: !!document.querySelector('#a3Sheet .a3fl'), fl: (document.querySelector('#a3Sheet .a3fl') || {}).textContent })")
            check('札を押すとその機体を選び、下のシートもその機体', r['sel'] == tid and r['card'], r)
            await pg.evaluate("document.querySelector('[data-a3-uncard]').click()"); await pg.wait_for_timeout(300)
        # 管制塔の視点：近い地上の機体は細かい形・押した時だけ便名
        await view(pg, 'tower')
        r = await pg.evaluate("(() => { const g = [...A3.objs.values()].filter(o => !a3Air(o.p)); return { hi: g.filter(o => !(o.lo && o.lo.visible)).length, near: g.filter(o => o.cd < 3000).length }; })()")
        check('管制塔の視点：3km 以内の地上の機体は細かい形', r['hi'] == r['near'] and r['near'] > 0, r)
        info['new_tower_day'] = await pg.evaluate(INFO)
        await pg.screenshot(path=os.path.join(SHOTS, 'new_tower_day.png'))
        await view(pg, 'tower', SE); info['new_towerSE_day'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_towerSE_day.png'))
        await view(pg, 'tower')
        # 11/27 t166-fix：こまの間が長い（重い端末・同時に流す）とき、答えの位置のまま描く地上の機体（走行中の速さつき）が前へずれていた（押す所から外れて選ばれない）。
        #   1.2 秒おきのこまを6回まねて、地上の機体の描く位置が答えの位置から動かないことを確かめる
        dr = await pg.evaluate("""(() => { let t = Date.now(), mx = 0, who = null;
          for(let i = 0; i < 6; i++){ t += 1200; const ps = a3Planes(t); a3Sync(ps, t);
            for(const p of ps){ if(a3Air(p) || (p.k && p.k.mv)) continue; const o = A3.objs.get(p.id), [x, z] = a3XZ(p.lat, p.lon), d = Math.hypot(o.g.position.x - x, o.g.position.z - z); if(d > mx){ mx = d; who = p.id; } } }
          A3.dirty = true; return [Math.round(mx * 10) / 10, who]; })()""")
        check('こまの間が長くても、止まって描く地上の機体は前へずれない（1m 未満）', dr[0] < 1, dr)
        await pg.wait_for_timeout(1700)   # 6回まねた時刻のずれ（smooth は 5 秒より前の状態を捨てて合わせ直す）が落ち着くまで
        # 管制塔から見えている地上の機体（シートの上）を、景色の中で押す。選ぶのと押すのは同じ評価の中で（間にこまが入って位置が変わらないように）
        gid = await pg.evaluate("""(() => { A3.r.render(A3.scene, A3.cam); a3Labels(a3Planes(Date.now()).filter(p => A3.objs.has(p.id)));
          const top = $('a3Sheet').getBoundingClientRect().top - $('a3Stage').getBoundingClientRect().top; const g = [...A3.objs.entries()].filter(([id, o]) => !a3Air(o.p) && o.sx != null && o.sy > 160 && o.sy < top - 160).sort((a, b) => a[1].cd - b[1].cd);
          if(!g.length) return null; const r = $('a3Stage').getBoundingClientRect(), [id, o] = g[0]; a3Tap({ clientX: r.left + o.sx, clientY: r.top + o.sy }); return [id, o.sx, o.sy]; })()""")
        check('管制塔から見える地上の機体がある', gid is not None, gid)
        if gid: await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ sel: A3.sel, fl: (document.querySelector('#a3Sheet .a3fl') || {}).textContent, now: [...document.querySelectorAll('#a3Sheet .a3grid div')].map(d => d.innerText).join('|'), tag: [...document.querySelectorAll('#a3Labels .a3tag')].filter(t => t.dataset.a3Pick === A3.sel).map(t => t.innerText) })")
        check('地上の機体を押すと便名の札とカード（いまの様子つき）', gid and r['sel'] == gid[0] and len(r['tag']) == 1 and ('走行中' in r['now'] or '止まっている' in r['now']), r)
        await pg.screenshot(path=os.path.join(SHOTS, 'new_tower_day_pick.png'))
        allerr += errs; await c.close()
        # ---- 夜
        c, pg, errs = await open3d(b, 'night', PORT)
        r = await pg.evaluate("(() => { const o = [...A3.objs.values()][0]; const m = o.g.children.find(x => x.isMesh).material; return m.emissive ? m.emissive.getHex() : 0; })()")
        check('夜は機体を少し自分で光らせる（輪郭が背景から浮く）', r > 0x202020, hex(r))
        await view(pg, 'all'); info['new_all_night'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_all_night.png'))
        col = await pg.evaluate("getComputedStyle($('a3NGnd')).color")
        check('夜のシートでも「地上 ○機」の数が読める（明るい字）', col.startswith('rgb(2'), col)
        await view(pg, 'tower'); info['new_tower_night'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_tower_night.png'))
        await view(pg, 'tower', SE); info['new_towerSE_night'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, 'new_towerSE_night.png'))
        allerr += errs; await c.close()
        # ---- 今の本番（比べ写真）
        if PORT_OLD:
            for sky in ('day', 'night'):
                c, pg, errs = await open3d(b, sky, PORT_OLD, ground=False)
                for v, k, y in (('all', 'all', 0), ('tower', 'tower', 0), ('tower', 'towerSE', SE)):
                    await view(pg, v, y); info[f'old_{k}_{sky}'] = await pg.evaluate(INFO); await pg.screenshot(path=os.path.join(SHOTS, f'old_{k}_{sky}.png'))
                await c.close()
        # 並べた写真（左：今の本番、右：この版）
        try:
            from PIL import Image, ImageDraw
            for k in ('all_day', 'tower_day', 'towerSE_day', 'all_night', 'tower_night', 'towerSE_night'):
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
