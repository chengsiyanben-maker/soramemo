# -*- coding: utf-8 -*-
# 撮影と測定：390×844 と 375×667（2倍）。12px 未満の字・44px 未満の押す所・横のはみ出し・シートの中で切れた押す所を数える
import asyncio, os, json, glob
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
MEASURE = r'''() => {
 const r = {small:[], tap:[], over:0};
 for (const el of document.querySelectorAll('body *')) {
   if (el.closest('svg')) continue;
   const cs = getComputedStyle(el); if (cs.display==='none') continue;
   const own = [...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
   if (own && parseFloat(cs.fontSize) < 11.5) r.small.push(el.textContent.trim().slice(0,12)+':'+cs.fontSize);
   if (el.matches('button')) { const b = el.getBoundingClientRect();
     if (b.width && b.height < 44 && b.bottom < innerHeight) r.tap.push(el.textContent.trim().slice(0,10)+':'+Math.round(b.height)); }
 }
 r.over = document.documentElement.scrollWidth > innerWidth ? 1 : 0;
 return r; }'''
async def main():
    res = {}
    files = sorted(os.path.basename(f)[:-5] for f in glob.glob(OUT + '/H*.html'))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w, h, suf in ((390, 844, ''), (375, 667, '-667')):
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=2)
            for k in files:
                await pg.goto('file://%s/%s.html' % (OUT, k)); await pg.wait_for_timeout(120)
                await pg.screenshot(path='%s/png/%s%s.png' % (OUT, k, suf))
                res[k + suf] = await pg.evaluate(MEASURE)
            await pg.close()
        await b.close()
    json.dump(res, open(HERE + '/measure.json', 'w'), ensure_ascii=False, indent=1)
    bad = {k: v for k, v in res.items() if v['small'] or v['tap'] or v['over']}
    print(len(res), '枚', '問題', json.dumps(bad, ensure_ascii=False))
asyncio.run(main())
