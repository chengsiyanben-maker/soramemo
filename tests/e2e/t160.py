import os, sys, json, gzip, shutil, asyncio, threading, functools, http.server, math
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D の完成度（PM 11/21 13時40分・checkin/a3-model）
#   不具合1 上半分の薄い青の四角：シートの箱がスクロールする箱だと、3D の絵の上にダイアログの背景が出ていた → 絵に背景の色（緑にして確かめる）が出ない
#   不具合2 名札が出典の札に重なる → 重ならない
#   不具合3 管制塔の視点が地平線だけ → 管制室の高さから少し見下ろす（俯角 2〜10°）・空港の形が画面の大部分
#   不具合4 機体の視点 → 追う機体が見えている所（上の操作とシートの間）に入る
#   形：OpenStreetMap を加工した 3d/hnd.json（ODbL）を開いたときだけ読む。建物・誘導路・駐機場・芝・海岸線・管制塔。滑走路は HND_RWY（AIP）で標示つき
#   機体：機種で形の種類（4発・大きな2発・細い胴・小さなジェット・プロペラ）。会社の色やロゴなし
#   光：昼・夕・夜で空の色と灯り。重いときは質を自動で下げる（影→細かさ）
#   大きさ：three.js と形のファイルを圧縮して 1.5MB まで（11/21 夜 checkin/a3-real で街の建物を足して約0.6MB）。入口の字と合う
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'a3srv')
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-a3-model')); os.makedirs(SHOTS, exist_ok=True)
THREE = os.path.join(os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'), 'three-0.160.0.module.min.js')
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)

# ---- 形のファイル ----
shape_path = os.path.join(WEB, '3d', 'hnd.json')
S = json.load(open(shape_path, encoding='utf-8'))
raw = open(shape_path, 'rb').read()
check('形のファイル：ODbL・OpenStreetMap の出典・滑走路は入れない', S.get('license') == 'ODbL-1.0' and 'OpenStreetMap' in S.get('attribution', '') and '滑走路は含まない' in S.get('note', ''))
check('形のファイル：建物100棟以上・誘導路・駐機場・芝・海岸線（島）・管制塔', len(S['bld']) >= 100 and len(S['twy']) >= 300 and len(S['apron']) >= 5 and len(S['grass']) >= 50 and len(S['land']) >= 2 and S.get('tower'), {k: len(v) for k, v in S.items() if isinstance(v, list)})
check('形のファイル：ターミナル（第1・第2・第3）がある', sum(1 for b in S['bld'] if b[0] == 't') >= 3)
tw = S['tower']; check('管制塔の位置は第1と第2のターミナルの間（中心から東に約260m）', 150 < tw[0] < 400 and 0 < tw[1] < 350, tw)
if os.path.exists(THREE):
    tot = len(gzip.compress(raw, 9)) + len(gzip.compress(open(THREE, 'rb').read(), 9))
    check('読み込む量は圧縮して 1.5MB まで・入口の「約0.6MB」と合う（0.55〜0.65MB）', 550_000 <= tot <= 650_000, tot)
