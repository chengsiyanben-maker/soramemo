import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate("""() => {
          const id = i => A.find(a => a.iata === i).id, cs = [], fs = [];
          const at = (y,m,d,h,mi=0) => new Date(y,m-1,d,h,mi).getTime();
          const ci = (i,t,term=null) => cs.push({a:id(i), t, acc:20, term});
          const fl = (f,to,dep,arr,al=null) => fs.push({id:'a'+arr, from:id(f), to:id(to), dep, arr, km:0, airline:al, no:null});
          // 2025年: 毎月羽田→新千歳（朝・夜まじえて）＝12か月連続、四季、往復
          for(let m=1;m<=12;m++){ ci('HND', at(2025,m,10,6,10), 'HND-T1'); ci('CTS', at(2025,m,10,8,0)); fl('HND','CTS',at(2025,m,10,6,10),at(2025,m,10,8,0),'JL'); ci('CTS', at(2025,m,12,22,30)); ci('HND', at(2025,m,13,0,10), 'HND-T2'); fl('CTS','HND',at(2025,m,12,22,30),at(2025,m,13,0,10),'NH'); }
          // 2026/1/1 元日、同じ日に 新千歳→那覇→石垣→与那国 （南北縦断・1日4空港）
          ci('CTS', at(2026,1,1,7,0)); ci('OKA', at(2026,1,1,11,0)); ci('ISG', at(2026,1,1,14,0)); ci('OGN', at(2026,1,1,16,0)); ci('WKJ', at(2026,1,3,12,0)); ci('SHB', at(2026,1,4,12,0));
          const km = (a,b) => { const R=6371,r=Math.PI/180,A1=A.find(x=>x.id===a),B1=A.find(x=>x.id===b); const dl=(B1.lat-A1.lat)*r, dn=(B1.lon-A1.lon)*r; const h=Math.sin(dl/2)**2+Math.cos(A1.lat*r)*Math.cos(B1.lat*r)*Math.sin(dn/2)**2; return 2*R*Math.asin(Math.sqrt(h)); };
          fs.forEach(f => f.km = km(f.from, f.to));
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:fs, manual:[]}));
        }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(700)
        r = await pg.evaluate("""(() => { const s = achState(); const ids = ['morn1','morn10','night1','night10','ny','season1','st3','st6','st12','st24','yr10','yrkm','day3','day5','rt_1','ends','ns','both','rep20','thnd'];
           return {done: ids.filter(i => s.done.has(i)), not: ids.filter(i => !s.done.has(i)), cur: s.curStreak, best: s.bestStreak, ends: s.value(ACH.find(x=>x.id==='ends'))}; })()""")
        print(json.dumps(r, ensure_ascii=False))
        print('streak line:', await pg.inner_text('#streak'))
        await pg.evaluate("goTab('ach')"); await pg.click('[data-title="ns"]'); await pg.wait_for_timeout(150)
        await pg.click('nav.tabs button[data-v=home]'); print('title:', await pg.inner_text('#titlePill'))
        await pg.screenshot(path=os.path.join(WORK,'y_home.png'))
        await pg.click('nav.tabs button[data-v=book]'); await pg.click('#v-book [data-seg=main]'); await pg.wait_for_timeout(200); await pg.screenshot(path=os.path.join(WORK,'y_book.png'))
        await pg.click('#book .cell.got >> nth=0'); await pg.wait_for_timeout(200); print('detail:', (await pg.inner_text('#dStampBody')).replace('\n',' ')); await pg.screenshot(path=os.path.join(WORK,'y_detail.png')); await pg.keyboard.press('Escape')
        await pg.click('nav.tabs button[data-v=stats]'); await pg.wait_for_timeout(200)
        print('year:', (await pg.inner_text('#yrBody')).replace('\n',' '))
        await pg.click('[data-year="2025"]'); print('2025:', (await pg.inner_text('#yrBody')).replace('\n',' '))
        h = await pg.locator('h2:has-text("年ごとの記録")').bounding_box(); await pg.evaluate(f"window.scrollTo(0,{h['y']-70})"); await pg.screenshot(path=os.path.join(WORK,'y_year.png'))
        print(errs); await b.close()
asyncio.run(main())
