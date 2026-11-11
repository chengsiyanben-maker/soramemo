# 見方だけの小さいシート（11/10 20時 PM の指示・改善担当 review-c5 の1）
#   見方の帯の鉛筆は、その画面の見方だけを ON／OFF するシートを開く（題・数・完了は上に固定）。図鑑の地方別は「いつも」・1つ以上残す・元に戻す
#   鉛筆の押せる所は 44×44。マイページの「全部を見直す」の1枚は題と閉じるが上に残る
import os, sys, asyncio
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web'))
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-all-in-tabs')); os.makedirs(SHOTS, exist_ok=True)
from playwright.async_api import async_playwright
fails = []
def check(label, ok, extra=''):
    print(label, ok, extra)
    if not ok: fails.append(label)
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.tp.tip','1');"
async def open_app(b, h=844):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, timezone_id='Asia/Tokyo')
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.add_init_script(NEW)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return c, pg, errs
TOP = "(() => { const t = document.querySelector('#vsTitle').getBoundingClientRect(), d = document.querySelector('#dViews .tpdone').getBoundingClientRect(); return t.top >= 0 && t.bottom <= innerHeight && d.top >= 0 && d.bottom <= innerHeight; })()"
async def main():
    allerr = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c, pg, errs = await open_app(b)
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(400)
        sz = await pg.evaluate("(() => { const r = document.querySelector('[data-vs-open=\"book\"]').getBoundingClientRect(); return [r.width, r.height]; })()")
        check('図鑑の鉛筆の押せる所は 44×44:', sz[0] >= 44 and sz[1] >= 44, str(sz))
        await pg.click('[data-vs-open="book"]'); await pg.wait_for_timeout(300)
        check('図鑑の鉛筆で「図鑑の見方」のシート（表示の編集の1枚ではない）:', await pg.evaluate("$('dViews').open && !$('dLayout').open") and (await pg.inner_text('#vsTitle')) == '図鑑の見方')
        check('題と完了が見える:', await pg.evaluate(TOP))
        check('地方別は「いつも」・地図と行った順は ON／OFF:', await pg.locator('#dViews .vsrow.lock').count() == 1 and 'いつも' in await pg.inner_text('#dViews .vsrow.lock') and await pg.locator('#dViews [data-vs-sw]').count() == 2 and await pg.locator('#dViews .losw[role="switch"][aria-checked="true"]').count() == 2)
        check('数は 3/3:', (await pg.inner_text('#dViews .tpcnt')).replace(' ', '').startswith('3/3'))
        await pg.screenshot(path=os.path.join(SHOTS, '30-844-book-views.png'))
        await pg.click('#dViews [data-vs-sw="chron"]'); await pg.wait_for_timeout(300)
        check('OFF にすると見方の帯から消え、行はその場に残る:', await pg.locator('#bookMain [data-vw="book:chron"], [data-vw="book:chron"]').count() == 0 and await pg.locator('#dViews .vsrow.off[data-vs="chron"]').count() == 1)
        check('元に戻すのトースト:', '「行った順」を隠しました' in await pg.inner_text('#dViews .tpundo'))
        await pg.screenshot(path=os.path.join(SHOTS, '31-844-book-views-off.png'))
        await pg.click('#dViews [data-vs-undo]'); await pg.wait_for_timeout(300)
        check('元に戻すで戻る:', await pg.locator('[data-vw="book:chron"]').count() == 1 and await pg.locator('#dViews .tpundo').count() == 0)
        await pg.click('#dViews [data-vs-sw="chron"]'); await pg.click('#dViews [data-vs-sw="map"]'); await pg.wait_for_timeout(200)
        check('地方別だけのときも地方別は消えない（1つ以上）:', await pg.evaluate("viewsShown('book').map(v => v[0]).join()") == 'region')
        await pg.click('#dViews [data-vs-sw="chron"]'); await pg.click('#dViews [data-vs-sw="map"]'); await pg.click('#dViews .tpdone'); await pg.wait_for_timeout(200)
        check('完了で閉じる:', await pg.evaluate("!$('dViews').open"))
        allerr += errs; await c.close()
        # 667：フライト（9つ）。一覧を送っても題と完了は上に残る。最後の1つは OFF にできない
        c, pg, errs = await open_app(b, h=667)
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(600)
        await pg.click('[data-vs-open="log"]'); await pg.wait_for_timeout(300)
        check('667：フライトの見方 3行（日誌は「いつも」・地図と年のまとめは ON／OFF）:', await pg.locator('#dViews .vsrow').count() == 3 and await pg.locator('#dViews [data-vs-sw]').count() == 2 and 'いつも' in await pg.inner_text('#dViews .vsrow.lock'))
        await pg.evaluate("document.querySelector('#dViews .tpscroll').scrollTop = 9999"); await pg.wait_for_timeout(200)
        check('667：一覧を送っても題と完了が見える:', await pg.evaluate(TOP))
        await pg.screenshot(path=os.path.join(SHOTS, '32-667-log-views.png'))
        for i in ['map', 'year']: await pg.click(f'#dViews [data-vs-sw="{i}"]')
        check('667：地図と年のまとめを OFF にしても日誌は残る:', await pg.evaluate("viewsShown('log').map(v => v[0]).join()") == 'diary')
        await pg.click('#dViews [data-vs-all]'); await pg.wait_for_timeout(400)
        check('「表示の編集をすべて見る」で今の1枚（フライトの所）:', await pg.evaluate("$('dLayout').open && LO_PAGE === 'log'"))
        tv = await pg.evaluate("(() => { const h = document.querySelector('#dLayout .spctop'), r = h.getBoundingClientRect(), x = h.querySelector('[data-close]').getBoundingClientRect(); return r.top >= -1 && x.bottom <= innerHeight && x.top >= 0; })()")
        check('667：表示の編集の1枚も題と閉じるが上に残る:', tv is True)
        await pg.screenshot(path=os.path.join(SHOTS, '33-667-layout-sticky.png'))
        allerr += errs; await c.close()
        # 運用も鉛筆はシート
        c, pg, errs = await open_app(b)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        await pg.click('[data-vs-open="ops"]'); await pg.wait_for_timeout(300)
        check('運用の鉛筆は「運用の見方」のシート（7行）:', (await pg.inner_text('#vsTitle')) == '運用の見方' and await pg.locator('#dViews [data-vs-sw]').count() == 7)
        allerr += errs; await c.close()
        await b.close()
    print('fails', fails)
    print('errors', fails + allerr)
asyncio.run(main())
