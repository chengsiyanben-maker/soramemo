# -*- coding: utf-8 -*-
# 今のアプリを測る：main の web/ を http://localhost:8765/ で開き（cd web && python3 -m http.server 8765）、デモに入って
# 下のタブを順に開き、見えている要素の字の大きさ・字の色・カードの地・角丸・影・枠を数える（昼と夜）。結果は survey.json
import asyncio, os, json
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
JS = r'''(() => {
 const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05; };
 const fs = {}, col = {}, rad = {}, sh = {}, bd = {}, cardbg = {}, num = {tab:0, prop:0}, pagebg = getComputedStyle(document.body).backgroundColor;
 const add = (o, k) => o[k] = (o[k] || 0) + 1;
 const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
 while (tw.nextNode()) { const n = tw.currentNode; const t = n.textContent.trim(); if (!t) continue; const e = n.parentElement; if (!vis(e) || e.closest('svg,.leaflet-container')) continue;
   const s = getComputedStyle(e); add(fs, s.fontSize); add(col, s.color);
   if (/\d/.test(t)) { if (s.fontVariantNumeric.includes('tabular')) num.tab++; else num.prop++; } }
 document.querySelectorAll('body *').forEach(e => { if (!vis(e) || e.closest('svg,.leaflet-container')) return; const s = getComputedStyle(e); const r = e.getBoundingClientRect();
   if (s.boxShadow !== 'none') { add(sh, s.boxShadow); if (r.width > 200 && r.height > 50) { add(cardbg, s.backgroundColor); add(rad, s.borderTopLeftRadius); } }
   if (s.borderTopStyle === 'solid' && parseFloat(s.borderTopWidth) >= 1) add(bd, s.borderTopWidth + ' ' + s.borderTopColor); });
 return {pagebg, fs, col, rad, sh, bd, cardbg, num};
})()'''
async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for night in (False, True):
            pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
            if night: await pg.add_init_script("try{localStorage.setItem('soramemo.night','on')}catch(e){}")
            await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2500)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('gateDemo')&&document.getElementById('gateDemo').click()")
            await pg.wait_for_timeout(3500); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
            if night: await pg.evaluate("document.documentElement.setAttribute('data-night','on')")
            tabs = await pg.evaluate("[...document.querySelectorAll('nav button, .tabs button, [role=tab]')].filter(e=>e.offsetParent).map((e,i)=>(e.textContent||'').trim().slice(0,8))")
            print('tabs', tabs)
            res = {'home': await pg.evaluate(JS)}
            await pg.screenshot(path=HERE + '/now-home%s.png' % ('-n' if night else ''))
            n = await pg.evaluate("[...document.querySelectorAll('nav.tabs button')].filter(e=>e.offsetParent).length")
            for i in range(n):
                name = await pg.evaluate("(i=>{const b=[...document.querySelectorAll('nav.tabs button')].filter(e=>e.offsetParent)[i]; if(!b) return null; b.click(); return (b.textContent||b.getAttribute('aria-label')||'').trim().slice(0,8)})(%d)" % i)
                await pg.wait_for_timeout(1500); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
                if name is None: continue
                res['tab%d %s' % (i, name)] = await pg.evaluate(JS)
                await pg.screenshot(path=HERE + '/now-tab%d%s.png' % (i, '-n' if night else ''))
            out['night' if night else 'day'] = res; await pg.close()
        await b.close()
    json.dump(out, open(HERE + '/survey.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
asyncio.run(main())
