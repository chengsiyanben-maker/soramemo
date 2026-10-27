import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 空港はどの一覧でも北から順（緯度の高い順）。米軍が管理する横田・嘉手納・普天間は「一般の人が行けない飛行場」の枠で、基地の枠は自衛隊だけ
import asyncio, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WEB)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(1500)
        north = "xs => xs.every((a, i) => i === 0 || xs[i - 1].lat >= a.lat)"
        check('86空港は北から順:', await pg.evaluate(f"({north})(A)") and await pg.evaluate("A.length") == 86)
        check('番外編も北から順:', await pg.evaluate(f"({north})(XA)"))
        k = await pg.evaluate("Object.fromEntries([1015, 1016, 1029, 1030].map(id => [id, BY[id].kind]))")
        check('横田・嘉手納・普天間は秘密、厚木は基地:', k == {'1015': 'secret', '1016': 'mil', '1029': 'secret', '1030': 'secret'})
        check('基地の枠は27か所・「米軍」の文字は出さない:', await pg.evaluate("XA.filter(a => a.kind === 'mil').length") == 27 and await pg.evaluate("XKIND.mil.label") == '自衛隊の飛行場')
        # 図鑑：地方の一覧と番外編の一覧が、画面の上でも北から順
        await pg.evaluate("goTab('book'); VIEW.book = 'tiles'; renderBook(); 0"); await pg.wait_for_timeout(500)
        await pg.click('.bk-tile[data-rg="北海道"]'); await pg.wait_for_timeout(400)
        names = await pg.evaluate("[...document.querySelectorAll('#book .cell .nm')].map(e => e.firstChild.textContent.replace('（離島）', ''))")
        lat = [x for x in await pg.evaluate("ns => ns.map(n => (A.find(a => a.name === n) || {}).lat)", names) if x is not None]   # 後ろのターミナルの印は除く
        check(f'北海道の一覧は北から（{names[:3]}…）:', len(lat) == 12 and all(lat[i - 1] >= lat[i] for i in range(1, len(lat))))
        for k in ['field', 'glider', 'mil', 'secret']:
            await pg.evaluate(f"(() => {{ const d = document.querySelector('details.xgrp[data-xk={k}]'); d.open = true; d.dispatchEvent(new Event('toggle')); }})()"); await pg.wait_for_timeout(300)
        for k in ['field', 'glider', 'mil']:
            ex = await pg.evaluate(f"[...document.querySelectorAll('details.xgrp[data-xk={k}] .cell .nm')].map(e => e.firstChild.textContent)")
            exl = await pg.evaluate("ns => ns.map(n => (XA.find(a => a.name === n) || {}).lat)", ex)
            check(f'番外編（{k}）の一覧も北から（{len(ex)}か所）:', len(exl) > 5 and all(x is not None for x in exl) and all(exl[i - 1] >= exl[i] for i in range(1, len(exl))))
        mil = await pg.evaluate("[...document.querySelectorAll('details.xgrp[data-xk=mil] .cell .nm')].map(e => e.firstChild.textContent)")
        sec = await pg.evaluate("[...document.querySelectorAll('details.xgrp[data-xk=secret] .cell .nm')].map(e => e.firstChild.textContent)")
        check('基地の一覧に米軍の3か所は出ず、秘密の枠は5つとも？？？:', not ({'横田基地', '嘉手納基地', '普天間飛行場'} & set(mil)) and len(mil) == 27 and sec == ['？？？'] * 5)
        ach = await pg.evaluate("ACH.find(x => x.id === 'milall').target")
        check('全基地制覇は27か所:', ach == 27)
        check('エラーなし:', not errs)
        if errs: print(errs[:3])
        await b.close()
asyncio.run(main()); srv.shutdown()
if fails: print('FAIL', fails); sys.exit(1)
print('errors []')
