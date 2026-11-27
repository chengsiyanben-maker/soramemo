# -*- coding: utf-8 -*-
# 2版（*-v2.html）を 390×844 と 390×667（2倍）で撮り、字・押す所・はみ出しと、予想の1便目の上の端を測る。
import asyncio, os, glob, json, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
sys.path.insert(0, HERE)
MEASURE = open(os.path.join(HERE, "shoot.py"), encoding="utf-8").read().split('MEASURE = r"""')[1].split('"""')[0]
FIRST = r"""() => { const e = document.querySelector('.tl li.edge, .mini li.edge'); const p = document.querySelector('.tl li.p, .mini li.p');
  const r = x => x ? [Math.round(x.getBoundingClientRect().top), Math.round(x.getBoundingClientRect().bottom)] : null; return {edge: r(e), pred: r(p)}; }"""
async def main():
    res = {}
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for f in sorted(glob.glob(os.path.join(OUT, "*-v2.html"))):
            k = os.path.basename(f)[:-5]
            for h in (844, 667):
                pg = await br.new_page(viewport={"width": 390, "height": h}, device_scale_factor=2)
                await pg.goto("file://" + f); await pg.wait_for_timeout(300)
                if h == 844:
                    res[k] = await pg.evaluate(MEASURE); res[k]["first"] = await pg.evaluate(FIRST)
                    await pg.screenshot(path=os.path.join(PNG, k + ".png"))
                    if k in ("A1-v2", "A4-v2"): await pg.screenshot(path=os.path.join(PNG, k + "-full.png"), full_page=True)
                else:
                    await pg.screenshot(path=os.path.join(PNG, k + "-667.png"))
                await pg.close()
        pg = await br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        await pg.goto("file://" + os.path.join(OUT, "index.html")); await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(PNG, "index.png"), full_page=True); await br.close()
    bad = 0
    for k, v in res.items():
        n = len(v["small"]) + len(v["tap"]) + len(v["over"]) + (v["docw"] > 390); bad += n
        print(k, "13px未満", len(v["small"]), "44px未満", len(v["tap"]), "はみ出し", len(v["over"]), "幅", v["docw"], "境目/予想1便目", v["first"], ("" if not n else json.dumps(v, ensure_ascii=False)[:500]))
    print("合計の問題", bad)
asyncio.run(main())
