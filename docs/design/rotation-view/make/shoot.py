# -*- coding: utf-8 -*-
# 画面案を 390×844（2倍）の PNG に撮り、字の大きさ・押す所・はみ出しを数える。長い画面は -full.png も撮る。
import asyncio, os, glob, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
FULL = {"A1", "A4", "B1", "C1"}
MEASURE = r"""() => {
  const small = [], tap = [], over = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && e.tagName !== 'text') { const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 12.95) small.push(e.textContent.trim().slice(0, 14) + ':' + fs); }
    if (e.matches('button, a, input')) { if (r.height < 43.5 || r.width < 43.5) tap.push(e.textContent.trim().slice(0, 12) + ':' + Math.round(r.height)); }
    if (r.right > 390.5 || r.left < -0.5) over.push((e.className || e.tagName) + ':' + Math.round(r.left) + '-' + Math.round(r.right));
    const c = e.closest('.card,.mini,.tl,.next,.after,.selc'); if (c && c !== e && !e.closest('.map')) { const q = c.getBoundingClientRect(); if (r.right > q.right + .5 && getComputedStyle(e).position !== 'absolute') over.push('カードの外:' + (e.className || e.tagName)); }
  }
  return { small, tap, over, docw: document.documentElement.scrollWidth };
}"""
async def main():
    os.makedirs(PNG, exist_ok=True); res = {}
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for f in sorted(glob.glob(os.path.join(OUT, "*.html"))):
            k = os.path.basename(f)[:-5]
            pg = await br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
            await pg.goto("file://" + f); await pg.wait_for_timeout(300)
            if k != "index":
                res[k] = await pg.evaluate(MEASURE)
                await pg.screenshot(path=os.path.join(PNG, k + ".png"))
                if k in FULL: await pg.screenshot(path=os.path.join(PNG, k + "-full.png"), full_page=True)
            await pg.close()
        # 一覧は PNG を作ってから撮る
        pg = await br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        await pg.goto("file://" + os.path.join(OUT, "index.html")); await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(PNG, "index.png"), full_page=True)
        await br.close()
    bad = 0
    for k, v in res.items():
        n = len(v["small"]) + len(v["tap"]) + len(v["over"]) + (v["docw"] > 390)
        bad += n; print(k, "13px未満", len(v["small"]), "44px未満", len(v["tap"]), "はみ出し", len(v["over"]), "幅", v["docw"], ("" if not n else json.dumps(v, ensure_ascii=False)[:400]))
    print("合計の問題", bad)
asyncio.run(main())
