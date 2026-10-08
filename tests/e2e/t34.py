import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
PTS=[('関西T1',34.4343,135.2442),('関西T1の端(600m)',34.4343,135.2508),('関西T2',34.4379,135.2318),('中部T1',34.8598,136.8160),('中部T2',34.8533,136.8158),
     ('新千歳 国内',42.7877,141.6808),('新千歳 国際',42.7862,141.6763),('福岡 国内',33.5973,130.4481),('福岡 国際',33.5848,130.4443),('福岡 滑走路の中ほど',33.5900,130.4500)]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
        for name,la,lo in PTS:
            r = await pg.evaluate(f"(()=>{{const n=nearest({{lat:{la},lon:{lo}}}); return n.within ? placeName(n.a,n.term) : '範囲外'}})()"); print(f'{name}: {r}')
        print('ACH total:', await pg.evaluate('ACH.length'), '| visit:', await pg.evaluate('ACH.filter(x=>x.cat==="同じ空港").length'), '| term:', await pg.evaluate('JSON.stringify(ACH.filter(x=>x.cat==="ターミナル").map(x=>x.id+":"+x.name+"/"+x.target))'))
        # 羽田に25回、関西T1/T2、新千歳国内→国際
        await pg.evaluate("""() => { const id=i=>A.find(a=>a.iata===i).id, cs=[]; let t=Date.parse('2026-01-01T12:00:00+09:00');
          for(let i=0;i<25;i++) cs.push({a:id('HND'),t:(t+=864e5),acc:20,term:'HND-T'+(1+i%3)});
          cs.push({a:id('KIX'),t:(t+=864e5),acc:20,term:'KIX-T1'}); cs.push({a:id('KIX'),t:(t+=36e5),acc:20,term:'KIX-T2'});
          cs.push({a:id('CTS'),t:(t+=864e5),acc:20,term:'CTS-D'});
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:[], manual:[]})); }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        print('done:', await pg.evaluate('JSON.stringify([...achState().done.keys()].filter(k=>/^v|^t/.test(k)))'))
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(200)
        await pg.locator('.vreg >> nth=0').scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(WORK,'vach.png'))
        await pg.click('[data-title="v1_5"]'); await pg.wait_for_timeout(100); print('title:', await pg.evaluate('titleName()'))
        await pg.click('nav.tabs button[data-v=book]'); await pg.click('#v-book [data-seg=main]'); await pg.wait_for_timeout(200)
        print('term headers:', await pg.locator('#book h3:has-text("ターミナル")').all_inner_texts())
        print(errs); await b.close()
asyncio.run(main())
