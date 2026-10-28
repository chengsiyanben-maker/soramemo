import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 計画：組む画面で区間ごとに金額を入れる（1ポイントあたり・案・予定・次からの目安）、空港を移る乗り継ぎ（羽田⇔成田 180分など）
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
D = (datetime.now(timezone.utc) + timedelta(hours=9) + timedelta(days=7)).strftime('%Y-%m-%d')
F = lambda no, dep, arr, t1, t2, ac=None: [no, dep, arr, t1, t2, 0, ac]
TT = [F('NH991', 'HND', 'OKA', '06:15', '09:00'), F('NH994', 'OKA', 'HND', '10:05', '12:20'),
      # 那覇→成田のあと、羽田から乗る（成田着 13:30 → 羽田発は 16:30 以降なら乗れる）
      F('NH2160', 'OKA', 'NRT', '10:30', '13:30'), F('NH463', 'HND', 'OKA', '16:00', '18:45'), F('NH465', 'HND', 'OKA', '16:40', '19:25'),
      F('NH476', 'OKA', 'HND', '19:30', '21:45'), F('NH478', 'OKA', 'HND', '20:10', '22:30'),
      F('NH469', 'HND', 'OKA', '13:15', '16:00'), F('NH472', 'OKA', 'HND', '16:35', '18:55')]
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
            data = {'date': D, 'operator': 'ANA', 'until': '2027-03-27', 'f': TT} if name == 'plan_timetable' and body.get('p_operator') == 'ANA' and body.get('p_date') == D else \
                   {'date': body.get('p_date'), 'operator': body.get('p_operator'), 'until': '2027-03-27', 'f': []} if name == 'plan_timetable' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(900)
        m = await pg.evaluate("[sgXfer('HND','NRT'), sgXfer('NRT','HND'), sgXfer('ITM','KIX'), sgXfer('ITM','UKB'), sgXfer('KIX','UKB'), sgXfer('CTS','OKD'), sgXfer('HND','ITM')]")
        check('空港を移る決まり（羽田⇔成田180・伊丹⇔関西180・伊丹⇔神戸170・関西⇔神戸190・新千歳⇔丘珠150）:', m == [180, 180, 180, 170, 190, 150, None])
        df = await pg.evaluate("[sgDefFare('ANA'), sgDefFare('JAL'), sgDefFare('ANA', Date.parse('2026-04-01')), (() => { sgGet().pq = { d:null }; return sgFareNow('ANA'); })()]")
        check('はじめの運賃は普通席（エコノミー）のフレックス:', df[:3] == ['ANA:E_FLEX', 'JAL:Y_FLEX', 'ANAO:FLEX'] and df[3] == 'ANA:E_FLEX')
        await pg.evaluate(f"sgGet().car = 'ANA'; sgGet().pq = {{ d:'{D}', home:'HND', start:'05:30', end:'23:00', mode:'count', fare:{{ ANA:'ANA:E_FLEX' }} }}; openShugyo('find')"); await pg.wait_for_timeout(900)
        legs = await pg.evaluate("SG_FIND.R.list.map(r => r.legs.map(f => f.no).join())")
        print('行程', legs)
        check('成田に着いて羽田から乗る行程が出る（成田13:30着 → 羽田16:40発。16:00発は180分に足りない）:', any('NH2160,NH465' in x for x in legs) and not any('NH2160,NH463' in x for x in legs))
        lab = await pg.evaluate("sgTripLabel(SG_FIND.R.list.find(r => r.legs.some(f => f.no === 'NH2160')).legs)")
        check('名前に移るところ（成田⇢羽田）:', '成田⇢羽田' in lab)
        # 組む：那覇から、成田へ行ったあと
        await pg.evaluate("sgOpenBuild([])"); await pg.wait_for_timeout(500)
        await pg.click('#v-sg [data-sg-add^="NH991|"]'); await pg.wait_for_timeout(200)
        await pg.click('#v-sg [data-sg-add^="NH2160|"]'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#v-sg'); print('BUILD', t[:900].replace('\n', ' | '))
        check('成田に着いたら、羽田へ移っても乗れる便を並べる（16:30以降）:', '（羽田へ移っても）' in t and await pg.locator('#v-sg [data-sg-add^="NH465|"]').count() == 1 and await pg.locator('#v-sg [data-sg-add^="NH463|"]').count() == 0)
        await pg.click('#v-sg [data-sg-add^="NH465|"]'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#v-sg')
        check('移って乗り継ぎ（決まり180分以上）と出す:', '成田から羽田へ移って乗り継ぎ 3時間10分（決まり 180分以上）' in t)
        await pg.click('#v-sg [data-sg-add^="NH478|"]'); await pg.wait_for_timeout(200)
        # 金額を入れる
        for i, v in enumerate(['28700', '31000', '28700']):
            await pg.fill(f'#v-sg [data-sg-bp="{i}"]', v); await pg.dispatch_event(f'#v-sg [data-sg-bp="{i}"]', 'change'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#v-sg .sgbar'); print('BAR', t.replace('\n', ' | '))
        check('3区間ぶんでは「金額は3区間ぶん」:', '金額は3区間ぶん' in t)
        await pg.fill('#v-sg [data-sg-bp="3"]', '27000'); await pg.dispatch_event('#v-sg [data-sg-bp="3"]', 'change'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#v-sg .sgbar'); pts = await pg.evaluate("(() => { const P = sgPtsOf('ANA', SG_BUILD.fare, SG_BUILD.d); return SG_BUILD.legs.reduce((x, f) => x + P(f), 0); })()")
        check(f'全部入れると合計と1PPあたり（115,400円・{round(115400 / pts, 1)}円）:', '115,400円' in t and f'{round(115400 / pts * 10) / 10}円' in t)
        check('入れた金額は次からの目安になる:', await pg.evaluate("sgGet().fp['ANA|' + sgAp('OKA') + '|' + sgAp('NRT') + '|E_FLEX']") == 31000)
        await pg.click('#v-sg [data-sg-savedraft]'); await pg.wait_for_timeout(400)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data.drafts[0]")
        check('案に区間の金額が残る:', [x.get('price') for x in d['legs']] == [28700, 31000, 28700, 27000])
        await pg.evaluate("sgGo('compare')"); await pg.wait_for_timeout(300)
        check('くらべる画面に合計の金額:', '115,400円' in await pg.inner_text('#v-sg'))
        await pg.click('#v-sg [data-sg-d2plan]'); await pg.wait_for_timeout(400)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data.plans")
        check('予定に入れると区間の金額も入る:', [x.get('price') for x in d] == [28700, 31000, 28700, 27000])
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
