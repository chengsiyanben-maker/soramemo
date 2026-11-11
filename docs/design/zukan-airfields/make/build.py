# -*- coding: utf-8 -*-
# 図鑑の飛行場・滑空場の入口の画面案を作る。今のアプリ（main の web/ を http://localhost:8765/ で開く）のデモに入り、
# 図鑑の上に inject.js で入口と別の図鑑を描き足して、1画面1ファイルの HTML（外部の読み込みなし）に書き出す。アプリのコードは変えない。
# 使い方：(cd web && python3 -m http.server 8765 &) ; python3 build.py ; python3 shoot.py
import asyncio, os, re, base64
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(OUT))), 'web')
INJ = open(os.path.join(HERE, 'inject.js'), encoding='utf-8').read()
# デモの記録に、飛行場・滑空場の印を足す（竜ヶ崎飛行場 2回・ホンダエアポート・加須滑空場）
VISITS = [(3004, '2026-09-21T10:00'), (3004, '2026-10-12T11:00'), (3002, '2026-10-05T09:30'), (2015, '2026-10-26T13:00')]

def sign_font():
    f = [x for x in os.listdir(os.path.join(WEB, 'fonts')) if x.startswith('sign')][0]
    return 'data:font/woff2;base64,' + base64.b64encode(open(os.path.join(WEB, 'fonts', f), 'rb').read()).decode()

CLEAN = r"""() => {
  document.querySelectorAll('script,link,dialog,meta[http-equiv],.demo-banner,#toast,noscript,iframe').forEach(e => e.remove());
  document.querySelectorAll('section.view').forEach(s => { if(s.id !== 'v-book') s.remove(); });
  document.querySelectorAll('img').forEach(e => { if(!e.src.startsWith('data:')) e.remove(); });
  document.querySelectorAll('[data-za-drop]').forEach(e => e.remove());
}"""

def finish(html, sf, scroll=None, title=''):
    html = re.sub(r'@font-face\s*\{font-family:"(Shippori Mincho|DotGothic16)"[^}]*\}', '', html)
    html = re.sub(r'url\(fonts/sign[^)]*\)', 'url(%s)' % sf, html)
    html = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % title, html)
    if scroll is not None:
        html = html.replace('</body>', '<script>scrollTo(0,%d)</script></body>' % scroll)
    return '<!doctype html>\n' + html

SCREENS = [  # ファイル名, 題, 夜, 作り方, 送る位置
    ('02-entry', '02 図鑑の最初の画面に入口', False, 'entry', None),
    ('02b-entry-zero', '02b まだ1つもないとき', False, 'entry0', None),
    ('03-airfield-book', '03 飛行場・滑空場の図鑑', False, 'book', None),
    ('03b-airfield-kanto', '03b 関東の扉（送ったところ）', False, 'book', '関東'),
    ('04-entry-night', '04 夜：図鑑の最初の画面に入口', True, 'entry', None),
    ('04b-airfield-book-night', '04b 夜：飛行場・滑空場の図鑑', True, 'book', None),
]

async def enter(pg):
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    await pg.click('nav.tabs button[data-v=book]'); await pg.wait_for_timeout(1000)

async def main():
    sf = sign_font()
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        for fn, title, night, kind, rg in SCREENS:
            pg = await br.new_page(viewport={'width': 390, 'height': 844}, bypass_csp=True)
            await enter(pg)
            await pg.add_script_tag(content=INJ)
            if kind != 'entry0':
                await pg.evaluate("v => { for(const [a, t] of v) S.checkins.push({a, t:new Date(t).getTime()}); }", VISITS)
            await pg.evaluate("night => { const r = document.documentElement; if(night){ r.dataset.night = 'on'; r.dataset.palette = 'board'; } const s = document.createElement('style'); s.textContent = ZA_CSS; document.head.appendChild(s); window.ZA_ON = %s; }" % ('"%s"' % rg if rg else 'null'), night)
            await pg.evaluate("setBookSeg('main'); DIRTY.book = true; renderVisible(); scrollTo(0,0)"); await pg.wait_for_timeout(400)
            if kind in ('entry', 'entry0'):
                await pg.evaluate("zaEntry()")
            else:
                await pg.evaluate("zaBook()")
            await pg.wait_for_timeout(300)
            scroll = None
            if rg:
                scroll = await pg.evaluate("rg => { const s = document.getElementById('zarg-' + rg); return Math.round(s.getBoundingClientRect().top + scrollY - 8); }", rg)
            await pg.evaluate(CLEAN)
            html = await pg.evaluate("document.documentElement.outerHTML")
            open(os.path.join(OUT, fn + '.html'), 'w', encoding='utf-8').write(finish(html, sf, scroll, title))
            print(fn, len(html))
            await pg.close()
        await br.close()
asyncio.run(main())
