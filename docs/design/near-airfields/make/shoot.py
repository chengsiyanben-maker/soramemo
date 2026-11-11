# -*- coding: utf-8 -*-
# 使い方：python3 shoot.py <画面案のフォルダ> [ファイル名の型（例 *-v2）]
# 各 HTML を幅390・高さ844（と667）で PNG にし、字の大きさ・押す所・はみ出し・枠の中の切れを測る
import asyncio, sys, os, glob, json
from playwright.async_api import async_playwright
D = sys.argv[1]
JS = r"""() => {
 const out = {small:[], tap:[], over:0, clip:[]};
 const W = document.documentElement.clientWidth;
 if (document.documentElement.scrollWidth > W + 1) out.over = document.documentElement.scrollWidth - W;
 const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
 const seen = new Set();
 while (walker.nextNode()) {
  const t = walker.currentNode; if (!t.textContent.trim()) continue;
  const el = t.parentElement; if (seen.has(el)) continue; seen.add(el);
  if (el.closest('style,title')) continue;
  let fs = parseFloat(getComputedStyle(el).fontSize);
  const svg = el.closest('svg');
  if (svg) { const m = svg.getScreenCTM(); if (m) fs = fs * Math.abs(m.a); }
  const r = el.getBoundingClientRect(); if (r.width === 0) continue;
  if (el.closest('.shot,.ann')) continue;
  const unit = el.classList.contains('u') || el.closest('.u');
  if (fs < 11.95 || (fs < 12.95 && !unit)) out.small.push(el.textContent.trim().slice(0,20) + ':' + fs.toFixed(1));
 }
 document.querySelectorAll('.pill,.btn,.tabs b,.seg b,.sw,.nr,.vr,.zoom b,.done,.strip .up').forEach(e => {
  const r = e.getBoundingClientRect(); if (!r.width) return;
  const h = e.classList.contains('sw') ? 34 : 44;
  if (r.height < h - .5 || (r.width < 44 - .5)) out.tap.push((e.className + ' ' + e.textContent.trim().slice(0,10)) + ' ' + r.width.toFixed(0) + 'x' + r.height.toFixed(0));
 });
 document.querySelectorAll('.nr .n,.bpm .nm,.clipchk').forEach(e => { if (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1) out.clip.push(e.textContent.trim().slice(0,16)); });
 // タブ帯と重なる字（最初の画面）
 const tb = document.querySelector('.tabs'); out.under = 0;
 return out;
}"""
async def main():
    os.makedirs(D + '/png', exist_ok=True)
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f in sorted(glob.glob(D + '/' + (sys.argv[2] if len(sys.argv) > 2 else '*') + '.html')):
            n = os.path.basename(f)[:-5]
            if n == 'index': continue
            for h in (844, 667):
                pg = await b.new_page(viewport={'width': 390, 'height': h}, device_scale_factor=2 if h == 844 else 1)
                await pg.goto('file://' + f); await pg.wait_for_timeout(250)
                await pg.screenshot(path='%s/png/%s%s.png' % (D, n, '' if h == 844 else '-667'))
                if h == 844:
                    res[n] = await pg.evaluate(JS)
                await pg.close()
        await b.close()
    bad = 0
    for n, r in res.items():
        if r['small'] or r['tap'] or r['over'] or r['clip']:
            bad += 1; print(n, json.dumps(r, ensure_ascii=False))
    print('測った画面', len(res), '問題のある画面', bad)
asyncio.run(main())
