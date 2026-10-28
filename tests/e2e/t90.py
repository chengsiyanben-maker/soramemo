import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 の画面：方針を選ぶ・満足度・見た機体（スイッチ co_v3 がオンのときだけ）
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });"
V3 = """window.__co = {name:'そらメモ航空', cash:100000, last:new Date().toISOString(), roles:{}, daily:300, gross:300, upkeep:0, bonus:0, routes:[], fleet:[], sky:{}, total_km:0, rep_points:0, stars:1, facilities:{}, bought:1, value:100000, friend_code:'ABCD1234', hide_rank:false, friends:0,
  v3:true, rating:5, rating_have:{routes:40, intl:5, fleet:35, stars:5, days:99}, policy:'fsc', premium:20, satisfaction:41.2, sat_mult:0.97, sat_parts:{base:50, packed:0, new_share:3, aging:-2, policy_adj:-5, target:46}};
window.__seen = [{reg:'JA861J', code:'B789', name:'B787-9', kind:'pax', airport:'成田', seen_at:new Date(Date.now()-864e5).toISOString(), flight:'JL4', dep:'NRT', arr:'JFK', price:55380, as_ridden:false},
  {reg:'JA11KZ', code:'B748F', name:'B747-8F', kind:'freighter', airport:'成田', seen_at:new Date(Date.now()-864e5).toISOString(), flight:'KZ110', dep:'NRT', arr:'ANC', price:72450, as_ridden:true}];"""
async def open_page(b, init_extra):
    c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script(INIT + init_extra)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page()
    return c, pg
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(500)
        check('v3 の欄が出る:', await pg.evaluate("!$('coV3').hidden"))
        v = await pg.inner_text('#coV3'); print('V3', v.replace('\n', ' | ')[:400])
        check('方針6枚:', await pg.locator('[data-pol]').count() == 6)
        check('今の方針 FSC:', '今の方針' in await pg.inner_text('[data-pol=fsc]') and '今の方針です' in v)
        check('満足度 41.2・目標値 46・効き目 −3%:', '41.2' in v and '46' in v and '−3%' in v)
        check('あしたは +0.5:', '+0.5' in v)
        check('目標値の中身:', '基本' in v and '機体の古さ' in v and '−2' in v and '方針の補正' in v and '−5' in v)
        await pg.click('[data-pol=lcc]'); await pg.wait_for_timeout(200)
        v = await pg.inner_text('#coV3'); check('LCC の中身:', '0.72倍' in v and 'LCCにする' in v)
        await pg.click('[data-setpol=lcc]'); await pg.wait_for_timeout(400)
        check('方針を変える（co3_set_policy）:', await pg.evaluate('window.__setPol && window.__setPol.p_policy') == 'lcc' and await pg.evaluate('CO.policy') == 'lcc')
        check('今の方針が LCC に:', '今の方針' in await pg.inner_text('[data-pol=lcc]') and '方針をLCCにしました' in await pg.inner_text('#coMsg'))
        await pg.screenshot(path=os.path.join(WORK, 't70_policy.png'), full_page=True)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('見た機体のタブ:', await pg.locator('[data-cotab=seen]').count() == 1)
        await pg.click('[data-cotab=seen]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#coFleet'); print('SEEN', t.replace('\n', ' | ')[:400])
        check('見た機体の一覧:', 'JA861J' in t and 'JA11KZ' in t and '（貨物機）' in t and '見ただけ' in t and '乗ったのと同じ扱い' in t)
        await pg.click('[data-seentab=freighter]'); await pg.wait_for_timeout(200)
        t2 = await pg.inner_text('#coFleet'); check('貨物機だけ:', 'JA11KZ' in t2 and 'JA861J' not in t2)
        await pg.click('[data-seentab=pax]'); await pg.wait_for_timeout(200)
        t2 = await pg.inner_text('#coFleet'); check('旅客機だけ:', 'JA861J' in t2 and 'JA11KZ' not in t2)
        await pg.click('[data-seentab=all]'); await pg.wait_for_timeout(200)
        check('値段:', '5億5,380万円' in t and '7億2,450万円' in t)
        await pg.evaluate("window.__seenLimit = true"); await pg.click('[data-buyseen=JA861J]'); await pg.wait_for_timeout(400)
        check('1日3機まで:', '1日3機まで' in await pg.inner_text('#coMsg'))
        await pg.evaluate("window.__seenLimit = false; renderFleet()"); await pg.wait_for_timeout(200)
        await pg.click('[data-buyseen=JA861J]'); await pg.wait_for_timeout(600)
        check('見た機体を買う:', await pg.evaluate('CO.cash') == 100000 - 55380 and await pg.evaluate('CO.fleet.some(f => f.reg === "JA861J")'))
        await pg.click('[data-cotab=seen]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#coFleet'); check('買った機体は一覧から消える:', 'JA861J' not in t and 'JA11KZ' in t)
        await pg.screenshot(path=os.path.join(WORK, 't70_seen.png'), full_page=True)
        await c.close()
        # スイッチがオフのとき：今までのまま
        c, pg = await open_page(b, ''); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(500)
        check('オフ：v3 の欄は出ない:', await pg.evaluate("$('coV3').hidden && !$('coV3').innerHTML"))
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300)
        check('オフ：見た機体のタブはない:', await pg.locator('[data-cotab=seen]').count() == 0)
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