SRC = open(os.path.join(HERE, '..', '..', 'src', 'index.html'), encoding='utf-8').read()
check('入口の字は「約0.6MB」（測った量に合う）', 'const A3_SIZE = "約0.6MB";' in SRC)
check('形のファイルは開いたときだけ読む（openAp3d の中）', 'const shape = a3Shape();' in SRC and SRC.index('const shape = a3Shape();') > SRC.index('async function openAp3d'))

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
async def main():
    if not os.path.exists(THREE): print('three.js がないので画面の確かめは飛ばす（t142 を先に流すと置かれる）'); return
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        c, pg, errs = await open3d(b, 'day')
        r = await pg.evaluate("({ shape: !!(A3 && A3.shape), q: A3.q, shadow: A3.r.shadowMap.enabled, rw: A3.scene.children.filter(o => o.isMesh && o.geometry.type === 'PlaneGeometry' && o.name !== 'clouds' && o.material && o.material.map).length, tower: A3.towerXZ })")
        check('形のファイルを読んで描く（滑走路4本は標示の絵つき・影あり・管制塔は形のファイルの位置）', r['shape'] and r['rw'] == 4 and r['shadow'] and r['q'] == 2 and r['tower'] == S['tower'], r)
        st = await pg.evaluate("(() => { const s = getComputedStyle(document.getElementById('a3Sheet')), y = document.querySelector('#a3Sheet .a3body'); return { ov: s.overflowY, body: !!y && getComputedStyle(y).overflowY }; })()")
        check('不具合1：シートは切り抜くだけ（overflow hidden）で、中の .a3body が送れる', st['ov'] == 'hidden' and st['body'] == 'auto', st)
        await pg.evaluate(GREEN); await pg.wait_for_timeout(400)
        g = await green_px(pg, 0, 500)
        check('不具合1：全体の視点で、3D の絵の上にダイアログの背景（緑）が出ない', g < 50, g)
        await pg.evaluate("document.getElementById('dAp3d').style.background = ''")
        ov = await pg.evaluate("(() => { const c = document.getElementById('a3Credit').getBoundingClientRect(); return [...document.querySelectorAll('.a3tag')].filter(t => { const r = t.getBoundingClientRect(); return r.left < c.right && r.right > c.left && r.top < c.bottom && r.bottom > c.top; }).map(t => t.innerText); })()")
        check('不具合2：名札は出典の札に重ならない', ov == [], ov)
        cr = await pg.evaluate('A3_CREDIT()')
        check('角の出典に OpenStreetMap と PLATEAU', 'OpenStreetMap' in cr and 'PLATEAU' in cr, cr)
        await pg.screenshot(path=os.path.join(SHOTS, 't160-all-day.png'))
        await pg.click('[data-a3-view="tower"]'); await pg.wait_for_timeout(900)
        r = await pg.evaluate("(() => { const d = new A3.THREE.Vector3(); A3.cam.getWorldDirection(d); return { y: Math.round(A3.cam.position.y), pitch: Math.asin(d.y) * 180 / Math.PI }; })()")
        check('不具合3：管制塔の視点は管制室の高さ（約106m）から少し見下ろす（俯角 2〜10°）', r['y'] == 106 and -10 < r['pitch'] < -2, r)
        await pg.evaluate(GREEN); await pg.wait_for_timeout(300)
        check('不具合3：管制塔の視点にも背景の緑が出ない', await green_px(pg, 0, 500) < 50)
        await pg.evaluate("document.getElementById('dAp3d').style.background = ''")
        await pg.screenshot(path=os.path.join(SHOTS, 't160-tower-day.png'))
        for pid in ('a1', 'a4'):
            await pg.evaluate("id => a3Select(id, true)", pid); await pg.wait_for_timeout(900)
            r = await pg.evaluate("(() => { const o = A3.objs.get(A3.sel), v = o.g.position.clone().project(A3.cam), st = document.getElementById('a3Stage').getBoundingClientRect(), top = document.getElementById('a3Sheet').getBoundingClientRect().top; return { sy: Math.round((1 - v.y) / 2 * st.height), top: Math.round(top), tag: [...document.querySelectorAll('.a3tag')].some(t => t.innerText.includes(a3No(o.p))) }; })()")
            check(f'不具合4：機体の視点（{pid}）で追う機体は上の操作とシートの間に見え、名札は重ねない', 120 < r['sy'] < r['top'] - 10 and not r['tag'], r)
        await pg.screenshot(path=os.path.join(SHOTS, 't160-plane-ground-day.png'))
        k = await pg.evaluate("['B744','A388','B789','B77W','A359','A320','B738','E190','CRJ7','DH8D','AT76'].map(a3Kind).join('')")
        check('機体の形の種類（4発・大きな2発・細い胴・小さなジェット・プロペラ）', k == 'qqwwwnnrrpp', k)
        m = await pg.evaluate("(() => { const o = A3.objs.get('a1'); const cols = new Set(); o.g.traverse(x => { if(x.material && x.material.color && x.name !== 'mv' && !(x.parent && x.parent.name === 'lo')) cols.add(x.material.color.getHexString()); }); return [...cols]; })()")
        # 11/23（checkin/a3-models）から近い機体は本物に近い形：白・灰色・金属の色に、尾翼だけ会社ごとの大まかな色（A3_TAIL）。ロゴや文字の絵は使わない（胴の絵は窓とドアだけ）
        tails = await pg.evaluate("[...new Set(Object.values(A3_TAIL).concat(0xE6E9EE))].map(c => c.toString(16).padStart(6, '0'))")
        grey = ('f4f6f8', '6b7280', '374151', 'c9a23a', 'ffffff', 'c3c9d0', 'f2f4f6', '2a2f36', '9ea4ab', '17191c', 'a8aeb5')
        check('機体は白と灰色だけ＋尾翼の会社の大まかな色（ロゴなし。窓の帯は濃いグレー。特別塗装機の尾翼は昼だけ金。地上を動く印の矢印と遠くの平らな形は除く）', all(x in grey or x in tails for x in m), m)
        await pg.evaluate("a3Quality(1)"); r1 = await pg.evaluate("[A3.r.shadowMap.enabled, A3.r.getPixelRatio()]")
        await pg.evaluate("a3Quality(0)"); r0 = await pg.evaluate("[A3.r.shadowMap.enabled, A3.r.getPixelRatio()]")
        check('重いときは質を下げる：影をやめる→細かさを下げる', r1[0] is False and r0 == [False, 1], (r1, r0))
        await pg.click('#a3Credit'); await pg.wait_for_timeout(300); src = await pg.inner_text('#a3Sheet')
        check('出典のシート：OpenStreetMap（ODbL 1.0）・管制塔の高さは国土交通省・航法には使えません', 'OpenStreetMap' in src and 'ODbL 1.0' in src and '国土交通省' in src and '航法には使えません' in src, src[:160])
        check('出典のシート：PLATEAU（大田区・川崎市・国土交通省を加工して作成・公共データ利用規約）', 'Project PLATEAU' in src and '大田区（2025年度）' in src and '川崎市（2022年度）' in src and '加工して作成' in src and '公共データ利用規約' in src, src[160:420])
        allerr += errs; await c.close()
        # 夕方と夜：空の色・灯り
        for sky in ('dusk', 'night'):
            c, pg, errs = await open3d(b, sky)
            r = await pg.evaluate("({ pts: A3.scene.children.filter(o => o.isPoints).length, top: A3.sky.material.uniforms.top.value.getHexString() })")
            check(f'{sky}：滑走路・誘導路の灯りがある・空の色が昼と違う', r['pts'] >= 4 and r['top'] != '4f8bcb', r)
            await pg.evaluate(GREEN); await pg.wait_for_timeout(300)
            check(f'{sky}：背景の緑が出ない', await green_px(pg, 0, 500) < 50)
            await pg.evaluate("document.getElementById('dAp3d').style.background = ''")
            await pg.screenshot(path=os.path.join(SHOTS, f't160-all-{sky}.png'))
            allerr += errs; await c.close()
        # 形のファイルが読めないときは前の仮の島で開く
        c, pg, errs = await open3d(b, 'day', noshape=True)
        r = await pg.evaluate("({ shape: A3.shape, r: !!A3.r, load: document.getElementById('a3Load').hidden })")
        check('形のファイルが読めなくても、前の仮の島で開く', r['shape'] is None and r['r'] and r['load'], r)
        allerr += errs; await c.close()
        await b.close()
    check('JS のエラーなし', not allerr, allerr[:3])
asyncio.run(main())
srv.shutdown()
print('fails', fails)
print('errors', fails)
