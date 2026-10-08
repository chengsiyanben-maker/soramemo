import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { const id = i => A.find(a => a.iata === i).id, t0 = Date.now() - 864e5;
          const cs = ['HND','CTS','OKA','ISG'].map((i,k) => ({a:id(i), t:t0 + k*36e5, acc:20, term:null}));
          const fs = [{id:'a1', from:id('HND'), to:id('CTS'), dep:t0, arr:t0+36e5, km:819.6, airline:null, no:null},{id:'a2', from:id('OKA'), to:id('ISG'), dep:t0+2*36e5, arr:t0+3*36e5, km:395.4, airline:null, no:null}];
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:fs, manual:[]}));
          localStorage.setItem('soramemo.company', JSON.stringify({name:'テスト航空', cash:200000, last:Date.now(), levels:{}, roles:{}, fleet:[], fac:{}})); }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500); await pg.evaluate('goTab("co")')
        st = lambda: pg.evaluate("JSON.stringify({cash:CO.cash, pts:coRepPoints(), stars:coStars(), costs:coRoutes().map(r=>r.k+':'+ECON.upCost(r.base,r.lv)), fleet:CO.fleet.length})")
        await pg.evaluate('goTab("co")')
        print('state:', await st()); print('cash label:', await pg.inner_text('.cash'))
        await pg.evaluate('goTab("fleet")')
        await pg.click('[data-up="5-6"]'); print('upgrade:', await st())
        for i in range(3):
            await pg.evaluate('goTab("fleet")')
            print(f' prop price #{i+1}:', await pg.inner_text('#coCatalog .ac >> nth=0')); await pg.click('[data-buy=prop]'); print('  ->', await st())
        await pg.evaluate('goTab("co")')
        hnd = await pg.evaluate("A.find(a=>a.iata==='HND').id"); await pg.select_option('#facPick', str(hnd)); await pg.click('[data-build=new]'); print('build:', await st())
        await pg.evaluate('goTab("co")')
        print('rate:', await pg.inner_text('#coRate'), '| collect:', await pg.inner_text('#coCollect'))
        print(errs); await b.close()
asyncio.run(main())
