import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の出資：申し込む・認める・引き上げは30日後から・格付け2
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
IV = "window.__co.invest = {flow:-30, taken:0.1, list:[{id:30, role:'in', partner:'ひこうき雲エア', amount:5000, pct:null, status:'offer'}, {id:29, role:'out', partner:'北の大地航空', amount:8000, pct:0.08, status:'active', daily:45, unlock:new Date(Date.now() + 5 * 864e5).toISOString()}]};"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + IV, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#coPartners')
        check('出資：受けている申し込み・出している出資（受け取り 45/日）:', 'ひこうき雲エア から出資' in t and '認め待ち' in t and '北の大地航空 に出資' in t and '受け取り 45/日' in t)
        check('30日たつまで引き上げられない:', await pg.is_disabled('[data-invwd="29"]'))
        await pg.click('[data-invok="30"]'); await pg.wait_for_timeout(400)
        check('認める（co3_inv_answer）:', await pg.evaluate('window.__invans.p_id === 30 && window.__invans.p_ok === true'))
        await pg.fill('#invCode', 'TSUBASA1'); await pg.fill('#invAmt', '12,000'); await pg.click('#invGo'); await pg.wait_for_timeout(400)
        check('申し込む（co3_inv_offer）:', await pg.evaluate('window.__invoff.p_code === "TSUBASA1" && window.__invoff.p_amount === 12000'))
        await pg.click('[data-invwd="31"]'); await pg.wait_for_timeout(400)
        check('申し込みを取り消す:', await pg.evaluate('window.__invwd.p_id === 31'))
        await c.close()
        c, pg = await open_page(b, V3 + IV + "window.__co.rating = 2;", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        check('格付け2：出資は出ない:', await pg.locator('#invGo').count() == 0)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
