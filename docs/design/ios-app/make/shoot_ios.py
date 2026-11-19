# -*- coding: utf-8 -*-
# 1版を PNG に撮る（390×844 と 390×667 の2倍。I3・index は -full も）。13px 未満の字・44px 未満の押す所・はみ出し・字の切れを測る。
import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
NAMES = ["I1", "I1n", "I1b", "I1c", "I1d", "I2", "I2n", "I2b", "I2c", "I3", "I3w", "I3h", "I3m", "index"]
FULL = {"I1", "I3", "index"}
CHECK = """() => {
  const small = [], tap = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length || ['STYLE','SCRIPT','svg','path','circle'].includes(el.tagName)) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && parseFloat(getComputedStyle(el).fontSize) < 13) small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12));
  }
  for (const el of document.querySelectorAll('.main, .sec, .nloc .bt span, .qbar .bt span, .tabbar span, .nc .oth, .dkb, .setl .go, .stat .up, .idx li a, .brand span')) {
    const r = el.getBoundingClientRect(); if (r.height && r.height < 44) tap.push(el.textContent.trim().slice(0, 10) + ':' + Math.round(r.height));
  }
  const cut = []; for (const el of document.querySelectorAll('body *')) { const cs = getComputedStyle(el); if (cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 1) cut.push(el.textContent.trim().slice(0, 16)); }
  const sh = document.querySelector('.hsheet3'); const shCut = sh ? sh.scrollHeight > sh.clientHeight + 1 : false;
  return { small, tap, cut, shCut, over: document.documentElement.scrollWidth > 390 };
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for h in (844, 667):
            pg = await b.new_page(viewport={"width": 390, "height": h}, device_scale_factor=2)
            for n in NAMES:
                if h == 667 and n in ("index", "I3"): continue
                await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(150)
                await pg.screenshot(path=os.path.join(PNG, n + ("" if h == 844 else "-667") + ".png"))
                if h == 844 and n in FULL: await pg.screenshot(path=os.path.join(PNG, n + "-full.png"), full_page=True)
                print(h, n, await pg.evaluate(CHECK))
            await pg.close()
        await b.close()
asyncio.run(main())
