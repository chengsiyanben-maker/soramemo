import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
        # 本番記録に直接データを作る：沖縄の全空港に10回ずつ、北海道の全空港に1回、新千歳だけ100回
        await pg.evaluate("""() => {
          const ok = A.filter(a => a.pref === '沖縄県'), hk = A.filter(a => a.pref === '北海道');
          const cs = []; let t = Date.parse('2026-01-01');
          for(let r=0;r<10;r++) for(const a of ok) cs.push({a:a.id, t:(t+=36e5), acc:20, term:null});
          for(const a of hk) cs.push({a:a.id, t:(t+=36e5), acc:20, term:null});
          const cts = A.find(a=>a.iata==='CTS'); for(let i=0;i<99;i++) cs.push({a:cts.id, t:(t+=36e5), acc:20, term:null});
          localStorage.setItem('soramemo.v1', JSON.stringify({checkins:cs, flights:[], manual:[]}));
        }""")
        await pg.wait_for_timeout(400); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        st = await pg.evaluate("(() => { const s = achState(); return {n:ACH.length, done:[...s.done.keys()].filter(k=>/^(lap|rg)/.test(k)), okinawa10: s.value(ACH.find(x=>x.id==='rg10_沖縄')), hk10: s.value(ACH.find(x=>x.id==='rg10_北海道')), all10: s.value(ACH.find(x=>x.id==='lapall10'))}; })()")
        print(json.dumps(st, ensure_ascii=False))
        await pg.evaluate("goTab('ach')"); await pg.wait_for_timeout(200)
        print('prog:', await pg.inner_text('#achProg'))
        h = await pg.locator('h3:has-text("地方制覇 10周")').bounding_box(); await pg.evaluate(f"window.scrollTo(0,{h['y']-70})"); await pg.wait_for_timeout(150)
        await pg.screenshot(path=os.path.join(WORK,'lap.png')); print(errs); await b.close()
asyncio.run(main())
