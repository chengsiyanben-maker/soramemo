import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用タブを一覧＋専用ページに（11/19 の決定・design/ops-hub 1版 案A・ブランチ checkin/ops-hub）
#   1 一覧：頭は空港のピル＋i、機体の検索窓は上に残す、カードは10枚（見出し1語＋大きな数字か絵）。「空港｜機体」と見方のタブは出さない
#   2 カードを押すと専用ページ（広がる動き 約0.46秒）。「‹ 運用」で戻る（約0.38秒）。戻るとカードに戻る
#   3 左端から引いて戻る（指の操作 CDP Input.dispatchTouchEvent）
#   4 10枚どれを押しても専用ページになり、その中身が見える
#   5 動きを減らす設定の人には動きなし
#   6 i は出典と注意のシート
#   7 検索窓から機体の1日（専用ページ）
#   8 字は13px以上・押す所は44px以上・横にはみ出さない（390×844・375×667）
#   9 隠す・出すは今の見方の設定（鉛筆のシート）。隠した見方のカードは出ない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat(); NOW = at(15, 0)
BOARD = {'iata': 'HND', 'next_arr': [{'flight': 'JL110', 'other': 'ITM', 'sched': iso(15, 18), 't': iso(15, 18), 'est': None, 'actual': None, 'aircraft': 'B767'}],
         'next_dep': [{'flight': 'NH241', 'other': 'FUK', 'sched': iso(15, 2), 't': iso(15, 2), 'est': None, 'actual': None, 'aircraft': 'B787'}],
         'hours': [{'h': h, 'flights': f, 'late': l, 'cancel': 0} for h, f, l in zip(range(24), [0,0,0,0,0,1,8,20,24,22,20,18,19,20,21,22,23,24,22,20,16,10,4,1], [0,0,0,0,0,0,1,2,3,2,1,1,1,2,2,1,0,0,0,0,0,0,0,0])]}
SPECIAL = [{'reg': 'JA819A', 'name': 'ポケモンジェット 赤', 'airline': 'ANA', 'callsign': 'ANA1', 'kind': 'livery', 'lat': 35.6, 'lon': 139.9, 'alt_ft': 3000, 'iata': 'HND', 'phase': 'arr'},
           {'reg': 'JA01XJ', 'name': 'A350 1号機', 'airline': 'JAL', 'callsign': 'JAL5', 'kind': 'livery', 'lat': 34.0, 'lon': 135.0, 'alt_ft': 30000, 'iata': None, 'phase': None}]
# 作り物の機体：羽田（35.55・139.78）の南の進入（34 に向かう 5機）が地図の「空港のまわり」の範囲の中に入るように置く（11/19 22時45分 PM の指示で置き直し）。
#   6機目は遠く（約85km 北）の出発機：数（6機）には入るが、地図カードの絵の外なので印は描かない
PLANES = [{'id': 't%d' % i, 'callsign': 'TST%d' % i, 'lat': 35.515 + i * .006, 'lon': 139.80, 'alt_ft': 2000, 'kt': 150, 'hdg': 340, 'fpm': -700, 'phase': 'arr', 'dist_km': 7, 'type': 'B738', 'reg': 'JA%03dA' % i} for i in range(5)] \
       + [{'id': 't9', 'callsign': 'FAR9', 'lat': 36.32, 'lon': 139.80, 'alt_ft': 20000, 'kt': 400, 'hdg': 0, 'fpm': 2000, 'phase': 'dep', 'dist_km': 85, 'type': 'B789', 'reg': 'JA999A'}] \
       + [{'id': 't8', 'callsign': 'OVR8', 'lat': 35.56, 'lon': 139.79, 'alt_ft': 35000, 'kt': 450, 'hdg': 90, 'fpm': 0, 'phase': 'other', 'dist_km': 1, 'type': 'A359', 'reg': 'B-18901'}]
#   7機目は真上を通るだけの機体（phase other）：地図にも出さず、カードの数にも入れない（11/20 本人）
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
                            "localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND');" + extra)
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2500)
    return c, pg, errs
async def visible(pg, sel):
    return await pg.evaluate("(s => { const e = document.querySelector(s); if(!e) return false; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })(%s)" % json.dumps(sel))
