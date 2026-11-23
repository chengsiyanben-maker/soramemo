import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-reorder')); os.makedirs(SHOTS, exist_ok=True)
# 並べ替え（11/22 本人「いろんなやつの順序を入れ替えられるように」・ブランチ checkin/reorder）
#   1 運用の一覧の右上に「並べ替え」。押すと編集の形（各カードの右上に ≡・カードを押しても開かない・下は「はじめの並びに戻す」）
#   2 マウスで ≡ を持って動かすと並びが変わり、layout.order.ohub に覚える（端末。ログインしていればサーバーの prefs にも入る）
#   3 指は 0.25秒押してから動かす（すぐ動かしたときは並べ替えない）
#   4 キーの矢印・読み上げ用の「上へ」「下へ」のボタンでも動く。焦点はつまみに残る
#   5 隠しているカードは前の場所のまま
#   6 完了で元の形（押すと開く）。開き直しても並びが残る。「はじめの並びに戻す」で戻り、全部乗せのまま（loAllOn）
#   7 ホームに出すもの：「並べ替え」で行に ≡（スイッチの代わり）。動かすとホームのシートの並びも変わる。はじめの並びに戻す
#   8 編集の形でも、字13px以上・押す所44px以上（読み上げ用のボタンを除く）・横にはみ出さない（390×844・375×667）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
NOW = (base + timedelta(hours=15)).astimezone(timezone.utc)
BOARD = {'iata': 'HND', 'next_arr': [], 'next_dep': [], 'hours': []}
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
MEASURE = """(sel) => { const out = { small: [], tiny: [], wide: [] }; const W = document.documentElement.clientWidth;
  document.querySelectorAll(sel).forEach(root => root.querySelectorAll('*').forEach(el => { const r = el.getBoundingClientRect(); if(!r.width || !r.height) return;
    if(el.classList.contains('rokb')) return;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); const fs = parseFloat(getComputedStyle(el).fontSize);
    if(own && fs < 13 && !el.closest('.hepc small')) out.small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12) + ':' + fs);
    if(el.tagName === 'BUTTON' && r.height < 44 && !el.closest('.mp-back')) out.tiny.push(el.tagName + ':' + el.className + ':' + el.textContent.trim().slice(0, 10) + ':' + Math.round(r.width) + 'x' + Math.round(r.height));
    if(r.right > W + 1 || r.left < -1) out.wide.push(el.tagName + ':' + el.className + ':' + Math.round(r.left) + '-' + Math.round(r.right)); }));
  return out; }"""
async def page(b, w=390, h=844, extra='', ctx=None):
    c = ctx or await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', has_touch=True)
    if not ctx:
        await c.route('https://cdn.jsdelivr.net/npm/three@**', lambda r: r.fulfill(status=404, body=''))
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
        async def hd(r):
            u = r.request.url; name = u.split('fake.supabase.co')[1].split('?')[0].rsplit('/', 1)[-1]
            body = {'airport_board': BOARD, 'special_now': [], 'airport-traffic': {'iata': 'HND', 'at': NOW.isoformat(), 'source': 'adsb.lol', 'planes': []},
                    'push-subscribe': {'key': None}}.get(name, {} if '/functions/' in u else [])
            await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
        await c.route('https://fake.supabase.co/rest/**', hd); await c.route('https://fake.supabase.co/functions/**', hd)
        await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
        await c.add_init_script("if(!sessionStorage.getItem('t167')){ sessionStorage.setItem('t167','1'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
                                "localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND'); " + extra + " }")
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true; goTab('ops')"); await pg.wait_for_timeout(2000)
    return c, pg, errs
CARDS = "[...document.querySelectorAll('#opsHubList .ohc')].map(x => x.dataset.ohub || x.dataset.ro)"
CENTER = "(s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })"
UPPER = "(s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left + r.width * 0.3, r.top + r.height * 0.25]; })"   # 前へ入れるときは相手の左上の方まで
async def drag(pg, frm, to, steps=12):
    a = await pg.evaluate(CENTER + '(%s)' % json.dumps(frm)); bb = await pg.evaluate(UPPER + '(%s)' % json.dumps(to))
    await pg.mouse.move(*a); await pg.mouse.down()
    for i in range(1, steps + 1):
        await pg.mouse.move(a[0] + (bb[0] - a[0]) * i / steps, a[1] + (bb[1] - a[1]) * i / steps); await pg.wait_for_timeout(16)
    return a, bb
