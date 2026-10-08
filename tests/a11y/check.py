# 誰でも使えるかの点検（アクセシビリティ、WCAG 2.1 AA）。全タブ・印の画面・設定を、明るい・暗いの両方で調べる
#   python3 tests/a11y/check.py [shu|beni|ai]   ← 配色
import asyncio, json, sys
from playwright.async_api import async_playwright
import os
HERE = os.path.dirname(os.path.abspath(__file__))
# axe-core を用意する： cd tests/a11y && npm install axe-core@4
AXE = open(os.path.join(HERE, 'node_modules', 'axe-core', 'axe.min.js')).read()
URL = 'file://' + os.path.abspath(os.path.join(HERE, '..', '..', 'web', 'index.html'))
PAL = sys.argv[1] if len(sys.argv) > 1 else 'shu'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); allv = {}
        for scheme in ['light','dark']:
            c=await b.new_context(viewport={'width':400,'height':860}, color_scheme=scheme, bypass_csp=True); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.palette','" + PAL + "')")
            pg=await c.new_page(); await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(800)
            await pg.click('#openSettings'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(200)
            cts = await pg.evaluate("'a:'+A.find(a=>a.iata=='CTS').id")
            for v in ['t:HND-T1', cts]:
                await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(600)
                if v == cts:
                    await pg.wait_for_timeout(1500)
                    await pg.add_script_tag(content=AXE); r = await pg.evaluate("axe.run(document.querySelector('dialog[open]'), {runOnly:['wcag2a','wcag2aa']})"); allv[(scheme,'stamp-dialog')] = r['violations']
                await pg.click('#dStamp [data-close]')
            async def scan(name):
                await pg.add_script_tag(content=AXE)
                r = await pg.evaluate("axe.run(document, {runOnly:['wcag2a','wcag2aa','best-practice'], rules:{region:{enabled:false}}})")
                allv[(scheme,name)] = r['violations']
            for v in ['home','book','log','stats']: await pg.evaluate(f"goTab('{v}')"); await pg.wait_for_timeout(200); await scan(v)
            for s in ['extra','ach']: await pg.evaluate(f"goTab('book','{s}')"); await pg.wait_for_timeout(200); await scan('book-'+s)
            await pg.click('[data-mode=game]')
            for v in ['co','fleet','gods']: await pg.evaluate(f"goTab('{v}')"); await pg.wait_for_timeout(200); await scan(v)
            await pg.click('[data-mode=rally]'); await pg.click('#openSettings'); await pg.wait_for_timeout(200)
            await pg.add_script_tag(content=AXE); r = await pg.evaluate("axe.run(document.querySelector('dialog[open]'), {runOnly:['wcag2a','wcag2aa']})"); allv[(scheme,'settings')] = r['violations']
            await c.close()
        pairs = {}
        for (scheme, view), vs in allv.items():
            for v in vs:
                if v['id'] != 'color-contrast': continue
                for n in v['nodes']:
                    d = (n.get('any') or [{}])[0].get('data') or {}
                    k = (scheme, d.get('fgColor'), d.get('bgColor'), d.get('contrastRatio'), d.get('expectedContrastRatio'))
                    pairs.setdefault(k, set()).add(n['target'][0][:40] if n['target'] else '')
        for k, t in sorted(pairs.items(), key=lambda x: (x[0][0], -len(x[1]))): print('PAIR', k, len(t), sorted(t)[:4])
        summary = {}
        for (scheme, view), vs in allv.items():
            for v in vs:
                k = v['id']; s = summary.setdefault(k, {'impact':v['impact'], 'help':v['help'], 'where':set(), 'n':0, 'samples':[]})
                s['where'].add(f'{scheme}:{view}'); s['n'] += len(v['nodes'])
                for n in v['nodes'][:2]:
                    if len(s['samples']) < 4: s['samples'].append((n['target'][0] if n['target'] else '', (n.get('failureSummary') or '').replace('\n',' ')[:160]))
        for k, s in sorted(summary.items(), key=lambda x: -x[1]['n']):
            print(f"[{s['impact']}] {k} ×{s['n']}  {s['help']}\n   画面: {', '.join(sorted(s['where']))[:200]}")
            for t, f in s['samples']: print('   -', t[:80], '|', f)
        print('合計の違反の種類:', len(summary))
        await b.close()
asyncio.run(main())
