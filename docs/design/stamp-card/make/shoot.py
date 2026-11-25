# -*- coding: utf-8 -*-
# 撮影と測定：docs/design/stamp-card を http://localhost:8766/ で開き、390×844（2倍）・夜・375×667 を撮る。
# 動きは ?t= で止めて撮り、横に並べる（m-*.png）。12px 未満の字・44 未満の押す所・横のはみ出し・エラー・動きを減らすで動くものを数える
import asyncio, os, json, subprocess, sys, time
from playwright.async_api import async_playwright
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PNG = ROOT + '/png'
SCREENS = ['b1-first', 'b2-memo', 'b3-repeat', 'b4a-mark-on', 'b4b-mark-off', 'b5-offline', 'a1-first', 'a3-repeat', 'b6-share']
FRAMES = {'b1-first': [0, .2, .45, .75, .95, 1.4], 'a1-first': [0, .2, .45, .75, .95, 1.4], 'b2-memo': [.15, .3, .5, .8, 1.0, 1.5]}
MEASURE = r'''(()=>{
  const out = {small:[], tap:[], over:false, cut:[]};
  const W = document.documentElement.clientWidth;
  out.over = document.documentElement.scrollWidth > W + 1;
  for(const el of document.querySelectorAll('body *')){
    const cs = getComputedStyle(el); if(cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect(); if(!r.width || !r.height) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if(own && parseFloat(cs.fontSize) < 12 && !el.closest('svg')) out.small.push(el.textContent.trim().slice(0, 20) + ' ' + cs.fontSize);
    if(el.matches('button, a, [role=button]') && (r.width < 44 || r.height < 44)) out.tap.push((el.textContent.trim() || el.getAttribute('aria-label') || el.className).slice(0, 20) + ' ' + Math.round(r.width) + '×' + Math.round(r.height));
    if(own && el.scrollWidth > el.clientWidth + 1 && cs.overflow !== 'visible') out.cut.push(el.textContent.trim().slice(0, 20));
  }
  const sc = document.querySelector('.sc'); if(sc){ out.scroll = sc.scrollHeight > sc.clientHeight + 1; const r = sc.getBoundingClientRect(); out.cardTop = Math.round(r.top); }
  return out;
})()'''

async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8766'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    res = {}
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            for name in SCREENS:
                for tag, vw, vh, q in (('', 390, 844, ''), ('-n', 390, 844, 'n=1'), ('-667', 375, 667, '')):
                    pg = await b.new_page(viewport={'width': vw, 'height': vh}, device_scale_factor=2)
                    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
                    await pg.goto('http://localhost:8766/%s.html?t=9&%s' % (name, q)); await pg.wait_for_timeout(500)
                    await pg.screenshot(path='%s/%s%s.png' % (PNG, name, tag))
                    m = await pg.evaluate(MEASURE); m['err'] = errs; res[name + tag] = m
                    # 動きを減らす：再生しても動くものがないか
                    if tag == '':
                        await pg.goto('http://localhost:8766/%s.html?rm=1' % name); await pg.wait_for_timeout(300)
                        res[name + tag]['rm_moving'] = await pg.evaluate("document.getAnimations().filter(a=>a.playState==='running').length")
                    await pg.close()
            # 動きのコマ
            for name, ts in FRAMES.items():
                for tag, q in (('', ''), ('-n', 'n=1')):
                    ims = []
                    pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
                    for t in ts:
                        await pg.goto('http://localhost:8766/%s.html?t=%s&%s' % (name, t, q)); await pg.wait_for_timeout(250)
                        f = '%s/_f.png' % PNG; await pg.screenshot(path=f); ims.append(Image.open(f).copy())
                    await pg.close()
                    W = Image.new('RGB', (390 * len(ims) + 12 * (len(ims) - 1), 844), (255, 255, 255) if not tag else (15, 20, 27))
                    for i, im in enumerate(ims): W.paste(im, (i * 402, 0))
                    W.save('%s/m-%s%s.png' % (PNG, name, tag)); os.remove('%s/_f.png' % PNG)
            # 一覧ページ（全体）
            for tag, vw, q in (('', 820, ''), ('-390', 390, ''), ('-n', 820, 'n=1')):
                pg = await b.new_page(viewport={'width': vw, 'height': 900}, device_scale_factor=1)
                await pg.goto('http://localhost:8766/index.html?%s' % q); await pg.wait_for_timeout(500)
                await pg.evaluate("document.querySelectorAll('iframe').forEach(f=>{f.loading='eager'; f.src=f.dataset.src+'?t=9&n=%s'})" % ('1' if q else '0'))
                await pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); await pg.wait_for_timeout(2500); await pg.evaluate("window.scrollTo(0,0)")
                await pg.screenshot(path='%s/index%s-full.png' % (PNG, tag), full_page=True)
                res['index' + tag] = await pg.evaluate(MEASURE)
                await pg.close()
            await b.close()
    finally:
        srv.terminate()
    json.dump(res, open(HERE + '/measure.json', 'w'), ensure_ascii=False, indent=1)
    tot = lambda k: sum(len(v.get(k, [])) for v in res.values())
    print('12px 未満', tot('small'), '／44 未満', tot('tap'), '／切れ', tot('cut'), '／はみ出し', sum(1 for v in res.values() if v.get('over')),
          '／エラー', tot('err'), '／動きを減らすで動く', sum(v.get('rm_moving', 0) for v in res.values()), '／カードがスクロール', [k for k, v in res.items() if v.get('scroll')])
    for k, v in res.items():
        bad = {x: v[x] for x in ('small', 'tap', 'cut', 'err') if v.get(x)}
        if bad: print(k, bad)
    print({k: v.get('cardTop') for k, v in res.items() if 'cardTop' in v})
asyncio.run(main())
