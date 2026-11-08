import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 全部乗せ＋フィルター（11/8 本人の決定）：はじめての人は全部乗せ／前からの人は今の見え方のまま／表示の編集（1枚・ピル・しぼりこみ・元に戻す・全部乗せに戻す）／
#   サーバーの表（user_view_prefs）に保存して別の端末でも同じ／表がまだないときは端末だけ／新規登録の答えから「これを隠しますか？」を1回だけ／はじめの1枚
#   偽のサーバー（fake_sb.js）を使う。読み込み直しを確かめるため、小さなサーバーから開く（file:// だと保存が消えることがある）
import asyncio, json, threading, http.server, socketserver, functools
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
SHOTS = os.path.join(WORK, 'allin_shots'); os.makedirs(SHOTS, exist_ok=True)
TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden && b.dataset.mode === 'rally').map(b => b.dataset.v).join(',')"
OLD = "[{user_id:'u1', display_name:'まえ', persona:'spot', terms_version:'2026-10-15', privacy_version:'2026-10-21', agreed_at:'2026-10-20T00:00:00Z'}]"
async def ctx(b, init='', scale=1):
    c = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=scale, timezone_id='Asia/Tokyo')
    await c.add_init_script("localStorage.setItem('soramemo.install.later','1');" + init)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://fake.supabase.co/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    return c