async def main():
    import shutil
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs_all = []
        c, pg, errs = await page(b)
        # 1 一覧
        r = await pg.evaluate("({ hub: $('v-ops').dataset.hub, n: document.querySelectorAll('#opsHubList [data-ohub]').length, ids: [...document.querySelectorAll('#opsHubList [data-ohub]')].map(x => x.dataset.ohub), txt: $('opsHubList').innerText })")
        check('1 一覧に10枚のカード（滑走路・地図・案内板・特別塗装機・遅れ・短冊・1日の山・定時・空の道すじ・撮る人）＋羽田だけの「3D」（地図のすぐ後。11/21）', r['hub'] == 'list' and r['ids'] == ['runway','map','a3','board','special','late','strip','day','ontime','art','photo'], r['ids'])
        check('1 「空港｜機体」と見方のタブは出さない', not await visible(pg, '#opsSide') and not await visible(pg, '#opsViews') and not await visible(pg, '#opsAside'))
        check('1 頭は空港のピル＋i、検索窓は上に残す（案A）', await visible(pg, '#opsApBtn') and await visible(pg, '#opsInfoBtn') and await visible(pg, '#opsPlForm'))
        t = r['txt']
        check('1 カードの数字：滑走路は北風・地図は6機（上空を通るだけの1機は数えない）・案内板は15:18着', '北風' in t and '6機' in t.replace('\n', '').replace(' ', ''), t.replace('\n', ' ')[:200])
        r = await pg.evaluate("[...document.querySelectorAll('[data-ohub=\"map\"] .ohplanes [data-ohpl]')].map(e => e.dataset.ohpl)")
        check('1 地図カードの絵に今の機体の印（近い5機・絵の外の遠い機体は描かない）', sorted(r) == ['TST0','TST1','TST2','TST3','TST4'], r)
        r = await pg.evaluate("(() => { const s = document.querySelector('[data-ohub=\"map\"] .ohart').getBoundingClientRect(); return [...document.querySelectorAll('[data-ohub=\"map\"] [data-ohpl]')].every(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.left >= s.left - 1 && r.right <= s.right + 1 && r.top >= s.top - 1 && r.bottom <= s.bottom + 1; }); })()")
        check('1 地図カードの機体の印はカードの中に見える', r)
        check('1 カードの数字：特別塗装機・短冊・定時が数で出る', '15:18' in t and '分後' in t and '%' in t, t.replace('\n', ' ')[:200])
        m = await pg.evaluate(MEASURE, '#v-ops')
        check('8 一覧（390）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't148_list_844.png'), full_page=True)
        # 2 開く・戻る
        y0 = await pg.evaluate("document.querySelector('[data-ohub=\"runway\"]').getBoundingClientRect().top")
        await pg.evaluate("document.querySelector('[data-ohub=\"runway\"]').click()"); await pg.wait_for_timeout(200)
        mid = await pg.evaluate("$('v-ops').style.clipPath")
        await pg.screenshot(path=os.path.join(WORK, 't148_open_mid.png'))
        await pg.wait_for_timeout(450)
        r = await pg.evaluate("({ hub: $('v-ops').dataset.hub, page: $('v-ops').dataset.page, clip: $('v-ops').style.clipPath, view: VIEW.ops })")
        check('2 滑走路のカードを押すと、広がる動き（途中は clip-path）', mid.startswith('inset('), mid)
        check('2 約0.46秒で専用ページ（動きが終わったら clip-path なし）', r['hub'] == 'page' and r['page'] == 'runway' and r['clip'] == '' and r['view'] == 'runway', r)
        check('2 専用ページ：「‹ 運用」と i、滑走路の中身が見え、地図は出さない', await visible(pg, '#opsHubBack') and await visible(pg, '#opsInfoBtn') and await visible(pg, '#opsInfo') and not await visible(pg, '#opsMap') and not await visible(pg, '#opsHubList'))
        check('2 専用ページ：「空港｜機体」と見方のタブは出さない', not await visible(pg, '#opsSide') and not await visible(pg, '#opsViews'))
        m = await pg.evaluate(MEASURE, '.opsbar')
        check('8 専用ページの頭：字・押す所・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't148_runway_844.png'))
        await pg.evaluate("$('opsHubBack').click()"); await pg.wait_for_timeout(150)
        mid = await pg.evaluate("$('v-ops').style.clipPath"); await pg.wait_for_timeout(400)
        r = await pg.evaluate("({ hub: $('v-ops').dataset.hub, f: document.activeElement && document.activeElement.dataset.ohub })")
        check('2 「‹ 運用」で戻る（カードの位置へ縮む・約0.38秒）', mid.startswith('inset(') and r['hub'] == 'list', (mid, r))
        check('2 戻るとカードに戻る（押したカードに焦点）', r['f'] == 'runway', r)
        # 3 左端から引いて戻る
        cdp = await c.new_cdp_session(pg)
        await pg.evaluate("document.querySelector('[data-ohub=\"board\"]').click()"); await pg.wait_for_timeout(700)
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 6, 'y': 400}]})
        for k in range(1, 11):
            await cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 6 + k * 22, 'y': 402}]}); await pg.wait_for_timeout(16)
        tf = await pg.evaluate("$('v-ops').style.transform")
        await pg.screenshot(path=os.path.join(WORK, 't148_swipe_mid.png'))
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); await pg.wait_for_timeout(600)
        r = await pg.evaluate("$('v-ops').dataset.hub")
        check('3 左端から引くとページが指に付いて右へ動き、小さくなる', 'translateX' in tf and 'scale' in tf, tf)
        check('3 離すと一覧に戻る', r == 'list', r)
        await pg.evaluate("document.querySelector('[data-ohub=\"board\"]').click()"); await pg.wait_for_timeout(700)
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 200, 'y': 400}]})
        for k in range(1, 8): await cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 200 + k * 20, 'y': 402}]})
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); await pg.wait_for_timeout(400)
        check('3 真ん中から右へ引いても戻らない（左端からだけ）', await pg.evaluate("$('v-ops').dataset.hub") == 'page')
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 6, 'y': 400}]})
        for k in range(1, 4): await cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 6 + k * 10, 'y': 402}]}); await pg.wait_for_timeout(40)
        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); await pg.wait_for_timeout(400)
        check('3 左端から少しだけゆっくり引いたときは戻らず元の位置へ', await pg.evaluate("$('v-ops').dataset.hub") == 'page' and await pg.evaluate("$('v-ops').style.transform") == '')
        await pg.evaluate("$('opsHubBack').click()"); await pg.wait_for_timeout(600)
        # 4 10枚それぞれ
        SHOW = {'runway': '#opsInfo', 'map': '#opsMap', 'board': '#opsBoard', 'special': '#opsPSpecial', 'late': '#opsAlerts', 'strip': '#opsStrip', 'day': '#opsDay', 'ontime': '#opsOntime', 'art': '#opsArt', 'photo': '#opsPhoto'}
        for cid, sel in SHOW.items():
            await pg.evaluate("document.querySelector('[data-ohub=\"%s\"]').click()" % cid); await pg.wait_for_timeout(1500)
            r = await pg.evaluate("({ hub: $('v-ops').dataset.hub, page: $('v-ops').dataset.page })")
            v = await visible(pg, sel) if cid not in ('late', 'ontime', 'art') else True   # 遅れ・定時・空の道すじは、その日のデータがあるときだけ欄が出る（偽のサーバーでは空）
            m = await pg.evaluate(MEASURE, '.opsbar')
            check(f'4 「{cid}」を押すと専用ページ（{sel} が見える・頭のはみ出しなし）', r['hub'] == 'page' and r['page'] == cid and v and not m['wide'], (r, v, m['wide']))
            if cid == 'map':
                r = await pg.evaluate("(() => { const m = $('opsMap').getBoundingClientRect(); const els = [...document.querySelectorAll('#opsMap .tplane')]; return { all: els.length, inside: els.filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.left >= m.left && r.right <= m.right && r.top >= m.top && r.bottom <= m.bottom; }).length }; })()")
                check('4 地図の専用ページ：着陸に向かう5機の印が地図の中に出る', r['inside'] == 5, r)
                r = await pg.evaluate("({ tin: (document.querySelector('#trafficNote [data-tin]') || {}).dataset, tout: (document.querySelector('#trafficNote [data-tout]') || {}).dataset, txt: $('trafficNote').innerText })")
                check('4 凡例に「この範囲に 5機」', r['tin'] and r['tin'].get('tin') == '5' and 'この範囲に' in r['txt'], r)
                check('4 範囲の外の1機は「ほかの1機は『経路の全体』で見られます」の1行', r['tout'] and r['tout'].get('tout') == '1' and 'ほかの1機は『経路の全体』で見られます' in r['txt'], r)
                m = await pg.evaluate(MEASURE, '#trafficNote')
                check('8 凡例：字13px以上・はみ出しなし', not m['small'] and not m['wide'], m)
                await pg.screenshot(path=os.path.join(WORK, 't148_map_legend_844.png'))
                await pg.evaluate("document.querySelector('#trafficNote [data-tout]').click()"); await pg.wait_for_timeout(1200)
                r = await pg.evaluate("({ scope: OPS_SCOPE, pressed: document.querySelector('.opsscope [data-scope=\"wide\"]').getAttribute('aria-pressed'), tin: (document.querySelector('#trafficNote [data-tin]') || {}).dataset, tout: !!document.querySelector('#trafficNote [data-tout]') })")
                check('4 その1行を押すと「経路の全体」に切り替わり、6機がこの範囲に入って1行は消える', r['scope'] == 'wide' and r['pressed'] == 'true' and r['tin'] and r['tin'].get('tin') == '6' and not r['tout'], r)
                await pg.screenshot(path=os.path.join(WORK, 't148_map_wide_844.png'))
                await pg.evaluate("document.querySelector('.opsscope [data-scope=\"near\"]').click()"); await pg.wait_for_timeout(800)
            if cid in ('map', 'special', 'photo'): await pg.screenshot(path=os.path.join(WORK, f't148_{cid}_844.png'))
            await pg.evaluate("$('opsHubBack').click()"); await pg.wait_for_timeout(600)
            if await pg.evaluate("$('v-ops').dataset.hub") != 'list': check(f'4 「{cid}」から戻れる', False)
        # 6 i
        await pg.evaluate("$('opsInfoBtn').click()"); await pg.wait_for_timeout(300)
        r = await pg.evaluate("({ open: $('dOpsSrc').open, t: $('dOpsSrcBody').innerText })")
        check('6 i は出典と注意のシート（adsb.lol・ODPT・気象通報・保証しません）', r['open'] and 'adsb.lol' in r['t'] and 'ODPT' in r['t'] and '気象通報' in r['t'] and '保証しません' in r['t'], r['t'][:80])
        m = await pg.evaluate(MEASURE, '#dOpsSrc')
        check('8 出典と注意のシート：字13px以上・はみ出しなし', not m['small'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't148_src_844.png'))
        await pg.evaluate("$('dOpsSrc').close()")
        # 7 検索窓
        await pg.fill('#opsPlQ', 'JA819A'); await pg.press('#opsPlQ', 'Enter'); await pg.wait_for_timeout(1500)
        r = await pg.evaluate("({ hub: $('v-ops').dataset.hub, page: $('v-ops').dataset.page, reg: OPS_PL_REG })")
        check('7 検索窓から機体の1日を専用ページで', r['hub'] == 'page' and r['page'] == 'plane' and r['reg'] == 'JA819A', r)
        await pg.evaluate("$('opsHubBack').click()"); await pg.wait_for_timeout(600)
        check('7 戻ると一覧（空港の側）', await pg.evaluate("$('v-ops').dataset.hub === 'list' && opsSide() === 'ap'"))
        # 9 隠す
        await pg.evaluate("(() => { const L = loEdit(); L.off = L.off || {}; })()")
        r = await pg.evaluate("(() => { const b = document.querySelector('#opsHubList [data-vs-open=\"ops\"]'); return b ? b.textContent : ''; })()")
        check('9 一覧の下に「隠す・出す」（見方の設定を開く）', r == '隠す・出す', r)
        await pg.evaluate("document.querySelector('#opsHubList [data-vs-open=\"ops\"]').click()"); await pg.wait_for_timeout(400)
        check('9 「隠す・出す」で見方のシートが開く', await pg.evaluate("$('dViews').open"))
        await pg.evaluate("$('dViews').close()")
        errs_all += errs; await c.close()
        # 5 動きを減らす
        c, pg, errs = await page(b, reduce=True)
        await pg.evaluate("document.querySelector('[data-ohub=\"runway\"]').click()"); await pg.wait_for_timeout(60)
        r = await pg.evaluate("({ clip: $('v-ops').style.clipPath, hub: $('v-ops').dataset.hub })")
        check('5 動きを減らす設定では動きなしですぐ専用ページ', r['clip'] == '' and r['hub'] == 'page', r)
        errs_all += errs; await c.close()
        # 8 375×667
        c, pg, errs = await page(b, 375, 667)
        m = await pg.evaluate(MEASURE, '#v-ops')
        check('8 一覧（375×667）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(WORK, 't148_list_667.png'))
        errs_all += errs; await c.close()
        # 10 前の形（試験用の切り替え）
        c, pg, errs = await page(b, extra="localStorage.setItem('soramemo.ops.hub','0');")
        r = await pg.evaluate("({ hub: $('v-ops').dataset.hub || '', list: $('opsHubList').hidden })")
        check('10 soramemo.ops.hub=0 なら前の形（見方のタブ）', r['hub'] == '' and r['list'] and await visible(pg, '#opsViews'), r)
        errs_all += errs; await c.close()
        await b.close()
        print('errors', errs_all + fails)
        if errs_all or fails: sys.exit(1)
asyncio.run(main())
