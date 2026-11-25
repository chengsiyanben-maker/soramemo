import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 11/18・11/19 の小さな直し
# 1. 乗る便：運航情報の「実際の出発時刻」に今より後の時刻（見込み）が入っていても「出発しました」にせず「出発の見込み」と出す（11/18 JL661）
#    前の便の到着・出発も同じ。過去の時刻なら今までどおり「出発しました」。データ側が first_of_day を返したら「朝一番の便です」
# 2. 半券：押せなかったとき（同じ空港に30分以内にもう押した など）は切れる動きをせず、理由を半券のすぐ下に出す（11/19 シミュレーター）
import asyncio, json, threading, http.server, socketserver, functools
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INB = {'flight': 'JL0660', 'dep': 'ITM', 'arr': 'HND', 'std': iso(-80), 'sta': iso(-10), 'atd': iso(-75), 'eta': None, 'ata': iso(20), 'cancelled': False,
       'phase': None, 'reg': 'JA737A', 'type': 'B738', 'takeoff': None, 'pos': None, 'share': 0.8, 'seen': 4}
CASE = {'ib': None}
def ib_for(kind):
    base = {'flight': 'JL0661', 'found': True, 'dep': 'HND', 'arr': 'ITM', 'std': iso(31), 'etd': None, 'atd': None, 'reg': 'JA737A', 'phase': None,
            'inbound': dict(INB), 'arr_at': iso(20), 'arr_src': 'actual', 'turn': 35, 'late': 0}
    if kind == 'future': base['atd'] = iso(34)
    if kind == 'past': base['atd'] = iso(-3); base['inbound']['ata'] = iso(-40); base['arr_at'] = iso(-40)
    if kind == 'first': base['inbound'] = None; base['first_of_day'] = True
    if kind == 'none': base['inbound'] = None
    return base
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WEB)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
async def drag(pg, dx):
    r = await pg.evaluate("(() => { const b = $('checkin').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; })()")
    await pg.mouse.move(r[0], r[1]); await pg.mouse.down()
    for k in range(1, 9): await pg.mouse.move(r[0] + dx * k / 8, r[1])
    await pg.mouse.up()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # ---- 1. 乗る便のカード（サーバー版・偽のサーバー）
        c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.layout', JSON.stringify({tabs:['home','book','log','ops','stats'], off:{home:[],book:[],log:[],ops:[],stats:[]}})); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            data = CASE['ib'] if name == 'inbound_aircraft' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        async def ride(kind):
            CASE['ib'] = ib_for(kind)
            await pg.evaluate("""() => { const d = new Date(Date.now() + 9*36e5).toISOString().slice(0, 10);
              localStorage.setItem('soramemo.plan', JSON.stringify({ from:A.find(a => a.iata === 'HND').id, to:A.find(a => a.iata === 'ITM').id, airline:'JL', no:'JL661', day:d })); goTab('home'); return renderRide(true); }""")
            await pg.wait_for_selector('#rideCard:not([hidden])', timeout=5000)
            return await pg.inner_text('#rideCard'), await pg.evaluate("(document.querySelector('#rideCard .rh + .rv') || {}).textContent || ''")
        t, st = await ride('future')
        check('未来の atd は「出発しました」にしない:', '出発しました' not in st)
        check('未来の atd は「出発の見込み」で出す:', '出発の見込み' in st and '航空会社の運航情報' in st)
        check('前の便の未来の到着は「到着しました」にしない:', '到着しました' not in t and '到着の見込み' in t)
        await pg.locator('#rideCard').screenshot(path=os.path.join(WORK, 't144_ride_future.png'))
        t, st = await ride('past')
        check('過去の atd は「出発しました」:', '出発しました（' in st and '出発の見込み' not in st)
        check('前の便の過去の到着は「到着しました」:', '到着しました' in t)
        t, st = await ride('first')
        check('first_of_day なら朝一番の便:', '朝一番の便です' in t and '見つかりませんでした' not in t)
        t, st = await ride('none')
        check('first_of_day がなければ「見つかりませんでした（朝一番の便なら…）」:', '見つかりませんでした' in t and '朝一番の便なら' in t)
        await c.close()
        # ---- 2. 半券（デモ。同じ空港に2回押す）
        for w, h in [(375, 667), (390, 844)]:
            c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo')
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
            pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(1500)
            if not await pg.evaluate("demo"): await pg.evaluate("$('toggleDemo').click(); 0"); await pg.wait_for_timeout(800)
            await pg.evaluate("goTab('home'); window.showStamp = () => {}; 0"); await pg.wait_for_timeout(700)   # 印の画面は t7 などで確かめる。ここでは閉じる手間を省く
            n0 = await pg.evaluate("S.checkins.length")
            await drag(pg, 70); await pg.wait_for_timeout(300)
            moved = await pg.evaluate("$('checkin').style.transform")
            await pg.wait_for_timeout(1400)
            check(f'{w}x{h} 1回目は押せて半券が切れる:', await pg.evaluate("S.checkins.length") == n0 + 1 and '210px' in moved)
            check(f'{w}x{h} 押せたときは理由の欄を出さない:', await pg.is_hidden('#stubMsg'))
            # 2回目：同じ空港に30分以内 → 押せない
            seen = []
            await pg.evaluate("window.__tf = []; new MutationObserver(() => window.__tf.push($('checkin').style.transform)).observe($('checkin'), { attributes:true, attributeFilter:['style'] }); 0")
            await drag(pg, 70); await pg.wait_for_timeout(700)
            tf = await pg.evaluate("window.__tf")
            check(f'{w}x{h} 2回目は印が増えない:', await pg.evaluate("S.checkins.length") == n0 + 1)
            check(f'{w}x{h} 押せなかったときは切れて飛ぶ動きをしない:', not any('210px' in x for x in tf))
            check(f'{w}x{h} 半券は元の位置に戻る:', await pg.evaluate("$('checkin').style.transform") == '' and await pg.evaluate("$('checkin').style.opacity") == '')
            check(f'{w}x{h} 理由を半券のすぐ下に出す:', await pg.is_visible('#stubMsg') and 'チェックインは完了しています' in await pg.inner_text('#stubMsg'))   # 11/25 stamp-edge で文をそろえた
            g = await pg.evaluate("(() => { const a = $('bpass').getBoundingClientRect(), m = $('stubMsg').getBoundingClientRect(); return { gap: m.top - a.bottom, bottom: m.bottom, h: innerHeight }; })()")
            check(f'{w}x{h} 理由は半券の真下で画面の中（すき間 {round(g["gap"])}px）:', 0 <= g['gap'] <= 16 and g['bottom'] <= g['h'])
            await pg.screenshot(path=os.path.join(WORK, f't144_stub_{w}x{h}.png'))
            # キーボード（Enter）でも同じ
            await pg.evaluate("$('stubMsg').hidden = true; 0")
            await pg.focus('#checkin'); await pg.keyboard.press('Enter'); await pg.wait_for_timeout(500)
            check(f'{w}x{h} キーボードでも理由を出す:', await pg.is_visible('#stubMsg'))
            await c.close()
        await b.close(); srv.shutdown()
        print('fails', fails)
        print('errors', errs if errs or fails else [])
asyncio.run(main())
