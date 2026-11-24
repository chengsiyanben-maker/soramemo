# -*- coding: utf-8 -*-
# マイページを「タイル」にした画面案を作る。main の web/ を http://localhost:8765/ で開き、デモでマイページを開いて
# #dSettings .dlg を inject.js で描き直し、1画面1ファイルの HTML（外部の読み込みなし）に書き出す。アプリのコードは変えない。
# 使い方：(cd web && python3 -m http.server 8765 &) ; python3 make/capture_now.py ; python3 make/build.py ; python3 make/shoot.py ; python3 make/make_pages.py
import asyncio, os, re, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
INJ = open(os.path.join(HERE, 'inject.js'), encoding='utf-8').read()
SCREENS = [('A1-tiles6', 'A1 案A：6枚のタイル＋設定はカードで並べる', 'A'),
           ('B1-wide', 'B1 案B：成績を横長に＋設定は1枚の目次', 'B'),
           ('B2-data', 'B2 案B：目次から開いた「データとバックアップ」', 'Bsub')]
CLEAN = r"""() => {
  document.querySelectorAll('script,link,meta[http-equiv],.demo-banner,#toast,noscript,iframe').forEach(e => e.remove());
  document.querySelectorAll('dialog').forEach(d => { if(d.id !== 'dSettings') d.remove(); });
  [...document.body.children].forEach(e => { if(e.id !== 'dSettings' && e.tagName !== 'STYLE') e.remove(); });
  document.querySelectorAll('img').forEach(e => { if(!e.src.startsWith('data:')) e.remove(); });
}"""
STATIC = '<style>html,body{background:#F4F5F7;margin:0}dialog#dSettings{position:static;display:block;width:100%;max-width:none;height:auto;min-height:100vh;max-height:none;border:0;margin:0;padding:0;overflow:visible}</style>'
def finish(html, title):
    html = re.sub(r'@font-face\s*\{[^}]*url\((?!data:)[^}]*\}', '', html)
    html = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % title, html)
    html = html.replace('</head>', STATIC + '</head>')
    return '<!doctype html>\n' + html
async def enter(pg):
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    await pg.evaluate("openMyPage()"); await pg.wait_for_timeout(600)
async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        for fn, title, v in SCREENS:
            pg = await br.new_page(viewport={'width': 390, 'height': 844}, bypass_csp=True)
            await enter(pg)
            await pg.add_script_tag(content=INJ)
            n = await pg.evaluate("v => mtRender({v})", v); await pg.wait_for_timeout(300)
            await pg.evaluate(CLEAN)
            html = await pg.evaluate("document.documentElement.outerHTML")
            open(os.path.join(OUT, fn + '.html'), 'w', encoding='utf-8').write(finish(html, title))
            print(fn, len(html), json.dumps(n, ensure_ascii=False))
            await pg.close()
        await br.close()
asyncio.run(main())
