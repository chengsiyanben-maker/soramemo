import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の方針ごとの画面：貨物の路線・プライベートジェット・地域航空の仕事（スイッチ co_v3 がオンのときだけ）
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });"
BASE = "{name:'そらメモ航空', cash:100000, last:new Date().toISOString(), roles:{}, daily:300, gross:300, upkeep:0, bonus:0, routes:[{k:'5-6', a:'HND', b:'CTS', km:820, base:344, level:1, cost:10320, mult:.5, hub:1, sky:1, min_size:4.5, sa:6, sb:4.5, ac_id:null, intl:false}], sky:{}, total_km:820, rep_points:0, stars:1, facilities:{}, bought:1, value:100000, friend_code:'ABCD1234', hide_rank:false, friends:0, v3:true, premium:0, satisfaction:50, sat_mult:0.98, sat_parts:{base:50, target:50}, plans:{}"
CARGO = "window.__co = Object.assign(" + BASE + "}, {policy:'cargo', fleet:[{id:1, type:'lg', reg:'JA11KZ', icao:'B748', kind:'freighter', route:null, paid:70000, age:1, value:70000, sell:21000, upkeep:48, bought_at:new Date().toISOString()}],\
  cargo_routes:[{k:'ANC-NRT', a:'ANC', b:'NRT', intl:true, km:5330, seen:true}, {k:'5-6', a:'HND', b:'CTS', intl:false, km:820, seen:false}],\
  cargo:[{k:'ANC-NRT', a:'ANC', b:'NRT', km:5330, intl:true, tons:391.2, n:3, flights:0, payload:0, carried:0, revenue:0, cost:0, landing:0, congestion:0, profit:0, ac_id:null}, {k:'5-6', a:'HND', b:'CTS', km:820, intl:false, tons:120.5, n:1, flights:0, payload:0, carried:0, revenue:0, cost:0, landing:0, congestion:0, profit:0, ac_id:null}]});"
PJ = "window.__co = Object.assign(" + BASE + "}, {policy:'pj', fleet:[{id:1, type:'rj', reg:'JA500G', icao:'GLF6', kind:'bizjet', route:'5-6', paid:50000, age:1, value:50000, sell:15000, upkeep:30, bought_at:new Date().toISOString()}],\
  pj:[{k:'5-6', a:'HND', b:'OKA', km:1560, intl:false, kind:'resort', vip:238, n:1, flights:4, seats:14, fill:0.9, revenue:905, cost:452, landing:4, congestion:0, profit:449, ac_id:1}]});"
REG = "window.__co = Object.assign(" + BASE + "}, {policy:'regional', fleet:[{id:1, type:'prop', reg:'SM-1A2F', icao:'C208', kind:'light', route:null, paid:1600, age:1, value:1600, sell:480, upkeep:2, bought_at:new Date().toISOString()}],\
  jobs:[{ac_id:1, job:'sightseeing', airport:'ISG', seats:9, earn:51.3}], subsidy:[{k:'5-6', kind:'island', load:0.38, subsidy:22}],\
  small:[{code:'C172', name:'セスナ172', kind:'small', seats:3, range:1200, price:625}, {code:'C208', name:'セスナ208 キャラバン', kind:'small', seats:9, range:1700, price:2000}]});"
async def open_page(b, extra, errs):
    c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script(INIT + extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
    await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(400)
    return c, pg
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # 貨物
        c, pg = await open_page(b, CARGO, errs)
        t = await pg.inner_text('#coOps'); print('CARGO', t.replace('\n', ' | ')[:400])
        check('貨物：画面が出る:', '貨物の路線' in t and 'ANC ⇄ NRT' in t and '見た貨物機の区間' in t and '飛んだ区間' in t)
        check('貨物：機体なしは貨物の量を出す:', '391.2' in t and '機体なし' in t)
        await pg.select_option('[data-cargoassign="ANC-NRT"]', '1'); await pg.wait_for_timeout(500)
        check('貨物：貨物機を入れる（co3_cargo_assign）:', await pg.evaluate('window.__cargoAssign.p_aircraft === 1 && window.__cargoAssign.p_route === "ANC-NRT"'))
        t = await pg.inner_text('#coOps')
        check('貨物：内わけ（運んだ量・積み込み・もうけ）:', '227.8' in t and '85' in t and '+952' in t and '3社で分ける' in t)
        await pg.screenshot(path=os.path.join(WORK, 't71_cargo.png'), full_page=True)
        await pg.select_option('[data-cargoassign="ANC-NRT"]', ''); await pg.wait_for_timeout(500)
        check('貨物：外す（路線なしで呼ぶ）:', await pg.evaluate('window.__cargoAssign.p_route === null'))
        await c.close()
        # プライベートジェット
        c, pg = await open_page(b, PJ, errs)
        t = await pg.inner_text('#coOps'); print('PJ', t.replace('\n', ' | ')[:400])
        check('PJ：画面が出る:', 'プライベートジェット' in t and 'リゾート' in t and '238' in t and '90' in t and '+449' in t)
        check('PJ：おまかせ:', 'おまかせ：いちばんもうかる4便' in t and await pg.get_attribute('[data-pjfl="5-6"][data-n="0"]', 'aria-pressed') == 'true')
        await pg.click('[data-pjfl="5-6"][data-n="2"]'); await pg.wait_for_timeout(400)
        check('PJ：2便に決める（co3_set_flights）:', await pg.evaluate('window.__setFl.p_flights === 2') and await pg.get_attribute('[data-pjfl="5-6"][data-n="2"]', 'aria-pressed') == 'true')
        await pg.click('[data-pjfl="5-6"][data-n="8"]'); await pg.wait_for_timeout(400)
        check('PJ：上限を超えると何便までか出す:', '4便までです' in await pg.inner_text('#coOps'))
        await pg.click('[data-pjfl="5-6"][data-n="0"]'); await pg.wait_for_timeout(400)
        check('PJ：おまかせに戻す（null）:', await pg.evaluate('window.__setFl.p_flights === null'))
        await pg.screenshot(path=os.path.join(WORK, 't71_pj.png'), full_page=True)
        await c.close()
        # 地域航空
        c, pg = await open_page(b, REG, errs)
        t = await pg.inner_text('#coOps'); print('REG', t.replace('\n', ' | ')[:400])
        check('地域航空：仕事・補助・小型機:', '地域航空の仕事' in t and '石垣で遊覧' in t and '遊覧' in t and '+51' in t and '+22' in t and '離島' in t and '38%' in t and 'セスナ208 キャラバン' in t)
        await pg.click('[data-buysmall=C208]'); await pg.wait_for_timeout(400)
        check('地域航空：小型機を買う（co3_buy_small）:', await pg.evaluate('window.__buySmall.p_code === "C208"') and await pg.evaluate('CO.cash') == 98000 and 'セスナ208 キャラバンを会社に入れました' in await pg.inner_text('#coMsg'))
        await pg.screenshot(path=os.path.join(WORK, 't71_regional.png'), full_page=True)
        await c.close()
        # FSC・スイッチがオフ：出ない
        c, pg = await open_page(b, "window.__co = Object.assign(" + BASE + "}, {policy:'fsc', fleet:[]});", errs)
        check('FSC：方針ごとの画面は出ない:', await pg.evaluate("$('coOps').hidden"))
        await c.close()
        c, pg = await open_page(b, '', errs)
        check('オフ：出ない:', await pg.evaluate("$('coOps').hidden && !$('coOps').innerHTML"))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
