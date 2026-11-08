import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 全部乗せ 案3「タブから選ぶ」（11/8 21時半 本人の決定。画面案 design/all-in-filter-alt の C1〜C4）
#   C1 タブ帯の長押しで「タブを選ぶ」：≡ で並べ替え・左へはらって外す・5つまで（6つ目は入れ替え）・ホームはいつも1番目・2つより減らせない
#   C2 ホームに出すもの：× で外し ＋ で戻す・元に戻す
#   C3 全部乗せに戻す：戻る数を見せてから戻す
#   保存：端末とサーバー（user_view_prefs）に並べた順も残る。偽のサーバー（fake_sb.js）を使い、小さなサーバーから開く
import asyncio, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright
fails = []
def check(label, ok, detail=''):
    print(label, ok, detail if detail != '' else '')
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WORK)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/index_server_test.html'
SHOTS = os.path.join(WORK, 'alltabs_shots'); os.makedirs(SHOTS, exist_ok=True)
TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden && b.dataset.mode === 'rally').map(b => b.dataset.v).join(',')"
NEW = "if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }"
async def ctx(b, init='', scale=1, h=844):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=scale, timezone_id='Asia/Tokyo')
    await c.add_init_script("localStorage.setItem('soramemo.install.later','1');" + init)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://fake.supabase.co/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    return c
async def page(c, errs, login=False):
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(700)
    if login: await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return pg
async def longpress(pg, sel, ms=800):
    r = await pg.locator(sel).bounding_box()
    await pg.mouse.move(r['x'] + r['width'] / 2, r['y'] + r['height'] / 2); await pg.mouse.down(); await pg.wait_for_timeout(ms); await pg.mouse.up(); await pg.wait_for_timeout(300)
async def drag(pg, frm, to):
    h = await pg.locator(frm).bounding_box(); t = await pg.locator(to).bounding_box()
    x, y0, y1 = h['x'] + h['width'] / 2, h['y'] + h['height'] / 2, t['y'] + t['height'] / 2 + (-8 if t['y'] < h['y'] else 8)
    await pg.mouse.move(x, y0); await pg.mouse.down()
    for k in range(1, 13): await pg.mouse.move(x, y0 + (y1 - y0) * k / 12)
    await pg.mouse.up(); await pg.wait_for_timeout(300)
