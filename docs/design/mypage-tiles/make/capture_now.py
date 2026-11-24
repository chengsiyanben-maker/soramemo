# -*- coding: utf-8 -*-
# 今のマイページを撮る：main の web/ を http://localhost:8765/ で開き、デモに入ってマイページを開く
import asyncio, os, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
async def enter(pg):
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    await pg.evaluate("openMyPage()"); await pg.wait_for_timeout(800)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w, h, s in ((390, 844, ''), (375, 667, '-667')):
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=2 if not s else 1, bypass_csp=True)
            await enter(pg)
            await pg.screenshot(path=HERE + '/now/now%s.png' % s)
            if not s:
                hh = await pg.evaluate("document.querySelector('#dSettings .dlg').scrollHeight")
                await pg.set_viewport_size({'width': w, 'height': hh + 40}); await pg.wait_for_timeout(300)
                await pg.screenshot(path=HERE + '/now/now-full.png')
                info = await pg.evaluate("""() => ({flights:S.flights.length, cars:S.flights.filter(f=>f.car||f.mode==='car').length, ap:visited().size, keys:Object.keys(S.flights[0]||{}), tabs:loTabs(), pins:(typeof pinList==='function'?pinList():null), dlg:getComputedStyle(document.getElementById('dSettings')).cssText.length})""")
                print(json.dumps(info, ensure_ascii=False))
            await pg.close()
        await b.close()
asyncio.run(main())
