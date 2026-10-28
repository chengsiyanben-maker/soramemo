import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 のリースと中古機：リースで借りる・返す・中古で売りに出す・取り下げる・中古機の売り場で買う
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
EXTRA = """window.__co.lease_room = 2; window.__co.market = [{id:5, reg:'JA55AA', code:'B738', name:'B737-800', type:'nb', price:20000, value:24000, age:0.9, seller:'つばさ商会', expires:new Date(Date.now() + 3 * 864e5).toISOString(), can_buy:true},
  {id:6, reg:'JA66BB', code:'A21N', name:'A321neo', type:'nb', price:30000, value:30000, age:1, seller:'ひこうき雲エア', expires:new Date(Date.now() + 5 * 864e5).toISOString(), can_buy:false}];"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + EXTRA, errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        await pg.click('[data-cotab=buy]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#coFleet')
        check('買える：リースで借りる（1日 約…）:', await pg.locator('[data-lease-ride]').count() >= 1 and 'リースで借りる（1日 約' in t)
        await pg.click('[data-lease-ride]'); await pg.wait_for_timeout(400)
        check('リースで借りる（co3_lease ride）:', await pg.evaluate('window.__lease.p_kind === "ride"') and 'リースで借りました' in await pg.inner_text('#coMsg'))
        await pg.click('[data-cotab=have]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coFleet')
        check('持っている：リースの機体（1日 75）・返す:', 'リースの機体（1日 75万円' in t and await pg.locator('[data-lease-return]').count() == 1)
        await pg.select_option('[data-mk-pct="1"]', '120'); await pg.click('[data-mk-list="1"]'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coFleet')
        check('中古で売りに出す 120%（co3_market_list）:', await pg.evaluate('window.__mkList.p_pct === 120') and '中古で売りに出し中 4億8,000万円' in t)
        await pg.click('[data-mk-cancel="77"]'); await pg.wait_for_timeout(300)
        check('取り下げる:', await pg.evaluate('window.__mkCancel.p_listing === 77') and await pg.locator('[data-mk-list="1"]').count() == 1)
        await pg.click('[data-lease-return]'); await pg.wait_for_timeout(300)
        check('リースを返す:', await pg.evaluate('!!window.__leaseRet') and 'リースの機体' not in await pg.inner_text('#coFleet'))
        await pg.click('[data-cotab=used]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coFleet')
        check('中古機の売り場：2機・知らない機種は買えない:', 'JA55AA' in t and 'つばさ商会' in t and 'この機種に乗る（見る）と買えます' in t and await pg.is_disabled('[data-mk-buy="6"]') and not await pg.is_disabled('[data-mk-buy="5"]'))
        await pg.click('[data-mk-buy="5"]'); await pg.wait_for_timeout(400)
        check('中古機を買う（co3_market_buy）:', await pg.evaluate('window.__mkBuy.p_listing === 5 && CO.fleet.some(f => f.reg === "JA55AA")') and '中古機を買いました' in await pg.inner_text('#coMsg'))
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA + "window.__co.rating = 1;", errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('格付け1：中古で売りに出せない:', await pg.is_disabled('[data-mk-list="1"]') and '格付け2から' in await pg.inner_text('#coFleet'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
