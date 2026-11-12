# 見方の設定の反映の前の直し（11/11 17時20分の PM の指示・改善担当 review-app-1）
#   1 表示の編集の上の「‹ マイページ」「閉じる」「すべて」「隠しているもの」は高さ 44px 以上
#   2 タブを全部出していて成績のタブがないとき、タブのカードの見出しは「成績はマイページのタイルにあります」
#   3 デモで隠した見方は、デモを終えると（開き直してデモが終わったときも）始める前に戻る
#   4 修行のカードがない間は、1枚の下に「修行の見方は、修行の画面の鉛筆から変えます。」
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web'))
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-view-settings')); os.makedirs(SHOTS, exist_ok=True)
from playwright.async_api import async_playwright
fails = []
def check(label, ok, extra=''):
    print(label, ok, extra)
    if not ok: fails.append(label)
NEW = "if(!sessionStorage.getItem('t126')){ sessionStorage.setItem('t126','1'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.tp.tip','1'); localStorage.setItem('soramemo.tpTaught','1'); }"
async def open_app(b, h=844):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, timezone_id='Asia/Tokyo')
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.add_init_script(NEW)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WEB,'index.html')); await ready(pg)
    return c, pg, errs
async def ready(pg):
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
async def heights(pg):
    return await pg.evaluate("""[...document.querySelectorAll('#dLayout .spctop .mp-back, #dLayout .lofilter .lochip')].map(e => [e.textContent.trim(), Math.round(e.getBoundingClientRect().height)])""")
async def main():
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for h in (844, 667):
            c, pg, errs = await open_app(b, h)
            # マイページから（‹ マイページ）
            await pg.evaluate("window.__sgx = LO_EXT.sg; delete LO_EXT.sg; openLayout('top', 'settings')"); await pg.wait_for_timeout(300)
            hs = await heights(pg)
            check(f'{h} マイページから：上の3つが 44px 以上:', len(hs) == 3 and all(x[1] >= 44 for x in hs), str(hs))
            sub = await pg.inner_text('#dLayout [data-lo-sec="tabs"] .lott small')
            check(f'{h} タブのカードの見出し（成績のタブなし）:', sub == '成績はマイページから', sub)
            check(f'{h} 修行のカードがない間の1行:', '修行の見方は、修行の画面の鉛筆から変えます。' in await pg.inner_text('#dLayout .losave'))
            if h == 844: await pg.screenshot(path=os.path.join(SHOTS, '20-844-top-44px.png'))
            await pg.evaluate("$('dLayout').close(); LO_EXT.sg = window.__sgx")
            # 鉛筆から（閉じる）
            await pg.evaluate("openLayout('book', 'screen')"); await pg.wait_for_timeout(300)
            hs = await heights(pg)
            check(f'{h} 鉛筆から：閉じる・すべて・隠しているもの が 44px 以上:', len(hs) == 3 and all(x[1] >= 44 for x in hs) and hs[0][0] == '閉じる', str(hs))
            if h == 667: await pg.screenshot(path=os.path.join(SHOTS, '21-667-close-44px.png'))
            await pg.evaluate("$('dLayout').close()")
            allerr += errs; await c.close()
        # 成績のタブを出したとき・隠しているものがあるときは前どおり
        c, pg, errs = await open_app(b)
        await pg.evaluate("loEdit().tabs = ['home','book','log','ops','stats']; loChanged('t')"); await pg.evaluate("openLayout('top', 'settings')"); await pg.wait_for_timeout(200)
        sub = await pg.inner_text('#dLayout [data-lo-sec="tabs"] .lott small')
        check('成績のタブがあるときは成績の1行を出さない（修行を外した分は「隠している：修行」）:', sub == '隠している：修行', sub)
        await pg.evaluate("$('dLayout').close(); loEdit().tabs = ['home','book','log']; loChanged('t')"); await pg.evaluate("openLayout('top', 'settings')"); await pg.wait_for_timeout(200)
        sub = await pg.inner_text('#dLayout [data-lo-sec="tabs"] .lott small')
        check('隠しているタブがあるときは「隠している：…」:', sub.startswith('隠している：'), sub)
        await pg.evaluate("$('dLayout').close(); loResetAll(); loSave(); applyLayout()")
        # 修行のカードが足されたら1行は消える
        await pg.evaluate("window.__sgx = LO_EXT.sg; LO_EXT.sg = { groups: () => [], toggle: () => false }; openLayout('top', 'settings')"); await pg.wait_for_timeout(200)
        check('修行のカードがあるときは1行を出さない:', '修行の見方は' not in await pg.inner_text('#dLayout .losave'))
        await pg.evaluate("LO_EXT.sg = window.__sgx; $('dLayout').close()")
        # デモ：隠した見方はデモを終えると戻る（終了ボタン）
        await pg.evaluate("loToggleOff('log', 'map', true); loSave(); applyLayout()")
        before = await pg.evaluate("[...loOff('book')].sort().join(',') + '|' + [...loOff('log')].sort().join(',')")
        await pg.evaluate("$('toggleDemo').click()"); await pg.wait_for_timeout(800)
        check('デモが始まった:', await pg.evaluate("demo === true"))
        await pg.evaluate("loToggleOff('book', 'region', true); loToggleOff('book', 'map', true); loToggleOff('log', 'map', false); loSave(); applyLayout()")
        check('デモの中で図鑑は行った順だけ:', await pg.evaluate("viewsShown('book').map(x => x[0]).join(',') === 'chron'"))
        await pg.evaluate("$('toggleDemo').click()"); await pg.wait_for_timeout(800)
        after = await pg.evaluate("[...loOff('book')].sort().join(',') + '|' + [...loOff('log')].sort().join(',')")
        check('終了ボタンで始める前の表示に戻る:', await pg.evaluate("demo === false") and after == before, f'{before} → {after}')
        check('控えは消える:', await pg.evaluate("localStorage.getItem('soramemo.demo.lobak') === null"))
        # デモ：開き直してデモが終わったときも戻る
        await pg.evaluate("$('toggleDemo').click()"); await pg.wait_for_timeout(800)
        await pg.evaluate("loToggleOff('book', 'region', true); loToggleOff('book', 'map', true); loSave(); applyLayout(); VIEW.book = 'chron'; localStorage.setItem('soramemo.view.book', 'chron')")
        await pg.reload(); await ready(pg)
        after = await pg.evaluate("[...loOff('book')].sort().join(',') + '|' + [...loOff('log')].sort().join(',')")
        shown = await pg.evaluate("viewsShown('book').map(x => x[0]).join(',')")
        check('開き直しても始める前の表示に戻る:', await pg.evaluate("demo === false") and after == before and 'region' in shown, f'{after} / {shown}')
        allerr += errs; await c.close()
        await b.close()
    check('ページのエラーなし:', not allerr, str(allerr[:3]))
    print('errors', fails)
asyncio.run(main())
