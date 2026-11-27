import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用の「遅れ」の専用ページの絞り込み（11/22 19時 PM・本人「今日の遅れもフィルター機能をつけて」・checkin/delay-filter）
#   サーバーの airport_board が bad（今日の15分以上の遅れと欠航の便）を返したときだけ、便ごとの一覧と絞り込みを出す
#   1 種類（すべて・遅れ・欠航。数を小さく）・向き（すべて・出発・到着）・航空会社（一覧にいる会社だけ）・30分以上の遅れだけ、のそれぞれで数が合う
#   2 0件のときは「この条件の便はありません」の1枚（「絞り込みを戻す」で戻る）
#   3 絞り込みは端末に覚える（開き直しても同じ）。覚えた会社が今日いなければ「すべて」で見せる
#   4 字は13px以上（絞り込み・一覧・0件の1枚。出典の小さい字は今までどおり）・押す所は44px・横にはみ出さない（390・375・夜の色）
#   5 bad がないとき（今の本番）は前の時間ごとの札のまま
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, shutil
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import goto_http   # 開き直すので http で開く（file:// だと書いた localStorage を落とすことがある。11/23 案B と合わせて毎回落ちた）
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-delay-filter')); os.makedirs(SHOTS, exist_ok=True)
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat(); NOW = at(15, 0)
# 今日の遅れ・欠航の便（出発6・到着4。JAL 4・ANA 3・スカイマーク 2・AIRDO 1。欠航2）
def bf(dir, fl, other, h, m, late=None, cancel=False, actual=False):
    t = None if cancel or late is None else iso(h, m + late)
    return {'dir': dir, 'flight': fl, 'other': other, 'sched': iso(h, m), 'est': None if actual else t, 'actual': t if actual else None,
            'late': None if cancel else late, 'cancelled': cancel, 'intl': False, 'aircraft': None}
BAD = [bf('dep', 'JL105', 'ITM', 7, 0, 20), bf('dep', 'JL501', 'CTS', 8, 0, 45, actual=True), bf('arr', 'JL110', 'ITM', 9, 10, 16),
       bf('dep', 'JL903', 'OKA', 10, 0, cancel=True), bf('dep', 'NH15', 'ITM', 7, 30, 35), bf('arr', 'NH242', 'FUK', 11, 0, 18),
       bf('arr', 'NH988', 'KIX', 12, 5, cancel=True), bf('dep', 'BC511', 'FUK', 13, 0, 60), bf('arr', 'BC302', 'KOJ', 14, 0, 22), bf('dep', 'HD13', 'CTS', 14, 30, 31)]
def hours_of(bad):
    late = [0] * 24; can = [0] * 24
    for f in bad:
        h = int((datetime.fromisoformat(f['sched']).astimezone(JST)).hour)
        if f['cancelled']: can[h] += 1
        else: late[h] += 1
    return [{'h': h, 'flights': 10, 'late': late[h], 'cancel': can[h]} for h in range(24)]
