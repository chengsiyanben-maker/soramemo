import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 「気軽に」はいちばん軽い構成：タブはホーム・図鑑・フライト、図鑑はタイル・フライトは搭乗券だけ（見方の列は出さない）、
# フライトの年ごと・記録帳と、ホームの地図の凡例は隠す（出典は残す）。＋で記録帳に来たら一覧へ戻れる。成績・運用はマイページから。
# 撮影・修行の構成は今までどおり
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
vis = "s => { const e = document.querySelector(s); return !!e && !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length) && getComputedStyle(e).visibility !== 'hidden'; }"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        for per in ['casual', 'spot', 'shugyo']:
            c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo')
            await c.add_init_script(f"localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','{per}');")
            pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(1500)
            tabs = await pg.evaluate("[...document.querySelectorAll('nav.tabs button:not([hidden])')].map(b => b.dataset.v)")
            await pg.evaluate("goTab('home'); 0"); await pg.wait_for_timeout(500)
            leg = await pg.evaluate(f"({vis})('#homeSheet .maplegend > span:not(.mcred)')"); cred = await pg.evaluate(f"({vis})('#homeSheet .maplegend .mcred')")
            await pg.evaluate("goTab('log'); 0"); await pg.wait_for_timeout(800)
            seg = await pg.evaluate(f"({vis})('#v-log .lseg')"); lrow = await pg.evaluate("[...document.querySelectorAll('#v-log .vwrow')].some(r => !r.hidden)")
            if per == 'casual':
                check('気軽に：タブはホーム・図鑑・フライト:', tabs == ['home', 'book', 'log'])
                check('気軽に：地図の凡例は隠し、出典は残す:', not leg and cred)
                check('気軽に：フライトは搭乗券だけで、見方の列と年ごと・記録帳を出さない:', not seg and not lrow and await pg.evaluate("VIEW.log") == 'pass')
                await pg.evaluate("$('flAdd').click(); 0"); await pg.wait_for_timeout(500)
                check('気軽に：＋で記録帳に来たら、一覧へ戻る切り替えが出る:', await pg.evaluate(f"({vis})('#v-log .lseg')") and not await pg.evaluate("$('lsBook').hidden"))
                await pg.evaluate("setLogSeg('list'); 0"); await pg.wait_for_timeout(200)
                check('気軽に：一覧に戻ると切り替えはまた隠れる:', not await pg.evaluate(f"({vis})('#v-log .lseg')"))
                await pg.evaluate("goTab('book'); 0"); await pg.wait_for_timeout(500)
                check('気軽に：図鑑はタイルだけで、見方の列を出さない:', await pg.evaluate("VIEW.book") == 'tiles' and not await pg.evaluate("[...document.querySelectorAll('#v-book .vwrow')].some(r => !r.hidden)"))
                check('気軽に：ホームの「これから乗る便」は出さない:', await pg.evaluate("loOff('home').has('ride')"))
                await pg.evaluate("$('openSettings').click(); 0"); await pg.wait_for_timeout(500)
                more = await pg.evaluate("[...document.querySelectorAll('#personaMore [data-persona-open]')].map(b => b.dataset.personaOpen)")
                check(f'気軽に：成績と運用はマイページから開ける（{more}）:', 'stats' in more and 'ops' in more)
            else:
                check(f'{per}：地図の凡例は今までどおり:', leg and cred)
                check(f'{per}：フライトの年ごと・記録帳は今までどおり:', seg)
                if per == 'shugyo': check('修行：フライトの見方の列は今までどおり:', lrow)
            await c.close()
        check('エラーなし:', not errs)
        if errs: print(errs[:3])
        await b.close()
asyncio.run(main()); srv.shutdown()
if fails: print('FAIL', fails); sys.exit(1)
print('errors []')
