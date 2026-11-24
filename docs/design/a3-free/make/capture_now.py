# -*- coding: utf-8 -*-
# 今の羽田の3D を撮る：main の web/ を http://localhost:8765/ で開き、デモに入って openAp3d() を呼ぶ
# 撮った写真は案の下の絵（背景）に使う。視点ごと（全体・管制塔・機体）に、上の操作を隠した写真も撮る
import asyncio, os, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(HERE + '/now', exist_ok=True)
async def enter(pg):
    pg.on('console', lambda m: m.type == 'error' and print('console:', m.text[:200]))
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo') && document.getElementById('gateDemo').click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    await pg.evaluate("openAp3d()"); await pg.wait_for_timeout(15000)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for w, h, s, dpr in ((390, 844, '', 2), (375, 667, '-667', 1)):
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr, bypass_csp=True)
            await enter(pg)
            await pg.screenshot(path=HERE + '/now/now%s.png' % s)
            # 上の操作を隠した背景
            await pg.add_style_tag(content='#dAp3d .a3top,#dAp3d .a3pills,#dAp3d .a3chip,#dAp3d .a3sheet,#dAp3d [class*=a3lab],#dAp3d .a3edge{visibility:hidden!important}')
            await pg.wait_for_timeout(500)
            await pg.screenshot(path=HERE + '/now/bg-all%s.png' % s)
            for v in ('tower',):
                await pg.evaluate("document.querySelector('[data-a3-view=%s]').click()" % v); await pg.wait_for_timeout(3000)
                await pg.screenshot(path=HERE + '/now/bg-%s%s.png' % (v, s))
            print(await pg.evaluate("JSON.stringify({snaps:A3&&A3.snaps.length, objs:A3&&A3.objs.size, lite:A3&&A3.lite, err:A3&&A3.err})"))
            await pg.close()
        await b.close()
asyncio.run(main())
