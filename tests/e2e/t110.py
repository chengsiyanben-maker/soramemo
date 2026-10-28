import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# シンプルな見た目：濃い面は紺1色（--hero）、3レターコードと大きな数字だけ標識の書体（Sign）、図鑑の上は大きな数字1枚、
# 地方のタイルは紺1色で点の列なし、「そのほか」の航路は灰色、成績のパスポートは平らな紺で英語の大文字の見出しなし、ホームの地図に航路の線なし
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
SEED = open(os.path.join(HERE, 'seed_flights.js')).read() if os.path.exists(os.path.join(HERE, 'seed_flights.js')) else None
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width': 390, 'height': 844}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.layout', JSON.stringify({tabs:['home','book','log','ops','stats'], off:{home:[],book:[],log:[],ops:[],stats:['sgsum']}}));")
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(1500)
        # 記録を少し入れる（羽田→新千歳 JAL、羽田→那覇 そのほか）
        await pg.evaluate("""() => { const id = i => A.find(a => a.iata === i).id, t = Date.parse('2026-06-01T08:00:00+09:00');
          S.checkins = [{a:id('HND'), t:t - 3600e3, acc:20}, {a:id('CTS'), t:t + 7200e3, acc:20}];
          S.flights = [{id:'a1', from:id('HND'), to:id('CTS'), dep:t, arr:t + 5400e3, km:820, airline:'JL', no:'JL501'}, {id:'a2', from:id('HND'), to:id('OKA'), dep:t + 86400e3, arr:t + 86400e3 + 9000e3, km:1550, airline:'XX', no:'XX1'}]; render(); }""")
        hero = await pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--hero').trim()")
        check('濃い面の紺は1色（--hero）:', hero.lower() == '#0f1b2d')
        await pg.evaluate("goTab('home'); 0"); await pg.wait_for_timeout(800)
        check('ホームの搭乗券は紺:', await pg.evaluate("getComputedStyle(document.querySelector('#v-home .bp-main')).backgroundColor") == 'rgb(15, 27, 45)')
        check('ホームの地図に航路の線を描かない:', await pg.evaluate("!ROUTE_LAYER"))
        await pg.evaluate("goTab('book'); VIEW.book = 'tiles'; renderBook(); 0"); await pg.wait_for_timeout(600)
        big = await pg.evaluate("(() => { const b = document.querySelector('#bkAlt .bkbento'); return { kids: b.children.length, n: b.querySelector('.n').textContent, font: getComputedStyle(b.querySelector('.n')).fontFamily, bg: getComputedStyle(b.querySelector('.big')).backgroundColor }; })()")
        check(f'図鑑の上は大きな数字1枚（{big["n"]}）・標識の書体・紺:', big['kids'] == 1 and big['n'] == '2/86' and big['font'].startswith('Sign') and big['bg'] == 'rgb(15, 27, 45)')
        check('地方のタイルは点の列を出さない:', await pg.evaluate("[...document.querySelectorAll('#v-book .bk-tile .dots')].every(d => getComputedStyle(d).display === 'none')"))
        check('地方の色は紺1色:', await pg.evaluate("new Set(Object.values(RG_COL)).size") == 1)
        check('「そのほか」の航路は灰色:', await pg.evaluate("FMAP_COL.OTHER") == '#8B95A3')
        await pg.evaluate("goTab('log'); 0"); await pg.wait_for_timeout(800)
        f = await pg.evaluate("[...document.querySelectorAll('#v-log .pass .pa b')].slice(0, 2).map(e => [e.textContent, getComputedStyle(e).fontFamily])")
        check(f'フライトの3レターコードは標識の書体（{f}）:', len(f) == 2 and all(x[1].startswith('Sign') for x in f))
        await pg.evaluate("goTab('stats'); 0"); await pg.wait_for_timeout(800)
        pp = await pg.evaluate("(() => { const p = document.querySelector('#v-stats .passport'); return { img: getComputedStyle(p).backgroundImage, txt: p.innerText }; })()")
        check('成績のパスポートは平らな紺で、英語の大文字の見出しなし:', pp['img'] == 'none' and 'SORAMEMO PASSPORT' not in pp['txt'])
        loaded = await pg.evaluate("document.fonts.check('700 30px Sign', 'HND')")
        check('標識の書体を読み込める:', loaded)
        await pg.screenshot(path=os.path.join(WORK, 't80_stats.png'))
        check('エラーなし:', not errs)
        if errs: print(errs[:3])
        await b.close()
asyncio.run(main()); srv.shutdown()
if fails: print('FAIL', fails); sys.exit(1)
print('errors []')
