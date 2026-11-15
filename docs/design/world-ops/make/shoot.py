# -*- coding: utf-8 -*-
# 画面案を PNG に撮る（390×844 の2倍。長い画面は -full も）。あわせて 13px 未満の字・44px 未満の押す所・横のはみ出しを数える。
import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
NAMES = ["00a", "00b", "W1", "W6", "W2", "W3", "W4", "W4b", "W5", "index"]
FULL = {"W1", "W6", "00a", "00b", "W5"}
CHECK = """() => {
  const small = [], tap = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length || ['STYLE','SCRIPT','svg','path','circle','text'].includes(el.tagName)) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const cs = getComputedStyle(el);
    if (own && parseFloat(cs.fontSize) < 13 && el.closest('.shot') == null) small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12));
  }
  for (const el of document.querySelectorAll('button, a, .go, .bdtabs span, .tabbar span')) {
    const r = el.getBoundingClientRect(); if (r.height && r.height < 44) tap.push(el.textContent.trim().slice(0, 10) + ':' + Math.round(r.height));
  }
  return { small, tap, over: document.documentElement.scrollWidth > 390 };
}"""
async def main():
    os.makedirs(PNG, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        for n in NAMES:
            await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(PNG, n + ".png"))
            if n in FULL: await pg.screenshot(path=os.path.join(PNG, n + "-full.png"), full_page=True)
            print(n, await pg.evaluate(CHECK))
        await pg.set_viewport_size({"width": 390, "height": 667})
        for n in ["W1", "W2", "W3", "W4"]:
            await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(PNG, n + "-667.png"))
        await b.close()
asyncio.run(main())
