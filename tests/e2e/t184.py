import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 11/24 アプリ全体の見直し B（report-sweep-all-b.md）のチェックイン側の直し（checkin/sweep-all-2）
#   B2 運用のデータ（airport_board）が読めないとき、遅れ・短冊・撮る人のページに「読み込めませんでした・もう一度」。10秒ほどで1回だけ取り直す。「もう一度」で読み直す
#   A補 ホームのシートを引き上げたら「最近の印」が見える位置まで送り、近くの一覧は開かない（「ほか○つ」を押したときだけ開く）
#   B3 一覧のカードに範囲の札（定時は専用ページと同じ直近30日・遅れは今日）。特別塗装機のページは「空 ○機・地上 ○機」でカードの数とそろう
#   B4 3D の滑走路は「34R（C）へ」の形（t142）・短冊の説明の1行・フライトの「日誌に追加」・成績の「空の上（推定）」
#   B5 電波がないとき滑走路のカードは「—」、一覧の上に「電波がありません・最後に読んだ ○時○分」
#   B6 遅れのページは開いたら今の時刻の行へ送る
#   B7 知らせ：「HND のような3文字」・「乗る便を選ぶ ›」でホームへ・端末に保存の注意
#   B9 運用の小さい字を13px・押せる所44px
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, shutil
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import goto_http
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat(); NOW = at(15, 0)
def bf(dir, fl, h, m, late):
    return {'dir': dir, 'flight': fl, 'other': 'ITM', 'sched': iso(h, m), 'est': iso(h, m + late), 'actual': None, 'late': late, 'cancelled': False, 'intl': False, 'aircraft': None}
