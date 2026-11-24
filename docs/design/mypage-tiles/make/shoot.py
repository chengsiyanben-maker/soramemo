# -*- coding: utf-8 -*-
# 各 HTML を 390×844（2倍）・375×667・390 の全体で PNG にし、足した所の字の大きさ・押す所・はみ出し・切れ・色の濃さを測る
import asyncio, os, glob, json
from playwright.async_api import async_playwright
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = r"""() => {
 const out = {small:[], tap:[], over:0, clip:[], low:[]};
 const W = document.documentElement.clientWidth;
 if (document.documentElement.scrollWidth > W + 1) out.over = document.documentElement.scrollWidth - W;
 const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055, 2.4); }; return .2126*f(m[0])+.7152*f(m[1])+.0722*f(m[2]); };
 const bgOf = el => { while (el) { const b = getComputedStyle(el).backgroundColor; if (b && !/rgba\(0, 0, 0, 0\)|transparent/.test(b)) return b; el = el.parentElement; } return 'rgb(255,255,255)'; };
 const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); const seen = new Set();
 while (walker.nextNode()) {
  const el = walker.currentNode.parentElement; if (!walker.currentNode.textContent.trim() || seen.has(el)) continue; seen.add(el);
  if (!el.closest('.mt-grid,.mt-sec,.mt-h,.mt-note')) continue;
  const r = el.getBoundingClientRect(); if (!r.width) continue;
  const fs = parseFloat(getComputedStyle(el).fontSize);
  if (fs < 11.95) out.small.push(el.textContent.trim().slice(0,16) + ':' + fs);
  const a = lum(getComputedStyle(el).color), b = lum(bgOf(el)); const cr = (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  if (cr < 4.5 && !el.closest('.mt-pend')) out.low.push(el.textContent.trim().slice(0,14) + ':' + cr.toFixed(2));
 }
 document.querySelectorAll('.mt,.mt-mini button,.mt-menu button,.mt-sec .btn2,.mt-sec .seg button,.mt-sec .swatch,.mp-back').forEach(e => {
  const r = e.getBoundingClientRect(); if (!r.width) return;
  if (r.height < 43.5 || r.width < 43.5) out.tap.push(e.textContent.trim().slice(0,10) + ' ' + r.width.toFixed(0) + 'x' + r.height.toFixed(0));
 });
 document.querySelectorAll('.mt,.mt .s,.mt-menu .t,.mt-mini button').forEach(e => { if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 3) out.clip.push(e.textContent.trim().slice(0,16)); });
 return out;
}"""
async def main():
    os.makedirs(D + '/png', exist_ok=True); res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in sorted(glob.glob(D + '/[AB]*.html')):
            n = os.path.basename(f)[:-5]
            for w, h, s, dpr in ((390, 844, '', 2), (375, 667, '-667', 1)):
                pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                await pg.goto('file://' + f); await pg.wait_for_timeout(300)
                await pg.screenshot(path='%s/png/%s%s.png' % (D, n, s))
                res[n + s] = await pg.evaluate(JS)
                if not s:
                    await pg.screenshot(path='%s/png/%s-full.png' % (D, n), full_page=True)
                await pg.close()
        await b.close()
    for n, r in res.items():
        print(n, json.dumps(r, ensure_ascii=False))
asyncio.run(main())
