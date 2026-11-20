import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 空の道すじの上限（移行190・data/adsblol-key2）に合わせた画面：
#   ログインしていないときは前の7日まで・ログインの鍵を付けて読む・login_required / rate_limited の一文・cold-tracks の 401 / 429
# （運用タブは前の形（見方のタブ）で確かめるので soramemo.ops.hub=0）
from datetime import datetime, timedelta, timezone
import asyncio, json
from playwright.async_api import async_playwright
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-track-quota')); os.makedirs(SHOTS, exist_ok=True)

def enc(pts):
    out, la0, lo0 = '', 0, 0
    def e(v):
        v = ~(v << 1) if v < 0 else v << 1; s = ''
        while v >= 0x20: s += chr((0x20 | (v & 0x1f)) + 63); v >>= 5
        return s + chr(v + 63)
    for la, lo in pts:
        a, b = round(la * 1e4), round(lo * 1e4); out += e(a - la0) + e(b - lo0); la0, lo0 = a, b
    return out
TR = [{'d': 1, 'h': 9, 'p': enc([(35.55 + i * .01, 139.78 + i * .012 * k) for i in range(30)])} for k in (1, -1, .3)]
TR += [{'d': 0, 'h': 15, 'p': enc([(35.2 + i * .012, 139.5 + i * .01) for i in range(30)])}]
JST = timezone(timedelta(hours=9)); TODAY = datetime.now(JST).date()
day = lambda n: (TODAY + timedelta(days=n)).isoformat()
FREE_MIN = max('2026-10-18', day(-7))
RL_DAY = day(-3)   # この日は上限に当たったことにする
res = []
def chk(name, ok): res.append(ok); print(('OK ' if ok else 'NG ') + name)

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.view.ops','art')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        calls=[]; H={'Access-Control-Allow-Origin':'*'}
        async def tracks(r):
            body = json.loads(r.request.post_data or '{}'); auth = r.request.headers.get('authorization', ''); calls.append((body.get('p_day'), auth))
            d = body.get('p_day', '')
            if auth == 'Bearer anon' and d < day(-7): data = {'error': 'login_required'}
            elif d == RL_DAY and auth != 'Bearer anon': data = {'error': 'rate_limited', 'retry_after_min': 35}
            elif d < day(-395): data = []
            else: data = TR
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers=H)
        await c.route('https://fake.supabase.co/rest/v1/rpc/airport_tracks', tracks)
        cold = []; cold_mode = {'v': 'ok'}
        async def coldf(r):
            cold.append(r.request.headers.get('authorization', ''))
            if cold_mode['v'] == '401': await r.fulfill(status=401, body='{"error":"login_required"}', content_type='application/json', headers=H)
            elif cold_mode['v'] == '429': await r.fulfill(status=429, body='{"error":"rate_limited","retry_after_min":20}', content_type='application/json', headers={**H, 'Retry-After': '1200'})
            else: await r.fulfill(status=200, body=json.dumps(TR), content_type='application/json', headers=H)
        await c.route('https://fake.supabase.co/functions/v1/cold-tracks**', coldf)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)

        # 1) ログインしていない：前の7日まで・anon の鍵
        await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_selector('#opsArt:not([hidden]) canvas', timeout=8000)
        chk('未ログインは anon の鍵で読む', calls and calls[-1][1] == 'Bearer anon')
        chk('未ログインの日付の下限は前の7日', await pg.get_attribute('#artDate', 'min') == FREE_MIN)
        chk('はじめは「ログインすると」の一文は出ない', await pg.locator('#artLock').count() == 0)
        await pg.fill('#artDate', FREE_MIN); await pg.dispatch_event('#artDate', 'change'); await pg.wait_for_timeout(500)
        chk('7日前の端で「前の日」は押せない', await pg.is_disabled('#opsArt [aria-label="前の日"]'))
        lk = await pg.locator('#artLock').inner_text() if await pg.locator('#artLock').count() else ''
        chk('7日前の端で「ログインすると見られます」', '8日より前の空の道すじはログインすると見られます' in lk)
        await pg.locator('#opsArt').screenshot(path=os.path.join(SHOTS, '01_logout_edge.png'))
        n0 = len(calls)
        await pg.evaluate(f"renderArt('{day(-30)}')"); await pg.wait_for_timeout(500)
        chk('もっと前の日を指定しても前の7日に戻す', calls[-1][0] == FREE_MIN and len(calls) >= n0)
        # あの日の空（乗った日が8日より前）は、未ログインだと login_required の一文
        await pg.evaluate("""() => { const t = Date.now() - 20 * 86400000; S.flights.push({ id:991, from:A.find(a => a.iata === 'HND').id, to:A.find(a => a.iata === 'CTS').id, dep:t, arr:t + 5400000, km:820, airline:'JL', no:'JL501', status:'with_flight_no' }); }""")
        await pg.evaluate("openThatDay('flown')"); await pg.wait_for_selector('#tdInfo .hint', timeout=8000); await pg.wait_for_timeout(400)
        chk('あの日の空：未ログインは「ログインすると見られます」', 'ログインすると見られます' in await pg.inner_text('#tdInfo'))
        await pg.evaluate("document.getElementById('dThatDay').close()")

        # 2) ログインした：ログインの鍵・記録の最初の日まで・上限の一文
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(700)
        await pg.evaluate("goTab('home'); goTab('ops'); ART = { iata:null, band:'all' }"); await pg.evaluate("renderArt()"); await pg.wait_for_timeout(600)
        chk('ログインした人はログインの鍵で読む', calls[-1][1] == 'Bearer tok-u1')
        chk('ログインした人の下限は記録の最初の日', await pg.get_attribute('#artDate', 'min') == '2026-10-18')
        old = max('2026-10-18', day(-20))
        await pg.evaluate(f"renderArt('{old}')"); await pg.wait_for_timeout(500)
        chk('8日より前の日も描ける', calls[-1] == (old, 'Bearer tok-u1') and await pg.locator('#artLock').count() == 0 and '出発 3便' in await pg.inner_text('#opsArt .artnav span'))
        await pg.evaluate(f"renderArt('{RL_DAY}')"); await pg.wait_for_timeout(500)
        lk = await pg.locator('#artLock').inner_text() if await pg.locator('#artLock').count() else ''
        chk('上限のときは「35分ほどあとで」', 'たくさん読んだので、35分ほどあとでまた見られます' in lk)
        await pg.locator('#opsArt').screenshot(path=os.path.join(SHOTS, '02_rate_limited.png'))
        n1 = len(calls); await pg.evaluate(f"renderArt('{RL_DAY}')"); await pg.wait_for_timeout(400)
        chk('上限の結果は覚えず、もう一度読みにいく', len(calls) == n1 + 1)

        # 3) cold-tracks（400日より前）：ログインの鍵・401・429
        t = await pg.evaluate(f"(async () => {{ ART = {{ iata:null }}; return (await loadArt('KIX', '{day(-420)}')).length; }})()")
        chk('cold-tracks もログインの鍵', cold and cold[-1] == 'Bearer tok-u1' and t == len(TR))
        cold_mode['v'] = '401'
        e = await pg.evaluate(f"(async () => {{ ART = {{ iata:null }}; await loadArt('KIX', '{day(-421)}'); return ART.err; }})()")
        chk('cold-tracks の 401 は login_required', e and e['kind'] == 'login_required')
        cold_mode['v'] = '429'
        e = await pg.evaluate(f"(async () => {{ ART = {{ iata:null }}; await loadArt('KIX', '{day(-422)}'); return [ART.err, artErrText(ART.err)]; }})()")
        chk('cold-tracks の 429 は rate_limited（20分）', e[0] and e[0]['kind'] == 'rate_limited' and '20分ほど' in e[1])

        # 4) デモは前の7日まで（ログインしていても）
        await pg.evaluate("demo = true; ART = { iata:null, band:'all' }"); await pg.evaluate("renderArt()"); await pg.wait_for_timeout(500)
        chk('デモは前の7日まで・anon の鍵', await pg.get_attribute('#artDate', 'min') == FREE_MIN and calls[-1][1] == 'Bearer anon')
        await pg.evaluate("demo = false")
        print('成功', sum(res), '/', len(res))
        if not all(res): errs.append('NG がある')
        print('errors', errs); await b.close()
asyncio.run(main())
