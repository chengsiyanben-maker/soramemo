import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 11/25 アプリ全体の見直し 2回目（kaizen/sweep-1125 の report-sweep-1125.md）のチェックイン側の直し（checkin/sweep-1125）
#   1 成績のパスポートの「空の上」をフライトと同じ数え方に（fbMin の合計）。推定の札もフライトと同じ決め方（odpt 以外がまじったら「推定を含む」）
#   3 運用の「遅れ」のページ：「いまごろ」の行を上の浮いたボタンの帯の下に送る。送ったら帯に背景。10行未満なら送らない
#   5 図鑑の「見方が3つになりました」は前の見方（タイル・案内標・年代記）を使っていた人だけ。2026年12月末で出さない
#   6 フライトの地図の「乗った区間」に車などを入れない。車などだけの区間は下に別の一覧
#   7 飛行場・滑空場・ヘリポートの図鑑：名前を字の途中で折らない・同じ字の大きさ・地方の見出しの札を外す・題と絞り込みの右にツメの幅
#   9 ウェブでも電波がないときにホームの帯（nvNetHome）。保留した印の数を1行
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, shutil
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import goto_http
SHOTS = os.path.join(WORK, 't191'); os.makedirs(SHOTS, exist_ok=True)
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat(); NOW = at(15, 0)
def bf(dir, fl, h, m, late):
    return {'dir': dir, 'flight': fl, 'other': 'ITM', 'sched': iso(h, m), 'est': iso(h, m + late), 'actual': None, 'late': late, 'cancelled': False, 'intl': False, 'aircraft': None}
