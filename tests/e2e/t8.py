import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def run(scheme):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c=await b.new_context(viewport={'width':400,'height':860}, color_scheme=scheme, device_scale_factor=2)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type=='error' and (None if ('woff2' in m.text or m.text.startswith('Failed to load resource')) else errs.append(m.text)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(1200)
        print(scheme,'guide open:', await pg.is_visible('#dGuide'))
        await pg.screenshot(path=os.path.join(WORK,f'u_guide_{scheme}.png'))
        for _ in range(3): await pg.click('#obNext'); await pg.wait_for_timeout(150)
        print('guide closed:', not await pg.is_visible('#dGuide'))
        await pg.screenshot(path=os.path.join(WORK,f'u_home_{scheme}.png'))
        await pg.click('#openSettings'); await pg.click('#toggleDemo')
        cts = await pg.evaluate("'a:'+A.find(a=>a.iata=='CTS').id"); oka = await pg.evaluate("'a:'+A.find(a=>a.iata=='ISG').id")
        for v in ['t:HND-T2', cts, oka]:
            await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(900)
            if v==oka: await pg.screenshot(path=os.path.join(WORK,f'u_stamp_{scheme}.png'))
            if v!=oka: await pg.click('#dStamp .row2 .btn2')
        await pg.click('#dStamp [data-share-a]'); await pg.wait_for_timeout(1200)
        await pg.screenshot(path=os.path.join(WORK,f'u_share_{scheme}.png'))
        src = await pg.get_attribute('#shareImg','src')
        import base64; open(os.path.join(WORK,f'u_card_{scheme}.png'),'wb').write(base64.b64decode(src.split(',')[1]))
        await pg.click('#shareClose')
        await pg.click('nav.tabs button[data-v=log]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(WORK,f'u_log_{scheme}.png'))
        await pg.click('#shareMap'); await pg.wait_for_timeout(1200)
        src = await pg.get_attribute('#shareImg','src'); open(os.path.join(WORK,f'u_mapcard_{scheme}.png'),'wb').write(base64.b64decode(src.split(',')[1]))
        print('errors', errs); await b.close()
async def main():
    await run('light'); await run('dark')
asyncio.run(main())
