# -*- coding: utf-8 -*-
# 飛行場・滑空場・ヘリポートの図鑑に「種類の絞り込み」と「県名」を足した画面案を作る。
# 今のアプリ（main の web/ を http://localhost:8765/ で開く）のデモに入り、#bookAir を inject.js で描き直して、
# 1画面1ファイルの HTML（外部の読み込みなし）に書き出す。アプリのコードは変えない。
# 使い方：(cd web && python3 -m http.server 8765 &) ; python3 build.py ; python3 shoot.py <このフォルダの上> ; python3 make_pages.py
import asyncio, os, re, base64
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(OUT))), 'web')
INJ = open(os.path.join(HERE, 'inject.js'), encoding='utf-8').read()
# デモの記録に印を足す：竜ヶ崎飛行場 2回・ホンダエアポート・加須滑空場・東京ヘリポート・北海道の滑空場1つ（滝川）
VISITS = [(3004, '2026-09-21T10:00'), (3004, '2026-10-12T11:00'), (3002, '2026-10-05T09:30'), (2015, '2026-10-26T13:00'), (5006, '2026-11-03T15:00')]
VISIT_NAMES = ['滝川']

def sign_font():
    f = [x for x in os.listdir(os.path.join(WEB, 'fonts')) if x.startswith('sign')][0]
    return 'data:font/woff2;base64,' + base64.b64encode(open(os.path.join(WEB, 'fonts', f), 'rb').read()).decode()

CLEAN = r"""() => {
  document.querySelectorAll('script,link,dialog,meta[http-equiv],.demo-banner,#toast,noscript,iframe').forEach(e => e.remove());
  document.querySelectorAll('section.view').forEach(s => { if(s.id !== 'v-book') s.remove(); });
  document.querySelectorAll('img').forEach(e => { if(!e.src.startsWith('data:')) e.remove(); });
}"""

def finish(html, sf, scroll=None, title=''):
    html = re.sub(r'@font-face\s*\{font-family:"(Shippori Mincho|DotGothic16)"[^}]*\}', '', html)
    html = re.sub(r'url\(fonts/sign[^)]*\)', 'url(%s)' % sf, html)
    html = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % title, html)
    if scroll is not None:
        html = html.replace('</body>', '<script>scrollTo(0,%d)</script></body>' % scroll)
    html = html.replace('</body>', '<script>document.querySelectorAll(".zf-seg.scroll").forEach(e=>e.scrollLeft=e.scrollWidth)</script></body>')
    return '<!doctype html>\n' + html

SCREENS = [  # ファイル名, 題, 絞り込み, 見方, 基地の扱い, 送る先（扉）
    ('F1-all', 'F1 すべて（地方別）', 'all', 'region', 'sep', 'TOP'),
    ('F1b-all-kanto', 'F1b すべて：関東まで送ったところ', 'all', 'region', 'sep', '関東'),
    ('F2-heli', 'F2 ヘリポートに絞った（地方別）', 'heli', 'region', 'sep', None),
    ('F3-heli-map', 'F3 ヘリポートに絞った（地図）', 'heli', 'map', 'sep', None),
    ('F4-base-pill', 'F4 案A：「基地」のピルを足す', 'mil', 'region', 'pill', None),
    ('F5-base-mix', 'F5 案B：基地は「すべて」の中だけ', 'all', 'region', 'mix', '関東'),
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
        for fn, title, kind, view, base, rg in SCREENS:
            pg = await br.new_page(viewport={'width': 393, 'height': 852}, bypass_csp=True)
            await enter(pg)
            await pg.add_script_tag(content=INJ)
            await pg.evaluate("([v, nm]) => { for(const [a, t] of v) S.checkins.push({a, t:new Date(t).getTime()}); for(const n of nm){ const x = XA.find(a => a.name.startsWith(n)); if(x) S.checkins.push({a:x.id, t:Date.now()}); } }", [VISITS, VISIT_NAMES])
            await pg.evaluate("() => { const s = document.createElement('style'); s.textContent = ZF_CSS; document.head.appendChild(s); }")
            await pg.evaluate("setBookSeg('air'); DIRTY.book = true; renderVisible(); scrollTo(0,0)"); await pg.wait_for_timeout(500)
            await pg.evaluate("o => zfRender(o)", {'kind': kind, 'view': view, 'base': base}); await pg.wait_for_timeout(300)
            scroll = None
            if rg == 'TOP':
                scroll = await pg.evaluate("() => Math.round(document.querySelector('#bookAir .book-head').getBoundingClientRect().top + scrollY - 140)")
            elif rg:
                scroll = await pg.evaluate("rg => { const s = document.querySelector('#bookAir .zk-rg[data-rg=\"' + rg + '\"]'); return Math.round(s.getBoundingClientRect().top + scrollY - 70); }", rg)
            elif kind != 'all' or view == 'map':
                scroll = await pg.evaluate("() => Math.round(document.querySelector('#bookAir .book-head').getBoundingClientRect().top + scrollY - 140)")
            await pg.evaluate(CLEAN)
            html = await pg.evaluate("document.documentElement.outerHTML")
            open(os.path.join(OUT, fn + '.html'), 'w', encoding='utf-8').write(finish(html, sf, scroll, title))
            print(fn, len(html), scroll)
            await pg.close()
        await br.close()
asyncio.run(main())
