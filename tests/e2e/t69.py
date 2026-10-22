import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# エアライン経営のつくり直し：乗った機体だけ買える・最初は半額・機体なしは半分・売る・路線の内わけ・ランキングと友だち
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); Object.defineProperty(window, 'SORAMEMO_CONFIG', { configurable:true, get(){ return this.__cfg; }, set(v){ this.__cfg = Object.assign({}, v, { gameReleased: true }); } });"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        # 端末だけの版
        c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script(INIT)
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        LOC = os.path.join(WORK, 'local'); os.makedirs(LOC, exist_ok=True); import shutil; shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(LOC, 'index.html'))
        open(os.path.join(LOC, 'config.js'), 'w').write('window.SORAMEMO_CONFIG = {};')   # サーバーなし
        await pg.goto('file://'+os.path.join(LOC,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { const id = i => A.find(a => a.iata === i).id, t0 = Date.now() - 864e5;
          const cs = ['HND','CTS','OKA','ISG'].map((i,k) => ({a:id(i), t:t0 + k*36e5, acc:20, term:null}));
          const fs = [{id:'a1', from:id('HND'), to:id('CTS'), dep:t0, arr:t0+36e5, km:819.6, airline:'JL', no:'JL501'},{id:'a2', from:id('OKA'), to:id('ISG'), dep:t0+2*36e5, arr:t0+3*36e5, km:395.4, airline:null, no:null}];
          S = Object.assign(blank(), {checkins:cs, flights:fs, manual:[]}); save(); render(); }""")
        await pg.wait_for_timeout(500)
        await pg.evaluate("FACTS = new Map([[factKey(S.flights.find(f => f.no)), {reg:'JA01XJ', type:'A359'}]]); CO = null; HANGAR = null; goTab('co')"); await pg.wait_for_timeout(300)
        check('はじめの資金 5,000:', await pg.evaluate('CO.cash') == 5000)
        check('機体なしは ×0.5:', await pg.evaluate('CO.routes.every(r => r.mult === .5)'))
        await pg.evaluate("goTab('fleet')"); await pg.click('[data-cotab=buy]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#coFleet'); print('HANGAR', t.replace('\n', ' | ')[:300])
        check('乗った機体：登録記号と名前のない機体:', 'JA01XJ' in t and '名前のない機体' in t and '（半額）' in t)
        check('お金が足りない機体は押せない:', await pg.is_disabled('[data-buy="r:JA01XJ"]'))
        await pg.click('[data-buy="f:a2"]'); await pg.wait_for_timeout(300)
        check('名前のない機体（プロペラ 8,000 の半額）を買う:', await pg.evaluate('CO.cash') == 1000 and await pg.evaluate('CO.fleet.length') == 1 and 'を会社に入れました' in await pg.inner_text('#coMsg'))
        await pg.click('[data-cotab=have]'); await pg.wait_for_timeout(200)
        oi = await pg.evaluate("CO.routes.find(r => r.a.iata === 'OKA' || r.b.iata === 'OKA').k")
        d0 = await pg.evaluate('CO.gross'); await pg.select_option('[data-assign]', oi); await pg.wait_for_timeout(300)
        check('路線に入れると収益が上がる（×0.5 → ×1.1）:', await pg.evaluate('CO.gross') > d0 and await pg.evaluate(f"CO.routes.find(r => r.k === '{oi}').mult") == 1.1)
        await pg.locator('#coRoutes details', has_text='名前のない機体').locator('summary').click(); await pg.wait_for_timeout(150)
        rc = await pg.inner_text('#coRoutes'); check('路線の内わけ（機体・古さ・実際の空）:', '基本（' in rc and '拠点' in rc and '機体の古さ' in rc and '実際の空' in rc)
        await pg.screenshot(path=os.path.join(WORK, 't69_local_fleet.png'), full_page=True)
        await pg.click('[data-sell]'); await pg.wait_for_timeout(150)
        check('売るのは2回押す（1回目は確かめ）:', await pg.evaluate('CO.fleet.length') == 1 and 'もう一度押すと' in await pg.inner_text('[data-sell]'))
        await pg.click('[data-sell]'); await pg.wait_for_timeout(200)
        check('売ると3割が戻る:', await pg.evaluate('CO.fleet.length') == 0 and await pg.evaluate('CO.cash') >= 1000 + 1200)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(200)
        check('端末だけの版はランキングを出さない:', 'サインインすると' in await pg.inner_text('#coRank'))
        await c.close()
        # サーバー版
        c = await b.new_context(viewport={'width':400,'height':860}); await c.add_init_script(INIT)
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("goTab('fleet')"); await pg.wait_for_timeout(300); await pg.click('[data-cotab=buy]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#coFleet'); print('S-HANGAR', t.replace('\n', ' | ')[:300])
        check('サーバー：乗った機体の一覧（co_hangar）:', 'co_hangar' in await pg.evaluate('window.__rpcs') and 'JA01XJ' in t and 'B737-800' in t)
        await pg.click('[data-buy="r:JA01XJ"]'); await pg.wait_for_timeout(400)
        check('サーバー：登録記号で買う（大型の半額 40,000）:', await pg.evaluate('CO.cash') == 460000 and await pg.evaluate('CO.fleet[0].reg') == 'JA01XJ')
        await pg.click('[data-cotab=have]'); await pg.wait_for_timeout(200)
        await pg.select_option('[data-assign]', '5-6'); await pg.wait_for_timeout(400)
        rt = await pg.inner_text('#coRoutes'); check('サーバー：路線に入った機体が出る:', 'JA01XJ' in rt)
        await pg.screenshot(path=os.path.join(WORK, 't69_server_fleet.png'), full_page=True)
        await pg.evaluate("goTab('co')"); await pg.wait_for_timeout(600)
        rk = await pg.inner_text('#coRank'); print('RANK', rk.replace('\n', ' | ')[:300])
        check('ランキング（全国・先週より）:', '全国 2位' in rk and 'ひこうき雲エア' in rk and '先週より +2位' in rk)
        k = await pg.inner_text('#coKpi'); check('収益・維持費・実際の空:', '維持費' in k and '−80' in k and '実際の空' in k)
        await pg.click('[data-rk=friends]'); await pg.wait_for_timeout(400)
        check('友だち：自分の合言葉:', 'ABCD1234' in await pg.inner_text('#coRank'))
        await pg.fill('#frCode', 'nope'); await pg.click('#frAdd'); await pg.wait_for_timeout(300)
        check('ちがう合言葉:', '見つかりません' in await pg.inner_text('#coMsg'))
        await pg.fill('#frCode', 'zzzz9999'); await pg.click('#frAdd'); await pg.wait_for_timeout(500)
        check('友だちになると一覧に出る:', 'つばさ商会' in await pg.inner_text('#coRank') and 'と友だちになりました' in await pg.inner_text('#coMsg'))
        await pg.screenshot(path=os.path.join(WORK, 't69_rank.png'), full_page=True)
        await pg.check('#rkHide'); await pg.wait_for_timeout(300)
        check('ランキングに出さない設定:', await pg.evaluate('window.__co.hide_rank') is True)
        await c.close(); await b.close()
    print('fails', fails)
    print('errors', errs if not fails else errs + fails)
asyncio.run(main())
