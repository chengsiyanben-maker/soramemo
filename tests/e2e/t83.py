import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の臨時便：繁忙期に予備機へ組む・やめる・繁忙期でなければ出ない・格付け2
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });"
V3 = """window.__co = {name:'そらメモ航空', cash:100000, last:new Date().toISOString(), roles:{}, daily:300, gross:300, upkeep:0, bonus:0,
  routes:[{k:'5-6', a:'HND', b:'CTS', km:820, base:344, level:1, cost:10320, mult:.5, hub:1, sky:1, min_size:4.5, sa:6, sb:4.5, ac_id:1, intl:false}],
  fleet:[{id:1, type:'lg', reg:'JA01XJ', icao:'A359', kind:'pax', route:'5-6', paid:40000, age:1, value:40000, sell:12000, upkeep:80, bought_at:new Date().toISOString()}],
  sky:{}, total_km:820, rep_points:0, stars:1, facilities:{}, bought:1, value:100000, friend_code:'ABCD1234', hide_rank:false, friends:0,
  v3:true, rating:5, rating_have:{routes:40, intl:5, fleet:35, stars:5, days:99}, policy:'fsc', premium:20, satisfaction:41.2, sat_mult:0.97, sat_parts:{base:50, meal:-8, bag:0, target:37}, meal:'none', bag:'free', home:null, home_since:null, plans:{}, legs:{'5-6':[{n:1,t:390,ta:490,f:'HND',to:'CTS',seats:369,biz:300,lei:30},{n:2,t:570,ta:670,f:'CTS',to:'HND',seats:369,biz:120,lei:160},{n:3,t:750,ta:850,f:'HND',to:'CTS',seats:369,biz:60,lei:140}]}, fares:{'5-6':{level:0, set_on:null, others:[-1, 0]}},
  econ:[{k:'5-6', kind:'big', real:52.4, demand:18500, n:3, own:1200, flights:12, seats:3888, carried:3110, revenue:2300, cost:1420, landing:84, congestion:35, profit:761, p_seats:466, p_pax:420, e_pax:2690}]};"""
async def open_page(b, extra, errs):
    c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script(INIT + extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    return c, pg
SP = "window.__co.fleet.push({id:2, type:'lg', reg:'JA02ZZ', icao:'A359', kind:'pax', route:null, paid:40000, age:1, value:40000, sell:12000, upkeep:80, bought_at:new Date().toISOString()});"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + SP + "window.__co.extra = {peak_end:'2027-01-04', list:[]};", errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('予備機に「臨時便を組む（01/04まで）」:', await pg.locator('[data-xgo="2"]').count() == 1 and '臨時便を組む（01/04まで）' in await pg.inner_text('#coFleet') and await pg.locator('[data-xgo="1"]').count() == 0)
        await pg.select_option('[data-xf="2"]', '6'); await pg.click('[data-xgo="2"]'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coFleet')
        check('臨時便を組む（co3_set_extra）:', await pg.evaluate('window.__extra.p_aircraft === 2 && window.__extra.p_route === "5-6" && window.__extra.p_flights === 6') and '臨時便：羽田 ⇄ 新千歳 1日6便・客 420人・もうけ +58（01/04まで）' in t)
        await pg.click('[data-xstop="9"]'); await pg.wait_for_timeout(400)
        check('やめる（co3_stop_extra）:', await pg.evaluate('window.__xstop.p_id === 9') and await pg.locator('[data-xgo="2"]').count() == 1)
        await c.close()
        c, pg = await open_page(b, V3 + SP + "window.__co.extra = {peak_end:null, list:[]};", errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('繁忙期でなければ出ない:', await pg.locator('[data-xgo]').count() == 0)
        await c.close()
        c, pg = await open_page(b, V3 + SP + "window.__co.extra = {peak_end:'2027-01-04', list:[]}; window.__co.rating = 2;", errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('格付け2：組めない:', await pg.locator('[data-xgo]').count() == 0 and '格付け3から組めます' in await pg.inner_text('#coFleet'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
