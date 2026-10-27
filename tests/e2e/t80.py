import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の乗員・整備士と地上の仕事：要る人・いる人・足りないと運休・雇う・減らす・地上の仕事・格付け2
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
EXTRA = """window.__co.people = {need:8, crew:6, mech:3, crew_hired:3, mech_hired:0, ground:'outsource', cost:60, crew_ratio:0.75, mech_mult:2.67};"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + EXTRA, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coV3')
        check('要る人8・乗員6・整備士3:', '乗員と整備士' in t and '6機分いる（雇った 3）・使う割合 133%' in t)
        check('乗員が足りない：75%まで飛ぶ・整備士：故障2.7倍:', '便は 75% まで飛び' in t and '故障が 2.7倍' in t)
        await pg.click('[data-hire=crew][data-d="1"]'); await pg.wait_for_timeout(400)
        check('乗員を1機分雇う（co3_hire）:', await pg.evaluate('window.__hire.p_kind === "crew" && window.__hire.p_delta === 1') and '乗員を1機分雇いました' in await pg.inner_text('#coMsg') and await pg.evaluate('CO.cash') == 100000 - 2000)
        check('整備士は雇っていないので減らせない:', await pg.is_disabled('[data-hire=mech][data-d="-1"]'))
        check('拠点がないと自社にできない:', await pg.is_disabled('[data-ground=self]') and '拠点を決めると自社にできます' in await pg.inner_text('#coV3'))
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA + "window.__co.home = 5;", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        await pg.click('[data-ground=self]'); await pg.wait_for_timeout(400)
        check('地上の仕事を自社（co3_set_ground）:', await pg.evaluate('window.__ground.p_mode === "self"') and '3%安く' in await pg.inner_text('#coV3'))
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA + "window.__co.rating = 2;", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coV3')
        check('格付け2：雇えない・不足は起きない:', '人の不足は起きません' in t and await pg.locator('[data-hire]').count() == 0)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
