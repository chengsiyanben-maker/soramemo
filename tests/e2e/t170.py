import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営の非表示（11/23 本人「経営ゲームは非表示に」）：切り替え KEIEI_VISIBLE が false の間は、
# どの画面にも経営の入口が出ない・経営の画面への直のリンクはホームへ戻る・デモでも出ない。
# 切り替えを true にしたとき（テストでは window.__SORAMEMO_TEST_KEIEI で同じ形にする）は今までどおり出る。
# この テストは keiei_on を import しない（はじめは隠れた状態を見る）
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)

# 原本の切り替えは1か所だけ、はじめは false
SRC = open(os.path.join(HERE, '..', '..', 'src', 'index.html'), encoding='utf-8').read()
check('src: 切り替えは1か所で false', len(re.findall(r'const KEIEI_VISIBLE = (true|false);', SRC)) == 1 and 'const KEIEI_VISIBLE = false;' in SRC)
check('src: gameAvail が切り替えを見る', 'const gameAvail = () => keieiShown() &&' in SRC)

INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });"
EV = "window.__events = [{name:'冬の行事', starts_at:new Date(Date.now()-864e5).toISOString(), ends_at:new Date(Date.now()+7*864e5).toISOString(), bonus:500, rare_mult:2, open:true, note:''}];"
CO = "window.__co = {name:'そらメモ航空', cash:100000, last:new Date().toISOString(), roles:{}, daily:0, gross:0, upkeep:0, bonus:0, routes:[], fleet:[], sky:{}, total_km:0, rep_points:0, stars:1, facilities:{}, bought:0, value:100000, friend_code:'ABCD1234', hide_rank:false, friends:0};"

async def open_server(b, errs, show, hash='', mode=None):
    c = await b.new_context(viewport={'width':400,'height':860})
    await c.add_init_script(INIT + EV + CO + (f"localStorage.setItem('soramemo.mode','{mode}');" if mode else '') + ('window.__SORAMEMO_TEST_KEIEI = true;' if show else ''))
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html') + hash); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(900)
    return c, pg

