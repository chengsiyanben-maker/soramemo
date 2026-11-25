import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-ops-3d')); os.makedirs(SHOTS, exist_ok=True)
THREE=os.path.join(WORK, 'three-0.160.0.module.min.js')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from three_local import ensure_three; ensure_three(THREE)   # 自分で用意する（t142 に頼らない・11/26 test-steady）
# 運用タブの一覧に「3D」のカード（11/21 本人「3Dの入口がわかりにくいから、運用にも追加して」・ブランチ checkin/ops-3d）
#   1 羽田を選んでいるときだけ、「地図」のカードのすぐ後に「3D」のカード（見出し1語＋小さな絵＋「約○MB」を小さく薄いグレー）
#   2 ほかの空港（伊丹）では出ない
#   3 押すと今の3D の画面（dAp3d）を開く。専用ページにはしない（一覧のまま）
#   4 字は13px以上・押す所は44px以上・横にはみ出さない（390×844・375×667）
#   5 鉛筆のシート（隠す・出す）と表示の編集の1枚に「「3D」のカード」の ON／OFF。OFF でカードが消え、ON で戻る。全部の数（loCount）は変わらない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
NOW = at(15, 0)
BOARD = {'iata': 'HND', 'next_arr': [], 'next_dep': [], 'hours': []}
SPECIAL = []
PLANES = []
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
MEASURE = """(sel) => { const out = { small: [], tiny: [], wide: [] }; const W = document.documentElement.clientWidth;
  document.querySelectorAll(sel).forEach(root => root.querySelectorAll('*').forEach(el => { const r = el.getBoundingClientRect(); if(!r.width || !r.height) return;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); const fs = parseFloat(getComputedStyle(el).fontSize);
    if(own && fs < 13) out.small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12) + ':' + fs);
    if((el.tagName === 'BUTTON' || el.tagName === 'FORM') && el.closest('.opsbar,#opsHubList') && (r.height < 44)) out.tiny.push(el.tagName + ':' + (el.textContent || el.placeholder).trim().slice(0, 10) + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
    if(r.right > W + 1 || r.left < -1) out.wide.push(el.tagName + ':' + el.className + ':' + Math.round(r.left) + '-' + Math.round(r.right)); }));
  return out; }"""
