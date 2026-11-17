# -*- coding: utf-8 -*-
# 4版を PNG に撮る（390×844 と 390×667 の2倍。長い画面は -full も）。13px 未満の字・44px 未満の押す所・はみ出しを測る。

import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
NAMES = [n + "-v4" for n in ["K0","K0i","K1","K1s","K1n","K1o","K1h","K2","K3","K3s","K3n","K4","K4d","K4t","K4u","K5","K5n","K6","K6n","K7","K7n","K8","K9","K9b","K10"]] + ["index"]
FULL = {"K5-v4", "K5n-v4", "K6-v4", "K6n-v4", "K7-v4", "index"}
TG = 'ON／OFF のスイッチ（.tg）は行全体（56px 以上）を押すので数えない'
CHECK = """() => {
  const small = [], tap = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length || ['STYLE','SCRIPT','svg','path','circle','text'].includes(el.tagName)) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && parseFloat(getComputedStyle(el).fontSize) < 13 && el.closest('.shot') == null) small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12));
  }
  for (const el of document.querySelectorAll('button, a, .tabbar span, .pen, .ic, .pinbtn, .pinpill, .pinlab, .dkb, .pinmark, .login1 span, .go2, .rm, .ed, .pillbtn, .keep a, .chip, .dot2, .more2, .danger, .apc .go')) {
    const r = el.getBoundingClientRect(); if (r.height && r.height < 44) tap.push(el.textContent.trim().slice(0, 10) + ':' + Math.round(r.height));
  }
  const cut = []; for (const el of document.querySelectorAll('body *')) { const cs = getComputedStyle(el); if (cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 1) cut.push(el.textContent.trim().slice(0, 16)); }
  const offR = [...document.querySelectorAll('.vw3 .pen, .krow3 .ci, .toast a, .nc .oth')].filter(e => e.getBoundingClientRect().right > 390).length;
  const tb = document.querySelector('.tabbar'), src = document.querySelector('.src, .key2'), bd = [...document.querySelectorAll('.u2')].pop(), sh = document.querySelector('.hs2');
  const lim = document.querySelector('.sheet') ? innerHeight : (tb ? tb.getBoundingClientRect().top : innerHeight);
  const shE = document.querySelector('.sheet'); const sheetCut = shE ? (shE.scrollHeight > shE.clientHeight + 1 || shE.getBoundingClientRect().top < 0) : false;
  return { small, tap, cut, offR, sheetCut, over: document.documentElement.scrollWidth > 390,
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
                if h == 667 and n in ("index", "K10-v4"): continue
                await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(200)
                await pg.screenshot(path=os.path.join(PNG, n + ("" if h == 844 else "-667") + ".png"))
                if h == 844 and n in FULL: await pg.screenshot(path=os.path.join(PNG, n + "-full.png"), full_page=True)
                print(h, n, await pg.evaluate(CHECK))
            await pg.close()
        await b.close()
asyncio.run(main())
