import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行：小さな動き 08「道のりの帯が伸びる」（11/25 本人 OK・design/micro の 08）
#   道のりの1枚の太い帯と大きな数字が、その日（日本時間）はじめて見たときだけ 0.4 秒で 0 から伸びる・数え上がる。
#   2回目からは動かさない。翌日はまた1回だけ。動きを減らす設定では動かさない。記録0の形では何もしない。1年の細い帯は動かさない
import asyncio
from playwright.async_api import async_playwright
NOW = '2026-11-25T14:30:00Z'   # 日本時間 2026-11-25 23:30（世界時ではまだ 11/25、日本時間の翌日をまたぐ確かめに使う）
SHOT = os.environ.get('SORAMEMO_SHOT_DIR')
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
# 修行の帯・数字への animate の呼び出しを数える
SPY = """(() => { const o = Element.prototype.animate; window.__an = [];
  Element.prototype.animate = function(k, t){ if(this.closest && this.closest('.sgb-hero')) window.__an.push((this.className || this.tagName) + '|' + (this.parentElement && this.parentElement.className || '')); return o.call(this, k, t); }; })()"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2 if SHOT else 1)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.add_init_script(SPY)
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.clock.install(time=NOW)
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.clock.run_for(800)
        await pg.evaluate("() => { __fake.db.flights.length = 0; }")
        await pg.evaluate('__fake.login()'); await pg.clock.run_for(1200)
        await pg.evaluate("""() => { const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, k = A.find(a => a.iata === 'CTS').id;
          g.car = 'JAL'; g.plans = []; g.drafts = []; g.sync = null; SG_VIEW = 'road';
          S.flights = [{ id:'x1', from:h, to:o, dep:Date.UTC(2026, 9, 1, 1), km:1500, airline:'JL', fare:'JAL:Y_FLEX' }, { id:'x2', from:o, to:h, dep:Date.UTC(2026, 9, 3, 1), km:1500, airline:'JL', fare:'JAL:Y_FLEX' }, { id:'x3', from:h, to:k, dep:Date.UTC(2026, 10, 2, 1), km:800, airline:'JL', fare:'JAL:Y_FLEX' }];
          try{ localStorage.removeItem('soramemo.sgbar'); }catch(e){} SG_BAR_DAY = null; }""")
        async def open_main():
            await pg.evaluate("() => { window.__an = []; openShugyo('main'); }")
        async def calls():
            return await pg.evaluate("window.__an.slice()")
        # 1 その日はじめて：太い帯と大きな数字が動く
        await open_main(); await pg.clock.run_for(50)
        a = await calls(); print(a)
        bar = [x for x in a if x.startswith('I|') and 'sgb-bar' in x]
        check('1回目：太い帯が伸びる（1本だけ。1年の細い帯は動かさない）:', len(bar) == 1 and 'thin' not in bar[0])
        check('1回目：大きな数字が数え上がる:', any(x.startswith('sgb-act') for x in a))
        mid = await pg.evaluate("document.querySelector('#v-sg .sgb-act').textContent")
        final = await pg.evaluate("fmtKm(sgRoadData().cur.pts)")
        print('途中', mid, '最後', final)
        if SHOT:
            os.makedirs(SHOT, exist_ok=True); await pg.wait_for_timeout(150); await pg.clock.run_for(20); await pg.screenshot(path=os.path.join(SHOT, '1-mid-390.png'))
        await pg.wait_for_timeout(600); await pg.clock.run_for(600)
        t = await pg.evaluate("document.querySelector('#v-sg .sgb-act').textContent")
        check('1回目：数え上げのあとは今の数字:', t == final and final != '0')
        check('1回目：読み上げは今の数字:', await pg.evaluate("document.querySelector('#v-sg .sgb-act').getAttribute('aria-label')") == final)
        w = await pg.evaluate("document.querySelector('#v-sg .sgb-hero .sgb-bar:not(.thin) i').style.width")
        check('1回目：帯の長さは今の所のまま（' + w + '）:', w.endswith('%') and w != '0%')
        check('この端末に今日（日本時間）を覚える:', await pg.evaluate("localStorage.getItem('soramemo.sgbar')") == '2026-11-25')
        if SHOT:
            await pg.screenshot(path=os.path.join(SHOT, '2-done-390.png'))
            await pg.set_viewport_size({'width':375,'height':667}); await pg.clock.run_for(300); await pg.screenshot(path=os.path.join(SHOT, '3-done-667.png')); await pg.set_viewport_size({'width':390,'height':844})
        # 2 同じ日の2回目：開き直しても、見方を変えて戻っても、会社を切り替えても動かない
        await open_main(); await pg.clock.run_for(100)
        await pg.evaluate("() => { window.__an = []; SG_VIEW = 'months'; sgKeep(() => {}); SG_VIEW = 'road'; sgKeep(() => {}); }"); await pg.clock.run_for(100)
        check('同じ日の2回目：動かない:', await calls() == [])
        await pg.evaluate("() => { window.__an = []; localStorage.removeItem('soramemo.sgbar'); openShugyo('main'); }"); await pg.clock.run_for(100)
        check('覚える所が消えても、開いている間は1回だけ:', await calls() == [])
        # 3 日本時間の翌日（世界時ではまだ同じ日）：また1回だけ動く
        await pg.clock.run_for(40 * 60 * 1000)   # 日本時間 11/26 0:10（世界時 11/25 15:10）
        await open_main(); await pg.clock.run_for(50)
        check('日本時間の翌日：また動く:', len(await calls()) >= 2)
        check('翌日の日付を覚える:', await pg.evaluate("localStorage.getItem('soramemo.sgbar')") == '2026-11-26')
        await open_main(); await pg.clock.run_for(50)
        check('翌日の2回目：動かない:', await calls() == [])
        # 4 動きを減らす設定：動かさず、数字と帯は最初から今の所
        await pg.emulate_media(reduced_motion='reduce')
        await pg.clock.run_for(24 * 3600 * 1000)
        await open_main(); await pg.clock.run_for(50)
        check('動きを減らす設定：動かない:', await calls() == [])
        t = await pg.evaluate("document.querySelector('#v-sg .sgb-act').textContent")
        check('動きを減らす設定：数字は今のまま:', t == await pg.evaluate("fmtKm(sgRoadData().cur.pts)"))
        await pg.emulate_media(reduced_motion='no-preference')
        # 5 見方が1便ごと：帯がないので動かさず、日付も覚えない。道のりに戻ったときに1回
        await pg.clock.run_for(24 * 3600 * 1000); day = await pg.evaluate("sgToday()")
        await pg.evaluate("() => { window.__an = []; SG_VIEW = 'flights'; openShugyo('main'); }"); await pg.clock.run_for(50)
        check('1便ごと：動かさず、日付も覚えない:', await calls() == [] and await pg.evaluate("localStorage.getItem('soramemo.sgbar')") != day)
        await pg.evaluate("() => { SG_VIEW = 'road'; sgKeep(() => {}); }"); await pg.clock.run_for(50)
        check('そのあと道のりへ：その日の1回目として動く:', len(await calls()) >= 2)
        # 6 記録0の形：帯がないので何もしない
        await pg.clock.run_for(24 * 3600 * 1000)
        await pg.evaluate("() => { S.flights = []; }"); await open_main(); await pg.clock.run_for(50)
        check('記録0の形：何もしない（日付も覚えない）:', await calls() == [] and await pg.evaluate("localStorage.getItem('soramemo.sgbar')") != await pg.evaluate("sgToday()") and await pg.locator('#v-sg .sgb-zero').count() == 1)
        check('エラーなし:', not errs)
        await b.close()
asyncio.run(main())
print('errors', fails)