async def page(c, errs, login=False):
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(700)
    if login: await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
    return pg
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # 1. はじめての端末：全部乗せ（タブはホーム・図鑑・フライト・運用・修行の5つ）
        c = await ctx(b); pg = await page(c, errs)
        check('はじめての人は全部乗せ:', await pg.evaluate('PERSONA') == 'all' and await pg.evaluate("localStorage.getItem('soramemo.persona')") == 'all')
        check('タブは5つ（成績はマイページ）:', await pg.evaluate(TABS) == 'home,book,log,ops,sg', await pg.evaluate(TABS))
        check('フライトの見方は全部（9つ）:', await pg.evaluate("viewsShown('log').length") == 9)
        await c.close()
        # 2. 前から使っている端末（はじめの案内を見た跡）：今までどおり「気軽に」
        c = await ctx(b, "localStorage.setItem('soramemo.onboarded','1');"); pg = await page(c, errs)
        check('前からの人は今の見え方のまま:', await pg.evaluate('PERSONA') == 'casual' and await pg.evaluate(TABS) == 'home,book,log')
        check('前からの人に「全部乗せ」を書かない:', await pg.evaluate("localStorage.getItem('soramemo.persona')") is None)
        await c.close()
        # 3. 表示の編集（ログインしていない）
        c = await ctx(b, "if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }", 2); pg = await page(c, errs)
        await pg.evaluate("$('dSettings').showModal(); renderMyPage()"); await pg.wait_for_timeout(300)
        check('マイページの入口に今の数:', '40 / 40' in await pg.inner_text('#personaNote') and '成績を開く' in await pg.inner_text('#personaMore'))
        await pg.click('#dSettings .lotile'); await pg.wait_for_timeout(300)
        check('表示の編集が開く（40/40・ひな形はない）:', await pg.evaluate("$('dLayout').open") and '40' in await pg.inner_text('#dLayout .lonum') and await pg.locator('#dLayout [data-lo-persona]').count() == 0)
        check('出す・隠すのピルは40こ:', await pg.locator('#dLayout .lopill[data-lo-tab], #dLayout .lopill[data-lo-view], #dLayout .lopill[data-lo-blk]').count() == 40)
        check('全部出しているときは「全部乗せに戻す」を押せない:', await pg.locator('#dLayout [data-lo-reset]').is_disabled())
        check('ログインしていないときは端末に保存と書く:', 'この端末に保存' in await pg.inner_text('#dLayout .losave'))
        await pg.screenshot(path=os.path.join(SHOTS, '01-filter-all.png'))
        await pg.click('#dLayout [data-lo-tab="ops"]'); await pg.wait_for_timeout(200)
        check('運用のタブを隠す:', await pg.evaluate(TABS) == 'home,book,log,sg' and await pg.locator('#dLayout [data-lo-tab="ops"]').get_attribute('aria-pressed') == 'false')
        check('押した直後に「元に戻す」:', 'タブを隠しました' in await pg.inner_text('#dLayout .loundo'))
        check('運用の見方は薄くせず1行で知らせる:', 'マイページの「運用」から' in await pg.inner_text('#dLayout [data-lo-go="ops"]') and await pg.locator('#dLayout [data-lo-view="ops:board"]').get_attribute('aria-pressed') == 'true')
        await pg.click('#dLayout [data-lo-undo]'); await pg.wait_for_timeout(200)
        check('元に戻すと運用のタブが戻る:', await pg.evaluate(TABS) == 'home,book,log,ops,sg' and await pg.locator('#dLayout .loundo').count() == 0)
        await pg.click('#dLayout [data-lo-tab="ops"]'); await pg.click('#dLayout [data-lo-view="log:alt"]'); await pg.click('#dLayout [data-lo-blk="home:recent"]'); await pg.wait_for_timeout(200)
        check('数が減る（37/40）:', (await pg.inner_text('#dLayout .lonum')).replace(' ', '').startswith('37'))
        check('タブは5つより増やせない・2つより減らせない（はじめは押せる）:', not await pg.locator('#dLayout [data-lo-tab="book"]').is_disabled())
        await pg.click('#dLayout [data-lo-filter="off"]'); await pg.wait_for_timeout(200)
        check('しぼりこみ「隠しているもの 3」:', await pg.locator('#dLayout .lopill').count() == 3 and '3' in await pg.inner_text('#dLayout [data-lo-filter="off"]'))
        await pg.screenshot(path=os.path.join(SHOTS, '02-filter-hidden.png'))
        await pg.click('#dLayout [data-close]'); await pg.wait_for_timeout(200)
        check('ホーム：最近の印が隠れる:', await pg.evaluate("document.querySelector('[data-lo=\"home:recent\"]').classList.contains('lo-off')"))
        await pg.reload(); await pg.wait_for_timeout(800)
        check('開き直しても残る:', await pg.evaluate(TABS) == 'home,book,log,sg' and 'alt' not in [v[0] for v in await pg.evaluate("viewsShown('log')")])
        await pg.evaluate("openLayout('top', 'settings')"); await pg.click('#dLayout [data-lo-reset]'); await pg.wait_for_timeout(200)
        check('戻すときは戻る数を見せる（タブ1・見方1・かたまり1）:', [x.strip() for x in (await pg.locator('#dLayout .loback b').all_inner_texts())] == ['1', '1', '1'])
        await pg.screenshot(path=os.path.join(SHOTS, '03-reset.png'))
        await pg.click('#dLayout [data-lo-reset-yes]'); await pg.wait_for_timeout(200)
        check('全部乗せに戻る:', await pg.evaluate(TABS) == 'home,book,log,ops,sg' and await pg.evaluate("localStorage.getItem('soramemo.layout')") is None and '3こをまた出しました' in await pg.inner_text('#dLayout .loundo'))
        await pg.evaluate("$('dLayout').close(); goTab('log')"); await pg.wait_for_timeout(600)
        await pg.click('[data-lo-open="log"]'); await pg.wait_for_timeout(300)
        check('フライトの鉛筆からはフライトの見方へ:', await pg.evaluate("$('dLayout').open && LO_PAGE === 'log'") and await pg.evaluate("(() => { const g = document.querySelector('#dLayout [data-lo-go=\"log\"]').getBoundingClientRect(); return g.top > 0 && g.top < 400; })()"))
        await c.close()
        # 4. サーバーに保存（表あり）：隠すとアカウントに残り、別の端末でも同じになる
        c = await ctx(b, "window.__viewPrefs = window.__viewPrefs || []; if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }"); pg = await page(c, errs, True)
        check('ログイン：アカウントに保存と書く（はじめは全部乗せの行を作る）:', await pg.evaluate("VP.ok === true") and await pg.evaluate("JSON.stringify(__fake.db.user_view_prefs.map(r => r.prefs))") == '[{}]')
        await pg.evaluate("openLayout('top', 'settings')"); await pg.click('#dLayout [data-lo-view="log:alt"]'); await pg.click('#dLayout [data-lo-tab="sg"]'); await pg.wait_for_timeout(900)
        saved = await pg.evaluate("JSON.stringify(__fake.db.user_view_prefs[0])")
        check('隠したものがサーバーに残る:', '"base":"all"' in saved and '"alt"' in saved and '"fmt":2' in saved, saved[:200])
        await c.close()
        c = await ctx(b, f"window.__viewPrefs = [{saved}]; localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all');"); pg = await page(c, errs, True)
        check('別の端末でも同じ（修行のタブ・高度が隠れる）:', await pg.evaluate(TABS) == 'home,book,log,ops' and 'alt' not in [v[0] for v in await pg.evaluate("viewsShown('log')")])
        await c.close()
        c = await ctx(b, "window.__viewPrefs = [{user_id:'u1', prefs:{}, fmt:2}]; localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','spot');"); pg = await page(c, errs, True)
        check('サーバーが全部乗せなら、端末の古いひな形より優先:', await pg.evaluate('PERSONA') == 'all' and await pg.evaluate(TABS) == 'home,book,log,ops,sg')
        await c.close()
        # 5. 前からの人（行がない）：前の答え（撮影）のまま、今の見え方を上げる
        c = await ctx(b, f"window.__viewPrefs = []; window.__profiles = {OLD}; localStorage.setItem('soramemo.onboarded','1');"); pg = await page(c, errs, True)
        check('前からの人は前の答えのまま・サーバーに上げる:', await pg.evaluate('PERSONA') == 'spot' and await pg.evaluate("JSON.stringify(__fake.db.user_view_prefs.map(r => r.prefs.base))") == '["spot"]')
        await c.close()
        # 6. 表がまだない（反映の前）：全部乗せの人は古い答えで変えない／前からの人は前と同じ
        c = await ctx(b, f"window.__profiles = {OLD}; if(!localStorage.getItem('soramemo.onboarded')){{ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }}"); pg = await page(c, errs, True)
        check('表がない：全部乗せのまま:', await pg.evaluate("VP.ok") is False and await pg.evaluate('PERSONA') == 'all')
        await pg.evaluate("openLayout('top', 'settings')"); await pg.click('#dLayout [data-lo-view="log:alt"]'); await pg.wait_for_timeout(600)
        check('表がない：端末には保存できる:', 'alt' in await pg.evaluate("localStorage.getItem('soramemo.layout')"))
        await c.close()
        c = await ctx(b, f"window.__profiles = {OLD}; localStorage.setItem('soramemo.onboarded','1');"); pg = await page(c, errs, True)
        check('表がない：前からの人は前と同じ（撮影）:', await pg.evaluate('PERSONA') == 'spot')
        await c.close()
        # 7. 新規登録の答え（気軽に）から「これを隠しますか？」を1回だけ
        c = await ctx(b, "window.__viewPrefs = []; if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }", 2); pg = await page(c, errs, True)
        first = await pg.evaluate("sb.rpc('view_prefs_claim_suggest').then(r => r.data)"); again = await pg.evaluate("sb.rpc('view_prefs_claim_suggest').then(r => r.data)")
        check('提案はサーバーが1回だけ許す:', first is True and again is False)
        await pg.evaluate("localStorage.setItem('soramemo.hideAsk', 'casual'); auFinish()"); await pg.wait_for_timeout(900)
        check('提案のシートが出る:', await pg.evaluate("$('dPersona').open") and '隠しておきたいものはありますか' in await pg.inner_text('#dPersona'))
        check('数は表示の編集と同じ数え方（15こ・これから乗る便は入れない）:', 'この15こを隠す' in await pg.inner_text('#dPersona [data-hs-yes]'))
        check('「全部のまま使う」も同じ見た目:', await pg.evaluate("getComputedStyle(document.querySelector('[data-hs-yes]')).backgroundColor === getComputedStyle(document.querySelector('[data-hs-no]')).backgroundColor"))
        await pg.screenshot(path=os.path.join(SHOTS, '04-suggest.png'))
        await pg.click('#dPersona [data-hs="0"]'); await pg.wait_for_timeout(100)
        check('押すと残せる（14こ）:', 'この14こを隠す' in await pg.inner_text('#dPersona [data-hs-yes]'))
        await pg.click('#dPersona [data-hs-yes]'); await pg.wait_for_timeout(900)
        check('隠す：運用は残し修行のタブは隠す:', await pg.evaluate(TABS) == 'home,book,log,ops' and await pg.evaluate("viewsShown('log').map(v => v[0]).join()") == 'pass')
        check('表示の編集で数がそろう（26/40）:', await pg.evaluate("loCount().on") == 26)
        check('「14こを隠しました」を1回だけ:', '14こを隠しました' in await pg.inner_text('#allinCard'))
        await pg.screenshot(path=os.path.join(SHOTS, '05-suggest-done.png'))
        check('サーバーにも残る:', '"pass"' not in await pg.evaluate("JSON.stringify(__fake.db.user_view_prefs[0].prefs)") and '"sgsum"' in await pg.evaluate("JSON.stringify(__fake.db.user_view_prefs[0].prefs)"))
        await pg.click('#allinCard [data-allin="ok"]'); await pg.reload(); await pg.wait_for_timeout(800)
        check('閉じたらもう出ない:', await pg.is_hidden('#allinCard'))
        await c.close()
        # 8. 「全部のまま使う」→ はじめの1枚。「あとで決める」も同じ1枚
        c = await ctx(b, "window.__viewPrefs = []; if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }", 2); pg = await page(c, errs, True)
        await pg.evaluate("localStorage.setItem('soramemo.hideAsk', 'spot'); auFinish()"); await pg.wait_for_timeout(900)
        await pg.click('#dPersona [data-hs-no]'); await pg.wait_for_timeout(300)
        check('断ったら全部のまま・はじめの1枚:', await pg.evaluate(TABS) == 'home,book,log,ops,sg' and '全部の機能を出しています' in await pg.inner_text('#allinCard'))
        await pg.screenshot(path=os.path.join(SHOTS, '06-allin-card.png'))
        await pg.click('#allinCard [data-allin="edit"]'); await pg.wait_for_timeout(300)
        check('「表示を編集」で表示の編集が開く:', await pg.evaluate("$('dLayout').open") and await pg.is_hidden('#allinCard'))
        await pg.evaluate("$('dLayout').close(); localStorage.setItem('soramemo.hideAsk', 'unanswered'); auFinish()"); await pg.wait_for_timeout(600)
        check('「あとで決める」：シートは出さず、はじめの1枚:', not await pg.evaluate("$('dPersona').open") and '全部の機能を出しています' in await pg.inner_text('#allinCard'))
        await c.close()
        # 9. 前からの人（ひな形）には提案を出さない
        c = await ctx(b, "window.__viewPrefs = []; localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','shugyo');"); pg = await page(c, errs, True)
        check('ひな形の人には出さない:', await pg.evaluate("showHideSuggest('casual')") is False)
        await c.close()
        print('errors', errs + fails); srv.shutdown(); await b.close()
asyncio.run(main())
