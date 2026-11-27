# -*- coding: utf-8 -*-
# 撮影と測定：各ページを 390 幅（2倍）と 375 幅（1倍）で全体を撮る。夜（-n）は T2・T3・T5。
# 測るもの：12px 未満の字（T3 の「今」の見本は除く）・44px 未満の押す所・横のはみ出し・コンソールのエラー
import asyncio, os, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE); PNG = D + '/png'
os.makedirs(PNG, exist_ok=True); URL = 'file://' + D + '/'
S = json.load(open(HERE + '/screens.json', encoding='utf-8'))
NIGHT = {'t2-surface', 't3-type', 't5-carrier'}
MEASURE = r'''(() => {
  const small = [], tiny = [], over = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (tw.nextNode()) { const n = tw.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement;
    const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 12 && !e.closest('.tb')) small.push(fs + 'px ' + n.textContent.trim().slice(0, 12)); }
  document.querySelectorAll('button,a').forEach(e => { const r = e.getBoundingClientRect(); if (r.height < 43.5 || r.width < 43.5) tiny.push(Math.round(r.width) + 'x' + Math.round(r.height)); });
  document.querySelectorAll('body *').forEach(e => { if (e.getBoundingClientRect().right > innerWidth + 0.5) over.push(e.className + ':' + e.textContent.trim().slice(0, 10)); });
  return {small, tiny, over: over.slice(0, 5), hscroll: document.documentElement.scrollWidth - innerWidth};
})()'''
async def main():
    rep = {}; errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, title, kind in S:
            k = name[:-5]
            vs = [('', '', 390, 844, 2), ('-375', '', 375, 667, 1)]
            if k in NIGHT: vs.append(('-n', '?night=1', 390, 844, 2))
            for sfx, qs, w, h, dpr in vs:
                pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                pg.on('console', lambda m: m.type == 'error' and errors.append(m.text)); pg.on('pageerror', lambda e: errors.append(str(e)))
                await pg.goto(URL + name + qs); await pg.wait_for_timeout(300)
                rep[k + sfx] = await pg.evaluate(MEASURE)
                await pg.screenshot(path='%s/%s%s.png' % (PNG, k, sfx), full_page=True); await pg.close()
        await b.close()
    rep['errors'] = errors
    json.dump(rep, open(HERE + '/measure.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in rep.items():
        if isinstance(v, dict):
            bad = len(v['small']) + len(v['tiny']) + len(v['over']) + (v['hscroll'] > 0)
            print(k, 'OK' if not bad else (v['small'][:3], v['tiny'][:3], v['over'][:3], v['hscroll']))
        else: print(k, v)
asyncio.run(main())
