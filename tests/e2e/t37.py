import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(300)
        # 以前の形で保存された記録（1,500回分）
        await pg.evaluate("""() => { const ids = A.map(a => a.id), cs = [], fs = [], ms = []; let t = Date.parse('2024-10-01T08:00:00+09:00');
          for(let i=0;i<1500;i++){ const a = ids[(i*7) % 60], b = ids[(i*7+3) % 60]; t += 6*36e5; const ts = TERMS.filter(z => z.a === a);
            cs.push({a, t, acc:18.37, term: ts.length ? ts[i % ts.length].id : null}); if(i%2) fs.push({id:'a'+t, from:b, to:a, dep:t-2*36e5, arr:t, km:812.345678, airline: i%3 ? 'JL' : null, no: i%5 ? null : 'JL123'}); }
          ms.push({from:ids[0], to:ids[1], d:'2025-01-01', airline:'NH'}, {from:ids[2], to:ids[3], d:'2025-02-02', airline:null});
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:fs, manual:ms, demoClock:null})); window.__old = localStorage.getItem('soramemo.v1').length; }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        before = await pg.evaluate("JSON.stringify(achState().done.size) + '|' + S.flights.filter(f=>f.no).length + '|' + S.manual.length")
        await pg.evaluate("save()")
        sizes = await pg.evaluate("({ old: JSON.stringify(JSON.parse(localStorage.getItem('soramemo.v1'))).length })")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        after = await pg.evaluate("JSON.stringify(achState().done.size) + '|' + S.flights.filter(f=>f.no).length + '|' + S.manual.length")
        new_len = await pg.evaluate("localStorage.getItem('soramemo.v1').length")
        f0 = await pg.evaluate("JSON.stringify([S.checkins[0], S.flights[0], S.flights[4], S.manual[0], S.manual[1]])")
        print('achievements|flightNo|manual before:', before, 'after:', after)
        print('sample:', f0)
        print(errs)
        await b.close()
asyncio.run(main())
