import os, sys, json, shutil, asyncio, threading, functools, http.server, subprocess
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 羽田の3D をもっとリアルに・動きの推測（PM 11/26 17時05分・本人「3Dモデルをもっとリアルに、動きも推測を加えて」・checkin/3d-real）
#   0 推測の計算の単体テスト（tests/kin/a3kin.test.mjs・ブラウザなし）
#   1 旋回中の機体は右に傾く（右の翼が下がる）・巡航はフラップも脚もしまう
#   2 着陸に向かう機体はフラップと脚を出す（細かい形・前の形とも）
#   3 データが途切れた着陸機は最終進入の道すじで進み「推定」・薄くなる
#   4 後ろ向きに動く地上の機体（プッシュバック）は機首の向きのまま・誘導路を走る機体は中心線に寄せて「推定」
#   5 動きを減らす設定では灯りを点滅させない
#   6 写真（390・375 の昼と夜）と短い動画（docs/pm/shots-3d-real/）
#   7 小型のジェット E170・E190 も細かい形（11/26 3d-real の2回目）
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3-real-kin')
THREE = os.path.join(BASE, 'three-0.160.0.module.min.js'); SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-3d-real')
sys.path.insert(0, HERE); from three_local import ensure_three; ensure_three(THREE)
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
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [], 'dep': []}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1'); localStorage.setItem('soramemo_a3_guide','1');"
async def open3d(b, port, sky='day', w=390, h=844, rm='no-preference', video=None):
    kw = {'record_video_dir': video, 'record_video_size': {'width': w, 'height': h}} if video else {}
    c = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True, reduced_motion=rm, **kw)
    await c.add_init_script(NEW + "Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}))
    async def fn(r):
        name = r.request.url.split('/functions/v1/')[1].split('?')[0]
        body = {'iata': 'HND', 'at': iso(-30), 'source': 'adsb.lol', 'planes': [], 'ground': []} if name == 'airport-traffic' else NOWD if name == 'airport-now' else {}
        await r.fulfill(body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/functions/v1/**', fn)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{port}/index.html')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    if sky == 'night': await pg.evaluate("document.documentElement.dataset.night = 'on'")
    await pg.evaluate("s => { a3Night = () => s; window.A3_QLOCK = 1; }", sky)
    await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(600)
    await pg.click('#dAirport .a3pill [data-ap3d]')
    await pg.wait_for_function("(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()", timeout=40000)
    await pg.wait_for_function("!!(A3 && A3.shape)", timeout=20000)
    await pg.evaluate(SEED); await pg.wait_for_timeout(2500)
    return c, pg, errs
# 作り物の答えを3つ（110秒前・75秒前・5秒前）。見せる時刻は60秒前なので、75秒前と5秒前のあいだ
#   t1：旋回（北西→北・75秒で90度）・a2：着陸に向かう 1,500ft・a3：巡航 12,000ft・gp：75秒前で途切れた着陸機（34R の延長線上）
#   g1：プッシュバック（機首は東・西へ動く）・g2：誘導路を走る（形のファイルの線から 8m ずらす）
SEED = r"""(() => {
  const N = Date.now(), M = 110574, ml = 111320 * Math.cos(35.55 * D2R), mv = (p, dx, dy) => ({ lat: p.lat + dy / M, lon: p.lon + dx / ml });
  const P = o => ({ callsign: 'TST', type: 'B738', kt: 180, fpm: 0, phase: 'arr', dist_km: 9, trail: [], ...o });
  const t1a = P({ id: 't1', callsign: 'JAL101', type: 'A359', lat: 35.60, lon: 139.74, alt_ft: 4000, hdg: 270, kt: 200 }), v = 200 * 0.5144, R = v * 75 / (Math.PI / 2);
  const t1b = { ...t1a, ...mv(t1a, -R, R), hdg: 0 };
  const a2 = P({ id: 'a2', callsign: 'ANA202', type: 'B789', lat: 35.50, lon: 139.82, alt_ft: 1500, hdg: 337, kt: 150, fpm: -750 });
  const a2b = { ...a2, ...mv(a2, -Math.sin(23 * D2R) * 150 * .5144 * 70, Math.cos(23 * D2R) * 150 * .5144 * 70), alt_ft: 650 };
  const a3 = P({ id: 'a3', callsign: 'SKY303', lat: 35.63, lon: 139.90, alt_ft: 12000, hdg: 90, kt: 300, phase: 'dep' }), a3b = { ...a3, ...mv(a3, 300 * .5144 * 70, 0) };
  const r34 = HND_RWY.find(r => /^34|^16/.test(r[0]) || /^34|^16/.test(r[4])), thr = /^34/.test(r34[0]) ? [r34[1], r34[2]] : [r34[5], r34[6]], opp = /^34/.test(r34[0]) ? [r34[5], r34[6]] : [r34[1], r34[2]];
  const crs = bearing(thr, opp), back = (crs + 180) * D2R, gpp = P({ id: 'gp', callsign: 'JAL909', type: 'B738', lat: thr[0] + Math.cos(back) * 9000 / M, lon: thr[1] + Math.sin(back) * 9000 / ml, alt_ft: 2800, hdg: crs, kt: 150, fpm: -750 });
  const gp0 = { ...gpp, lat: gpp.lat - Math.cos(crs * D2R) * 150 * .5144 * 35 / M, lon: gpp.lon - Math.sin(crs * D2R) * 150 * .5144 * 35 / ml, alt_ft: 3200 };
  const g1 = { id: 'g1', callsign: 'ANA55', type: 'B763', lat: 35.5470, lon: 139.7830, alt_ft: 0, ground: true, phase: 'ground', hdg: 90, kt: 0 }, g1b = { ...g1, ...mv(g1, -25, 0), hdg: 270, kt: 3 };
  const s = A3.tws, ax = s[0], az = s[1], bx = s[2], bz = s[3], L = Math.hypot(bx - ax, bz - az), mx = (ax + bx) / 2 - (bz - az) / L * 8, mz = (az + bz) / 2 + (bx - ax) / L * 8;
  const ll = (x, z) => ({ lat: A3_C[0] - z / M, lon: A3_C[1] + x / ml }), th = (Math.atan2(bx - ax, -(bz - az)) / D2R + 360) % 360;
  const g2 = { id: 'g2', callsign: 'JAL77', type: 'B788', ...ll(mx, mz), alt_ft: 0, ground: true, phase: 'ground', hdg: (th + 8) % 360, kt: 15 };
  window.__TW = { x: mx, z: mz, hdg: th };
  const e1 = P({ id: 'e1', callsign: 'JAL2201', type: 'E190', reg: 'JA241J', lat: 35.47, lon: 139.86, alt_ft: 2400, hdg: 337, kt: 160, fpm: -700 });
  const e1b = { ...e1, ...mv(e1, -Math.sin(23 * D2R) * 160 * .5144 * 70, Math.cos(23 * D2R) * 160 * .5144 * 70), alt_ft: 1600 };
  A3.snaps = [{ t: N - 110e3, planes: [t1a, a2, a3, gp0, g1, g2, e1] }, { t: N - 75e3, planes: [t1a, a2, a3, gpp, g1, g2, e1] }, { t: N - 5e3, planes: [t1b, a2b, a3b, g1b, g2, e1b] }];
  A3.poll && clearInterval(A3.poll); a3Poll = async () => {}; A3.dirty = true;
})()"""
async def main():
    r = subprocess.run(['node', os.path.join(ROOT, 'tests', 'kin', 'a3kin.test.mjs')], capture_output=True, text=True)
    check('0 推測の計算の単体テスト（tests/kin）', r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-300:])
    if not os.path.exists(THREE): print('three.js がないので飛ばす（CDN から取れなかった）'); sys.exit(1)
    port = serve(); allerr = []; os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        c, pg, errs = await open3d(b, port)
        ST = """(id => { const o = A3.objs.get(id); if(!o) return null; const fl = a3FlapList(o.g), gh = o.g.getObjectByName('gearHD'), ge = o.g.getObjectByName('gear');
          return { bk: o.bk, rz: o.g.rotation.z, rx: o.g.rotation.x, pt: o.pt, fl: o.fl, flaps: fl.length, flapOn: fl.filter(f => f.visible).length, flapAng: fl.length ? 2 * Math.acos(Math.min(1, Math.abs(fl[0].quaternion.w))) * 180 / Math.PI : 0,
            gear: !!((gh && gh.visible) || (ge && ge.visible)), est: o.p.est || null, push: !!o.p.push, hdg: o.p.hdg, faded: o.faded ? o.faded[0].opacity : 1 }; })"""
        t1 = await pg.evaluate(ST, 't1'); a3 = await pg.evaluate(ST, 'a3')
        check('1 旋回中（右へ1.2度/秒）は右に傾く：右の翼が下がる（rotation.z が負）・30度まで', t1 and t1['bk'] > 8 and t1['bk'] <= 30 and t1['rz'] < 0, t1)
        check('1 巡航（12,000ft）はフラップも脚もしまう・傾かない', a3 and a3['flapOn'] == 0 and not a3['gear'] and abs(a3['bk']) < .5, a3)
        a2 = await pg.evaluate(ST, 'a2')
        check('2 着陸に向かう（1,000ft あたり）はフラップを出す（約35度）・脚を出す', a2 and a2['fl'] > .8 and a2['flapOn'] >= 1 and a2['flapAng'] > 25 and a2['gear'], a2)
        check('2 フラップは前の形と細かい形の両方にある（左右）', a2['flaps'] >= 4, a2['flaps'])
        gp = await pg.evaluate(ST, 'gp'); q = await pg.evaluate("(() => { const q = a3Planes().find(x => x.id === 'gp'); return q && { est: q.est, op: q.k.op, alt: Math.round(q.alt_ft) }; })()")
        check('3 途切れた着陸機は消さずに最終進入で進む（推定・高さが下がる）', q and q['est'] == 'gap' and q['alt'] < 2800, q)
        check('3 途切れて10秒を過ぎたら薄くする', gp and gp['faded'] < 1, gp and gp['faded'])
        await pg.evaluate("a3Select('gp')"); await pg.wait_for_timeout(500)
        txt = await pg.evaluate("$('a3Sheet').innerText")
        check('3 機体のカードに「この機体の位置は推定です」と姿勢の推定の断り', 'この機体の位置は推定です' in txt and '実際の操作の記録ではありません' in txt, txt[-160:])
        await pg.evaluate("document.querySelector('[data-a3-uncard]') && document.querySelector('[data-a3-uncard]').click()"); await pg.wait_for_timeout(300)
        g1 = await pg.evaluate(ST, 'g1')
        check('4 プッシュバック：西へ動いても機首は東（90度）のまま', g1 and g1['push'] and abs(((g1['hdg'] - 90) + 540) % 360 - 180) < 2, g1)
        g2 = await pg.evaluate("(() => { const o = A3.objs.get('g2'), [x, z] = a3XZ(o.p.lat, o.p.lon), t = window.__TW; return { est: o.p.est, d: Math.hypot(x - t.x, z - t.z), hdg: o.p.hdg, line: t.hdg }; })()")
        check('4 誘導路：中心線に寄せる（8m）・向きを線にそろえる・推定', g2['est'] == 'twy' and 6 < g2['d'] < 10 and abs(((g2['hdg'] - g2['line']) + 540) % 360 - 180) < 1, g2)
        await pg.evaluate("a3Select('g2')"); await pg.wait_for_timeout(600)
        tag = await pg.evaluate("(() => { const e = A3.labels.get('g2'); return e ? e.innerHTML : null; })()")
        check('4 誘導路に寄せた機体の名札に「推定」', tag is None or '推定' in tag, tag)
        txt = await pg.evaluate("$('a3Sheet').innerText")
        check('4 カード：「地上の道すじは推定です」', '地上の道すじは推定です' in txt, txt[-120:])
        await pg.evaluate("document.querySelector('[data-a3-uncard]') && document.querySelector('[data-a3-uncard]').click()"); await pg.wait_for_timeout(300)
        src = await pg.evaluate("(() => { a3SrcHTML($('a3Sheet')); return $('a3Sheet').innerText; })()")
        check('出典：機体の動きは推定と書く', '機体の動き' in src and '推定' in src)
        # 写真：着陸に向かう機体を追う（フラップと脚）・旋回の機体を追う（傾き）
        await pg.evaluate("a3Select('a2', true)"); await pg.evaluate("A3.fside = 1; A3.fk = .45; A3.fup = .6; A3.yaw = -0.5; A3.dirty = true"); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=os.path.join(SHOTS, 'day-approach-flaps.png'))
        await pg.evaluate("a3Select('t1', true)"); await pg.evaluate("A3.fside = 2; A3.fk = .5; A3.fup = .4; A3.yaw = 0.35; A3.dirty = true"); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=os.path.join(SHOTS, 'day-turn-bank.png'))
        # 小型のジェット（E170・E190）も細かい形（11/26 3d-real の2回目）
        await pg.evaluate("a3Select('e1', true)"); await pg.evaluate("A3.fside = 1; A3.fk = .5; A3.fup = .6; A3.yaw = -0.5; A3.dirty = true"); await pg.wait_for_timeout(2500)
        e = await pg.evaluate("(() => { const o = A3.objs.get('e1'), hd = o.g.getObjectByName('hd'); return { key: a3HdKey('E190'), k2: a3HdKey('E170'), k3: a3HdKey('E75L'), hd: !!(hd && hd.visible), flapOn: a3FlapList(o.g).filter(f => f.visible).length }; })()")
        check('E190・E170 は細かい形（近いとき）・フラップも出す', e['key'] == 'e190' and e['k2'] == 'e170' and e['k3'] == 'e170' and e['hd'] and e['flapOn'] >= 2, e)
        await pg.screenshot(path=os.path.join(SHOTS, 'day-e190-390.png'))
        allerr += errs; await c.close()
        # 375×667：昼と夜（着陸に向かう機体と E190）
        for sky in ('day', 'night'):
            c, pg, errs = await open3d(b, port, sky, 375, 667)
            await pg.evaluate("a3Select('a2', true)"); await pg.evaluate("A3.fside = 1; A3.fk = .5; A3.fup = .6; A3.yaw = -0.5; A3.dirty = true"); await pg.wait_for_timeout(2500)
            await pg.screenshot(path=os.path.join(SHOTS, f'{sky}-approach-375.png'))
            await pg.evaluate("a3Select('e1', true)"); await pg.evaluate("A3.fside = 1; A3.fk = .5; A3.fup = .6; A3.yaw = -0.5; A3.dirty = true"); await pg.wait_for_timeout(2500)
            await pg.screenshot(path=os.path.join(SHOTS, f'{sky}-e190-375.png'))
            await pg.evaluate("A3.fside = 0; A3.fk = 1; A3.fup = 1; A3.yaw = 0; a3Home && a3Home(); A3.dirty = true"); await pg.wait_for_timeout(2500)
            await pg.screenshot(path=os.path.join(SHOTS, f'{sky}-all-375.png'))
            allerr += errs; await c.close()
        # 夜：航法灯・着陸灯（写真）
        c, pg, errs = await open3d(b, port, 'night')
        a2n = await pg.evaluate("(() => { const o = A3.objs.get('a2'), l = o.g.getObjectByName('land'); return { land: !!(l && l.visible) }; })()")
        check('2 夜：着陸に向かう機体は着陸灯を灯す', a2n['land'], a2n)
        st = await pg.evaluate("(A3.lmats || []).map(m => m.uniforms.uStill.value)")
        check('5 ふつうの設定では点滅する（uStill＝0）', len(st) > 0 and all(v == 0 for v in st), st[:4])
        await pg.evaluate("a3Select('a2', true)"); await pg.evaluate("A3.fside = 1; A3.fk = .6; A3.fup = .6; A3.yaw = -0.5; A3.dirty = true"); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=os.path.join(SHOTS, 'night-approach-lights.png'))
        allerr += errs; await c.close()
        c, pg, errs = await open3d(b, port, 'night', rm='reduce')
        st = await pg.evaluate("(A3.lmats || []).map(m => m.uniforms.uStill.value)")
        check('5 動きを減らす設定では点滅させない（uStill＝1）', len(st) > 0 and all(v == 1 for v in st), st[:4])
        allerr += errs; await c.close()
        # 短い動画：旋回の機体を追う（約6秒）
        vd = os.path.join(BASE, 'a3-real-video'); shutil.rmtree(vd, ignore_errors=True)
        c, pg, errs = await open3d(b, port, 'day', video=vd)
        await pg.evaluate("a3Select('t1', true)"); await pg.evaluate("A3.fside = 2; A3.fk = .5; A3.fup = .4; A3.yaw = 0.35; A3.dirty = true"); await pg.wait_for_timeout(7000)
        vp = await pg.video.path(); allerr += errs; await c.close()
        try: shutil.copy(vp, os.path.join(SHOTS, 'turn-follow.webm'))
        except Exception as e: print('動画を写せなかった', e)
        # 夜の短い動画：着陸に向かう機体（灯りの点滅・着陸灯）
        shutil.rmtree(vd, ignore_errors=True)
        c, pg, errs = await open3d(b, port, 'night', video=vd)
        await pg.evaluate("a3Select('a2', true)"); await pg.evaluate("A3.fside = 1; A3.fk = .6; A3.fup = .6; A3.yaw = -0.5; A3.dirty = true"); await pg.wait_for_timeout(6000)
        vp = await pg.video.path(); allerr += errs; await c.close()
        try: shutil.copy(vp, os.path.join(SHOTS, 'night-approach.webm'))
        except Exception as e: print('動画を写せなかった', e)
        await b.close()
    print('JS のエラー', allerr)
    if allerr: fails.append('JS のエラー')
    print('fails', fails)
    print('全部成功' if not fails else 'errors ' + str(fails))
    sys.exit(1 if fails else 0)
asyncio.run(main())