async def swipe(pg, sel, dx=-140):
    r = await pg.locator(sel).bounding_box(); x, y = r['x'] + 40, r['y'] + r['height'] / 2
    await pg.mouse.move(x, y); await pg.mouse.down()
    for k in range(1, 11): await pg.mouse.move(x + dx * k / 10, y)
    await pg.mouse.up(); await pg.wait_for_timeout(300)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # 1. C1：タブ帯の長押し（ログインしていない・はじめての人）
        c = await ctx(b, NEW, 2); pg = await page(c, errs)
        await pg.click('nav.tabs button[data-v="book"]'); await pg.wait_for_timeout(300)
        check('ふつうに押すと画面が変わる（長押しにならない）:', await pg.evaluate('currentView()') == 'book' and not await pg.evaluate("$('dTabs').open"))
        await pg.evaluate("goTab('home')"); await longpress(pg, 'nav.tabs button[data-v="log"]')
        check('長押しで「タブを選ぶ」が開く・画面は変わらない:', await pg.evaluate("$('dTabs').open") and await pg.evaluate('currentView()') == 'home')
        check('タブ帯が金の縁:', await pg.evaluate("document.querySelector('nav.tabs').classList.contains('tppick')"))
        check('ホームはいつも1番目・並べ替えの ≡ はない:', 'いつも' in await pg.inner_text('#dTabs .tprow.lock') and await pg.locator('#dTabs .tprow.lock [data-tp-h]').count() == 0)
        check('並べる行は4つ・タブにないものは成績:', await pg.locator('#dTabs .tprow[data-tp]').count() == 4 and await pg.locator('#dTabs [data-tp-on]').count() == 1 and await pg.locator('#dTabs [data-tp-on="stats"]').count() == 1)
        await pg.screenshot(path=os.path.join(SHOTS, '01-c1-pick.png'))
        await drag(pg, '[data-tp-h="sg"]', '[data-tp-h="book"]')
        check('≡ を持って並べ替える（修行を図鑑の前へ）:', await pg.evaluate(TABS) == 'home,sg,book,log,ops', await pg.evaluate(TABS))
        await pg.focus('[data-tp-h="ops"]'); await pg.keyboard.press('ArrowUp'); await pg.wait_for_timeout(200)
        check('矢印のキーでも並べ替えられる:', await pg.evaluate(TABS) == 'home,sg,book,ops,log' and await pg.evaluate("document.activeElement.dataset.tpH") == 'ops')
        await drag(pg, '[data-tp-h="sg"]', '.tprow.lock')
        check('ホームより前には動かない:', (await pg.evaluate(TABS)).startswith('home,'))
        await swipe(pg, '.tprow[data-tp="ops"]')
        check('左へはらうとタブから外れる:', 'ops' not in await pg.evaluate(TABS) and await pg.locator('#dTabs [data-tp-on="ops"]').count() == 1)
        check('外したら「元に戻す」:', '運用」をタブから外しました' in await pg.inner_text('#dTabs .tpundo'))
        await pg.screenshot(path=os.path.join(SHOTS, '02-c1-removed.png'))
        await pg.click('#dTabs [data-tp-undo]'); await pg.wait_for_timeout(200)
        check('元に戻すと運用が戻る:', 'ops' in await pg.evaluate(TABS))
        await swipe(pg, '.tprow[data-tp="log"]', -30)
        check('少しだけ動かしたときは外さない:', 'log' in await pg.evaluate(TABS))
        await pg.click('#dTabs [data-tp-on="stats"]'); await pg.wait_for_timeout(200)
        check('5つあるとき6つ目は入れ替えを聞く:', await pg.locator('#dTabs .tpswap').count() == 1 and len((await pg.evaluate(TABS)).split(',')) == 5)
        await pg.click('#dTabs [data-tp-swap="log"]'); await pg.wait_for_timeout(200)
        check('入れ替える（フライト → 成績、同じ場所）:', await pg.evaluate(TABS) == 'home,sg,book,ops,stats', await pg.evaluate(TABS))
        for v in ['sg', 'book', 'ops']: await pg.evaluate(f"document.querySelector('#dTabs [data-tp-off=\"{v}\"]').click()")   # 読み上げ用の「外す」ボタン（見た目は出さない）
        await pg.evaluate("document.querySelector('#dTabs [data-tp-off=\"stats\"]').click()"); await pg.wait_for_timeout(200)
        check('2つより減らせない（知らせる）:', await pg.evaluate(TABS) == 'home,stats' and 'より減らせません' in await pg.inner_text('#dTabs .tpmsg'))
        await pg.click('#dTabs [data-tp-done], #dTabs .tpdone'); await pg.wait_for_timeout(200)
        check('完了で閉じる・金の縁が消える:', not await pg.evaluate("$('dTabs').open") and not await pg.evaluate("document.querySelector('nav.tabs').classList.contains('tppick')"))
        await pg.reload(); await pg.wait_for_timeout(800)
        check('開き直しても並びが残る:', await pg.evaluate(TABS) == 'home,stats')
        # C3：全部乗せに戻す
        await pg.evaluate("openTabPicker('screen')"); await pg.wait_for_timeout(200)
        await pg.click('#dTabs [data-tp-reset]'); await pg.wait_for_timeout(300)
        rows = await pg.inner_text('#dReset .rsrows')
        check('戻す前に戻る数を見せる（タブ・見方・かたまり）:', await pg.evaluate("$('dReset').open") and '図鑑・フライト・運用・修行を戻す' in rows and '成績を外す' in rows, rows)
        check('戻したあとのタブ帯を小さく見せる（5つ）:', await pg.locator('#dReset .tpmini b').count() == 5)
        await pg.screenshot(path=os.path.join(SHOTS, '03-c3-reset.png'))
        await pg.click('#dReset [data-rs-yes]'); await pg.wait_for_timeout(300)
        check('全部乗せに戻る:', await pg.evaluate(TABS) == 'home,book,log,ops,sg' and await pg.evaluate('loAllOn()') and await pg.locator('#dTabs [data-tp-reset]').is_disabled())
        await pg.evaluate("$('dTabs').close()")
        # C2：ホームに出すもの（ホームのシートの1行から）
        check('ホームのシートの下に「ホームに出すものを選ぶ」:', await pg.locator('#v-home .helink[data-he-open]').count() == 1)
        await pg.evaluate("document.querySelector('#v-home .helink').click()"); await pg.wait_for_timeout(300)
        check('ホームに出すものが開く（半券と今日の数字はいつも・外せるのは4つ）:', await pg.evaluate("$('dHomeEd').open") and await pg.locator('#dHomeEd .helk').count() == 2 and await pg.locator('#dHomeEd [data-he-off]').count() == 4)
        await pg.click('#dHomeEd [data-he-off="ride"]'); await pg.click('#dHomeEd [data-he-off="event"]'); await pg.wait_for_timeout(200)
        check('× で外すと「外したもの 2」に ＋ で並ぶ:', '外したもの 2' in await pg.inner_text('#dHomeEd .hesec') and await pg.locator('#dHomeEd [data-he-on]').count() == 2)
        check('ホームでも隠れる:', await pg.evaluate("document.querySelector('[data-lo=\"home:event\"]').classList.contains('lo-off')"))
        check('「元に戻す」:', 'イベントのお知らせ」を外しました' in await pg.inner_text('#dHomeEd .heundo'))
        await pg.screenshot(path=os.path.join(SHOTS, '04-c2-home.png'))
        await pg.click('#dHomeEd [data-he-undo]'); await pg.wait_for_timeout(200)
        check('元に戻すとイベントが戻る:', await pg.locator('#dHomeEd [data-he-on]').count() == 1)
        await pg.click('#dHomeEd [data-he-on="ride"]'); await pg.wait_for_timeout(200)
        check('＋ で戻す:', await pg.locator('#dHomeEd [data-he-on]').count() == 0 and await pg.evaluate('loOff("home").size') == 0)
        await pg.click('#dHomeEd [data-he-off="recent"]'); await pg.click('#dHomeEd [data-tp-reset]'); await pg.wait_for_timeout(300)
        check('ここからも全部乗せに戻せる（かたまり ホーム 1）:', 'ホーム 1' in await pg.inner_text('#dReset .rsrows'))
        await pg.screenshot(path=os.path.join(SHOTS, '05-c3-from-home.png'))
        await pg.click('#dReset .rsno'); await pg.evaluate("$('dHomeEd').close()")
        # マイページの入口
        await pg.evaluate("$('dSettings').showModal(); renderMyPage()"); await pg.wait_for_timeout(300)
        check('マイページ：タブを選ぶ・ホームに出すもの・全部を見直す:', await pg.locator('#dSettings [data-tp-open]').count() == 1 and await pg.locator('#dSettings .lotile[data-he-open]').count() == 1 and await pg.locator('#dSettings [data-lo-open="top"]').count() == 1)
        check('数（タブ 5/5・ホーム 3/4）:', (await pg.inner_text('#tpTileN')).replace('\n', '') == '5/5' and (await pg.inner_text('#heTileN')).replace('\n', '') == '3/4')
        await pg.locator('#dSettings [aria-labelledby="mpPersona"]').screenshot(path=os.path.join(SHOTS, '06-mypage.png'))
        await pg.click('#dSettings [data-tp-open]'); await pg.wait_for_timeout(300)
        check('マイページからも同じシート:', await pg.evaluate("$('dTabs').open"))
        await c.close()
        # 2. 小さい画面（667）でも完了と並べる行が見える
        c = await ctx(b, NEW, 2, 667); pg = await page(c, errs)
        await longpress(pg, 'nav.tabs button[data-v="book"]')
        check('667：完了と修行の行が見える:', await pg.locator('#dTabs .tpdone').is_visible() and await pg.evaluate("document.querySelector('.tprow[data-tp=\"sg\"]').getBoundingClientRect().bottom < innerHeight"))
        await pg.screenshot(path=os.path.join(SHOTS, '07-c1-667.png'))
        await c.close()
        # 3. エアライン経営のときは長押しで開かない
        c = await ctx(b, NEW); pg = await page(c, errs)
        await pg.evaluate("setMode('game', false)"); await pg.wait_for_timeout(300)
        btn = await pg.evaluate("(() => { const b = [...document.querySelectorAll('nav.tabs button')].find(x => !x.hidden); return b && b.dataset.v; })()")
        if btn: await longpress(pg, f'nav.tabs button[data-v="{btn}"]')
        check('経営のタブ帯では開かない:', not await pg.evaluate("$('dTabs').open"))
        await c.close()
        # 4. サーバーに並べた順が残り、別の端末でも同じ
        c = await ctx(b, "window.__viewPrefs = window.__viewPrefs || [];" + NEW); pg = await page(c, errs, True)
        await pg.evaluate("openTabPicker('screen')"); await pg.wait_for_timeout(200)
        await drag(pg, '[data-tp-h="ops"]', '[data-tp-h="book"]'); await pg.wait_for_timeout(900)
        saved = await pg.evaluate("JSON.stringify(__fake.db.user_view_prefs[0])")
        check('並べた順がサーバーに残る:', '"tabs":["home","ops","book","log","sg"]' in saved, saved[:200])
        await c.close()
        c = await ctx(b, f"window.__viewPrefs = [{saved}]; localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all');"); pg = await page(c, errs, True)
        check('別の端末でも同じ並び:', await pg.evaluate(TABS) == 'home,ops,book,log,sg', await pg.evaluate(TABS))
        await c.close()
        # 5. 提案（撮る：修行のタブだけ外す → タブを4つに）
        c = await ctx(b, "window.__viewPrefs = [];" + NEW, 2); pg = await page(c, errs, True)
        await pg.evaluate("showHideSuggest('spot')"); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#dPersona')
        check('撮る：タブを4つにしますか・あわせて3こ:', 'タブを4つにしますか' in t and 'あわせて3こ' in t and '4つにする' in t and '5つのまま使う' in t)
        await pg.screenshot(path=os.path.join(SHOTS, '08-c4-spot.png'))
        await pg.click('#dPersona [data-hs-yes]'); await pg.wait_for_timeout(500)
        check('撮る：修行のタブが外れる:', await pg.evaluate(TABS) == 'home,book,log,ops')
        await c.close()
        print('errors', errs + fails); srv.shutdown(); await b.close()
asyncio.run(main())
