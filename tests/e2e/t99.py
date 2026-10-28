import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の発着枠（毎月の申し込み）：路線と発着枠のタブ・使えている枠・来月の申し込み・おまかせの切り替え・格付け2
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
EXTRA = """window.__co.slots = {month:'2026-10-01', next:'2026-11-01', decided:true, auto:true, list:[
  {iata:'HND', pool:'main', use:12, granted:9, applied:12, cong:1.35, apply:null}, {iata:'HND', pool:'regional', use:0, granted:null, applied:null, cong:1.35, apply:null},
  {iata:'NRT', pool:'main', use:0, granted:null, applied:null, cong:0.4, apply:null}, {iata:'KIX', pool:'main', use:0, granted:null, applied:null, cong:null, apply:null},
  {iata:'ITM', pool:'main', use:6, granted:6, applied:6, cong:0.9, apply:null}, {iata:'FUK', pool:'main', use:0, granted:null, applied:null, cong:null, apply:null}]};"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + EXTRA, errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('路線と発着枠のタブ:', await pg.locator('[data-rtab=slots]').count() == 1)
        await pg.click('[data-rtab=slots]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coRoutes')
        check('10月に使えている枠：羽田 9 / 申し込み 12便（75%）:', '10月に使えている枠' in t and '/ 申し込み 12便（75%）' in t and '約1.35倍' in t and '3便ぶんが運休中' in t and '混雑料金 7%' in t)
        check('伊丹は申し込みどおり:', '申し込みどおり使えます' in t)
        check('11月の申し込み（10月31日まで）・おまかせのあいだはボタンが押せない:', '11月の申し込み（10月31日まで）' in t and await pg.is_disabled('[data-slot="HND:main"][data-v="14"]'))
        await pg.click('#slotAuto'); await pg.wait_for_timeout(400)
        check('自分で申し込む（co3_set_slot_auto）:', await pg.evaluate('window.__slotAuto.p_on === false') and not await pg.is_disabled('[data-slot="HND:main"][data-v="14"]'))
        await pg.click('[data-slot="HND:main"][data-v="14"]'); await pg.wait_for_timeout(400)
        check('羽田に14便を申し込む（co3_slot_apply）:', await pg.evaluate('window.__slotApply.p_iata === "HND" && window.__slotApply.p_flights === 14') and '申し込みずみ' in await pg.inner_text('#coRoutes') and '1日14便を申し込みました' in await pg.inner_text('#coMsg'))
        check('地方の枠の行:', '羽田（地方の枠）' in await pg.inner_text('#coRoutes'))
        await pg.click('[data-rtab=routes]'); await pg.wait_for_timeout(300)
        check('路線のタブに戻る:', '羽田 ⇄ 新千歳' in await pg.inner_text('#coRoutes'))
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA + "window.__co.rating = 2;", errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        await pg.click('[data-rtab=slots]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coRoutes')
        check('格付け2：おまかせだけ:', '格付け3' in t and await pg.locator('#slotAuto').count() == 0 and await pg.is_disabled('[data-slot="HND:main"][data-v="14"]'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
