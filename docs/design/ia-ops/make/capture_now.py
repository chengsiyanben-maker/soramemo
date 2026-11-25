# -*- coding: utf-8 -*-
# 今の画面を撮る（色と文字を合わせる見本）：main の web/ を http://localhost:8765/ で開き、デモに入る
import asyncio, os
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(HERE + '/now', exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo') && document.getElementById('gateDemo').click()")
        await pg.wait_for_timeout(3500)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        await pg.screenshot(path=HERE + '/now/home.png')
        print(await pg.evaluate("[...document.querySelectorAll('nav.tabs button, nav button')].map(b=>b.textContent.trim()+':'+JSON.stringify(b.dataset)).join(' | ')"))
        for t in ('ops',):
            await pg.evaluate("(()=>{const b=[...document.querySelectorAll('nav button')].find(x=>JSON.stringify(x.dataset).includes('%s'));b&&b.click()})()" % t)
            await pg.wait_for_timeout(2500)
            await pg.screenshot(path=HERE + '/now/%s.png' % t)
            await pg.screenshot(path=HERE + '/now/%s-full.png' % t, full_page=True)
        await b.close()
asyncio.run(main())
