import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の格付け：いまの格付け・次の条件・解放の鍵（運賃・機内食と荷物は2から、上級席は4から）
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
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + "window.__co.rating = 1; window.__co.rating_have = {routes:3, intl:0, fleet:1, stars:1, days:4};", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        v = await pg.inner_text('#coV3'); print('V3', v.replace('\n', ' | ')[:400])
        check('格付け1：名前・次は「国内線の航空会社」・路線 3/5・機体 1/3:', '地域航空会社' in v and '「国内線の航空会社」' in v and '3/5本' in v and '1/3機' in v and '上がると使える：運賃の5段階' in v)
        check('格付け1：機内食と荷物は押せない・鍵の文:', await pg.is_disabled('[data-svc=meal][data-v=free]') and await pg.is_disabled('[data-svc=bag][data-v=paid]') and '格付け2「国内線の航空会社」から使えます' in v)
        check('上級席は格付け4から:', await pg.is_disabled('[data-prem="30"]') and '格付け4「国際航空会社」から変えられます' in v)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300); await pg.click('#coRoutes details summary'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#coRoutes')
        check('格付け1：運賃は押せない:', await pg.is_disabled('[data-fare="5-6"][data-lv="-1"]') and '格付け2「国内線の航空会社」から使えます' in t and 'きょうはもう変えました' not in t)
        await pg.screenshot(path=os.path.join(WORK, 't74_rating1.png'), full_page=True)
        await c.close()
        c, pg = await open_page(b, V3 + "window.__co.rating = 2; window.__co.rating_have = {routes:7, intl:0, fleet:4, stars:2, days:22};", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        v = await pg.inner_text('#coV3')
        check('格付け2：次は「国内大手」・路線 7/12・★2/★3・22/30日:', '「国内大手」' in v and '7/12本' in v and '★2' in v and '22/30日' in v)
        check('格付け2：機内食は押せる・上級席はまだ:', not await pg.is_disabled('[data-svc=meal][data-v=free]') and await pg.is_disabled('[data-prem="30"]'))
        await pg.click('[data-svc=meal][data-v=free]'); await pg.wait_for_timeout(300)
        check('格付け2：機内食を無料に:', await pg.evaluate('window.__setSvc && window.__setSvc.p_meal === "free"'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