def board(bad=BAD, with_bad=True):
    d = {'iata': 'HND', 'next_arr': [], 'next_dep': [], 'hours': hours_of(bad)}
    if with_bad: d['bad'] = bad
    return d
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, w=390, h=844, bd=None, extra='', ctx=None):
    c = ctx or await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', has_touch=True)
    if not ctx:
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
        async def hd(r):
            u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
            body = {'airport_board': bd or board(), 'special_now': [], 'airport-traffic': {'iata': 'HND', 'at': NOW.isoformat(), 'source': 'adsb.lol', 'planes': []},
                    'push-subscribe': {'key': None}}.get(name, {} if '/functions/' in u else [])
            try: await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
            except Exception: pass
        await c.route('https://fake.supabase.co/rest/**', hd); await c.route('https://fake.supabase.co/functions/**', hd)
        await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
                                "localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND');" + extra)
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await goto_http(pg, os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    await pg.evaluate("OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2200)
    await pg.evaluate("document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1200)
    return c, pg, errs
ST = """(() => { const q = s => [...document.querySelectorAll('#opsLate ' + s)];
  const seg = k => Object.fromEntries(q(`[data-ltf="${k}"]`).map(b => [b.dataset.v, { on: b.getAttribute('aria-pressed') === 'true', n: (b.querySelector('small') || {}).textContent || null }]));
  return { rows: q('.ltrows li').length, fl: q('.ltrows li .ltfl small').map(e => e.textContent.split('・')[0]), kind: seg('kind'), dir: seg('dir'), al: seg('al'),
    long: (q('[data-ltf="long"]')[0] || { getAttribute: () => null }).getAttribute('aria-checked'), zero: (q('.ltzero p')[0] || {}).textContent || '', big: (q('.ltbig b')[0] || {}).textContent }; })()"""
async def st(pg): return await pg.evaluate(ST)
async def tap(pg, k, v=None):
    sel = f'#opsLate [data-ltf="{k}"]' + (f'[data-v="{v}"]' if v else '')
    await pg.evaluate(f"document.querySelector('{sel}').click()"); await pg.wait_for_timeout(150)
LOOK = """(() => { const W = document.documentElement.clientWidth, box = $('opsLate'); const bad = [], small = [], tiny = [];
  box.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); if(!r.width || !r.height) return;
    if(!e.closest('.ltals') && (r.right > W + 0.5 || r.left < -0.5)) bad.push(e.className || e.tagName);
    const t = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if(t && e.closest('.ltfilt, .ltrows, .ltzero') && parseFloat(getComputedStyle(e).fontSize) < 13) small.push((e.className || e.tagName) + ':' + getComputedStyle(e).fontSize);
    if(e.matches('button') && e.closest('.ltfilt, .ltzero') && r.height < 44) tiny.push(e.textContent + ':' + Math.round(r.height)); });
  return { bad: bad.slice(0, 5), small: small.slice(0, 5), tiny: tiny.slice(0, 5), sw: document.documentElement.scrollWidth, W }; })()"""
async def main():
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs_all = []
        c, pg, errs = await page(b)
        r = await st(pg)
        check('0 はじめは全部（10便）・大きな数はカードと同じ', r['rows'] == 10 and r['big'] == '10', r)
        check('1 種類のピルに数（すべて10・遅れ8・欠航2）', r['kind']['all']['n'] == '10' and r['kind']['late']['n'] == '8' and r['kind']['cancel']['n'] == '2' and r['kind']['all']['on'], r['kind'])
        check('1 航空会社は一覧にいる会社だけ（すべて・JAL・ANA・スカイマーク・AIRDO の順）', list(r['al'].keys()) == ['all', 'JAL', 'ANA', 'スカイマーク', 'AIRDO'], list(r['al'].keys()))
        check('1 便は定刻の順', r['fl'][:3] == ['JL105', 'NH15', 'JL501'], r['fl'])
        await pg.screenshot(path=os.path.join(SHOTS, '01_all_390.png'), full_page=True)
        await tap(pg, 'kind', 'late'); r = await st(pg)
        check('1 遅れだけ → 8便', r['rows'] == 8 and r['kind']['late']['on'], r['rows'])
        await tap(pg, 'kind', 'cancel'); r = await st(pg)
        check('1 欠航だけ → 2便（JL903・NH988）', r['rows'] == 2 and sorted(r['fl']) == ['JL903', 'NH988'], r['fl'])
        await tap(pg, 'kind', 'all'); await tap(pg, 'dir', 'dep'); r = await st(pg)
        check('1 出発 → 6便・種類の数も出発で数え直す（遅れ5・欠航1）', r['rows'] == 6 and r['kind']['late']['n'] == '5' and r['kind']['cancel']['n'] == '1', (r['rows'], r['kind']))
        await tap(pg, 'dir', 'arr'); r = await st(pg)
        check('1 到着 → 4便', r['rows'] == 4, r['rows'])
        await tap(pg, 'dir', 'all'); await tap(pg, 'al', 'ANA'); r = await st(pg)
        check('1 ANA → 3便', r['rows'] == 3 and all(f.startswith('NH') for f in r['fl']), r['fl'])
        await tap(pg, 'al', 'all'); await tap(pg, 'long'); r = await st(pg)
        check('1 30分以上だけ → 遅れ4（JL501・NH15・BC511・HD13）＋欠航2 ＝ 6便', r['rows'] == 6 and r['long'] == 'true' and r['kind']['late']['n'] == '4', (r['rows'], r['fl']))
        await tap(pg, 'kind', 'late'); await tap(pg, 'al', 'スカイマーク'); r = await st(pg)
        check('1 重ねがけ：遅れ・スカイマーク・30分以上 → BC511 の1便', r['fl'] == ['BC511'], r['fl'])
        await pg.screenshot(path=os.path.join(SHOTS, '02_filtered_390.png'), full_page=True)
        await tap(pg, 'dir', 'arr'); r = await st(pg)
        check('2 0件のときは「この条件の便はありません」の1枚', r['rows'] == 0 and r['zero'] == 'この条件の便はありません', r)
        look = await pg.evaluate(LOOK)
        check('4 0件の1枚も字13px以上・押す所44px', not look['small'] and not look['tiny'], look)
        await pg.screenshot(path=os.path.join(SHOTS, '03_zero_390.png'), full_page=True)
        # 3 覚える：開き直しても同じ
        saved = await pg.evaluate("localStorage.getItem('soramemo.ops.lateFilter')")
        c2pg = await c.new_page(); await pg.close()
        pg = c2pg; await pg.clock.set_fixed_time(NOW); pg.on('pageerror', lambda e: errs.append(str(e)))
        await goto_http(pg, os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
        await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        await pg.evaluate("OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2200)
        await pg.evaluate("document.querySelector('[data-ohub=\"late\"]').click()"); await pg.wait_for_timeout(1200)
        r = await st(pg)
        check('3 開き直しても絞り込みは同じ（遅れ・到着・スカイマーク・30分以上）', r['kind']['late']['on'] and r['dir']['arr']['on'] and r['al']['スカイマーク']['on'] and r['long'] == 'true', (saved, r))
        await tap(pg, 'reset'); r = await st(pg)
        check('2 「絞り込みを戻す」で全部（10便）', r['rows'] == 10 and r['kind']['all']['on'] and r['long'] == 'false', r['rows'])
        errs_all += errs; await c.close()
        # 3 覚えた会社が今日いないとき
        c, pg, errs = await page(b, extra="localStorage.setItem('soramemo.ops.lateFilter', JSON.stringify({kind:'all',dir:'all',al:'ピーチ',long:false}));")
        r = await st(pg)
        check('3 覚えた会社（ピーチ）が今日いなければ「すべて」で見せる', r['rows'] == 10 and r['al']['all']['on'], r['rows'])
        errs_all += errs; await c.close()
        # 4 見た目：390・375・夜
        for w, h, night in ((390, 844, False), (375, 667, False), (390, 844, True)):
            c, pg, errs = await page(b, w, h, extra=("localStorage.setItem('soramemo.palette','board');" if night else ''))
            if night: await pg.evaluate("document.documentElement.dataset.palette = 'board'"); await pg.wait_for_timeout(200)
            look = await pg.evaluate(LOOK)
            tag = f'{w}' + ('・夜' if night else '')
            check(f'4 横にはみ出さない（{tag}）', not look['bad'] and look['sw'] <= look['W'], look)
            check(f'4 字は13px以上（{tag}）', not look['small'], look['small'])
            check(f'4 押す所は44px以上（{tag}）', not look['tiny'], look['tiny'])
            await pg.screenshot(path=os.path.join(SHOTS, f'04_look_{w}{"_night" if night else ""}.png'), full_page=True)
            errs_all += errs; await c.close()
        # 5 bad がないとき（今の本番）は前のまま
        c, pg, errs = await page(b, bd=board(with_bad=False))
        r = await pg.evaluate("({ hrs: document.querySelectorAll('#opsLate .lthrs li').length, filt: !!document.querySelector('#opsLate .ltfilt'), big: (document.querySelector('#opsLate .ltbig b') || {}).textContent })")
        check('5 bad がないときは時間ごとの札のまま・絞り込みは出さない', r['hrs'] > 0 and not r['filt'] and r['big'] == '10', r)
        errs_all += errs; await c.close()
        check('ページのエラーなし', not errs_all, errs_all[:3])
        await b.close()
    print('\n' + ('全部成功' if not fails else f'失敗 {len(fails)}件：' + ' / '.join(fails)))
    sys.exit(1 if fails else 0)
asyncio.run(main())
