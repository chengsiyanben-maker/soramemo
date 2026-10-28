import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の天気の備えと台風の計画欠航：備えを建てる・横風の訓練・CAT III・計画欠航を決める
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
WX = "window.__co.wx = {prep:[{iata:'CTS', kind:'deice', level:1}], wind:'none', cat3_airports:['NRT'], typhoon:[{day:'2026-09-11', iata:'CTS', k:'5-6', cancel:null}]}; window.__co.fleet[0].cat3_cost = 800;"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + WX, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coV3')
        check('台風：9月11日 新千歳・まだ決めていない:', '台風が近づきそうです' in t and '9月11日' in t and 'まだ決めていない' in t)
        await pg.click('[data-typh="5-6"][data-v="1"]'); await pg.wait_for_timeout(400)
        check('計画欠航する（co3_typhoon_decide）:', await pg.evaluate('window.__typh.p_route === "5-6" && window.__typh.p_cancel === true') and '計画欠航にしました' in await pg.inner_text('#coMsg'))
        check('天気の備え：新千歳 防除氷1段:', '新千歳 ・ 防除氷の設備' in await pg.inner_text('#coV3') and await pg.locator('.lvb[aria-label="3段のうち1段"]').count() == 1)
        await pg.click('#wxOpen'); await pg.wait_for_timeout(200); await pg.click('[data-wxk=deice]'); await pg.click('[data-wxap=CTS]'); await pg.wait_for_timeout(200); await pg.click('#wxBuild'); await pg.wait_for_timeout(400)
        check('防除氷を上げる（co3_build_prep）:', await pg.evaluate('window.__prep.p_kind === "deice" && window.__prep.p_iata === "CTS" && CO.wx.prep[0].level === 2'))
        await pg.click('[data-wind=high]'); await pg.wait_for_timeout(400)
        check('横風の訓練：手厚い:', await pg.evaluate('window.__wind.p_level === "high"') and '−40%' in await pg.inner_text('#coV3'))
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        await pg.click('[data-cat3="1"]'); await pg.wait_for_timeout(400)
        check('CAT III を付ける:', await pg.evaluate('window.__cat3.p_aircraft === 1') and '付いています' in await pg.inner_text('#coFleet') and await pg.locator('[data-cat3]').count() == 0)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