VIS_TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b=>!b.hidden).map(b=>b.dataset.v)"
ON_VIEW = "document.querySelector('section.view.on').id"
GAME_TEXT = "(() => { const t = []; for(const el of document.querySelectorAll('body *')){ if(el.closest('[hidden]') || el.closest('dialog:not([open])') || el.closest('section.view:not(.on)')) continue; const s = getComputedStyle(el); if(s.display === 'none' || s.visibility === 'hidden') continue; for(const n of el.childNodes) if(n.nodeType === 3 && /エアライン経営|経営の資金|守り神と|会社の価値/.test(n.textContent)) t.push(n.textContent.trim().slice(0, 40)); } return t; })()"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []

        # 1. 隠している間（サーバー版・ログイン・経営は公開済み・行事あり）
        c, pg = await open_server(b, errs, False)
        check('隠す: keieiShown() は false', await pg.evaluate('keieiShown()') is False)
        check('隠す: gameAvail() は false', await pg.evaluate('gameAvail()') is False)
        check('隠す: 切り替えのピル（スタンプラリー／エアライン経営）が出ない', await pg.evaluate("$('modeSw').hidden"))
        check('隠す: 経営とはの説明が出ない', await pg.evaluate("$('gameNote').hidden"))
        tabs = await pg.evaluate(VIS_TABS)
        check(f'隠す: 下のタブに会社・路線・機体・守り神がない {tabs}', not any(v in tabs for v in ['co','routes','fleet','gods']))
        check('隠す: 行事のボーナス（経営の資金）のお知らせが出ない', await pg.evaluate("$('eventBar').hidden"))
        check('隠す: ホームに経営の字がない', not await pg.evaluate(GAME_TEXT))
        await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(300)
        check('隠す: マイページ（設定）の経営のオン／オフの行が出ない', await pg.evaluate("$('gameRow').hidden"))
        g = await pg.evaluate(GAME_TEXT)
        check(f'隠す: マイページに経営の字がない {g}', not g)
        for v in ['co', 'routes', 'fleet', 'gods']:
            await pg.evaluate(f'goTab("{v}")'); await pg.wait_for_timeout(100)
            check(f'隠す: goTab("{v}") はホームへ', await pg.evaluate(ON_VIEW) == 'v-home' and await pg.evaluate('MODE') == 'rally')
        await pg.evaluate("setMode('game')"); await pg.wait_for_timeout(100)
        check('隠す: setMode("game") でもスタンプラリーのまま', await pg.evaluate('MODE') == 'rally' and await pg.evaluate(ON_VIEW) == 'v-home')
        check('隠す: 会社の計算（co_state）を頼まない', await pg.evaluate("typeof CO === 'undefined' || !CO || CO.friendCode !== 'ABCD1234' && CO.friend_code !== 'ABCD1234' && CO.cash !== 100000"))
        await c.close()

        # 2. 経営の画面への直のリンク（#co など）はホームへ戻り、リンクの印も消える
        for h in ['#co', '#routes', '#fleet', '#gods', '#game']:
            c, pg = await open_server(b, errs, False, hash=h)
            await pg.wait_for_timeout(200)
            check(f'隠す: {h} を開くとホーム', await pg.evaluate(ON_VIEW) == 'v-home' and await pg.evaluate('location.hash') == '')
            await c.close()
        # 前に経営の画面で閉じた人（soramemo.mode = game）も、ホームで開く
        c, pg = await open_server(b, errs, False, mode='game')
        check('隠す: 前に経営で閉じた人もホームで開く', await pg.evaluate('MODE') == 'rally' and await pg.evaluate(ON_VIEW) == 'v-home')
        await pg.evaluate("location.hash = '#co'"); await pg.wait_for_timeout(300)
        check('隠す: 開いたあとに #co に変わってもホーム', await pg.evaluate(ON_VIEW) == 'v-home' and await pg.evaluate('location.hash') == '')
        await c.close()

        # 3. デモ（サーバーなしの版）でも出ない。初めての空港でも「守り神と出会った」を出さない
        c = await b.new_context(viewport={'width':400,'height':860})
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = { supabaseUrl: "", supabaseAnonKey: "" };', content_type='application/javascript'))
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"')
        await pg.evaluate('openMyPage()'); await pg.click('#toggleDemo'); await pg.evaluate('S = blank(); save(); render()')
        check('デモ: 切り替えのピルが出ない', await pg.evaluate("$('modeSw').hidden"))
        check('デモ: 経営のオン／オフの行が出ない', await pg.evaluate("$('gameRow').hidden"))
        await pg.select_option('#demoAirport', 't:HND-T1'); await pg.press('#checkin', 'Enter'); await pg.wait_for_timeout(600)
        check('デモ: 初めての空港でも守り神の出会いを出さない', await pg.locator('#dStamp .meet').count() == 0)
        await c.close()

        # 4. 切り替えを true にしたとき：今までどおり出る
        c, pg = await open_server(b, errs, True)
        check('出す: 切り替えのピルが出る', not await pg.evaluate("$('modeSw').hidden"))
        check('出す: 行事のボーナスのお知らせが出る', not await pg.evaluate("$('eventBar').hidden") and '経営の資金' in await pg.inner_text('#eventBar'))
        await pg.click('[data-mode=game]'); await pg.wait_for_timeout(300)
        tabs = await pg.evaluate(VIS_TABS)
        check(f'出す: 経営の画面と会社・路線・機体・守り神のタブ {tabs}', await pg.evaluate(ON_VIEW) == 'v-co' and all(v in tabs for v in ['co','routes','fleet','gods']))
        await pg.click('[data-mode=rally]'); await pg.wait_for_timeout(200)
        await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(200)
        check('出す: 経営のオン／オフの行が出る', not await pg.evaluate("$('gameRow').hidden"))
        await c.close()
        c, pg = await open_server(b, errs, True, hash='#fleet')
        await pg.wait_for_timeout(300)
        check('出す: #fleet で経営の機体の画面', await pg.evaluate(ON_VIEW) == 'v-fleet' and await pg.evaluate('MODE') == 'game')
        await c.close()

        await b.close()
        check('ページのエラーなし ' + str(errs[:3]), not errs)
        print('fails', fails)
        print('errors', fails if fails else [])

asyncio.run(main())
