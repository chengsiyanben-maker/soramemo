# マイページを閉じてすぐ別のページで開き直しても、そのページのまま（11/25 t30 が落ちた件）
#   ダイアログの「閉じた」知らせ（close）はあとから届く。前は、その知らせで開き直したページが目次に戻り（詳しい設定のデモの「開始」が隠れた）、
#   戻る操作の積み（CX_STACK）からも外れていた。同じ流れを1回の evaluate で起こして確かめる
import os, sys, asyncio
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, HERE); from keepls import goto_http
from playwright.async_api import async_playwright

async def main():
    ok = True
    def check(name, cond):
        nonlocal ok; print(('OK ' if cond else 'NG ') + name); ok = ok and bool(cond)
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');")
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await goto_http(pg, os.path.join(WEB, 'index.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        # 1) 目次で開いて閉じ、同じ流れのうちに「詳しい設定」で開き直す
        await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(200)
        await pg.evaluate("""() => { $('dSettings').close(); openMyPage('adv'); }"""); await pg.wait_for_timeout(300)
        st = await pg.evaluate("""() => ({ page: $('dSettings').dataset.mpPage || null, open: $('dSettings').open, title: $('mpTitle').textContent,
            h: $('toggleDemo').getBoundingClientRect().height, inStack: CX_STACK.includes($('dSettings')) })""")
        check('開き直したページは詳しい設定のまま', st['page'] == 'adv' and st['title'] == '詳しい設定' and st['open'])
        check('デモの「開始」が見える', st['h'] > 0)
        check('戻る操作の積みに残っている', st['inStack'])
        await pg.screenshot(path=os.path.join(WORK, 't193_adv.png'))
        await pg.click('#toggleDemo'); await pg.wait_for_timeout(300)
        check('デモを始められる', await pg.evaluate('demo === true'))
        # 2) 戻る操作でマイページが閉じる（積みから外れていると閉じない）
        await pg.evaluate("""() => { if($('dSettings').open) $('dSettings').close(); }"""); await pg.wait_for_timeout(300)
        await pg.evaluate("""() => { openMyPage(); }"""); await pg.wait_for_timeout(200)
        await pg.evaluate("""() => { $('dSettings').close(); openMyPage('show'); }"""); await pg.wait_for_timeout(300)
        await pg.go_back(); await pg.wait_for_timeout(400)
        check('戻るで開き直したマイページが閉じる', not await pg.evaluate("$('dSettings').open"))
        # 3) ふつうに閉じれば目次に戻る（次に目次で開く）
        await pg.evaluate("openMyPage('data')"); await pg.wait_for_timeout(200); await pg.evaluate("$('dSettings').close()"); await pg.wait_for_timeout(300)
        check('ふつうに閉じたら目次に戻す', await pg.evaluate("!$('dSettings').dataset.mpPage && $('mpTitle').textContent === 'マイページ'"))
        await b.close()
    print('errors:', errs if ok else errs + ['NG あり'])

asyncio.run(main())
