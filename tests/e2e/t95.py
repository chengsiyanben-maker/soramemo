import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の機体の故障と予備機：機体の画面の運休・トラブルの原因・遅れの波・満足度の定時率
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });"
V3 = """(() => { const now = Date.now(), iso = t => new Date(t).toISOString(), y = new Date(now - 864e5 + 9 * 36e5).toISOString().slice(0, 10), y3 = new Date(now - 3 * 864e5 + 9 * 36e5).toISOString().slice(0, 10);
window.__co = {name:'そらメモ航空', cash:100000, last:iso(now), roles:{}, daily:300, gross:300, upkeep:0, bonus:0,
  routes:[{k:'5-6', a:'HND', b:'CTS', km:820, base:344, level:1, cost:10320, mult:.5, hub:1, sky:1, min_size:4.5, sa:6, sb:4.5, ac_id:1, intl:false}],
  fleet:[{id:1, type:'lg', reg:'JA01XJ', icao:'A359', kind:'pax', route:'5-6', paid:40000, age:1, value:40000, sell:12000, upkeep:80, bought_at:iso(now)}],
  sky:{}, total_km:820, rep_points:0, stars:1, facilities:{}, bought:1, value:100000, friend_code:'ABCD1234', hide_rank:false, friends:0,
  v3:true, rating:5, rating_have:{routes:40, intl:5, fleet:35, stars:5, days:99}, policy:'fsc', premium:20, satisfaction:41.2, sat_mult:0.97, sat_parts:{base:50, meal:-8, bag:0, response:0, target:37}, meal:'none', bag:'free', home:null, home_since:null, plans:{}, fares:{}, auto_trouble:false, morning:{day:y, profit:1240, prev_profit:1100, gross:1500, upkeep:260, sat:41.2, prev_sat:40.9, cancelled:1, open:1, god:0, legs_done:6, delayed:2, cxl_legs:1, wave:[{k:'5-6', reg:'JA01XJ', legs:[{n:1,f:'HND',to:'CTS',t:390,blk:100,s:'ok',d:0,c:0},{n:2,f:'CTS',to:'HND',t:570,blk:100,s:'delay',d:70,c:0},{n:3,f:'HND',to:'CTS',t:750,blk:100,s:'delay',d:30,c:30},{n:4,f:'CTS',to:'HND',t:930,blk:100,s:'ok',d:0,c:0},{n:5,f:'HND',to:'CTS',t:1110,blk:100,s:'cxl',d:0,c:0},{n:6,f:'CTS',to:'HND',t:1290,blk:100,s:'ok',d:0,c:0}]}], sky:[{k:'5-6', mult:0.9, n:18, cxl:2, avg4:20}]},
  econ:[{k:'5-6', kind:'big', real:20, demand:1190, n:1, own:1118, flights:6, seats:369, carried:1118, revenue:938, cost:556, landing:36, congestion:0, profit:346, p_seats:0, p_pax:0, e_pax:1118}],
  troubles:[{id:11, k:'5-6', day:y, flights:6, cancelled:1, real_n:18, real_cxl:2, rev_flight:156.4, created_at:iso(now - 18 * 6e4), god_until:iso(now + 42 * 6e4), deadline:iso(now + 342 * 6e4), card:null, cost:null, result:null, auto:false, done_at:null},
            {id:12, k:'5-6', day:y, leg:5, kind:'delay', delay_min:150, dep_at:iso(now + 3 * 36e5), dep:'HND', arr:'CTS', fits:['snack'], flights:6, cancelled:0, real_n:2, real_cxl:0, rev_flight:156.4, created_at:iso(now - 5 * 6e4), god_until:iso(now + 55 * 6e4), deadline:iso(now + 355 * 6e4), card:null, cost:null, result:null, auto:false, done_at:null},
            {id:9, k:'5-6', day:y3, flights:6, cancelled:2, real_n:10, real_cxl:5, rev_flight:156.4, created_at:iso(now - 3 * 864e5), god_until:iso(now - 3 * 864e5 + 36e5), deadline:iso(now - 3 * 864e5 + 6 * 36e5), card:null, cost:null, result:'none', auto:false, done_at:null}]}; })();"""
async def open_page(b, extra, errs):
    c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script(INIT + extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
    return c, pg
EXTRA = """(() => { const y = new Date(Date.now() - 864e5 + 9 * 36e5).toISOString().slice(0, 10), y2 = new Date(Date.now() + 864e5 + 9 * 36e5).toISOString().slice(0, 10);
 window.__co.breakdowns = [{id:1, ac_id:1, reg:'JA01XJ', k:'5-6', start:y, end:y2, days:3, spare_id:null, spare_reg:null}];
 window.__co.troubles = [{id:21, k:'5-6', day:y, leg:2, kind:'cxl', cause:'breakdown', delay_min:0, dep_at:new Date(Date.now() + 2 * 36e5).toISOString(), dep:'CTS', arr:'HND', fits:['transfer'], flights:6, cancelled:1, real_n:0, real_cxl:0, rev_flight:156.4, created_at:new Date().toISOString(), god_until:new Date(Date.now() + 36e5).toISOString(), deadline:new Date(Date.now() + 6 * 36e5).toISOString(), card:null, cost:null, result:null, auto:false, done_at:null}];
 window.__co.morning.wave = [{k:'5-6', reg:'JA01XJ', legs:[{n:1,f:'HND',to:'CTS',t:390,blk:100,s:'ok',d:0,c:0},{n:2,f:'CTS',to:'HND',t:570,blk:100,s:'cxl',d:0,c:0,why:'breakdown'},{n:3,f:'HND',to:'CTS',t:750,blk:100,s:'cxl',d:0,c:0,why:'breakdown'}]}];
 window.__co.sat_parts = Object.assign({}, window.__co.sat_parts, {ontime:-15, own_cxl:-2, ontime_rate:0.33}); })();"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + EXTRA, errs)
        v = await pg.inner_text('#coV3'); print('V3', v.replace('\n', ' | ')[:300])
        check('トラブル：機体の故障（会社のせい）:', '機体の故障（会社のせい）' in v and '予備機もないため欠航' in v)
        check('遅れの波：故障で2便が欠航（予備機があれば飛べた）:', '機体の故障で 2便が欠航（予備機があれば飛べた）' in v and await pg.locator('.wv .wt i.x.b').count() == 2)
        check('満足度：定時率 33% −15・自分のせいの欠航 −2:', '定時率（前の30日、会社のせいの欠航だけ） 33%' in v and '−15' in v and '自分のせいの欠航（故障）' in v)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coFleet')
        check('機体の画面：故障で運休中・予備機なし:', '故障で運休中' in t and '予備機がないので、この路線は欠航' in t)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
