# -*- coding: utf-8 -*-
# 今の入口を撮る（色と流れを合わせる見本）：web/ を http://localhost:8765/ で開く
import asyncio, os
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); os.makedirs(HERE + '/now', exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 390, 'height': 844})
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=HERE + '/now/1-gate.png')
        for d in ('dAuth', 'dGuide', 'dPersona', 'dLocWhy'):
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(x=>x.close());const d=document.getElementById('%s');d&&d.showModal&&d.showModal()" % d)
            await pg.wait_for_timeout(600); await pg.screenshot(path=HERE + '/now/%s.png' % d)
            print(d, (await pg.evaluate("(document.getElementById('%s')||{}).innerText||''" % d))[:400].replace('\n', ' / '))
        await b.close()
asyncio.run(main())