async def page(b, w=390, h=844, extra='', reduce=False):
    c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', has_touch=True, reduced_motion='reduce' if reduce else 'no-preference')
    await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(path=THREE, content_type='application/javascript') if os.path.exists(THREE) else r.fulfill(status=404, body=''))
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    async def hd(r):
        u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
        body = {'airport_board': BOARD, 'special_now': SPECIAL, 'airport-traffic': {'iata': 'HND', 'at': NOW.isoformat(), 'source': 'adsb.lol', 'planes': PLANES},
                'metar': {'id': 'RJTT', 'time': NOW.isoformat(), 'raw': 'TEST', 'wdir': 340, 'wspd': 7, 'wgst': None, 'vis_m': 10000, 'vis_plus': True},
                'push-subscribe': {'key': None}}.get(name, {} if '/functions/' in u else [])
        await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/rest/**', hd); await c.route('https://fake.supabase.co/functions/**', hd)
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
                            "localStorage.setItem('soramemo.persona','all'); " + extra)
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2500)
    return c, pg, errs
async def visible(pg, sel):
    return await pg.evaluate("(s => { const e = document.querySelector(s); if(!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })(%s)" % json.dumps(sel))
AP = lambda c: "localStorage.setItem('soramemo.opsAirport','%s');" % c
CARDS = "[...document.querySelectorAll('#opsHubList [data-ohub]')].map(x => x.dataset.ohub)"
async def main():
    import shutil
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs_all = []
        c, pg, errs = await page(b, extra=AP('HND'))
        ids = await pg.evaluate(CARDS)
        check('1 羽田：「3D」のカードが「地図」のすぐ後', 'a3' in ids and ids.index('a3') == ids.index('map') + 1, ids)
        r = await pg.evaluate("""(() => { const e = document.querySelector('[data-ohub="a3"]'); const t = e.querySelector('.oht'), s = e.querySelector('.ohv small'), svg = e.querySelector('svg.oh3d');
          return { t: t.textContent, s: s && s.textContent, sc: s && getComputedStyle(s).color, sub: getComputedStyle(document.querySelector('#v-ops')).getPropertyValue('--op-sub').trim(), fs: s && parseFloat(getComputedStyle(s).fontSize),
            art: !!svg && svg.getBoundingClientRect().width > 30, wide: e.classList.contains('wide'), aria: e.getAttribute('aria-label'), size: A3_SIZE }; })()""")
        check('1 見出しは1語「3D」・小さな絵・「約○MB」（今の3D の入口と同じ大きさの字）', r['t'] == '3D' and r['art'] and r['s'] == r['size'] and r['size'].startswith('約') and r['size'].endswith('MB'), r)
        check('1 「約○MB」は小さく薄いグレー（13px・--op-sub）', r['fs'] == 13 and r['sc'] != 'rgb(17, 24, 39)', r)
        check('1 読み上げ：「3Dの羽田を開く（押すと約○MBを読み込みます）」', '3Dの羽田を開く' in r['aria'] and r['size'] in r['aria'], r['aria'])
        m = await pg.evaluate(MEASURE, '#v-ops')
        check('4 一覧（390×844）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.evaluate("document.querySelector('[data-ohub=\"a3\"]').scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '01_list_hnd_390.png'))
        await pg.evaluate("window.scrollTo(0, 0)")
        # 3 押すと3D
        await pg.click('[data-ohub="a3"]'); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ open: $('dAp3d').open, a3: !!A3, page: OPS_PAGE, hub: $('v-ops').dataset.hub })")
        check('3 押すと今の3D の画面（dAp3d）が開く', r['open'] and r['a3'], r)
        check('3 専用ページにはしない（一覧のまま）', r['page'] is None and r['hub'] == 'list', r)
        await pg.screenshot(path=os.path.join(SHOTS, '02_open_3d_390.png'))
        await pg.evaluate("closeAp3d()"); await pg.wait_for_timeout(300)
        check('3 閉じると運用の一覧に戻る', await pg.evaluate("!$('dAp3d').open && $('v-ops').dataset.hub === 'list' && currentView() === 'ops'"))
        # 5 鉛筆のシート
        n0 = await pg.evaluate("loCount().all")
        await pg.evaluate("document.querySelector('#opsHubList [data-vs-open=\"ops\"]').click()"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("(() => { const b = document.querySelector('#dViews [data-vs-a3]'); return { has: !!b, on: b && b.getAttribute('aria-checked'), txt: $('dViewsBody').innerText }; })()")
        check('5 鉛筆のシートに「「3D」のカード」の ON／OFF（はじめ ON）', r['has'] and r['on'] == 'true' and '「3D」のカード' in r['txt'], r['txt'][-200:])
        m = await pg.evaluate(MEASURE, '#dViews')
        m['small'] = [x for x in m['small'] if x != 'B:ON:11.5' and x != 'B:OFF:11.5']   # スイッチの中の「ON／OFF」の札は今の部品のまま（11/9 の決定の形）
        check('4 鉛筆のシート：字13px以上（スイッチの札は除く）・はみ出しなし', not m['small'] and not m['wide'], m)
        await pg.evaluate("document.querySelector('#dViews [data-vs-a3]').scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=os.path.join(SHOTS, '03_sheet_390.png'))
        await pg.evaluate("document.querySelector('#dViews [data-vs-a3]').click()"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("({ on: document.querySelector('#dViews [data-vs-a3]').getAttribute('aria-checked'), lay: LAYOUT && LAYOUT.opsA3, undo: ($('dViewsBody').querySelector('.tpundo') || {}).innerText || '', n: loCount().all })")
        check('5 OFF にすると LAYOUT.opsA3 = 0・「元に戻す」の帯', r['on'] == 'false' and r['lay'] == 0 and '「3D」のカードを隠しました' in r['undo'], r)
        check('5 全部の数（loCount）は変わらない', r['n'] == n0, (n0, r['n']))
        await pg.evaluate("$('dViews').close()"); await pg.wait_for_timeout(200)
        ids = await pg.evaluate(CARDS)
        check('5 OFF のあいだ一覧に「3D」のカードは出ない', 'a3' not in ids and 'map' in ids, ids)
        # 表示の編集の1枚
        await pg.evaluate("openLayout('ops', 'screen')"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("(() => { const b = document.querySelector('#dLayout [data-lo-a3]'); return { has: !!b, on: b && b.getAttribute('aria-checked') }; })()")
        check('5 表示の編集の1枚（運用（空港））にも同じ行（OFF のまま見える）', r['has'] and r['on'] == 'false', r)
        await pg.evaluate("document.querySelector('#dLayout [data-lo-a3]').scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=os.path.join(SHOTS, '04_layout_off_390.png'))
        await pg.evaluate("document.querySelector('#dLayout [data-lo-a3]').click()"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("({ on: document.querySelector('#dLayout [data-lo-a3]').getAttribute('aria-checked'), lay: LAYOUT ? LAYOUT.opsA3 : null })")
        check('5 表示の編集で ON に戻す', r['on'] == 'true' and r['lay'] is None, r)
        await pg.evaluate("$('dLayout').close()"); await pg.wait_for_timeout(300)
        ids = await pg.evaluate(CARDS)
        check('5 ON に戻すと一覧に「3D」のカードが戻る', 'a3' in ids and ids.index('a3') == ids.index('map') + 1, ids)
        errs_all += errs; await c.close()
        # 2 ほかの空港
        c, pg, errs = await page(b, extra=AP('ITM'))
        r = await pg.evaluate("({ ap: OPS_AP, ids: %s })" % CARDS)
        check('2 伊丹では「3D」のカードを出さない', r['ap'] == 'ITM' and 'a3' not in r['ids'] and len(r['ids']) >= 5, r)
        await pg.evaluate("document.querySelector('#opsHubList [data-vs-open=\"ops\"]').click()"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("!!document.querySelector('#dViews [data-vs-a3]')")
        check('5 鉛筆のシートの行は空港によらず出す（羽田で出るカードの設定）', r)
        errs_all += errs; await c.close()
        # 4 375×667
        c, pg, errs = await page(b, 375, 667, extra=AP('HND'))
        m = await pg.evaluate(MEASURE, '#v-ops')
        check('4 一覧（375×667）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.evaluate("document.querySelector('[data-ohub=\"a3\"]').scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '05_list_hnd_375.png'))
        errs_all += errs; await c.close()
        # 夜の画面
        c, pg, errs = await page(b, extra=AP('HND'))
        await pg.evaluate("document.documentElement.dataset.night = 'on'"); await pg.wait_for_timeout(200)   # 夜の画面（参考の写真）
        await pg.evaluate("document.querySelector('[data-ohub=\"a3\"]').scrollIntoView({ block: 'center' })"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '06_list_hnd_night_390.png'))
        errs_all += errs; await c.close()
        await b.close()
        print('errors', errs_all + fails)
        if errs_all or fails: sys.exit(1)
asyncio.run(main())
