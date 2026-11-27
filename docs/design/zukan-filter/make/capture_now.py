# -*- coding: utf-8 -*-
# 今の画面を撮る：main の web/ を http://localhost:8765/ で開き、デモで図鑑→「飛行場・滑空場・ヘリポートの図鑑」と、図鑑の地図の見方を撮る
import asyncio, os, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
async def enter(pg):
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    await pg.click('nav.tabs button[data-v=book]'); await pg.wait_for_timeout(1000)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 393, 'height': 852}, bypass_csp=True)
        await enter(pg)
        await pg.screenshot(path=HERE + '/now/now-main.png')
        await pg.evaluate("setBookSeg('air'); DIRTY.book = true; renderVisible(); scrollTo(0,0)"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=HERE + '/now/now-air.png')
        await pg.screenshot(path=HERE + '/now/now-air-full.png', full_page=True)
        info = await pg.evaluate("""() => { const c = {}; for(const a of XA){ c[a.kind] = (c[a.kind]||0)+1; } return {c, heli: XA.filter(a=>a.kind==='heli').map(a=>a.name+'/'+a.pref), tile: (()=>{const t=document.querySelector('#bookAir .zk-ap'); const r=t.getBoundingClientRect(); return [r.width,r.height, t.outerHTML.slice(0,300)];})(), vis:[...visitedExtra()].map(i=>BY[i].name) }; }""")
        print(json.dumps(info, ensure_ascii=False))
        await b.close()
asyncio.run(main())
