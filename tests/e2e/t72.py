import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の旅客の路線：お客さん・取り合い・便数・もうけ、本拠地、上級席（スイッチ co_v3 がオンのときだけ）
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
        c, pg = await open_page(b, V3, errs)
        # 本拠地と上級席（会社の画面）
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        v = await pg.inner_text('#coV3'); print('V3', v.replace('\n', ' | ')[:300])
        check('本拠地：まだ決めていない:', 'まだ決めていません' in v)
        opts = await pg.evaluate("[...$('v3Home').options].map(o => o.textContent)")
        check('本拠地：チェックインした空港だけ:', len(opts) == 2 and '羽田' in opts[1])
        await pg.select_option('#v3Home', '5'); await pg.wait_for_timeout(500)
        v = await pg.inner_text('#coV3')
        check('本拠地を決める（co3_set_home）:', await pg.evaluate('window.__setHome.p_airport') == 5 and '羽田' in v and '地元の応援まで' in v and '30' in v)
        check('上級席：FSC は 0・10・20・30%:', await pg.locator('[data-prem]').count() == 4 and await pg.get_attribute('[data-prem="20"]', 'aria-pressed') == 'true')
        await pg.click('[data-prem="30"]'); await pg.wait_for_timeout(400)
        check('上級席を30%に（co3_set_premium）:', await pg.evaluate('window.__setPrem.p_pct') == 30 and await pg.get_attribute('[data-prem="30"]', 'aria-pressed') == 'true')
        check('サービス：はじめは機内食なし・荷物無料:', await pg.get_attribute('[data-svc=meal][data-v=none]', 'aria-pressed') == 'true' and await pg.get_attribute('[data-svc=bag][data-v=free]', 'aria-pressed') == 'true')
        await pg.click('[data-svc=meal][data-v=free]'); await pg.wait_for_timeout(400)
        check('サービス：機内食を無料に（co3_set_service）:', await pg.evaluate('window.__setSvc.p_meal === "free" && window.__setSvc.p_bag === "free"') and '満足度 +8' in await pg.inner_text('#coV3'))
        check('サービス：目標値の中身に機内食:', '機内食' in await pg.inner_text('#coV3') and '+8' in await pg.inner_text('#coV3'))
        await pg.click('[data-svc=bag][data-v=paid]'); await pg.wait_for_timeout(400)
        check('サービス：荷物を有料に（機内食は無料のまま）:', await pg.evaluate('window.__setSvc.p_meal === "free" && window.__setSvc.p_bag === "paid"') and '旅行の客 −5%' in await pg.inner_text('#coV3'))
        await pg.screenshot(path=os.path.join(WORK, 't72_home.png'), full_page=True)
        # 路線（v3 の内わけ）
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coRoutes'); print('ROUTE', t.replace('\n', ' | ')[:300])
        check('路線：もうけと便数・搭乗率:', '+761' in t and '1日12便' in t and '搭乗率 80%' in t)
        check('路線：増便の段は出さない:', await pg.locator('#coRoutes [data-up]').count() == 0)
        await pg.click('#coRoutes details summary'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#coRoutes')
        check('路線：お客さん・取り合い・取り分:', '18,500' in t and '3,110' in t and '3' in t and '17%' in t and '大きい空港どうし' in t)
        check('路線：費用・着陸料・混雑料・上級席:', '−1,420' in t and '−84' in t and '−35' in t and '420人' in t and '仕事の客の運賃' in t and '+20%' in t)
        check('便ごとの搭乗率:', '便ごとの搭乗率（1日3便・平均 73%）' in t and '06:30' in t and '89%' in t and 'いちばん空いているのは 12:30 の便（54%）' in t)
        check('運賃：5段階・ほかの会社の段:', await pg.locator('[data-fare]').count() == 5 and 'ほかの会社：安い・普通' in t and await pg.get_attribute('[data-fare="5-6"][data-lv="0"]', 'aria-pressed') == 'true')
        await pg.click('[data-fare="5-6"][data-lv="-1"]'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#coRoutes')
        check('運賃を安いに（co3_set_fare）・きょうはほかの段を押せない:', await pg.evaluate('window.__setFare.p_level') == -1 and 'きょうはもう変えました' in t and await pg.is_disabled('[data-fare="5-6"][data-lv="1"]'))
        await pg.click('[data-pjfl="5-6"][data-n="6"]'); await pg.wait_for_timeout(400)
        check('路線：便数を決める（co3_set_flights）:', await pg.evaluate('window.__setFl.p_route === "5-6" && window.__setFl.p_flights === 6'))
        check('路線：決めたあとも開いたまま:', await pg.evaluate('document.querySelector("#coRoutes details").open'))
        check('路線：v3 の説明:', await pg.is_visible('#coRouteHintV3') and not await pg.is_visible('#coRouteHint'))
        await pg.screenshot(path=os.path.join(WORK, 't72_route.png'), full_page=True)
        await c.close()
        # LCC：上級席は出さない
        c, pg = await open_page(b, V3 + "window.__co.policy = 'lcc'; window.__co.premium = 0;", errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        check('LCC：上級席は出さない:', await pg.locator('[data-prem]').count() == 0)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300); await pg.click('#coRoutes details summary'); await pg.wait_for_timeout(200)
        check('LCC：仕事の客の運賃は上げない（行を出さない）:', '仕事の客の運賃' not in await pg.inner_text('#coRoutes'))
        await c.close()
        # スイッチがオフ：前の路線の画面のまま
        c, pg = await open_page(b, '', errs)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(400)
        check('オフ：増便の段のまま:', await pg.locator('#coRoutes [data-up]').count() == 1)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
