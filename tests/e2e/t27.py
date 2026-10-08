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
          localStorage.setItem('soramemo.company', JSON.stringify({name:'テスト航空', cash:500000, last:Date.now(), levels:{}, roles:{}, fleet:[], fac:{}})); }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500); await pg.evaluate('goTab("co")')
        st = lambda: pg.evaluate("JSON.stringify({pts:coRepPoints(), stars:coStars(), daily:coDaily(), cash:CO.cash, fac:CO.fac})")
        print('start:', await st())
        hnd = await pg.evaluate("A.find(a=>a.iata==='HND').id"); cts = await pg.evaluate("A.find(a=>a.iata==='CTS').id")
        await pg.evaluate('goTab("co")')
        await pg.select_option('#facPick', str(hnd)); await pg.click('[data-build=new]'); print('build HND:', await st(), await pg.inner_text('#coMsg'))
        await pg.evaluate('goTab("co")')
        await pg.select_option('#facPick', str(cts)); print('CTS button:', await pg.inner_text('[data-build=new]'), await pg.is_disabled('[data-build=new]'))
        await pg.evaluate('goTab("co")')
        await pg.click(f'[data-build="{hnd}"]'); print('HND->2:', await st())
        await pg.evaluate('goTab("co")')
        await pg.select_option('#facPick', str(cts)); await pg.click('[data-build=new]'); print('build CTS:', await st())
        await pg.evaluate('goTab("co")')
        await pg.click(f'[data-build="{hnd}"]'); print('HND->3:', await st())
        await pg.evaluate('goTab("co")')
        print('rate:', await pg.inner_text('#coRate'))
        await pg.evaluate('goTab("co")')
        await pg.locator('#coRep').scroll_into_view_if_needed(); await pg.evaluate('window.scrollBy(0,250)'); await pg.screenshot(path=os.path.join(WORK,'rep.png'))
        print(errs); await b.close()
asyncio.run(main())
