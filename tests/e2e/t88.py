import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の共同運航とアライアンス：売れる路線・申し込む・認める・やめる・アライアンスに入る・抜ける・作る
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
CS = "window.__co.cs = {limit:20, income:0, list:[{id:20, k:'5-6', kind:'free', status:'pending', role:'op', partner:'ひこうき雲エア', a:'HND', b:'CTS', share:null, block_price:null}]};"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3 + CS, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#coV3')
        check('頼まれている：運航 自社・販売 ひこうき雲エア:', '運航：自社 ・ 販売：ひこうき雲エア' in t and '（認め待ち）' in t)
        check('売れる路線：つばさ商会 羽田⇄広島 +120/日:', 'つばさ商会 ・ 羽田 ⇄ 広島' in t and 'フリーセールで +120/日' in t)
        await pg.click('[data-csok="20"]'); await pg.wait_for_timeout(400)
        check('認める（co3_cs_answer）:', await pg.evaluate('window.__csans.p_id === 20 && window.__csans.p_ok === true'))
        await pg.click('[data-csreq="TSUBASA1"][data-kind=block]'); await pg.wait_for_timeout(600)
        check('ブロック買い取りを申し込む（co3_cs_request）:', await pg.evaluate('window.__csreq.p_op_code === "TSUBASA1" && window.__csreq.p_kind === "block" && window.__csreq.p_route === "5-9"') and '運航：つばさ商会 ・ 販売：自社' in await pg.inner_text('#coV3'))
        await pg.click('[data-csend="21"]'); await pg.wait_for_timeout(400)
        check('やめる（co3_cs_end）:', await pg.evaluate('window.__csend.p_id === 21'))
        await pg.click('[data-rk=ally]'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#coRank')
        check('アライアンスの一覧:', 'みなみの空連合' in t and '12社' in t and await pg.locator('[data-ajoin="3"]').count() == 1)
        await pg.click('[data-ajoin="3"]'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#coRank')
        check('入る（co3_ally_join）:', await pg.evaluate('window.__ajoin.p_id === 3') and 'あなたのアライアンス' in t and 'みなみ風エア' in t)
        await pg.click('#allyLeave'); await pg.wait_for_timeout(600)
        check('抜ける・7日は入れない:', await pg.evaluate('window.__aleave === true') and await pg.is_disabled('[data-ajoin="3"]') and 'から入れます' in await pg.inner_text('#coRank'))
        await c.close()
        c, pg = await open_page(b, V3 + CS, errs)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        await pg.click('[data-rk=ally]'); await pg.wait_for_timeout(600)
        await pg.fill('#allyName', 'そらの輪'); await pg.click('#allyMake'); await pg.wait_for_timeout(600)
        check('作る（co3_ally_create）:', await pg.evaluate('window.__amake.p_name === "そらの輪"') and 'そらの輪' in await pg.inner_text('#coRank'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