# 指の動き（pointerType touch の PointerEvent を順に送る）
TOUCH = """async ([sel, to, hold]) => { const h = document.querySelector(sel), r = h.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
  const t = document.querySelector(to).getBoundingClientRect(), tx = t.left + t.width * 0.3, ty = t.top + t.height * 0.25;
  const ev = (type, cx, cy, el) => (el || h).dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, pointerId: 7, pointerType: 'touch', isPrimary: true, clientX: cx, clientY: cy, button: 0 }));
  const wait = ms => new Promise(f => setTimeout(f, ms));
  ev('pointerdown', x, y); await wait(hold);
  for(let i = 1; i <= 10; i++){ ev('pointermove', x + (tx - x) * i / 10, y + (ty - y) * i / 10); await wait(16); }
  ev('pointerup', tx, ty); await wait(50); }"""
async def main():
    import shutil
    shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
    if not os.path.exists(os.path.join(WORK, 'config.js')):
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs_all = []
        c, pg, errs = await page(b)
        ids0 = await pg.evaluate(CARDS)
        r = await pg.evaluate("""(() => { const b = document.querySelector('#opsHubList [data-oh-ro]'), l = document.querySelector('#opsHubList').getBoundingClientRect(), r = b.getBoundingClientRect();
          return { t: b.textContent.trim(), h: r.height, right: Math.round(l.right - r.right), top: Math.round(r.top - l.top), first: document.querySelector('#opsHubList').firstElementChild.className }; })()""")
        check('1 一覧の右上に「並べ替え」（押す所44px）', r['t'] == '並べ替え' and r['h'] >= 44 and r['right'] <= 4 and r['top'] <= 4, r)
        await pg.screenshot(path=os.path.join(SHOTS, '01_ops_list_390.png'))
        await pg.click('#opsHubList [data-oh-ro]'); await pg.wait_for_timeout(200)
        r = await pg.evaluate("""(() => { const L = document.querySelector('#opsHubList'); const cards = [...L.querySelectorAll('.ohc')];
          return { n: cards.length, grips: L.querySelectorAll('.ohc [data-ro-h]').length, btn: cards.filter(c => c.tagName === 'BUTTON').length, done: L.querySelector('[data-oh-ro]').textContent.trim(),
            foot: L.lastElementChild.textContent.trim(), footDis: L.lastElementChild.disabled, lead: (L.querySelector('.ohrolead') || {}).textContent }; })()""")
        check('1 編集の形：全部のカードに ≡・カードはボタンでない・右上は「完了」・下は「はじめの並びに戻す」（まだ押せない）', r['n'] == len(ids0) and r['grips'] == r['n'] and r['btn'] == 0 and r['done'] == '完了' and r['foot'] == 'はじめの並びに戻す' and r['footDis'], r)
        await pg.click('#opsHubList .ohc[data-ro="board"] .oht'); await pg.wait_for_timeout(300)
        check('1 編集の形ではカードを押しても開かない', await pg.evaluate("OPS_PAGE") is None)
        m = await pg.evaluate(MEASURE, '#opsHubList')
        check('8 編集の形（390×844）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(SHOTS, '02_ops_edit_390.png'))
        # 2 マウスで「案内板」を「滑走路」の前へ
        await drag(pg, '#opsHubList [data-ro-h="board"]', '#opsHubList .ohc[data-ro="runway"]')
        await pg.screenshot(path=os.path.join(SHOTS, '03_ops_dragging_390.png'))
        await pg.mouse.up(); await pg.wait_for_timeout(200)
        ids1 = await pg.evaluate(CARDS)
        saved = await pg.evaluate("(JSON.parse(localStorage.getItem('soramemo.layout') || '{}').order || {}).ohub")
        check('2 マウスで動かすと並びが変わる（案内板が先頭）', ids1[0] == 'board' and sorted(ids1) == sorted(ids0), ids1)
        check('2 端末に覚える（layout.order.ohub）', isinstance(saved, list) and saved[0] == 'board', saved)
        check('2 サーバーに送る中身にも入る（vpPrefs）', await pg.evaluate("((vpPrefs().layout || {}).order || {}).ohub?.[0]") == 'board')
        check('2 動かしたあとも編集の形のまま・「はじめの並びに戻す」が押せる', await pg.evaluate("OH_EDIT && !document.querySelector('[data-oh-rodef]').disabled"))
        # 3 指：すぐ動かすと並べ替えない／0.25秒押してから動かすと並べ替える
        before = await pg.evaluate(CARDS)
        await pg.evaluate(TOUCH, ['#opsHubList [data-ro-h="late"]', '#opsHubList .ohc[data-ro="board"]', 0])
        check('3 指ですぐ動かしたときは並べ替えない', await pg.evaluate(CARDS) == before, await pg.evaluate(CARDS))
        await pg.evaluate(TOUCH, ['#opsHubList [data-ro-h="late"]', '#opsHubList .ohc[data-ro="board"]', 320])
        ids2 = await pg.evaluate(CARDS)
        check('3 指で0.25秒押してから動かすと並べ替える（遅れが先頭）', ids2[0] == 'late', ids2)
        # 4 キーの矢印
        await pg.focus('#opsHubList [data-ro-h="late"]'); await pg.keyboard.press('ArrowDown'); await pg.wait_for_timeout(150)
        ids3 = await pg.evaluate(CARDS)
        foc = await pg.evaluate("document.activeElement.dataset.roH")
        live = await pg.evaluate("($('roLive') || {}).textContent")
        check('4 矢印のキーで1つ動く・焦点はつまみに残る', ids3[1] == 'late' and foc == 'late', [ids3[:3], foc])
        await pg.wait_for_timeout(100)
        live = await pg.evaluate("($('roLive') || {}).textContent")
        check('4 読み上げ：「○○」を2番目にしました', '「遅れ」を2番目にしました' in (live or ''), live)
        # 4 読み上げ用の「上へ」
        await pg.focus('#opsHubList [data-ro-mv="-1"][data-ro-id="late"]')
        vis = await pg.evaluate("document.activeElement.getBoundingClientRect().width > 20")
        await pg.keyboard.press('Enter'); await pg.wait_for_timeout(150)
        ids4 = await pg.evaluate(CARDS)
        check('4 「上へ」のボタン（焦点が来ると見える）で1つ上へ', vis and ids4[0] == 'late', [vis, ids4[:3]])
        await pg.screenshot(path=os.path.join(SHOTS, '04_ops_kb_390.png'))
        # 5 隠しているカードは前の場所のまま
        await pg.evaluate("loToggleOff('ops', 'strip', true); loChanged('t'); opsHubRender()"); await pg.wait_for_timeout(150)
        pos_strip = await pg.evaluate("ohOrder().indexOf('strip')")
        await pg.evaluate("document.querySelector('#opsHubList [data-ro=\"photo\"]').scrollIntoView({ block: 'end' })"); await pg.wait_for_timeout(100)
        await drag(pg, '#opsHubList [data-ro-h="photo"]', '#opsHubList .ohc[data-ro="day"]'); await pg.mouse.up(); await pg.wait_for_timeout(150)
        r = await pg.evaluate("({ o: ohOrder(), strip: ohOrder().indexOf('strip') })")
        o5 = r['o']; check('5 隠しているカード（短冊）は前の場所のまま・見えているカードは動く（撮る人が1日の山の前）', o5.index('photo') < o5.index('day') and r['strip'] == pos_strip, [pos_strip, r])
        await pg.evaluate("window.scrollTo(0, 0)")
        await pg.evaluate("loToggleOff('ops', 'strip', false); loChanged('t'); opsHubRender()"); await pg.wait_for_timeout(150)
        # 6 完了 → 押すと開く
        await pg.click('#opsHubList [data-oh-ro]'); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({ edit: OH_EDIT, btn: document.querySelectorAll('#opsHubList button.ohc[data-ohub]').length, grips: document.querySelectorAll('#opsHubList [data-ro-h]').length, ids: " + CARDS + " })")
        check('6 完了で元の形（カードはボタン・≡ なし）。新しい並びのまま', not r['edit'] and r['btn'] > 5 and r['grips'] == 0 and r['ids'] == [x for x in o5 if x in r['ids']], r)
        await pg.screenshot(path=os.path.join(SHOTS, '05_ops_after_390.png'))
        await pg.click('#opsHubList [data-ohub="late"]'); await pg.wait_for_timeout(900)
        check('6 完了のあとは押すと専用ページが開く', await pg.evaluate("OPS_PAGE") == 'late')
        await pg.evaluate("opsHubBack()"); await pg.wait_for_timeout(700)
        order_now = await pg.evaluate(CARDS)
        # 開き直し
        await pg.close()
        c, pg, errs2 = await page(b, ctx=c); errs += errs2
        check('6 開き直しても並びが残る', await pg.evaluate(CARDS) == order_now, await pg.evaluate(CARDS))
        await pg.click('#opsHubList [data-oh-ro]'); await pg.wait_for_timeout(150)
        await pg.click('#opsHubList [data-oh-rodef]'); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({ ids: " + CARDS + ", all: loAllOn(), dis: document.querySelector('[data-oh-rodef]').disabled })")
        check('6 「はじめの並びに戻す」で戻る・全部乗せのまま（loAllOn）・ボタンはまた押せなくなる', r['ids'] == ids0 and r['all'] and r['dis'], r)
        await pg.click('#opsHubList [data-oh-ro]'); await pg.wait_for_timeout(150)
        # 7 ホームに出すもの
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(500)
        await pg.evaluate("openHomeEd('screen')"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(SHOTS, '06_home_ed_390.png'))
        await pg.click('#dHomeEd [data-he-ro]'); await pg.wait_for_timeout(200)
        r = await pg.evaluate("""(() => { const d = $('dHomeEd'); return { grips: d.querySelectorAll('.hepc [data-ro-h]').length, sw: d.querySelectorAll('.hepc.ro .losw').length, n: loOrder('home').length,
          fixGrip: d.querySelectorAll('.hepc.fix [data-ro-h]').length, pill: d.querySelector('[data-he-ro]').textContent.trim(), rodef: !!d.querySelector('[data-he-rodef]'), dis: d.querySelector('[data-he-rodef]').disabled }; })()""")
        check('7 並べ替えの形：動かせる行に ≡（スイッチの代わり）・「いつも」の行は動かせない・「完了」', r['grips'] == r['n'] and r['sw'] == 0 and r['fixGrip'] == 0 and r['pill'] == '完了' and r['rodef'] and r['dis'], r)
        m = await pg.evaluate(MEASURE, '#dHomeEd .hehd, #dHomeEd .helead, #dHomeEd .hepc.ro, #dHomeEd .rodef')   # 前からある見本の札などは除く
        check('8 ホームに出すもの・並べ替えの形（390×844）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        first_mv = await pg.evaluate("loOrder('home')[0]")
        await drag(pg, '#dHomeEd [data-ro-h="recent"]', '#dHomeEd .hepc[data-ro="%s"]' % first_mv)
        await pg.screenshot(path=os.path.join(SHOTS, '07_home_dragging_390.png'))
        await pg.mouse.up(); await pg.wait_for_timeout(250)
        r = await pg.evaluate("({ o: loOrder('home'), dom: [...document.querySelectorAll('#homeBlocks > .lo')].map(x => x.dataset.lo.split(':')[1]), saved: (JSON.parse(localStorage.getItem('soramemo.layout') || '{}').order || {}).home })")
        check('7 動かすと並びが変わり、ホームのシートも同じ並びになる（最近の印が先）', r['o'][0] == 'recent' and r['dom'][0] == 'recent' and (r['saved'] or [None])[0] == 'recent', r)
        await pg.screenshot(path=os.path.join(SHOTS, '08_home_edit_390.png'))
        await pg.click('#dHomeEd [data-he-rodef]'); await pg.wait_for_timeout(200)
        r = await pg.evaluate("({ o: loOrder('home'), def: loOrderDef('home'), all: loAllOn() })")
        check('7 はじめの並びに戻す（全部乗せのまま）', r['o'] == r['def'] and r['all'], r)
        await pg.click('#dHomeEd [data-he-ro]'); await pg.wait_for_timeout(150)
        check('7 完了でスイッチの形に戻る', await pg.evaluate("$('dHomeEd').querySelectorAll('.hepc .losw').length > 3 && !$('dHomeEd').querySelector('[data-ro-h]')"))
        errs_all += errs; await c.close()
        # 375×667
        c, pg, errs = await page(b, 375, 667)
        await pg.click('#opsHubList [data-oh-ro]'); await pg.wait_for_timeout(200)
        m = await pg.evaluate(MEASURE, '#opsHubList')
        check('8 編集の形（375×667）：字13px以上・押す所44px以上・はみ出しなし', not m['small'] and not m['tiny'] and not m['wide'], m)
        await pg.screenshot(path=os.path.join(SHOTS, '09_ops_edit_375.png'))
        await pg.evaluate("document.documentElement.dataset.night = 'on'"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '10_ops_edit_night_375.png'))
        errs_all += errs; await c.close()
        await b.close()
        print('errors', errs_all + fails)
        if errs_all or fails: sys.exit(1)
asyncio.run(main())
