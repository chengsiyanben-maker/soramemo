# -*- coding: utf-8 -*-
# 1版を PNG に撮る（390×844 と 390×667 の2倍。長い画面は -full も）。13px 未満の字・44px 未満の押す所・はみ出しを測る。

import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
NAMES = ["P1", "P1g", "P1m", "P1e", "P1x", "P2o", "P2", "P3", "P4", "P5", "P5f", "P6", "P7", "index"]
FULL = {"P1", "P1m", "P3", "P5", "index"}
TG = 'ON／OFF のスイッチ（.tg）は行全体（56px 以上）を押すので数えない'
CHECK = """() => {
  const small = [], tap = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length || ['STYLE','SCRIPT','svg','path','circle','text'].includes(el.tagName)) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && parseFloat(getComputedStyle(el).fontSize) < 13 && el.closest('.shot') == null) small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12));
  }
  for (const el of document.querySelectorAll('button, a, .tabbar span, .pen, .ic, .pinbtn, .pinpill, .rm, .ed, .pillbtn, .keep a, .chip')) {
    const r = el.getBoundingClientRect(); if (r.height && r.height < 44) tap.push(el.textContent.trim().slice(0, 10) + ':' + Math.round(r.height));
  }
  const tb = document.querySelector('.tabbar'), src = document.querySelector('.src, .key2'), bd = [...document.querySelectorAll('.u2')].pop(), sh = document.querySelector('.hs2');
  const lim = document.querySelector('.sheet') ? innerHeight : (tb ? tb.getBoundingClientRect().top : innerHeight);
  return { small, tap, over: document.documentElement.scrollWidth > 390,
    sheetTop: sh ? Math.round(sh.getBoundingClientRect().top) : null,
    badgeBottom: bd ? Math.round(bd.getBoundingClientRect().bottom) : null,
    srcBottom: src ? Math.round(src.getBoundingClientRect().bottom) : null, limit: Math.round(lim) };
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for h in (844, 667):
            pg = await b.new_page(viewport={"width": 390, "height": h}, device_scale_factor=2)
            for n in NAMES:
                if h == 667 and n in ("index", "P7"): continue
                await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(200)
                await pg.screenshot(path=os.path.join(PNG, n + ("" if h == 844 else "-667") + ".png"))
                if h == 844 and n in FULL: await pg.screenshot(path=os.path.join(PNG, n + "-full.png"), full_page=True)
                print(h, n, await pg.evaluate(CHECK))
            await pg.close()
        await b.close()
asyncio.run(main())
