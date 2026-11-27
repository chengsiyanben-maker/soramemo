import os, sys, json, shutil, asyncio, threading, functools, http.server
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 登録記号を決めて羽田の3D を開く（11/26 checkin/a3-reg・撮る人用の依頼①）
#   openAp3dReg(reg)・ボタンなら data-ap3d-reg="JA01XJ"
#   位置が届いたらその機体を「追う」で開く。小文字・ハイフンでも同じ機体
#   いま近くにいない機体なら全体のまま、下に「○○ はいま羽田の近くにいません」と「ほかを追う」
#   ふつうの「3D」（data-ap3d）は今までどおり全体で開く
#   偽のサーバーを使う。本物の Supabase には接続しない
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); WEB = os.path.join(ROOT, 'web')
BASE = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); WORK = os.path.join(BASE, 'a3-reg')
THREE = os.path.join(BASE, 'three-0.160.0.module.min.js')
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
def pl(i, cs, lat, lon, alt, kt, hdg, fpm, ph, dist, typ, reg): return {'id': i, 'callsign': cs, 'lat': lat, 'lon': lon, 'alt_ft': alt, 'kt': kt, 'hdg': hdg, 'fpm': fpm, 'phase': ph, 'dist_km': dist, 'type': typ, 'reg': reg, 'trail': []}
AIR = [pl('a1', 'JAL318', 35.512, 139.8340, 1300, 145, 337, -700, 'arr', 6, 'A359', 'JA01XJ'), pl('a2', 'ANA59', 35.585, 139.7560, 2600, 190, 337, 2200, 'dep', 4, 'B789', 'JA871A')]
GROUND = [{'id': 'g0', 'callsign': 'JAL98', 'lat': 35.54807, 'lon': 139.77256, 'hdg': 240, 'kt': 10, 'type': 'B789', 'reg': 'JA877J', 'moving': True}]
NOWD = {'at': iso(-20), 'weather': {'time': iso(-600), 'wdir': 170, 'wspd': 14, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None}, 'taf': None, 'flights': {'arr': [], 'dep': []}}
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1'); localStorage.setItem('soramemo_a3_guide','1');"
LOADED = "(() => { const l = document.getElementById('a3Load'); return !!l && l.hidden; })()"
MODE = "[...document.querySelectorAll('[data-a3-mode]')].filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.dataset.a3Mode).join('')"
async def until(pg, cond, ms=30000):
    try: await pg.wait_for_function(cond, timeout=ms); return True
    except Exception: return False
async def page(b, port):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1, timezone_id='Asia/Tokyo', bypass_csp=True)
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
    await pg.evaluate("a3Night = () => 'day'")
    return c, pg, errs
async def add_btn(pg, reg):
    # 撮る人用のくわしくに付く想定のボタン（属性だけで動くか）
    await pg.evaluate("r => { document.querySelectorAll('#tReg').forEach(x => x.remove()); const b = document.createElement('button'); b.id = 'tReg'; b.type = 'button'; b.dataset.ap3dReg = r; b.textContent = '3Dで見る'; b.style.cssText = 'position:fixed;left:8px;top:8px;z-index:9;width:120px;height:48px'; document.body.appendChild(b); }", reg)
async def main():
    if not os.path.exists(THREE): print('three.js がないので飛ばす（CDN から取れなかった）'); sys.exit(1)
    port = serve(); allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        c, pg, errs = await page(b, port)
        check('関数がある（openAp3dReg）', await pg.evaluate("typeof openAp3dReg === 'function'"))
        # 1) ボタンの属性だけで開き、位置が届いたらその機体を追う（小文字・ハイフンでも）
        await add_btn(pg, 'ja-01xj'); await pg.click('#tReg')
        check('data-ap3d-reg で 3D が開く', await until(pg, LOADED, 40000))
        ok = await until(pg, "A3 && A3.sel === 'a1' && A3.view === 'plane'", 30000)
        r = await pg.evaluate("({ sel: A3 && A3.sel, view: A3 && A3.view, mode: %s, want: A3 && A3.wantReg, ban: !$('a3Ban').hidden && $('a3Ban').innerText })" % MODE)
        check('JA01XJ（ja-01xj と書いても）の機体を「追う」で開く', ok and r['mode'] == 'follow' and r['want'] is None, r)
        ok = await until(pg, "!$('a3Ban').hidden && $('a3Ban').innerText.includes('JL 318 を追っています')", 15000)
        check('上に「JL 318 を追っています」', ok, await pg.evaluate("$('a3Ban').innerText"))
        await pg.screenshot(path=os.path.join(SHOTS, 'follow-390.png'))
        await pg.wait_for_timeout(2500)
        check('2.5秒たっても見失わない（届かなくなった一言は出ない）', await pg.evaluate("A3.sel === 'a1' && $('a3Toast').hidden"))
        # 2) 地上の機体も登録記号で選べる
        await pg.click('.a3top [data-a3-close]'); await pg.wait_for_timeout(400)
        await pg.evaluate("openAp3dReg('JA877J')")
        ok = await until(pg, "A3 && A3.sel === 'g0' && A3.view === 'plane'", 40000)
        check('地上の機体（JA877J）も追う', ok, await pg.evaluate("A3 && [A3.sel, A3.view]"))
        # 3) いま近くにいない機体：全体のまま・一言と「ほかを追う」
        await pg.click('.a3top [data-a3-close]'); await pg.wait_for_timeout(400)
        await add_btn(pg, 'JA8941'); await pg.click('#tReg')
        ok = await until(pg, "A3 && !$('a3Toast').hidden", 40000)
        r = await pg.evaluate("({ sel: A3.sel, view: A3.view, t: $('a3Toast').innerText, other: !!document.querySelector('#a3Toast [data-a3-other]') })")
        check('近くにいない機体：全体のまま', ok and r['sel'] is None and r['view'] == 'all', r)
        check('「JA8941 はいま羽田の近くにいません」と「ほかを追う」', 'JA8941' in r['t'] and 'いま羽田の近くにいません' in r['t'] and r['other'], r['t'])
        await pg.screenshot(path=os.path.join(SHOTS, 'miss-390.png'))
        await pg.click('#a3Toast [data-a3-other]'); await pg.wait_for_timeout(400)
        check('「ほかを追う」で機体を選ぶ一覧', await pg.evaluate("A3.picking === true"))
        # 4) ふつうの「3D」は今までどおり全体で開く
        await pg.click('.a3top [data-a3-close]'); await pg.wait_for_timeout(400)
        await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(600)
        await pg.click('#dAirport .a3pill [data-ap3d]')
        await until(pg, LOADED, 40000); await pg.evaluate("a3Poll()"); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ sel: A3.sel, view: A3.view, want: A3.wantReg || null, toast: $('a3Toast').hidden })")
        check('ふつうの 3D は全体で開く（機体を選ばない・一言なし）', r['sel'] is None and r['view'] == 'all' and r['want'] is None and r['toast'], r)
        allerr += errs; await c.close()
        await b.close()
    print('JS のエラー', allerr)
    if allerr: fails.append('JS のエラー')
    print('fails', fails)
    print('全部成功' if not fails else 'errors ' + str(fails))
    sys.exit(1 if fails else 0)
SHOTS = os.path.join(ROOT, 'docs', 'pm', 'shots-a3-reg'); os.makedirs(SHOTS, exist_ok=True)
asyncio.run(main())
