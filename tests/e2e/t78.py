import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の定期点検（A点検）：飛んだ時間・点検まで・やり方の切り替え・今夜入れる・期限切れ・朝のまとめ・格付け2は自動
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
EXTRA = """Object.assign(window.__co.fleet[0], {fly_hours:1830, check_left_hours:30, checked_day:'2026-10-01', check_req:false, check_cost:57.2});
window.__co.fleet.push({id:2, type:'nb', reg:'JA02XJ', icao:'B738', kind:'pax', route:null, paid:20000, age:1, value:20000, sell:6000, upkeep:30, bought_at:new Date().toISOString(), fly_hours:900, check_left_hours:-2, checked_day:null, check_req:false, check_cost:26});
window.__co.check_mode = 'self'; window.__co.morning = {day:new Date(Date.now() + 9 * 36e5 - 864e5).toISOString().slice(0, 10), profit:500, prev_profit:400, cancelled:0, god:0, open:0, sat:41, prev_sat:41};"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + EXTRA, errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coFleet')
        check('飛んだ時間・A点検まで あと30時間:', '飛んだ時間 1,830時間・A点検まで あと30時間・前の点検 10/01' in t)
        check('期限切れの機体は飛べない:', 'A点検の期限切れで飛べません' in t and '期限です' in t)
        check('やり方：自分で入れる が選ばれている:', await pg.get_attribute('[data-chkmode=self]', 'aria-pressed') == 'true')
        await pg.click('[data-chk="1"]'); await pg.wait_for_timeout(400)
        check('今夜A点検を入れる（co3_request_check）:', await pg.evaluate('window.__chkReq.p_aircraft === 1 && window.__chkReq.p_on === true') and '今夜A点検を入れます' in await pg.inner_text('#coMsg'))
        check('入れたら「取り消す」になる:', '今夜の点検を取り消す' in await pg.inner_text('#coFleet'))
        await pg.click('[data-chkmode=auto]'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coFleet')
        check('おまかせにする（co3_set_check_mode）:', await pg.evaluate('window.__chkMode.p_mode === "auto"') and '費用は1割高い' in t and await pg.locator('[data-chk]').count() == 0 and 'A点検の期限切れで飛べません' not in t)
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        body = await pg.inner_text('body')
        check('朝のまとめ：A点検の期限が近い（2機）:', 'A点検の期限が近い：JA01XJ（あと30時間）・JA02XJ（期限切れ）' in body)
        await c.close()
        c, pg = await open_page(b, V3 + EXTRA + "window.__co.rating = 2;", errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coFleet')
        check('格付け2：自動・ボタンなし・期限切れにならない:', '維持費に込み・+10%' in t and await pg.locator('[data-chk],[data-chkmode]').count() == 0 and 'A点検の期限切れで飛べません' not in t)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
