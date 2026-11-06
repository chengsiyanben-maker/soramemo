import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営：日付の表示が端末の時間帯に左右されないこと（台風の日付・発着枠の申し込みの締め切り）
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
  econ:[{k:'5-6', kind:'big', real:52.4, demand:18500, n:3, own:1200, flights:12, seats:324, carried:3110, revenue:2300, cost:1420, landing:84, congestion:35, profit:761, p_seats:466, p_pax:420, e_pax:2690}]};"""
WX = "window.__co.wx = {prep:[], wind:'none', cat3_airports:[], typhoon:[{day:'2026-09-11', iata:'CTS', src:'jma', k:'5-6', cancel:null}]};"
EXTRA = """window.__co.slots = {month:'2026-10-01', next:'2026-11-01', decided:true, auto:true, list:[
  {iata:'HND', pool:'main', use:12, granted:9, applied:12, cong:1.35, apply:null}, {iata:'HND', pool:'regional', use:0, granted:null, applied:null, cong:1.35, apply:null},
  {iata:'NRT', pool:'main', use:0, granted:null, applied:null, cong:0.4, apply:null}, {iata:'KIX', pool:'main', use:0, granted:null, applied:null, cong:null, apply:null},
  {iata:'ITM', pool:'main', use:6, granted:6, applied:6, cong:0.9, apply:null}, {iata:'FUK', pool:'main', use:0, granted:null, applied:null, cong:null, apply:null}]};"""
async def open_page(b, tz, extra, errs):
    c = await b.new_context(viewport={'width':400,'height':860}, timezone_id=tz); await c.add_init_script(INIT + extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    return c, pg
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        for tz in ['Asia/Tokyo', 'UTC', 'America/Los_Angeles', 'Pacific/Kiritimati']:
            c, pg = await open_page(b, tz, V3 + WX + EXTRA + "window.__co.slots.next = '2026-03-01';", errs)
            await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
            check(f'{tz}：台風は9月11日:', '9月11日' in await pg.inner_text('#coV3'))
            await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
            await pg.evaluate("goTab('routes')"); await pg.wait_for_timeout(150)
            await pg.click('[data-rtab=slots]'); await pg.wait_for_timeout(300)
            await pg.evaluate("goTab('routes')"); await pg.wait_for_timeout(150)
            check(f'{tz}：3月の申し込みは2月28日まで:', '3月の申し込み（2月28日まで）' in await pg.inner_text('#coRoutes'))
            await c.close()
        await b.close()
        print('errors', errs + fails)
asyncio.run(main())
