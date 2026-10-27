import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営 v3 のトラブル：対応してください（1日まとめ）・対応カード・神対応・自動で対応する
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
  v3:true, policy:'fsc', premium:20, satisfaction:41.2, sat_mult:0.97, sat_parts:{base:50, meal:-8, bag:0, response:0, target:37}, meal:'none', bag:'free', home:null, home_since:null, plans:{}, fares:{}, auto_trouble:false, morning:{day:y, profit:1240, prev_profit:1100, gross:1500, upkeep:260, sat:41.2, prev_sat:40.9, cancelled:1, open:1, god:0, sky:[{k:'5-6', mult:0.9, n:18, cxl:2, avg4:20}]},
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
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c, pg = await open_page(b, V3, errs)
        v = await pg.inner_text('#coV3'); print('V3', v.replace('\n', ' | ')[:500])
        check('朝のまとめ：きのうのもうけ・前の日より・欠航・実際の空:', 'のまとめ' in v and '+1,240' in v and '前の日より +140' in v and '羽田' in v and '欠航 2便' in v and '−10%' in v and '（+0.3）' in v)
        check('対応してください：欠航の中身:', '対応してください' in v and '6便のうち 1便が欠航' in v and '20便のうち 2便が欠航' in v and '理由は分かりません' in v)
        check('神対応まであと何分:', '神対応まで あと4' in v)
        check('カード3枚・振替が合う・費用:', await pg.locator('[data-trsel="11"]').count() == 3 and 'この欠航に合う' in v and '約32' in v and '約47' in v and '約16' in v)
        check('前の7日：対応なし:', '前の7日のトラブル' in v and '対応なし' in v)
        check('便ごとの遅れ：時刻・向き・約150分・軽食が合う・はじめから軽食を選ぶ:', '遅れ 約150分' in v and '発 羽田' in v and '新千歳' in v and 'この遅れに合う' in v and await pg.get_attribute('[data-trsel="12"][data-card="snack"]', 'aria-checked') == 'true' and '軽食とおわびを使う' in await pg.inner_text('[data-trgo="12"]'))
        await pg.screenshot(path=os.path.join(WORK, 't73_trouble.png'), full_page=True)
        await pg.click('[data-trsel="11"][data-card="snack"]'); await pg.wait_for_timeout(200)
        check('カードを選ぶとボタンが変わる:', '軽食とおわびを使う' in await pg.inner_text('[data-trgo="11"]') and await pg.get_attribute('[data-trsel="11"][data-card="snack"]', 'aria-checked') == 'true')
        await pg.click('[data-trsel="11"][data-card="transfer"]'); await pg.wait_for_timeout(200)
        await pg.click('[data-trgo="11"]'); await pg.wait_for_timeout(500)
        check('振替の手配で神対応（co3_trouble_respond）:', await pg.evaluate('window.__trResp.p_id === 11 && window.__trResp.p_card === "transfer"') and '神対応！' in await pg.inner_text('#coMsg') and await pg.evaluate('CO.cash') == 100000 - 32)
        v = await pg.inner_text('#coV3')
        check('対応のあと：その欠航は消え（遅れの1件は残る）・前の7日に神対応:', await pg.locator('[data-trgo="11"]').count() == 0 and await pg.locator('[data-trgo="12"]').count() == 1 and '神対応' in v)
        await pg.click('#morningClose'); await pg.wait_for_timeout(200)
        check('朝のまとめを閉じると出さない:', 'のまとめ' not in await pg.inner_text('#coV3'))
        await pg.reload(); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600); await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800); await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(400)
        v2 = await pg.inner_text('#coV3'); print('RELOAD', v2[:200].replace('\n', ' | '))
        check('開き直しても閉じたまま（その日だけ）:', 'のまとめ' not in v2)
        await pg.click('#trAuto'); await pg.wait_for_timeout(400)
        check('自動で対応する（co3_set_auto_trouble）:', await pg.evaluate('window.__trAuto.p_on === true') and await pg.is_checked('#trAuto'))
        await c.close()
        # トラブルがなければ出さない
        c, pg = await open_page(b, V3 + "window.__co.troubles = []; window.__co.morning = null;", errs)
        check('トラブルがなければ欄を出さない:', '対応してください' not in await pg.inner_text('#coV3'))
        await c.close(); await b.close()
        print('errors', errs + fails)
asyncio.run(main())
