import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行：記録した便が0のとき（11/24 PM：アプリ全体の見直しから）
#   今年の JAL・ANA の記録が0で、合わせた数字・予定・計画の案もないときは、修行タブを「まだ記録した便がありません」と「計画を作る」だけにする。
#   目標を勝手に入れず、「届きません」の文を出さない。予定か記録が1つでもあれば、今までの「道のりの1枚」に戻る（確定した修行の形は変えない）
import asyncio
from playwright.async_api import async_playwright
NOW = '2026-11-24T03:00:00Z'   # 日本時間 2026-11-24 12:00
SHOT = os.environ.get('SORAMEMO_SHOT_DIR')   # 置くと写真を撮る（スマホ幅 390×844 と 375×667）
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2 if SHOT else 1)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.clock.install(time=NOW)
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.clock.run_for(800)
        await pg.evaluate("() => { __fake.db.flights.length = 0; }")
        await pg.evaluate('__fake.login()'); await pg.clock.run_for(1200)
        await pg.evaluate("() => { const g = sgGet(); g.car = null; g.goal.JAL = null; g.goal.ANA = null; g.plans = []; g.drafts = []; g.sync = null; S.flights = []; }")
        async def body():
            await pg.evaluate("openShugyo('main')"); await pg.clock.run_for(600)
            return await pg.inner_text('#v-sg')
        # 1 便が1つもない
        t = await body()
        print(repr(t[:300]))
        check('記録0：「まだ記録した便がありません」と「計画を作る」:', 'まだ記録した便がありません' in t and '計画を作る' in t)
        check('記録0：目標・届くかの文・あと○・ポイントの棒を出さない:', all(w not in t for w in ['目標', '届きません', '届きます', 'あと ', 'ポイント 0%', '1年 ']))
        n = await pg.evaluate("() => ({ seg:document.querySelectorAll('#v-sg .sgb-hd [data-sg-car], #v-sg .sgb-hd .sg-seg button').length, views:document.querySelectorAll('#v-sg [data-sg-view]').length, pen:document.querySelectorAll('#v-sg [data-sgvs-open]').length, zero:document.querySelectorAll('#v-sg .sgb-zero').length, hero:document.querySelectorAll('#v-sg .sgb-hero').length, prof:document.querySelectorAll('#v-sg [data-sg-go=profile]').length, btn:[...document.querySelectorAll('#v-sg .sgb-zero [data-sg-go]')].map(x => x.dataset.sgGo) })")
        print(n)
        check('記録0：会社の切り替え・見方のピル・鉛筆を出さず、会員情報は残す:', n['seg'] == 0 and n['views'] == 0 and n['pen'] == 0 and n['zero'] == 1 and n['hero'] == 0 and n['prof'] == 1)
        check('記録0：「計画を作る」はサーバー版で便を探す画面へ・目標を使わない計算の入口は残す:', n['btn'] == ['find'] and '路線を入れて計算する' in t)
        g = await pg.evaluate("() => { const g = sgGet(); return [g.goal.JAL, g.goal.ANA, g.car]; }")
        check('記録0：目標を保存に勝手に入れない:', g == [None, None, None])
        if SHOT:
            os.makedirs(SHOT, exist_ok=True); await pg.screenshot(path=os.path.join(SHOT, '1-zero-390.png'))
            await pg.set_viewport_size({'width':375,'height':667}); await pg.clock.run_for(300); await pg.screenshot(path=os.path.join(SHOT, '2-zero-667.png')); await pg.set_viewport_size({'width':390,'height':844})
        # 見方を「月ごと」にしていても、記録0の形
        await pg.evaluate("() => { SG_VIEW = 'months'; }"); t = await body()
        check('記録0：見方が月ごとでも記録0の形（12月31日の残りを出さない）:', 'まだ記録した便がありません' in t and '12月31日の残り' not in t)
        await pg.evaluate("() => { SG_VIEW = 'road'; }")
        await pg.click('#v-sg .sgb-zero [data-sg-go]'); await pg.clock.run_for(400)
        check('記録0：押すと計画の画面へ:', await pg.evaluate("SG_PAGE") == 'find')
        await pg.evaluate("() => { SG_PAGE = 'main'; }")
        # 2 車などと航空会社なしの便だけ → まだ JAL・ANA の便はない
        await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, k = A.find(a => a.iata === 'KIX').id;
          S.flights = [{ id:'x1', from:h, to:k, dep:Date.UTC(2026, 9, 1, 1), km:400, airline:null }]; }""")
        t = await body(); print(repr(t[:200]))
        check('JAL・ANA 以外の便だけ：「JAL・ANA の便は、まだ記録がありません」:', 'JAL・ANA の便は、まだ記録がありません' in t and '目標' not in t)
        # 3 前の年だけ便がある → 今年はまだ
        await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id;
          S.flights = [{ id:'x2', from:h, to:o, dep:Date.UTC(2025, 5, 1, 1), km:1500, airline:'JL', fare:'JAL:Y_SAVER' }]; }""")
        t = await body(); print(repr(t[:200]))
        check('前の年だけ：「2026年は、まだ記録した便がありません」:', '2026年は、まだ記録した便がありません' in t and '目標' not in t and '届きません' not in t)
        # 4 予定の便がある → 今までの道のり（予定は分けて出す）
        await pg.evaluate("""() => { const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id;
          g.plans = [{ id:'p1', d:'2026-12-05', hm:'07:00', from:h, to:o, car:'JAL', fare:'JAL:Y_SAVER', no:'JL903' }]; }""")
        t = await body()
        check('予定がある：道のりの1枚に戻る（目標と予定）:', 'まだ記録した便がありません' not in t and '目標' in t and '予定' in t and await pg.locator('#v-sg .sgb-hero').count() == 1)
        # 5 今年の便がある → 今までの道のり
        await pg.evaluate("""() => { const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.plans = [];
          S.flights = [{ id:'x3', from:h, to:o, dep:Date.UTC(2026, 9, 1, 1), km:1500, airline:'JL', fare:'JAL:Y_SAVER' }]; }""")
        t = await body()
        check('今年の便がある：道のりの1枚（大きな数字・見方のピル）:', 'まだ記録した便がありません' not in t and '目標' in t and await pg.locator('#v-sg [data-sg-view]').count() >= 1)
        # 6 会社のサイトに合わせた数字だけある → 今までの道のり
        await pg.evaluate("() => { const g = sgGet(); S.flights = []; g.sync = { JAL:{ use:true, at:'2026-11-01', pts:12000, n:10 } }; }")
        t = await body()
        check('合わせた数字がある：道のりの1枚:', 'まだ記録した便がありません' not in t and '12,000' in t)
        # 7 計画の案だけある → 今までの道のり
        await pg.evaluate("""() => { const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.sync = null;
          g.drafts = [{ car:'JAL', d:'2026-12-10', legs:[{ d:0, from:h, to:o, fare:'JAL:Y_SAVER' }] }]; }""")
        z = await pg.evaluate("sgZero()")
        check('計画の案がある：記録0の形にしない:', z is False)
        check('エラーなし:', not errs)
        if errs: print(errs[:3])
        await b.close()
asyncio.run(main())
print('errors', fails)
