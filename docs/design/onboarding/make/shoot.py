# -*- coding: utf-8 -*-
# 撮影と測定：390×844（2倍）・375×667（1倍）・夜（-n）。12px 未満の字・44px 未満の押す所・横のはみ出し・本文の切れ・エラー
import asyncio, os, json, glob
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE); PNG = D + '/png'
os.makedirs(PNG, exist_ok=True)
NIGHT = {'o1-intro', 'o3-visited', 'o6-home'}
SCROLL = {'o3-visited', 'o3b-zero', 'o4-plan', 'o4b-myap'}  # 本文を送れる画面（下に続くのはわざと）
M = r'''(() => { const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && !e.closest('[hidden]'); };
 const small = [], tiny = []; const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
 while (tw.nextNode()) { const n = tw.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement; if (!vis(e) || e.closest('svg')) continue; const f = parseFloat(getComputedStyle(e).fontSize); if (f < 12) small.push(f + ' ' + n.textContent.trim().slice(0, 10)); }
 document.querySelectorAll('button').forEach(e => { if (!vis(e)) return; const r = e.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return; if (r.height < 43.5 || r.width < 43.5) tiny.push(Math.round(r.width) + 'x' + Math.round(r.height) + ' ' + e.textContent.trim().slice(0, 10)); });
 const b = document.querySelector('.body'); return {small, tiny, cut: b ? b.scrollHeight - b.clientHeight : 0, h: document.documentElement.scrollWidth - innerWidth}; })()'''
async def main():
    rep = {}; err = []
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for f in sorted(glob.glob(D + '/*.html')):
            k = os.path.basename(f)[:-5]
            if k == 'index': continue
            vs = [('', '', 390, 844, 2), ('-667', '', 375, 667, 1)] + ([('-n', '?night=1', 390, 844, 2)] if k in NIGHT else [])
            for sfx, qs, w, h, dpr in vs:
                pg = await br.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                pg.on('pageerror', lambda e: err.append(str(e))); pg.on('console', lambda m: m.type == 'error' and err.append(m.text))
                await pg.goto('file://' + f + qs); await pg.wait_for_timeout(500)
                r = await pg.evaluate(M); r['scroll'] = k in SCROLL; rep[k + sfx] = r
                await pg.screenshot(path='%s/%s%s.png' % (PNG, k, sfx))
                if k in SCROLL and not sfx:
                    await pg.evaluate("document.querySelector('.body').scrollTop=9999"); await pg.wait_for_timeout(200)
                    await pg.screenshot(path='%s/%s-end.png' % (PNG, k))
                await pg.close()
        # 動き：選ぶと数字が増える（0 → 1）
        pg = await br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
        await pg.goto('file://' + D + '/o3b-zero.html'); await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('.chips .chip').click()"); await pg.wait_for_timeout(120)
        await pg.screenshot(path=PNG + '/o3b-zero-move1.png'); await pg.close()
        await br.close()
    rep['errors'] = err
    json.dump(rep, open(HERE + '/measure.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in rep.items():
        print(k, v if not isinstance(v, dict) else '12px未満 %d 44未満 %d 切れ %d%s はみ出し %d %s %s' % (len(v['small']), len(v['tiny']), v['cut'], '（送れる）' if v['scroll'] else '', v['h'], v['small'][:2], v['tiny'][:3]))
asyncio.run(main())
