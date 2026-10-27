import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# （「気軽に」の構成は画面を減らしたので、このテストは前の構成どおり、タブと見方をすべて出した表示で試す）
# 見方の切り替え：図鑑（5つ）・フライト（8つ）・運用（7つ・ものさしと空港をめくるはなくした）。選んだ見方は覚える
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 時刻は昼の12時（日本時間）に固定する（深夜は滑走路が1本になり、撮影地から見える機体が変わるため）
_d = datetime.now(timezone.utc); now = datetime(_d.year, _d.month, _d.day, 3, 0, tzinfo=timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
HRS = [{'h': h, 'flights': [0,0,0,0,0,2,30,48,52,50,44,46,48,44,42,46,48,50,52,48,40,30,20,6][h], 'late': (h % 5 == 0) * 2, 'cancel': 0, 'ref': 1} for h in range(24)]
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': HRS,
  'next_arr': [{'flight': 'JL500', 'other': 'ITM', 'sched': iso(5), 't': iso(5), 'aircraft': 'B738'}, {'flight': 'NH212', 'other': 'LHR', 'sched': iso(25), 't': iso(25), 'intl': True, 'aircraft': 'B789'}],
  'next_dep': [{'flight': 'NH106', 'other': 'LAX', 'sched': iso(15), 't': iso(15), 'intl': True, 'aircraft': 'B77W'}, {'flight': 'JL903', 'other': 'OKA', 'sched': iso(30), 'est': iso(48), 't': iso(48), 'aircraft': 'A359'}, {'flight': 'BC101', 'other': 'UKB', 'sched': iso(40), 't': iso(40), 'aircraft': 'B738'}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.layout', JSON.stringify({tabs:['home','book','log','ops','stats'], off:{home:[],book:[],log:[],ops:[],stats:['sgsum']}})); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            await r.fulfill(status=200, body=json.dumps(BOARD if name == 'airport_board' else []), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/airport-foreign**', lambda r: r.fulfill(status=200, body=json.dumps({'planes': []}), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); await pg.clock.set_fixed_time(now); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        # 図鑑
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(300)
        check('図鑑の見方が5つ:', await pg.locator('#bookViews [data-vw]').count() == 5)
        for v, sel in [('map', '#bkAlt .bkmap'), ('signs', '#bkAlt .bksign'), ('chron', '#bkAlt .bktl,#bkAlt .vwcard'), ('region', '#bkBars .bk-bar'), ('tiles', '#bkAlt .bkbento')]:
            await pg.click(f'[data-vw="book:{v}"]'); await pg.wait_for_timeout(200)
            check(f'図鑑 {v}:', await pg.locator(sel).count() > 0)
        await pg.click('[data-vw="book:map"]'); await pg.wait_for_timeout(200)
        await pg.locator('#bkAlt [data-bka]').first.click(); await pg.wait_for_timeout(400)
        check('地図の点から空港ページ:', await pg.evaluate("$('dAirport').open"))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # フライト
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(400)
        check('フライトの見方が9つ（修行を足した）:', await pg.locator('#logViews [data-vw]').count() == 9)
        for v, sel in [('board', '.lgboard'), ('cal', '.lgcal'), ('month', '.lgsum'), ('alt', '.lgalt'), ('text', '.lgtext'), ('route', '.lgroute'), ('map', '#flights .lgrows'), ('pass', '#flights .pass')]:
            await pg.click(f'[data-vw="log:{v}"]'); await pg.wait_for_timeout(250)
            check(f'フライト {v}:', await pg.locator(f'#flights {sel}' if not sel.startswith('#') else sel).count() > 0)
        await pg.click('[data-vw="log:route"]'); await pg.wait_for_timeout(200)
        await pg.locator('#flights [data-flight]').first.click(); await pg.wait_for_timeout(300)
        check('路線から便の画面:', await pg.evaluate("[...document.querySelectorAll('dialog')].some(d => d.open)"))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 運用
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1500)
        check('運用の見方が7つ（ものさし・空港をめくるはない）:', await pg.locator('#opsViews [data-vw]').count() == 7 and await pg.locator('[data-vw="ops:ruler"], [data-vw="ops:aps"]').count() == 0)
        check('はじめは滑走路:', await pg.is_visible('#opsInfo') and not await pg.is_visible('#opsBoard'))
        for v, sel in [('board', '#opsBoard'), ('day', '#opsDay'), ('strip', '#opsStrip'), ('photo', '#opsPhoto')]:
            await pg.click(f'[data-vw="ops:{v}"]'); await pg.wait_for_timeout(700)
            check(f'運用 {v}:', await pg.is_visible(sel) and not await pg.is_visible('#opsInfo'))
            await pg.screenshot(path=os.path.join(WORK, f't61_ops_{v}.png'))
        t = await pg.inner_text('#opsPhoto') if False else ''
        await pg.click('[data-vw="ops:photo"]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#opsPhoto')
        print('PHOTO', t.replace('\n',' | '))
        check('撮る人：大きな機体だけ:', 'NH106' in t and ('A359' in t or 'ほかの撮影地から見える機体' in t) and 'BC101' not in t)
        await pg.click('[data-vw="ops:strip"]'); await pg.wait_for_timeout(500)
        check('短冊に遅れ:', '18分遅れ' in (await pg.inner_text('#opsStrip')))
        # 覚えている
        await pg.click('[data-vw="ops:day"]'); await pg.wait_for_timeout(300)
        await pg.reload(); await pg.wait_for_timeout(800); await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        check('選んだ見方を覚える:', await pg.is_visible('#opsDay') and await pg.get_attribute('[data-vw="ops:day"]', 'aria-selected') == 'true')
        print('errors', errs + fails); await b.close()
asyncio.run(main())