BAD46 = [bf('dep' if i % 2 else 'arr', f'JL{100 + i}', i // 2, (i % 2) * 30, 20) for i in range(46)]
BAD5 = [bf('dep', f'JL{200 + i}', 10 + i * 2, 0, 25) for i in range(5)]
STATE = {'bad': BAD46}
def board():
    bad = STATE['bad']
    hrs = [{'h': h, 'flights': 10, 'late': sum(1 for f in bad if int(datetime.fromisoformat(f['sched']).astimezone(JST).hour) == h), 'cancel': 0} for h in range(24)]
    return {'iata': 'HND', 'next_arr': [], 'next_dep': [], 'hours': hrs, 'bad': bad}
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def demo_page(b, w, h, extra=''):
    c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=1, timezone_id='Asia/Tokyo')
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1'); localStorage.setItem('soramemo.persona','all');" + extra)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(500)
    await pg.evaluate('openMyPage("adv")'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(700)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return c, pg, errs
async def server_page(b, w, h):
    c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', has_touch=True)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    async def hd(r):
        u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
        body = {'airport_board': board(), 'special_now': [], 'airport_ontime': {'measured': 200, 'ontime': 148, 'cancelled': 2, 'from': '2026-10-25', 'to': '2026-11-23', 'routes': []},
                'airport-traffic': {'iata': 'HND', 'at': NOW.isoformat(), 'source': 'adsb.lol', 'planes': []}, 'push-subscribe': {'key': None}}.get(name, {} if '/functions/' in u else [])
        try: await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        except Exception: pass
    await c.route('https://fake.supabase.co/rest/**', hd); await c.route('https://fake.supabase.co/functions/**', hd)
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
                            "localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND');")
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await goto_http(pg, os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return c, pg, errs
LATE_GEOM = """(() => { const li = document.querySelector('#opsLate li.ltnowrow'), bar = document.querySelector('#v-ops .opsbar'), bk = $('opsHubBack');
  const rows = [...document.querySelectorAll('#opsLate .ltrows li')].map(x => x.getBoundingClientRect()).filter(r => r.bottom > 0 && r.top < innerHeight);
  const bb = bk.getBoundingClientRect(), br = bar.getBoundingClientRect();
  const hit = rows.filter(r => r.top < bb.bottom && r.bottom > bb.top).length;
  return { y: Math.round(scrollY), now: li ? Math.round(li.getBoundingClientRect().top) - 22 : null, barB: Math.round(br.bottom), stuck: $('v-ops').hasAttribute('data-stuck'),
    bg: getComputedStyle(bar, '::before').content !== 'none', hit, t: li ? li.querySelector('.lttm b').textContent : '' }; })()"""
WORD_BREAKS = """(() => [...document.querySelectorAll('#bookAir .zx-nm')].map(n => {
  const parts = n.innerHTML.split('<wbr>').map(h => { const d = document.createElement('div'); d.innerHTML = h; return d.textContent.length; });
  const ok = new Set(); let o = 0; for(const l of parts.slice(0, -1)){ o += l; ok.add(o); }
  const w = document.createTreeWalker(n, NodeFilter.SHOW_TEXT); let t, i = 0, prev = null; const bad = [];
  while((t = w.nextNode())){ for(let k = 0; k < t.length; k++, i++){ const r = document.createRange(); r.setStart(t, k); r.setEnd(t, k + 1); const rc = r.getClientRects()[0]; if(!rc) continue;
    const top = Math.round(rc.top); if(prev != null && top > prev + 4 && !ok.has(i)) bad.push(i); prev = top; } }
  return bad.length || n.scrollHeight > n.clientHeight + 2 || n.scrollWidth > n.clientWidth + 1 ? n.textContent : null; }).filter(Boolean))()"""
async def main():
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- 1 空の上（デモの30便） ----
        c, pg, errs = await demo_page(b, 390, 844)
        r = await pg.evaluate("""(() => { const es = fbEntries(), f = fbSum(es), st = passStats('all'); renderPassport();
          return { fb: f.min, pass: st.mins, fbEst: f.est, est: st.est, n: st.n, fn: f.n - es.filter(e => e.kind === 'book').length, txt: $('passport').innerText, want: fbDurTxt(f.min) }; })()""")
        check('1 成績の空の上の分 = フライトの空の上の分（同じ数え方）', r['fb'] == r['pass'] and r['fb'] > 0, (r['fb'], r['pass']))
        check('1 成績のパスポートにフライトと同じ書き方の時間（例 49時間20分）', r['want'] in r['txt'] and '1日16時間' not in r['txt'], (r['want'], r['txt'][:160]))
        check('1 推定の札はフライトと同じ決め方（推定を含む）', r['est'] == r['fbEst'] and (('推定を含む' in r['txt']) == r['est']), (r['est'], r['fbEst']))
        sh = await pg.evaluate("(async () => { const cv = await passCard('all'); return cv.width > 0; })()")
        check('1 共有の画像（passCard）が描ける', sh)
        # ---- 6 フライトの地図の「乗った区間」 ----
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(400)
        await pg.evaluate("(() => { const b = document.querySelector('#logViews [data-vw=\"log:map\"]'); if(b) b.click(); })()"); await pg.wait_for_timeout(600)
        m = await pg.evaluate("""(() => { const hs = [...document.querySelectorAll('#v-log h3.fbh')].map(h => h.innerText.replace(/\\s+/g, ' '));
          const fly = document.querySelector('#v-log .fbrts:not([data-fbcar])'), car = document.querySelector('#v-log .fbrts[data-fbcar]');
          const es = FB_ES.filter(e => fbYOf(e) === FB_Y), st = fbSum(es);
          return { hs, fly: fly ? fly.children.length : 0, car: car ? car.children.length : 0, carTxt: car ? car.innerText : '', rt: st.rt, flyCarOnly: fly ? [...fly.querySelectorAll('.w.dash')].length : -1 }; })()""")
        hf = next((h for h in m['hs'] if h.startswith('乗った区間')), '')
        check('6 「乗った区間」の数は便のある区間だけ（日誌の路線の数と同じ）', m['fly'] == m['rt'] and f"{m['rt']}区間" in hf and m['flyCarOnly'] == 0, (hf, m['fly'], m['rt']))
        check('6 車などだけの区間は下に別の一覧（福岡 ⇄ 長崎）', m['car'] >= 1 and any(h.startswith('車など') for h in m['hs']) and '長崎' in m['carTxt'], (m['hs'], m['carTxt'][:60]))
        await pg.screenshot(path=os.path.join(SHOTS, '06-flight-map-390.png'), full_page=True)
        check('ページのエラーがない（成績・フライト）', not errs, errs[:3])
        await c.close()
        # ---- 5 図鑑のお知らせ ----
        c, pg, errs = await demo_page(b, 390, 844)
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(400)
        check('5 前の見方を使っていない人（はじめての人・デモ）には出さない', await pg.locator('#zkNotice .zk-notice').count() == 0)
        await c.close()
        c, pg, errs = await demo_page(b, 390, 844, "localStorage.setItem('soramemo.view.book','tiles');")
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(400)
        check('5 タイルを使っていた人には出す', await pg.locator('#zkNotice .zk-notice').count() == 1)
        await c.close()
        c, pg, errs = await demo_page(b, 390, 844, "localStorage.setItem('soramemo.view.book','chron');")
        await pg.clock.set_fixed_time(datetime(2027, 1, 2, 10, 0, tzinfo=JST)); await pg.reload(); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(500)
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(400)
        check('5 2027年1月からは出さない', await pg.locator('#zkNotice .zk-notice').count() == 0)
        await c.close()
        # ---- 7 飛行場・滑空場・ヘリポートの図鑑 ----
        for w, h in [(390, 844), (375, 667)]:
            c, pg, errs = await demo_page(b, w, h)
            await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(400)
            await pg.click('#zkBody .zx-entry'); await pg.wait_for_timeout(600)
            g = await pg.evaluate("""(() => { const t = $('zkxTsume').getBoundingClientRect(), h = document.querySelector('#bookAir .book-head h2'), s = $('zkxSeg');
              const rr = el => { const r = document.createRange(); r.selectNodeContents(el); return Math.max(...[...r.getClientRects()].map(x => x.right)); };
              const fs = new Set([...document.querySelectorAll('#bookAir .zx-nm')].map(n => getComputedStyle(n).fontSize));
              return { tl: Math.round(t.left), h: Math.round(rr(h)), s: Math.round(s.getBoundingClientRect().right), dtag: document.querySelectorAll('#bookAir .zx-dtag').length, fs: [...fs] }; })()""")
            check(f'{w} 7 地方の見出しの札を外した', g['dtag'] == 0, g['dtag'])
            check(f'{w} 7 題と絞り込みの右端がツメから12px 以上離れる', g['h'] <= g['tl'] - 12 and g['s'] <= g['tl'] - 12, g)
            check(f'{w} 7 名前はどの枠も同じ字の大きさ（13px 以上）', len(g['fs']) == 1 and float(g['fs'][0][:-2]) >= 13, g['fs'])
            bad = await pg.evaluate(WORD_BREAKS)
            check(f'{w} 7 名前を字の途中で折らない・枠で切れない（スカイポー／ト など）', not bad, bad)
            await pg.evaluate("window.scrollBy(0, 520)"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(SHOTS, f'07-airbook-{w}.png'))
            check(f'{w} ページのエラーがない（図鑑）', not errs, errs[:3])
            await c.close()
        # ---- 3 遅れのページの送り方 ----
        for w, h in [(390, 844), (375, 667)]:
            STATE['bad'] = BAD46
            c, pg, errs = await server_page(b, w, h)
            await pg.evaluate("OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2000)
            await pg.evaluate("window.scrollTo(0, 0); document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1900)
            j = await pg.evaluate(LATE_GEOM)
            check(f'{w} 3 開いたら送る・「いまごろ」の札が上のボタンの帯の下', j['y'] > 200 and j['now'] is not None and j['now'] >= j['barB'] and j['now'] < h * 0.5 and j['t'] >= '14:30', j)
            check(f'{w} 3 送ったら帯に背景（中身がボタンの下にもぐって見えない）', j['stuck'] and j['bg'], j)
            await pg.screenshot(path=os.path.join(SHOTS, f'03-late-{w}.png'))
            await pg.evaluate("window.scrollTo(0, 0)"); await pg.wait_for_timeout(200)
            j0 = await pg.evaluate(LATE_GEOM)
            check(f'{w} 3 いちばん上では帯の背景なし', not j0['stuck'], j0)
            await c.close()
            STATE['bad'] = BAD5
            c, pg, errs = await server_page(b, w, h)
            await pg.evaluate("OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2000)
            await pg.evaluate("window.scrollTo(0, 0); document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1900)
            j = await pg.evaluate(LATE_GEOM)
            check(f'{w} 3 10行未満なら送らない（題・大きな数・絞り込みから見せる）', j['y'] == 0, j)
            await pg.screenshot(path=os.path.join(SHOTS, f'03-late5-{w}.png'))
            check(f'{w} ページのエラーがない（運用）', not errs, errs[:3])
            await c.close()
        # ---- 9 電波がないときのホーム（ウェブ） ----
        STATE['bad'] = BAD46
        c, pg, errs = await server_page(b, 390, 844)
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300)
        check('9 電波があるときは帯を出さない', await pg.evaluate("$('nvNetHome').hidden"))
        await c.set_offline(True); await pg.evaluate("window.dispatchEvent(new Event('offline'))"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({ h: $('nvNetHome').hidden, t: $('nvNetHome').innerText })")
        check('9 ウェブでも電波がないとホームに「電波がありません／チェックインは保留して…」', r['h'] is False and '電波がありません' in r['t'] and 'チェックインは保留して' in r['t'], r)
        await pg.evaluate("enqueue({ lat: 35.5497, lon: 139.7869, acc: 12, ts: Date.now() })"); await pg.wait_for_timeout(200)
        r = await pg.evaluate("$('nvNetHome').innerText")
        check('9 保留した印を1行（送っていない印 1）', '送っていない印 1' in r, r)
        await pg.screenshot(path=os.path.join(SHOTS, '09-home-offline-390.png'))
        await c.set_offline(False); await pg.evaluate("window.dispatchEvent(new Event('online'))"); await pg.wait_for_timeout(300)
        check('9 電波が戻ると帯を消す', await pg.evaluate("$('nvNetHome').hidden"))
        check('ページのエラーがない（ホーム）', not errs, errs[:3])
        await c.close()
        await b.close()
    print('errors', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
