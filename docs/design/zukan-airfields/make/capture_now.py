import asyncio, sys
from playwright.async_api import async_playwright
OUT = sys.argv[1]
async def enter(pg):
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo').click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
    await pg.click('nav.tabs button[data-v=book]'); await pg.wait_for_timeout(1200)
async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        for h in (844,667):
            pg = await br.new_page(viewport={'width':390,'height':h})
            await enter(pg)
            await pg.screenshot(path=f'{OUT}/now-main-{h}.png')
            await pg.screenshot(path=f'{OUT}/now-main-full-{h}.png', full_page=True)
            await pg.evaluate("setBookSeg('others'); DIRTY.book=true; renderVisible(); scrollTo(0,0)"); await pg.wait_for_timeout(500)
            await pg.screenshot(path=f'{OUT}/now-others-{h}.png')
            await pg.evaluate("setBookSeg('air'); DIRTY.book=true; renderVisible(); scrollTo(0,0)"); await pg.wait_for_timeout(500)
            await pg.screenshot(path=f'{OUT}/now-air-{h}.png', full_page=True)
            if h==844:
                await pg.evaluate("setBookSeg('main'); DIRTY.book=true; renderVisible(); scrollTo(0,0)"); await pg.wait_for_timeout(500)
                print(await pg.evaluate("document.getElementById('bookMain').outerHTML.length"))
                open(f'{OUT}/bookMain.html','w').write(await pg.evaluate("document.getElementById('bookMain').outerHTML"))
                print(await pg.evaluate("visitedExtra().size"), await pg.evaluate("XA.filter(a=>a.kind=='field').length"), await pg.evaluate("XA.filter(a=>a.kind=='glider').length"))
            await pg.close()
        await br.close()
asyncio.run(main())
