# -*- coding: utf-8 -*-
# 画面案を PNG にする（390×844 は2倍・375×667 は1倍）。あわせて測る：12px 未満の字・44px 未満の押す所・横のはみ出し・字の切れ
import asyncio, os, glob, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
MEASURE = r"""() => { const r = {small:[], tap:[], over:[], clip:[]}; const W = innerWidth;
  for(const el of document.querySelectorAll('body *')){ const cs = getComputedStyle(el), b = el.getBoundingClientRect(); if(!b.width || cs.visibility === 'hidden') continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if(own && parseFloat(cs.fontSize) < 12) r.small.push(el.textContent.trim().slice(0, 20) + ' ' + cs.fontSize);
    if(el.tagName === 'BUTTON' && (b.width < 44 - .5 || b.height < 44 - .5)) r.tap.push(el.textContent.trim().slice(0, 12) + ' ' + Math.round(b.width) + 'x' + Math.round(b.height));
    if(b.right > W + .5 || b.left < -.5) r.over.push(el.className + ' ' + Math.round(b.left) + '-' + Math.round(b.right));
    if(own && el.scrollWidth > el.clientWidth + 1 && cs.overflow !== 'visible') r.clip.push(el.textContent.trim().slice(0, 20)); }
  return r; }"""
async def main():
    os.makedirs(ROOT + '/png', exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in sorted(glob.glob(ROOT + '/*.html')):
            n = os.path.basename(f)[:-5]
            if n == 'index': continue
            for w, h, s, dpr in ((390, 844, '', 2), (375, 667, '-667', 1)):
                pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                await pg.goto('file://' + f); await pg.wait_for_timeout(300)
                await pg.screenshot(path='%s/png/%s%s.png' % (ROOT, n, s))
                m = await pg.evaluate(MEASURE)
                bad = {k: v for k, v in m.items() if v}
                print(n, w, 'OK' if not bad else json.dumps(bad, ensure_ascii=False))
                await pg.close()
        await b.close()
asyncio.run(main())