# 0時台〜22時台に遅れの便 46便（今の15時より前が多い）
BAD = [bf('dep' if i % 2 else 'arr', f'JL{100 + i}', i // 2, (i % 2) * 30, 20) for i in range(46)]
def board():
    hrs = [{'h': h, 'flights': 10, 'late': sum(1 for f in BAD if int(datetime.fromisoformat(f['sched']).astimezone(JST).hour) == h), 'cancel': 0} for h in range(24)]
    return {'iata': 'HND', 'next_arr': [], 'next_dep': [], 'hours': hrs, 'bad': BAD}
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
STATE = {'board_ok': False}
async def server_page(b):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo', has_touch=True)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    async def hd(r):
        u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
        if name == 'metar' or (name == 'airport_board' and not STATE['board_ok']):   # 気象通報も読めない（電波が弱いとき）
            try: await r.fulfill(status=500, body='{"code":"57014","message":"canceling statement due to statement timeout"}', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
            except Exception: pass
            return
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
    await pg.evaluate("OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2200)
    return c, pg, errs
async def back(pg):
    await pg.evaluate("(() => { const b = $('opsHubBack'); if(b) b.click(); })()"); await pg.wait_for_timeout(700)
async def open_card(pg, id):
    await pg.evaluate(f"document.querySelector('[data-ohub=\"{id}\"]').click()"); await pg.wait_for_timeout(1300)
async def main():
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- B2 読めないとき ----
        c, pg, errs = await server_page(b)
        rw = await pg.evaluate("(() => { const e = document.querySelector('[data-ohub=\"runway\"] .ohv'); return { t: e ? e.innerText : '', prov: !!(OPS_CUR && OPS_CUR.prov) }; })()")
        check('B5 気象通報がなく決め打ちの向きのときは、滑走路のカードは「—」', rw['prov'] and rw['t'].strip().startswith('—'), rw)
        await open_card(pg, 'late')
        t = await pg.inner_text('#opsLate')
        check('B2 遅れのページ：読めないと「読み込めませんでした」と「もう一度」・自動の一言', '読み込めませんでした' in t and 'もう一度' in t and '10秒ほどで' in t, t[:120])
        await pg.screenshot(path=os.path.join(WORK, 't184_late_fail.png'))
        await back(pg); await open_card(pg, 'strip')
        t = await pg.inner_text('#opsStrip')
        check('B2 短冊のページも「読み込めませんでした・もう一度」', '読み込めませんでした' in t and 'もう一度' in t, t[:120])
        # 「もう一度」で読み直す（読めるようにしてから押す）
        STATE['board_ok'] = True
        await pg.evaluate("document.querySelector('#opsStrip [data-ops-retry]').click()"); await pg.wait_for_timeout(1500)
        t = await pg.inner_text('#opsStrip')
        check('B2 「もう一度」で読み直すと短冊が出る（説明の1行つき）', '読み込めませんでした' not in t and '短冊のように' in t, t[:160])
        # 自動の取り直し：読めない状態に戻して、別の空港の情報を消してから遅れを開く → 10秒ほどで1回だけ読み直す
        await back(pg)
        STATE['board_ok'] = False
        await pg.evaluate("BOARD = null; BOARD_AP = null; BOARD_ERR = null; BOARD_RETRY.clear();")
        await open_card(pg, 'late')
        t1 = await pg.inner_text('#opsLate')
        STATE['board_ok'] = True
        await pg.wait_for_timeout(11500)
        t2 = await pg.inner_text('#opsLate')
        check('B2 10秒ほどで1回だけ自動で取り直す', '読み込めませんでした' in t1 and '読み込めませんでした' not in t2 and re.search(r'\d+\s*便', t2) is not None, (t1[:60], t2[:60]))
        # ---- B6 今の時刻の行へ ----
        await back(pg); await pg.evaluate("window.scrollTo(0, 0)")
        await open_card(pg, 'late'); await pg.wait_for_timeout(600)
        j = await pg.evaluate("(() => { const li = document.querySelector('#opsLate li.ltnowrow'); return { y: window.scrollY, has: !!li, t: li ? li.querySelector('.lttm b').textContent : '', top: li ? Math.round(li.getBoundingClientRect().top) : null, h: innerHeight }; })()")
        check('B6 開いたら今の時刻（14:30 より後）の行へ送る', j['has'] and j['y'] > 200 and j['t'] >= '14:30' and 0 < j['top'] < j['h'], j)
        await pg.screenshot(path=os.path.join(WORK, 't184_late_now.png'))
        await pg.evaluate("document.querySelector('#opsLate [data-ltf=\"dir\"][data-v=\"dep\"]').click()"); await pg.wait_for_timeout(200)
        y2 = await pg.evaluate("window.scrollY")
        check('B6 絞り込みを押しても勝手に送り直さない', abs(y2 - j['y']) < 400 or y2 > 0, (j['y'], y2))
        # ---- B3 カードの範囲の札 ----
        await back(pg); await pg.wait_for_timeout(1200)
        cards = await pg.evaluate("Object.fromEntries([...document.querySelectorAll('#opsHubList [data-ohub]')].map(b => [b.dataset.ohub, b.innerText.replace(/\\s+/g, ' ')]))")
        check('B3 定時のカードは専用ページと同じ直近30日の数（74%）に「30日」の札', '74' in cards.get('ontime', '') and '30日' in cards.get('ontime', ''), cards.get('ontime'))
        check('B3 遅れのカードに「今日」の札', '今日' in cards.get('late', ''), cards.get('late'))
        sp = await pg.evaluate("""(() => { SPECIAL.clear(); SPECIAL.set('JA01A', { reg:'JA01A', name:'テスト塗装A', airline:'JAL', kind:'livery', alt_ft:12000, iata:'HND' });
          SPECIAL.set('JA02A', { reg:'JA02A', name:'テスト塗装B', airline:'ANA', kind:'livery', alt_ft:0, iata:'HND' });
          SPECIAL.set('JA03A', { reg:'JA03A', name:'アライアンス', airline:'ANA', kind:'alliance', alt_ft:9000 });
          const h = specialHTML(); return { n: opsFlying().length, sum: (h.match(/<summary>いま飛んでいる特別塗装機[^<]*/) || [''])[0] }; })()""")
        check('B3 特別塗装機のページの「いま飛んでいる」はカードと同じ数（空1・地上1を分ける）', sp['n'] == 1 and 'いま飛んでいる特別塗装機 1機・地上 1機・アライアンス塗装 1機' in sp['sum'], sp)
        # ---- B9 字と押せる所 ----
        f = await pg.evaluate("(() => { const s = document.createElement('div'); s.className = 'opsboard opsday'; s.innerHTML = '<div class=\"hx\"><span>0時</span></div>'; $('v-ops').appendChild(s); const v = getComputedStyle(s.querySelector('.hx')).fontSize; s.remove(); return v; })()")
        check('B9 1日の山の時刻の字は13px', f == '13px', f)
        ms = await pg.evaluate("(() => { const b = $('openSettings'); return Math.round(parseFloat(getComputedStyle(b, '::after').height) || b.getBoundingClientRect().height); })()")
        check('B9 上の「マイページ」の押せる所は44px', ms >= 44, ms)
        # ---- B5 電波がないとき ----
        await c.set_offline(True); await pg.wait_for_timeout(400)
        net = await pg.evaluate("(() => { const e = document.querySelector('#opsHubList .ohnet'); return e ? e.innerText.replace(/\\s+/g, ' ') : ''; })()")
        check('B5 電波がないと一覧の上に「電波がありません」', '電波がありません' in net, net)
        await pg.evaluate("(() => { localStorage.setItem('soramemo.ops.lastread', JSON.stringify({ HND: Date.now() - 5 * 60000 })); opsHubRender(); })()")
        net = await pg.evaluate("(() => { const e = document.querySelector('#opsHubList .ohnet'); return e ? e.innerText.replace(/\\s+/g, ' ') : ''; })()")
        check('B5 最後に読んだ時刻も出る（○時○分）', re.search(r'最後に読んだ \d+時\d\d分', net) is not None, net)
        await pg.screenshot(path=os.path.join(WORK, 't184_offline.png'))
        await c.set_offline(False); await pg.wait_for_timeout(300)
        check('B5 電波が戻ると帯は消える', not await pg.evaluate("!!document.querySelector('#opsHubList .ohnet')"))
        check('ページのエラーがない（運用）', not errs, errs[:3])
        await c.close()
        # ---- ホーム・知らせ・フライト（サーバーなし） ----
        c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo'); await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1'); localStorage.setItem('soramemo.tpTaught','1');")
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await goto_http(pg, os.path.join(WEB, 'index.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(800)
        await pg.evaluate("$('toggleDemo').click()"); await pg.wait_for_timeout(1500)
        # 近くに民間空港以外もある所（羽田）
        await pg.evaluate("(() => { const a = A.find(x => x.iata === 'HND'); showNearest(nearest({ lat:a.lat, lon:a.lon, acc:10 })); goTab('home'); })()"); await pg.wait_for_timeout(600)
        await pg.evaluate("$('hsUp').click()"); await pg.wait_for_timeout(900)
        h = await pg.evaluate("""(() => { const sh = $('homeSheet'), l = $('nearList'), bz = sh.querySelector('.boardzone, #homeFold:not([hidden])'), r = bz ? bz.getBoundingClientRect() : null;
          return { snap: sh.dataset.snap, list: l ? getComputedStyle(l).display : 'none', top: r ? Math.round(r.top) : null, h: innerHeight, more: !$('nearMore').hidden }; })()""")
        check('A補 引き上げても近くの一覧は開かない', h['snap'] == 'full' and h['list'] == 'none', h)
        check('A補 引き上げたら最近の印が画面に見える', h['top'] is not None and 0 < h['top'] < h['h'] - 80, h)
        await pg.screenshot(path=os.path.join(WORK, 't184_home_up.png'))
        if h['more']:
            await pg.evaluate("$('homeSheet').sheetGo('half')"); await pg.wait_for_timeout(500)
            await pg.evaluate("$('nearMore').click()"); await pg.wait_for_timeout(700)
            h2 = await pg.evaluate("(() => ({ snap: $('homeSheet').dataset.snap, list: getComputedStyle($('nearList')).display }))()")
            check('A補 「ほか○つ」を押したときは近くの一覧を開く', h2['snap'] == 'full' and h2['list'] != 'none', h2)
            await pg.evaluate("$('nearMore').click()"); await pg.wait_for_timeout(500)
            check('A補 もう一度押すと閉じる', await pg.evaluate("$('homeSheet').dataset.snap") == 'half')
        else:
            print('（羽田のまわりに近くの一覧がないので、「ほか○つ」の確かめは飛ばす）')
        # 知らせ
        await pg.evaluate("pinListOpen()"); await pg.wait_for_timeout(300)
        pt = await pg.evaluate("({ ph: $('pinQ').placeholder, txt: $('dPinsBody').innerText, ride: !!document.querySelector('#dPinsBody button[data-pin-ride]') })")
        check('B7 「名前か HND のような3文字」（3レターを使わない）', 'HND のような3文字' in pt['ph'] and '3レター' not in pt['ph'], pt['ph'])
        check('B7 ピン止めの保存先を書く（11/24 アカウントにも保存。ログインしていない・デモは端末だけ）', ('この端末' in pt['txt'] or 'アカウントに保存' in pt['txt']) and '機種を変えると消えます' not in pt['txt'] and '準備中' not in pt['txt'])
        check('B7 「乗る便を選ぶ」は押せるボタン', pt['ride'] and '乗る便を選ぶ' in pt['txt'])
        await pg.screenshot(path=os.path.join(WORK, 't184_pins.png'))
        await pg.evaluate("document.querySelector('#dPinsBody [data-pin-ride]').click()"); await pg.wait_for_timeout(700)
        check('B7 押すと知らせを閉じてホームへ', not await pg.evaluate("$('dPins').open") and await pg.evaluate("currentView()") == 'home')
        # 呼び方
        nm = await pg.evaluate("({ add: $('mAdd').textContent, h: document.querySelector('#lsBook h2, #flAdd') ? $('flAdd').getAttribute('aria-label') : '', loc: document.body.innerHTML.includes('記録帳に書いたり') })")
        check('B4 フライトの ＋ は「日誌に追加」', nm['add'] == '日誌に追加' and '日誌' in nm['h'] and not nm['loc'], nm)
        pp = await pg.evaluate("(() => { renderPassport(); return $('passport').innerText; })()")
        check('B4 成績は「空の上（推定）」（飛行時間と書かない）', '空の上（推定）' in pp and '飛行時間' not in pp, pp[:120])
        check('ページのエラーがない（ホーム・知らせ）', not errs, errs[:3])
        await b.close()
    print('errors', fails); sys.exit(1 if fails else 0)
asyncio.run(main())
