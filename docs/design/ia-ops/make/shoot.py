# -*- coding: utf-8 -*-
# 画面案を 390（844 の高さ）と 375（667 の高さ）で PNG に撮り、小さい字・小さいボタン・はみ出しを数える
import os, json, glob
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
PNG = os.path.join(OUT, 'png'); os.makedirs(PNG, exist_ok=True)
MEASURE = r'''() => {
  const r = {small:[], tap:[], over:[]};
  const W = document.documentElement.clientWidth;
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el); if (cs.display==='none'||cs.visibility==='hidden') continue;
    const b = el.getBoundingClientRect(); if (!b.width) continue;
    const own = [...el.childNodes].some(n => n.nodeType===3 && n.textContent.trim());
    if (own && parseFloat(cs.fontSize) < 12 && !el.closest('svg')) r.small.push(el.className+':'+el.textContent.trim().slice(0,12));
    if (el.matches('button') && (b.width < 44 || b.height < 40)) r.tap.push(el.className+':'+el.textContent.trim().slice(0,10)+' '+Math.round(b.width)+'x'+Math.round(b.height));
    if (b.right > W + 0.5 || b.left < -0.5) r.over.push(el.tagName+'.'+el.className);
  }
  if (document.documentElement.scrollWidth > W) r.over.push('page');
  return r;
}'''
res = {}
with sync_playwright() as p:
    br = p.chromium.launch()
    for f in sorted(glob.glob(OUT + '/[abk]*.html')):
        name = os.path.basename(f)[:-5]
        for w, h, suf in [(390, 844, ''), (375, 667, '-667')]:
            pg = br.new_page(viewport={'width': w, 'height': h}, device_scale_factor=2)
            pg.goto('file://' + f); pg.wait_for_timeout(150)
            pg.screenshot(path=os.path.join(PNG, name + suf + '.png'))
            res[name + suf] = pg.evaluate(MEASURE)
            pg.close()
    br.close()
json.dump(res, open(HERE + '/measure.json', 'w'), ensure_ascii=False, indent=1)
tot = {k: sum(len(v[k]) for v in res.values()) for k in ['small', 'tap', 'over']}
print('12px 未満', tot['small'], '／ 小さいボタン', tot['tap'], '／ はみ出し', tot['over'])
for k, v in res.items():
    for kk in v:
        if v[kk]: print(k, kk, v[kk][:5])
