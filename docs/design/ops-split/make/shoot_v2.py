# -*- coding: utf-8 -*-
# 2版の画面案を PNG に撮る（390×844 の2倍。長い画面は -full、主な画面は -667 も）。
# 数えるもの：13px 未満の字・44px 未満の押す所・横のはみ出し・帯の鉛筆と選んだ見方が画面の中か・「…」で切れた字・主な位置。
import os, asyncio
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
NAMES = ["A1-v2","A1x-v2","A1b-v2","A2-v2","A2e-v2","A3-v2","A3x-v2","A4-v2","Q1-v2","Q2-v2","P1-v2","P2-v2","C1-v2","V1-v2","V1b-v2","V3-v2","V1c-v2","V2-v2","index"]
FULL = {"A1b-v2","A2-v2","A2e-v2","A3-v2","A4-v2","Q1-v2","Q2-v2","P2-v2","C1-v2","V2-v2","index"}
S667 = ["A1-v2","A1x-v2","A1b-v2","A2-v2","A3-v2","A3x-v2","Q1-v2","P2-v2","V1-v2","V1b-v2","V1c-v2"]
CHECK = """() => {
  const small = [], tap = [], cut = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length || ['STYLE','SCRIPT','svg','path','circle','text'].includes(el.tagName)) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const cs = getComputedStyle(el);
    if (own && parseFloat(cs.fontSize) < 13 && el.closest('.shot') == null) small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12));
    if (own && cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 1) cut.push(el.textContent.trim().slice(0, 16));
  }
  for (const el of document.querySelectorAll('a, .go, .kind span, .chip, .pillbtn, .back, .ap, .search, .ic, .vs span, .vrow .pen, .tg, .tabbar span, .shh button, .bdtabs span')) {
    const r = el.getBoundingClientRect(); if (!r.height) continue;
    if (el.matches('.tg')) { if (r.height < 36) tap.push('tg'); continue; }
    if (el.matches('.kind span')) { if (r.height < 40) tap.push('kind'); continue; }
    if (el.matches('.bdtabs span')) { if (r.height < 38) tap.push('bdtabs'); continue; }
    if (r.height < 44 && !el.matches('.tabbar span')) tap.push(el.textContent.trim().slice(0, 10) + ':' + Math.round(r.height));
  }
  // 見方の帯：鉛筆と選んだ見方が画面の中か
  const band = [];
  for (const row of document.querySelectorAll('.vrow')) {
    const pen = row.querySelector('.pen').getBoundingClientRect(); const vs = row.querySelector('.vs').getBoundingClientRect();
    const on = row.querySelector('.vs .on');
    const r = on ? on.getBoundingClientRect() : null;
    band.push({pen: Math.round(pen.right), sel: r ? [Math.round(r.left), Math.round(r.right)] : null, ok: pen.right <= 390 && (!r || (r.left >= vs.left - 1 && r.right <= vs.right + 1)), top: Math.round(vs.top)});
  }
  const y = s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top) : null; };
  const yb = s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().bottom) : null; };
  const kinds = [...document.querySelectorAll('.trow, .kindrow')].map(e => Math.round(e.getBoundingClientRect().right));
  return { small: small.length, tap, cut, over: document.documentElement.scrollWidth > 390, band, rowRight: kinds,
           pos: { tabbar: y('.tabbar'), firstPred: yb('.rtl li.pr em'), mapCard: y('.hero ~ .card') } };
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
            print("844", n, await pg.evaluate(CHECK))
        await pg.set_viewport_size({"width": 390, "height": 667})
        for n in S667:
            await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(PNG, n + "-667.png"))
            print("667", n, await pg.evaluate(CHECK))
        await b.close()
asyncio.run(main())
