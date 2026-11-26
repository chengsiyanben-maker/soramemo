import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json, shutil
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import goto_http
# 11/24 マイページ案B（design/mypage-tiles の B1・B2・本人 OK）・成績の修行の部分を入口1枚に（その3）・知らせのピン止めをアカウントにも保存（checkin/mypage-b）
#   1 マイページ：成績を横長の1枚（16空港・30便・24,017km・車などの1行）＋修行・知らせ。タブにある画面はタイルにしない。外したタブだけタイルが増える
#   2 設定は5行の目次。押すと1枚のページ（戻るは「マイページ」）。各ページの中の行が出る
#   3 成績：「ステータスの目安」「修行のまとめ」「修行の計画」が出ない。修行の入口1枚（今のポイント）を押すと修行の画面。あの日の空は別の行
#   4 ピン止め：ログインで my_pins を読み、サーバーが null なら端末の分を上げる・行があればサーバーの分にそろえる・変えたら my_pins_put・conflict はサーバーの分を出し直す
SHOTS = os.path.join(WORK, 't189'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
async def demo_page(b, w, h, persona='all'):
    c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=1, timezone_id='Asia/Tokyo')
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.add_init_script(f"localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1'); localStorage.setItem('soramemo.persona','{persona}');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(500)
    await pg.evaluate('openMyPage("adv")'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(700)
    return c, pg, errs
async def server_page(b, extra):
    c = await b.new_context(viewport={'width':390,'height':844})
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');" + extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    return c, pg, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- 1・2 マイページ（デモ・全部乗せ） ----
        for w, h in [(390, 844), (375, 667)]:
            c, pg, errs = await demo_page(b, w, h)
            await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(250)
            await pg.screenshot(path=os.path.join(SHOTS, f'01-mypage-{w}.png'))
            t = await pg.inner_text('#mpTiles')
            chips = await pg.inner_text('#mpChips')
            if w == 390:
                check('頭の札に空港・フライトの数を出さない', 'フライト' not in chips, chips.replace('\n', ' '))
                check('成績のタイル：16空港・30便・24,017km・図鑑 16/86', re.search(r'16\s*空港', t) and re.search(r'30\s*便', t) and '24,017' in t and '図鑑 16/86' in t, t.replace('\n', ' ')[:160])
                check('成績のタイルに車などの1行', '車など 1（90 km）は便と距離に入れず、別に数えています' in t)
                check('修行のタイル（ポイントと「○まで ○%」）', re.search(r'修行\s*[\d,]+\s*(PP|FOP)', t) is not None and re.search(r'まで \d+%', t) is not None, t.replace('\n', ' '))
                check('知らせのタイル「0 / 12 空港」', re.search(r'知らせ\s*0\s*/ 12 空港', t) is not None)
                ks = await pg.evaluate("[...document.querySelectorAll('#mpTiles .mt .k')].map(e => e.textContent)")
                check('全部乗せではタイルは成績・修行・知らせの3枚（タブにある図鑑・フライト・運用は出さない）', ks == ['成績', '修行', '知らせ'], ks)
                n = await pg.inner_text('#mpTNote')
                check('タブ帯の言い方', '図鑑・フライト・いまの空港は下のタブ帯から' in n, n)
                idx = await pg.evaluate("[...document.querySelectorAll('#mpIdx b')].map(e => e.textContent)")
                check('設定は5行の目次', idx == ['表示の編集', 'データとバックアップ', '表示と色', 'アカウント', '詳しい設定'], idx)
                vis = await pg.evaluate("[...document.querySelectorAll('#dSettings .mp-sec')].filter(e => e.offsetParent).length")
                check('目次のときは設定の中身を出さない', vis == 0, vis)
                # 各ページ
                for k, title, sel in [('lo', '表示の編集', '[data-tp-open]'), ('data', 'データとバックアップ', '[data-export="json"]'), ('show', '表示と色', '.swatch'), ('acct', 'アカウント', '#acctLocal'), ('adv', '詳しい設定', '#toggleDemo')]:
                    await pg.click(f'#mpIdx [data-mp-page="{k}"]'); await pg.wait_for_timeout(150)
                    r = await pg.evaluate(f"({{ t:$('mpTitle').textContent, back:$('mpBackT').textContent, home:!!$('mpHome').offsetParent, sel:!!document.querySelector('{sel}').offsetParent, others:[...document.querySelectorAll('#dSettings .mp-sec')].filter(e => e.offsetParent && e.dataset.mpSec !== '{k}').length }})")
                    check(f'目次から「{title}」のページ', r['t'] == title and r['back'] == 'マイページ' and not r['home'] and r['sel'] and r['others'] == 0, r)
                    if k == 'data':
                        bk = await pg.inner_text('#mpBk'); check('データとバックアップの箱（デモの言い方）', 'デモ' in bk, bk.replace('\n', ' '))
                        await pg.screenshot(path=os.path.join(SHOTS, '02-data-390.png'))
                    await pg.click('#mpBack'); await pg.wait_for_timeout(120)
                    check(f'「{title}」から戻ると目次', await pg.evaluate("!!$('mpHome').offsetParent && $('dSettings').open && !$('dSettings').dataset.mpPage"))
                await pg.click('#mpBack'); await pg.wait_for_timeout(120)
                check('目次の戻るはマイページを閉じる', not await pg.evaluate("$('dSettings').open"))
                # 知らせのタイル → 知らせの画面
                await pg.evaluate('openMyPage()'); await pg.click('#mpTiles [data-pins-open]'); await pg.wait_for_timeout(200)
                check('知らせのタイルで知らせの画面', await pg.evaluate("$('dPins').open"))
                note = await pg.inner_text('#dPinsBody')
                check('「機種を変えると消えます」「準備中」がない', '機種を変えると消えます' not in note and '準備中' not in note)
                await pg.evaluate("$('dPins').close()")
                # 修行のタイル → 修行
                await pg.click('#mpTiles [data-persona-open="sg"]'); await pg.wait_for_timeout(300)
                check('修行のタイルで修行の画面', await pg.evaluate("currentView() === 'sg' && !$('dSettings').open"))
                # 押せる大きさ・はみ出し
                await pg.evaluate('openMyPage()')
                sz = await pg.evaluate("[...document.querySelectorAll('#mpTiles .mt, #mpIdx button, #mpBack')].map(e => Math.round(e.getBoundingClientRect().height))")
                check('タイル・目次・戻るは高さ 44px 以上', min(sz) >= 44, sz)
            ov = await pg.evaluate("document.querySelector('#dSettings').scrollWidth <= document.querySelector('#dSettings').clientWidth + 1")
            check(f'{w}px で横にはみ出さない', ov)
            check(f'JS のエラーがない（{w}）', not errs, errs[:3])
            await c.close()
        # ---- 外したタブはタイルが増える（気軽に：図鑑・フライトだけのタブ） ----
        c, pg, errs = await demo_page(b, 390, 844, 'casual')
        await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(200)
        ks = await pg.evaluate("[...document.querySelectorAll('#mpTiles .mt .k')].map(e => e.textContent)")
        check('タブから外した運用はタイルになる', ks == ['成績', '修行', '知らせ', 'いまの空港'], ks)
        await pg.click('#mpTiles [data-persona-open="ops"]'); await pg.wait_for_timeout(400)
        check('運用のタイルで運用の画面', await pg.evaluate("currentView() === 'ops'"))
        await c.close()
        # ---- 3 成績 ----
        c, pg, errs = await demo_page(b, 390, 844)
        await pg.evaluate('openMyPage()'); await pg.click('#mpTiles [data-persona-open="stats"]'); await pg.wait_for_timeout(500)
        st = await pg.inner_text('#v-stats')
        check('成績タイルで成績の画面', await pg.evaluate("currentView() === 'stats'"))
        check('成績に「ステータスの目安」「修行のまとめ」「修行の計画」が出ない', all(x not in st for x in ['ステータスの目安', '修行のまとめ', '修行の計画', 'この路線に乗ったら']), st[-300:].replace('\n', ' '))
        sg = await pg.inner_text('#stSg')
        check('修行の入口1枚に今のポイント', re.search(r'[\d,]+\s*(PP|FOP)', sg) is not None and '修行の画面を開く' in sg, sg.replace('\n', ' '))
        check('あの日の空は別の行', await pg.locator('#v-stats .strow[data-thatday]').is_visible())
        await pg.locator('#stSg').scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(SHOTS, '03-stats-390.png'))
        await pg.click('#stSg'); await pg.wait_for_timeout(400)
        check('修行の入口を押すと修行の画面', await pg.evaluate("currentView() === 'sg' || $('dShugyo').open"))
        cnt = await pg.evaluate("LO_BLOCKS.stats.map(b => b[0])")
        check('成績のかたまりは5つ（status＝入口・thatday）', cnt == ['passport', 'fleet', 'airline', 'status', 'thatday'], cnt)
        check('JS のエラーがない（成績）', not errs, errs[:3])
        await c.close()
        # ---- 4 ピン止めをアカウントへ ----
        # (a) サーバーが null・端末にピン → 上げる
        c, pg, errs = await server_page(b, "window.__pinRpc = true; localStorage.setItem('soramemo.pins', JSON.stringify([{k:'HND', sp:true, dl:false, ga:false}, {k:'#9999999', sp:false}]));")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
        puts = await pg.evaluate('window.__pinPuts || []')
        check('はじめてのログイン：サーバーが null なら端末のピン止めを上げる', len(puts) == 1 and [x['k'] for x in puts[0]['p_pins']] == ['HND'] and puts[0]['p_rev'] is None, puts)
        await pg.evaluate("pinAdd('CTS')"); await pg.wait_for_timeout(900)
        puts = await pg.evaluate('window.__pinPuts || []')
        check('足したら my_pins_put（rev を付ける）', len(puts) == 2 and [x['k'] for x in puts[1]['p_pins']] == ['HND', 'CTS'] and puts[1]['p_rev'] == 1, puts[-1:])
        await pg.evaluate("pinListOpen()"); t = await pg.inner_text('#dPinsBody')
        check('ログイン中は「アカウントに保存しています」', 'アカウントに保存しています' in t)
        await pg.evaluate("$('dPins').close()")
        # (b) 別の端末が先に直していた → サーバーの分を出し直す
        await pg.evaluate("window.__pinRow = {pins:[{k:'FUK', sp:true, dl:true, ga:false}], spot:null, rev:9}")
        await pg.evaluate("pinAdd('OKA')"); await pg.wait_for_timeout(900)
        loc = await pg.evaluate("pins().map(p => p.k)")
        check('conflict ならサーバーの分にそろえる', loc == ['FUK'], loc)
        check('JS のエラーがない（ピン止め a・b）', not errs, errs[:3])
        await c.close()
        # (c) サーバーに行がある → 端末をそろえる（端末の分は上げない）
        c, pg, errs = await server_page(b, "window.__pinRpc = true; window.__pinRow = {pins:[{k:'ITM', sp:false, dl:true, ga:false}], spot:null, rev:3}; localStorage.setItem('soramemo.pins', JSON.stringify([{k:'HND', sp:true}]));")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
        loc = await pg.evaluate("pins()")
        check('サーバーに行があれば端末をそろえる', [x['k'] for x in loc] == ['ITM'] and loc[0]['dl'] is True and not await pg.evaluate('(window.__pinPuts || []).length'), loc)
        await c.close()
        # (d) 関数がない古いサーバー → 端末だけ（エラーにしない）
        c, pg, errs = await server_page(b, "localStorage.setItem('soramemo.pins', JSON.stringify([{k:'HND', sp:true}]));")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.evaluate("pinAdd('CTS')"); await pg.wait_for_timeout(600)
        check('関数がないサーバーでは端末に残すだけ', await pg.evaluate("pins().map(p => p.k).join()") == 'HND,CTS' and not await pg.evaluate('(window.__pinPuts || []).length'))
        check('JS のエラーがない（ピン止め c・d）', not errs, errs[:3])
        await c.close(); await b.close()
    print('errors', fails)
    sys.exit(1 if fails else 0)
asyncio.run(main())
