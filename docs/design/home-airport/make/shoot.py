# -*- coding: utf-8 -*-
# 撮影と測定：各画面を 390×844（2倍）・375×667（1倍）・夜（-n）・タブ4つ（-ta）で撮る。
# 測るもの：12px 未満の字・44px 未満の押す所・横のはみ出し・シートの中で切れたカード・コンソールのエラー
import asyncio, os, json, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE); PNG = D + '/png'
os.makedirs(PNG, exist_ok=True); URL = 'file://' + D + '/'
S = json.load(open(HERE + '/screens.json', encoding='utf-8'))
NIGHT = {'n1-futsu', 'b1-stub', 'b3-done', 'a1-pill'}
TABA = {'n1-futsu', 'b1-stub'}
MEASURE = r'''(() => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };
  const small = [], tiny = [], cut = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (tw.nextNode()) { const n = tw.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement; if (!vis(e) || e.closest('svg')) continue;
    const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 12) small.push(fs + 'px ' + n.textContent.trim().slice(0, 12)); }
  const sh = document.querySelector('.sheet'); const sb = sh ? sh.getBoundingClientRect().bottom : innerHeight; const tb = document.querySelector('.tabs').getBoundingClientRect().top;
  document.querySelectorAll('button,a,[role=slider]').forEach(e => { if (!vis(e)) return; const r = e.getBoundingClientRect(); if (r.top > tb && !e.closest('.tabs')) return;
    if (r.height < 44 - 0.5 || r.width < 44 - 0.5) tiny.push(Math.round(r.width) + 'x' + Math.round(r.height) + ' ' + (e.textContent.trim() || e.getAttribute('aria-label') || e.className).slice(0, 14)); });
  document.querySelectorAll('.sheet .in > *').forEach(e => { const r = e.getBoundingClientRect(); if (r.top < tb && r.bottom > tb) cut.push((e.className + ' ' + e.textContent.trim()).slice(0, 18)); });
  const over = []; document.querySelectorAll('.sheet *').forEach(e => { if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'hidden' && e.clientWidth > 0 && !e.closest('svg')) over.push(e.className + ':' + e.textContent.trim().slice(0, 10)); });
  return {small, tiny, cut, over: over.slice(0, 5), hscroll: document.documentElement.scrollWidth - innerWidth};
})()'''
async def main():
    only = sys.argv[1:]
    rep = {}; errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, title in S:
            k = name[:-5]
            if only and k not in only: continue
            vs = [('', '', 390, 844, 2), ('-667', '', 375, 667, 1)]
            if k in NIGHT: vs.append(('-n', '?night=1', 390, 844, 2))
            if k in TABA: vs.append(('-ta', '?tabs=a', 390, 844, 2))
            for sfx, qs, w, h, dpr in vs:
                pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                pg.on('console', lambda m: m.type == 'error' and errors.append(m.text)); pg.on('pageerror', lambda e: errors.append(str(e)))
                await pg.goto(URL + name + qs); await pg.wait_for_timeout(500)
                rep[k + sfx] = await pg.evaluate(MEASURE)
                await pg.screenshot(path='%s/%s%s.png' % (PNG, k, sfx)); await pg.close()
        # 動き：案A は押したあと、案B は引いた途中と切れたあと
        for name, js, waits in (('a1-pill', "document.querySelector('.ckpill').click()", (150, 600)),
                                ('b1-stub', "__pull(.5)", (300,)),
                                ):
            if only and name not in only: continue
            pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
            await pg.goto(URL + name + '.html'); await pg.wait_for_timeout(500); await pg.evaluate(js)
            for i, wt in enumerate(waits):
                await pg.wait_for_timeout(wt if i == 0 else wt - waits[i - 1]); await pg.screenshot(path='%s/%s-move%d.png' % (PNG, name, i + 1))
            await pg.close()
        await b.close()
    rep['errors'] = errors
    old = json.load(open(HERE + '/measure.json')) if only and os.path.exists(HERE + '/measure.json') else {}
    old.update(rep); json.dump(old, open(HERE + '/measure.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in rep.items():
        if isinstance(v, dict): print(k, '12px未満', len(v['small']), '44未満', len(v['tiny']), '切れ', len(v['cut']), 'はみ出し', len(v['over']), v['hscroll'], v['small'][:2], v['tiny'][:3], v['cut'][:2], v['over'][:2])
        else: print(k, v)
asyncio.run(main())
