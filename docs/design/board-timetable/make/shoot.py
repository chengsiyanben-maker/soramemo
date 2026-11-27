# -*- coding: utf-8 -*-
# 画面案を 390×844（2倍）・375×667・夜（-n）・全体（-full）で PNG に撮り、
# 小さい字・小さいボタン・はみ出し・字の切れ・動きを減らす設定で動くものを数える。パタパタは途中のコマを横に並べて m-*.png に
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
    const cs = getComputedStyle(el); if (cs.display==='none'||cs.visibility==='hidden') continue;
    const b = el.getBoundingClientRect(); if (!b.width) continue;
    const own = [...el.childNodes].some(n => n.nodeType===3 && n.textContent.trim());
    if (own && parseFloat(cs.fontSize) < 12 && !el.closest('svg')) r.small.push(el.className+':'+el.textContent.trim().slice(0,12));
    if (el.matches('button') && (b.width < 44 || b.height < 40)) r.tap.push(el.className+':'+el.textContent.trim().slice(0,10)+' '+Math.round(b.width)+'x'+Math.round(b.height));
    if (b.right > W + 0.5 || b.left < -0.5) r.over.push(el.tagName+'.'+el.className);
    if (own && el.scrollWidth > el.clientWidth + 1 && cs.overflow==='hidden') r.cut.push(el.textContent.trim().slice(0,12));
  }
  // 列のセルからのはみ出し（行の中で隣の列に食い込む字）
  for (const c of document.querySelectorAll('.r > span')) {
    const b = c.getBoundingClientRect();
    for (const k of c.querySelectorAll('*')) { const kb = k.getBoundingClientRect(); if (kb.width && (kb.right > b.right + 1)) r.cut.push('列:'+k.textContent.trim().slice(0,10)); }
  }
  if (document.documentElement.scrollWidth > W) r.over.push('page');
  return r;
}'''
res = {}
errs = []
with sync_playwright() as p:
    br = p.chromium.launch()
    def open_(name, w, h, q='', rm=False):
        ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, reduced_motion='reduce' if rm else 'no-preference')
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(name + ' ' + str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(name + ' ' + m.text))
        pg.goto('file://' + os.path.join(OUT, name + '.html') + q); pg.wait_for_timeout(120)
        return ctx, pg
    for name, title, kind, plan, desc in SCREENS:
        # 今日の便の一覧が見える所まで少し送った位置（実際に開いたときは上から）
        for w, h, suf, q in [(390, 844, '', ''), (375, 667, '-667', ''), (390, 844, '-n', '?n=1')]:
            ctx, pg = open_(name, w, h, q)
            pg.screenshot(path=os.path.join(PNG, name + suf + '.png'))
            res[name + suf] = pg.evaluate(MEASURE)
            if suf == '':
                pg.evaluate("document.querySelector('.bd').scrollIntoView({block:'start'}); window.scrollBy(0,-12)")
                pg.screenshot(path=os.path.join(PNG, name + '-list.png'))
                pg.screenshot(path=os.path.join(PNG, name + '-full.png'), full_page=True)
            if suf == '-667':
                pg.evaluate("document.querySelector('.bd').scrollIntoView({block:'start'}); window.scrollBy(0,-12)")
                pg.screenshot(path=os.path.join(PNG, name + '-667-list.png'))
            ctx.close()
        # 動きを減らす設定：状況を変えても動くものが 0 か
        ctx, pg = open_(name, 390, 844, '', rm=True)
        pg.evaluate("Object.values(__demo).slice(0,3).forEach(a=>a.forEach(x=>setState.apply(null,x)))")
        res[name + '-rm'] = {'running': pg.evaluate("document.getAnimations().length")}
        ctx.close()
        # パタパタのコマ：0／0.12／0.24／0.6 秒を撮って横に並べる
        ctx, pg = open_(name, 390, 844)
        rid = __import__('json').loads(pg.evaluate("JSON.stringify(__demo.chg[0][0])"))
        pg.evaluate("document.getElementById(%r).scrollIntoView({block:'center'})" % rid)
        shots = []
        for i, t in enumerate([0, 0.12, 0.24, 0.8]):
            if t:
                pg.evaluate("setState.apply(null, __demo.chg[0]); __frame(%s)" % t)
            el = pg.query_selector('#' + rid)
            f = os.path.join(PNG, '_f%d.png' % i); el.screenshot(path=f); shots.append(f)
            if t: pg.evaluate("setState.apply(null, __demo.back[0]); document.querySelectorAll('.fch').forEach(s=>s.className='fch')")
        ctx.close()
        from PIL import Image
        ims = [Image.open(f) for f in shots]
        W = max(i.width for i in ims); H = sum(i.height for i in ims) + 16 * (len(ims) - 1)
        bg = (238, 241, 245) if plan == 'b' else (14, 30, 54)
        canvas = Image.new('RGB', (W, H), bg); y = 0
        for im in ims:
            canvas.paste(im, (0, y)); y += im.height + 16
        canvas.save(os.path.join(PNG, 'm-' + name + '.png'))
        for f in shots: os.remove(f)
    br.close()
json.dump({'measure': res, 'errors': errs}, open(HERE + '/measure.json', 'w'), ensure_ascii=False, indent=1)
tot = {k: sum(len(v.get(k, [])) for v in res.values()) for k in ['small', 'tap', 'over', 'cut']}
print('12px 未満', tot['small'], '／ 小さいボタン', tot['tap'], '／ はみ出し', tot['over'], '／ 切れ', tot['cut'], '／ エラー', len(errs))
print('動きを減らす設定で動くもの', {k: v['running'] for k, v in res.items() if k.endswith('-rm')})
for k, v in res.items():
    for kk in v:
        if isinstance(v[kk], list) and v[kk]: print(k, kk, v[kk][:6])
