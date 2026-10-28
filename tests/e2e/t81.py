import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 のラウンジ・マイル・安全への投資・借金：建てる・段を選ぶ・出来事・借りる・返す・格付け2
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
EXTRA = """window.__co.money3 = {lounges:[{iata:'HND', level:1}], miles:0, miles_since:null, miles_eff:0, safety:'normal', debt:0, debt_room:60000, debt_next:null,
  rates:{drink:0.8, maint:0.65}, events:[{day:'2026-10-20', kind:'drink', until:'2026-10-22', type:null}]};
window.__co.sat_parts = Object.assign({}, window.__co.sat_parts, {lounge:2, miles:0});"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + EXTRA, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coV3')
        check('ラウンジ：羽田1段・出来事・起きやすさ:', 'ラウンジ・マイル・安全・借金' in t and await pg.locator('.lvb[aria-label="3段のうち1段"]').count() == 1 and '10/20 乗員の飲酒問題' in t and '約0.8' in t)
        await pg.select_option('#lgAp', 'HND'); await pg.click('#lgBuild'); await pg.wait_for_timeout(400)
        check('ラウンジを上げる（co3_build_lounge）:', await pg.evaluate('window.__lounge.p_iata === "HND" && CO.money3.lounges[0].level === 2') and 'ラウンジを建てました' in await pg.inner_text('#coMsg'))
        await pg.click('[data-miles="2"]'); await pg.wait_for_timeout(400)
        check('マイル2段（co3_set_miles）:', await pg.evaluate('window.__miles.p_level === 2') and '費用は収益の 4%' in await pg.inner_text('#coV3'))
        await pg.click('[data-safety=high]'); await pg.wait_for_timeout(400)
        check('安全：手厚い（co3_set_safety）:', await pg.evaluate('window.__safety.p_level === "high"') and '0.4倍' in await pg.inner_text('#coV3'))
        check('残りがあれば借りられる:', not await pg.is_disabled('[data-borrow="50000"]'))
        await pg.click('[data-borrow="50000"]'); await pg.wait_for_timeout(400)
        check('借りる（co3_borrow）:', await pg.evaluate('window.__borrow.p_amount === 50000 && CO.money3.debt === 50000') and await pg.locator('[data-borrow^="-"]').count() == 1)
        check('残りが足りないと借りられない:', await pg.is_disabled('[data-borrow="50000"]'))
        await pg.click('[data-borrow^="-"]'); await pg.wait_for_timeout(400)
        check('返す:', await pg.evaluate('window.__borrow.p_amount === -50000 && CO.money3.debt === 0'))
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA + "window.__co.rating = 2;", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        check('格付け2：使えない:', await pg.locator('[data-borrow],[data-miles],#lgBuild').count() == 0 and '格付け3' in await pg.inner_text('#coV3'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
