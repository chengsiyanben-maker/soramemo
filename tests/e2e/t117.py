# テストの道具 keepls.py（読み込み直すテストを http で開く）の確かめ
# 読み込み直すテストの開き方（http）で、書いた直後に読み込み直しても、記録（soramemo.v1）が毎回残るか。
# 新しく書いた鍵（1件）と、書き換えた値（1件→2件。古い値に戻らないか）の両方を、20回くり返す
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import reload_keep, goto_http
async def main():
    fails = []
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for i in range(20):
            c=await b.new_context(viewport={'width':400,'height':860}); await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');")
            pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
            await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"')
            await pg.evaluate("""() => { const id = A.find(a => a.iata === 'HND').id;
              localStorage.setItem('soramemo.v1', JSON.stringify({checkins:[{a:id, t:Date.parse('2026-01-01T12:00:00+09:00'), acc:20, term:null}], flights:[], manual:[]})); }""")
            await reload_keep(pg); await pg.wait_for_function('typeof render === "function" && typeof S !== "undefined"')
            n = await pg.evaluate('S.checkins.length')
            if n != 1: fails.append(f'{i}回目: 記録が {n} 件')
            await pg.evaluate("""() => { const id = A.find(a => a.iata === 'CTS').id; S.checkins.push({a:id, t:Date.parse('2026-01-02T12:00:00+09:00'), acc:20, term:null}); save(); }""")
            await reload_keep(pg); await pg.wait_for_function('typeof render === "function" && typeof S !== "undefined"')
            n = await pg.evaluate('S.checkins.length')
            if n != 2: fails.append(f'{i}回目（書き換え）: 記録が {n} 件')
            if errs: fails.append(f'{i}回目: {errs}')
            await c.close()
        await b.close()
    print('20回とも記録が残る（新しい鍵・書き換えた値）:', not fails)
    print('errors', fails)
asyncio.run(main())
