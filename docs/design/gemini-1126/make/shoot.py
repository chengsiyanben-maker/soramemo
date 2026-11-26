# -*- coding: utf-8 -*-
# 撮影と測定：各画面を 390×844（2倍）・375×667（1倍）、夜（-n）は G1・G2・F2・R1。表のページ（doc）は全体を撮る。
# 測るもの：12px 未満の字・44px 未満の押す所・横のはみ出し・下のタブに隠れたカード・コンソールのエラー
import asyncio, os, json, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE); PNG = D + '/png'
os.makedirs(PNG, exist_ok=True); URL = 'file://' + D + '/'
S = json.load(open(HERE + '/screens.json', encoding='utf-8'))
NIGHT = {'g1-boarding', 'g2-arrive', 'g2c-after', 'g3-same', 'f2-form', 'r1-repeat', 'c2-outdoor'}
MEASURE = r'''(() => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };
  const small = [], tiny = [], cut = [], over = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (tw.nextNode()) { const n = tw.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement; if (!vis(e) || e.closest('svg')) continue;
    const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 12) small.push(fs + 'px ' + n.textContent.trim().slice(0, 12)); }
  const tabs = document.querySelector('.tabs'); const tb = tabs ? tabs.getBoundingClientRect().top : 1e9;
  const dlg = document.querySelector('.dlg,.stdlg');
  document.querySelectorAll('button,a,[role=slider],textarea').forEach(e => { if (!vis(e)) return; if (dlg && !dlg.contains(e) && !e.closest('.tabs')) return; const r = e.getBoundingClientRect(); if (r.top > tb && !e.closest('.tabs')) return; if (r.top > innerHeight) return;
    if (r.height < 44 - 0.5 || r.width < 44 - 0.5) tiny.push(Math.round(r.width) + 'x' + Math.round(r.height) + ' ' + (e.textContent.trim() || e.getAttribute('aria-label') || e.className).slice(0, 14)); });
  if (!dlg) document.querySelectorAll('.sheet .in > :not(.more), .pg > *').forEach(e => { const r = e.getBoundingClientRect(); if (r.top < tb && r.bottom > tb + 2) cut.push((e.className + ' ' + e.textContent.trim()).slice(0, 18)); });
  if (dlg) { const r = dlg.getBoundingClientRect(); if (r.bottom > innerHeight + 1 || r.top < -1) cut.push('ダイアログが画面の外 ' + Math.round(r.top) + '〜' + Math.round(r.bottom)); }
  document.querySelectorAll('body *').forEach(e => { if (e.closest('svg') || e.closest('.views')) return; if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'hidden' && e.clientWidth > 0 && getComputedStyle(e).display !== 'inline') over.push(e.className + ':' + e.textContent.trim().slice(0, 10)); });
  return {small, tiny, cut, over: over.slice(0, 5), hscroll: document.documentElement.scrollWidth - innerWidth};
})()'''
async def main():
    only = sys.argv[1:]
    rep = {}; errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, title, kind in S:
            k = name[:-5]
            if only and k not in only: continue
            vs = [('', '', 390, 844, 2), ('-667', '', 375, 667, 1)]
            if k in NIGHT: vs.append(('-n', '?night=1', 390, 844, 2))
            for sfx, qs, w, h, dpr in vs:
                if kind == 'doc' and sfx == '-667': continue
                pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                pg.on('console', lambda m: m.type == 'error' and errors.append(m.text)); pg.on('pageerror', lambda e: errors.append(str(e)))
                await pg.goto(URL + name + qs); await pg.wait_for_timeout(400)
                rep[k + sfx] = await pg.evaluate(MEASURE)
                await pg.screenshot(path='%s/%s%s.png' % (PNG, k, sfx), full_page=(kind == 'doc')); await pg.close()
        await b.close()
    rep['errors'] = errors
    old = json.load(open(HERE + '/measure.json')) if only and os.path.exists(HERE + '/measure.json') else {}
    old.update(rep); json.dump(old, open(HERE + '/measure.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in rep.items():
        if isinstance(v, dict):
            bad = len(v['small']) + len(v['tiny']) + len(v['cut']) + len(v['over']) + (v['hscroll'] > 0)
            print(k, 'OK' if not bad else ('12px未満', v['small'][:2], '44未満', v['tiny'][:3], '切れ', v['cut'][:2], 'はみ出し', v['over'][:2], v['hscroll']))
        else: print(k, v)
asyncio.run(main())
