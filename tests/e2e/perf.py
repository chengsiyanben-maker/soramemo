import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, sys
from playwright.async_api import async_playwright
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_timeout(400)
        await pg.evaluate(f"""() => {{ const ids = A.map(a => a.id), cs = [], fs = []; let t = Date.parse('2024-10-01T08:00:00+09:00');
          for(let i=0;i<{N};i++){{ const a = ids[(i*7) % 40], b = ids[(i*7+3) % 40]; t += 6*36e5;
            cs.push({{a, t, acc:20, term:null}}); if(i%2) fs.push({{id:'a'+t, from:b, to:a, dep:t-2*36e5, arr:t, km:800, airline: i%3 ? 'JL' : 'NH', no:null}}); }}
          localStorage.setItem('soramemo.v1', JSON.stringify({{checkins:cs, flights:fs, manual:[]}})); }}""")
        await pg.reload(); await pg.wait_for_timeout(1500)
        print("loaded", await pg.evaluate("S.checkins.length"), await pg.evaluate("S.flights.length"))
        r = await pg.evaluate("""() => { const T = f => { const s = performance.now(); f(); return Math.round(performance.now() - s); };
          const parts = {}; for(const fn of ['renderMap','renderAirlines','renderAch','renderYears','renderYearPlus','renderCompany','renderQueue','renderPlusSettings','visited','routes','visitedTerms']){ const orig = window[fn]; if(!orig) continue; window[fn] = function(){ const s = performance.now(); const r = orig.apply(this, arguments); parts[fn] = (parts[fn] || 0) + performance.now() - s; return r; }; }
          const total = T(render); for(const k in parts) parts[k] = Math.round(parts[k]);
          return { render: total, parts, achState: T(achState), renderAch: T(renderAch), renderCompany: T(renderCompany), renderYears: T(() => { renderYears(); renderYearPlus(); }), book: T(() => {}) }; }""")
        print(f'{N} check-ins:', r, errs)
        await b.close()
asyncio.run(main())
