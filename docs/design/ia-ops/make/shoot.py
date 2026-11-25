# -*- coding: utf-8 -*-
# 撮影と測定：390×844 と 375×667（2倍）。12px 未満の字・44px 未満の押す所・横のはみ出しを数える
import asyncio, os, json, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE); from build import SCREENS
MEASURE = r'''() => {
 const r = {small:[], tap:[], over:0};
 for (const el of document.querySelectorAll('body *')) {
   const cs = getComputedStyle(el); if (cs.display==='none'||cs.visibility==='hidden') continue;
   const own = [...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
   if (own && parseFloat(cs.fontSize) < 11.5) r.small.push(el.textContent.trim().slice(0,12)+':'+cs.fontSize);
   if (el.matches('button,a,.chip,.dir span')) { const b = el.getBoundingClientRect();
     if (b.width && (b.height < 44 && !el.matches('.dir span') || el.matches('.dir span') && b.height < 38)) r.tap.push(el.textContent.trim().slice(0,10)+':'+Math.round(b.height)); }
 }
 r.over = document.documentElement.scrollWidth > innerWidth ? 1 : 0;
 return r; }'''
async def main():
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w, h, suf in ((390, 844, ''), (375, 667, '-667')):
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=2)
            for k in SCREENS:
                await pg.goto('file://%s/%s.html' % (OUT, k)); await pg.wait_for_timeout(150)
                await pg.screenshot(path='%s/png/%s%s.png' % (OUT, k, suf))
                if suf == '' and k in ('A1', 'B1', 'A2', 'C1', 'C2', 'C4'):
                    await pg.screenshot(path='%s/png/%s-full.png' % (OUT, k), full_page=True)
                res['%s%s' % (k, suf)] = await pg.evaluate(MEASURE)
            await pg.close()
        await b.close()
    json.dump(res, open(HERE + '/measure.json', 'w'), ensure_ascii=False, indent=1)
    for k, v in res.items():
        print(k, '小さい字', len(v['small']), v['small'][:3], '押す所', len(v['tap']), v['tap'][:3], 'はみ出し', v['over'])
asyncio.run(main())
