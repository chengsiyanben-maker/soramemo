# -*- coding: utf-8 -*-
# 画面案を 390×844（2倍）・375×667・夜（-n）・全体（-full）で PNG に撮り、
# 小さい字・小さいボタン・はみ出し・字の切れ・動きを減らす設定で動くものを数える
import os, json
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
PNG = os.path.join(OUT, 'png'); os.makedirs(PNG, exist_ok=True)
SCREENS = json.load(open(HERE + '/screens.json', encoding='utf-8'))
MEASURE = r'''() => {
  const r = {small:[], tap:[], over:[], cut:[]};
  const W = document.documentElement.clientWidth;
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('.under')) continue;
    const cs = getComputedStyle(el); if (cs.display==='none'||cs.visibility==='hidden'||el.closest('[hidden]')) continue;
    const b = el.getBoundingClientRect(); if (!b.width) continue;
    const own = [...el.childNodes].some(n => n.nodeType===3 && n.textContent.trim());
    if (own && parseFloat(cs.fontSize) < 12 && !el.closest('svg')) r.small.push(el.className+':'+el.textContent.trim().slice(0,12));
    if (el.matches('button') && (b.width < 44 || b.height < 40)) r.tap.push(el.className+':'+el.textContent.trim().slice(0,10)+' '+Math.round(b.width)+'x'+Math.round(b.height));
    if ((b.right > W + 0.5 || b.left < -0.5) && !el.closest('.chips') && !el.closest('svg')) r.over.push(el.tagName+'.'+el.className);
    if (own && el.scrollWidth > el.clientWidth + 1 && cs.overflow==='hidden' && !el.classList.contains('blk')) r.cut.push(el.textContent.trim().slice(0,12));
  }
  for (const c of document.querySelectorAll('.lr > span')) {
    if (c.closest('[hidden]')) continue;
    const b = c.getBoundingClientRect();
    for (const k of c.querySelectorAll('*')) { const kb = k.getBoundingClientRect(); if (kb.width && (kb.right > b.right + 1)) r.cut.push('列:'+k.textContent.trim().slice(0,10)); }
  }
  // 地図の字（SVG）は、実際の大きさで 12px 以上か
  for (const t of document.querySelectorAll('svg text')) { const h = t.getBoundingClientRect().height; if (h && h < 12) r.small.push('地図の字:'+t.textContent.slice(0,6)+' '+h.toFixed(1)); }
  if (document.documentElement.scrollWidth > W) r.over.push('page');
  return r;
}'''
res = {}; errs = []
with sync_playwright() as p:
    br = p.chromium.launch()
    def open_(name, w, h, q='', rm=False):
        ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, reduced_motion='reduce' if rm else 'no-preference')
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(name + ' ' + str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(name + ' ' + m.text))
        pg.goto('file://' + os.path.join(OUT, name + '.html') + q); pg.wait_for_timeout(150)
        return ctx, pg
    for name, title, desc in SCREENS:
        for w, h, suf, q in [(390, 844, '', ''), (375, 667, '-667', ''), (390, 844, '-n', '?n=1')]:
            ctx, pg = open_(name, w, h, q)
            pg.screenshot(path=os.path.join(PNG, name + suf + '.png'))
            res[name + suf] = pg.evaluate(MEASURE)
            if suf in ('', '-n') and not name.startswith(('s1', 'e2', 'e3')):
                pg.add_style_tag(content='.tabs{position:absolute!important;top:auto;bottom:14px}body{position:relative}')
                pg.screenshot(path=os.path.join(PNG, name + suf + '-full.png'), full_page=True)
            ctx.close()
        ctx, pg = open_(name, 390, 844, '', rm=True)
        pg.evaluate("[...document.querySelectorAll('[data-fold]')].slice(0,2).forEach(b=>b.click())")
        res[name + '-rm'] = {'running': pg.evaluate("document.getAnimations().length")}
        ctx.close()
    # 地図の日のピル：今日だけ・11月26日だけ
    ctx, pg = open_('m1-map', 390, 844)
    pg.click('[data-day=d26]'); pg.wait_for_timeout(80)
    pg.screenshot(path=os.path.join(PNG, 'm1-map-d26.png')); ctx.close()
    br.close()
json.dump({'measure': res, 'errors': errs}, open(HERE + '/measure.json', 'w'), ensure_ascii=False, indent=1)
tot = {k: sum(len(v.get(k, [])) for v in res.values()) for k in ['small', 'tap', 'over', 'cut']}
print('12px 未満', tot['small'], '／ 小さいボタン', tot['tap'], '／ はみ出し', tot['over'], '／ 切れ', tot['cut'], '／ エラー', len(errs), errs[:3])
print('動きを減らす設定で動くもの', sum(v['running'] for k, v in res.items() if k.endswith('-rm')))
for k, v in res.items():
    for kk in v:
        if isinstance(v[kk], list) and v[kk]: print(k, kk, v[kk][:6])
