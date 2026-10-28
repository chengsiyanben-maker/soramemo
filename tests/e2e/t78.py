import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運賃を座席と区分に分ける（便の記録・計画）、計画を作るの「自動で作る／手動で作る」と行く空港（寄る・だけで・行かない・まだ行っていない空港を優先）
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
D = (datetime.now(timezone.utc) + timedelta(hours=9) + timedelta(days=7)).strftime('%Y-%m-%d')
F = lambda no, dep, arr, t1, t2, ac=None: [no, dep, arr, t1, t2, 0, ac]
TT = [F('NH991', 'HND', 'OKA', '06:15', '09:00', '788'), F('NH461', 'HND', 'OKA', '07:30', '10:15'), F('NH469', 'HND', 'OKA', '13:15', '16:00', '772'), F('NH471', 'HND', 'OKA', '15:00', '17:45'),
      F('NH994', 'OKA', 'HND', '10:05', '12:20', '789'), F('NH468', 'OKA', 'HND', '16:20', '18:40'), F('NH472', 'OKA', 'HND', '16:35', '18:55'), F('NH470', 'OKA', 'HND', '16:50', '19:15', '789'),
      F('NH476', 'OKA', 'HND', '17:55', '20:20'), F('NH1763', 'OKA', 'ISG', '11:00', '12:00'), F('NH1765', 'OKA', 'ISG', '17:20', '18:20'), F('NH92', 'ISG', 'HND', '17:40', '20:50'),
      F('NH15', 'HND', 'ITM', '06:30', '07:40'), F('NH21', 'HND', 'ITM', '09:00', '10:10'), F('NH16', 'ITM', 'HND', '08:30', '09:40'), F('NH24', 'ITM', 'HND', '11:00', '12:10')]
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
        # 座席の分け方
        s = await pg.evaluate("[fareSeats('JAL'), fareSeats('ANA'), fareSeats('ANAO'), fareParts('JAL', 'Y_SAVER').name, fareParts('JAL', 'Y_SAVER').sub]")
        check('座席：JAL 普通席・クラスJ・ファースト、ANA エコノミー・プレミアムクラス、前の ANA プレミアムクラス・普通席:', s[0] == ['普通席', 'クラスJ', 'ファースト'] and s[1] == ['エコノミー', 'プレミアムクラス'] and sorted(s[2]) == sorted(['プレミアムクラス', '普通席']))
        check('区分の名前と中身（セイバー／スペシャルセイバー・往復セイバー）:', s[3] == 'セイバー' and s[4] == 'スペシャルセイバー・往復セイバー')
        # 便の記録：座席のピルと区分の札
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(300)
        await pg.evaluate("openFlight(fid(S.flights[0]))"); await pg.wait_for_timeout(300)
        await pg.select_option('#fAirline', 'JL'); await pg.dispatch_event('#fAirline', 'change'); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#fFareBox'); print('FARE', t.replace('\n', ' | ')[:300])
        check('座席のピルが3つ・はじめは普通席の区分だけ（選ばない＋4）:', await pg.locator('#fFareSeat [data-fseat]').count() == 3 and await pg.locator('#fFareBox .flist2 button').count() == 5 and 'クラスJ' in t and 'フレックス' in t and 'セイバー' in t and '75%' in t)
        await pg.click('#fFareSeat [data-fseat="クラスJ"]'); await pg.wait_for_timeout(200)
        check('クラスJを選ぶとクラスJの区分だけ:', await pg.evaluate("[...$('fFare').options].filter(o => o.value).every(o => o.value.startsWith('JAL:J_'))") and await pg.locator('#fFareSeat [data-fseat="クラスJ"][aria-pressed="true"]').count() == 1)
        await pg.locator('#fFareBox').screenshot(path=os.path.join(WORK, 't78_fare.png'))
        await pg.click('#dFlight [data-flv="JAL:J_SAVER"]'); await pg.wait_for_timeout(100)
        await pg.click('#fSave'); await pg.wait_for_timeout(600)
        check('保存する運賃の記号は今までどおり（JAL:J_SAVER）:', await pg.evaluate("__fake.db.flights[0].fare") == 'JAL:J_SAVER')
        await pg.evaluate("openFlight(fid(S.flights.find(f => f.fare === 'JAL:J_SAVER')))"); await pg.wait_for_timeout(300)
        check('記録した便を開くと、その座席（クラスJ）とセイバー:', await pg.locator('#fFareSeat [data-fseat="クラスJ"][aria-pressed="true"]').count() == 1 and await pg.evaluate("$('fFare').value") == 'JAL:J_SAVER')
        await pg.evaluate("$('dFlight').close()")
        # 計画を作る：運賃の座席を変える（同じ名前の区分を引き継ぐ）
        await pg.evaluate(f"sgGet().car = 'ANA'; sgGet().pq = {{ d:'{D}', home:'HND', start:'05:30', end:'22:00', mode:'pts', fare:{{ ANA:'ANA:E_FLEX' }} }}; openShugyo('find')"); await pg.wait_for_timeout(800)
        await pg.click('#v-sg [data-ftarget="#sgPqF"][data-fseat="プレミアムクラス"]'); await pg.wait_for_timeout(500)
        check('計画の運賃：プレミアムクラスに変えると同じ名前の区分（フレックス）:', await pg.evaluate("sgGet().pq.fare.ANA") == 'ANA:F_FLEX')
        await pg.click('#v-sg [data-ftarget="#sgPqF"][data-fseat="エコノミー"]'); await pg.wait_for_timeout(500)
        # 自動で作る・行く空港
        t = await pg.inner_text('#v-sg')
        check('はじめは「自動で作る」・おまかせ:', '自動で作る' in t and '手動で作る' in t and '行く空港' in t and await pg.evaluate("sgGet().pq.how") == 'auto' and await pg.evaluate("sgGet().pq.apmode") == 'any')
        any_n = await pg.evaluate("SG_FIND.R.total")
        await pg.click('#v-sg [data-sg-set="apmode"][data-v="via"]'); await pg.wait_for_timeout(300)
        await pg.select_option('#sgPqVia', 'ISG'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("SG_FIND.R.list.map(r => r.legs.map(f => f.arr))")
        check('この空港に寄る（石垣）：全部の行程が石垣を通る:', len(r) >= 1 and all('ISG' in x for x in r) and await pg.evaluate("SG_FIND.R.total") < any_n)
        check('見出しに「石垣を通る」:', '石垣を通る' in await pg.inner_text('#v-sg'))
        await pg.click('#v-sg [data-sg-apdel="via:ISG"]'); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-set="apmode"][data-v="only"]'); await pg.wait_for_timeout(300)
        await pg.select_option('#sgPqVia', 'OKA'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("SG_FIND.R.list.map(r => r.legs.map(f => [f.dep, f.arr]).flat())")
        check('この空港だけで（那覇）：羽田と那覇のあいだだけ:', len(r) >= 1 and all(set(x) <= {'HND', 'OKA'} for x in r))
        await pg.click('#v-sg [data-sg-set="apmode"][data-v="any"]'); await pg.wait_for_timeout(300)
        await pg.select_option('#sgPqAvoid', 'ITM'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("SG_FIND.R.list.map(r => r.legs.map(f => [f.dep, f.arr]).flat())")
        check('行かない空港（伊丹）：伊丹を通る行程は出ない:', len(r) >= 1 and all('ITM' not in x for x in r))
        await pg.click('#v-sg [data-sg-pfresh]'); await pg.wait_for_timeout(600)
        fr = await pg.evaluate("SG_FIND.R.list.map(r => r.fresh.length)")
        check('まだ行っていない空港を優先：新しい空港の多い順:', fr == sorted(fr, reverse=True) and await pg.evaluate("sgGet().pq.fresh") is True)
        await pg.screenshot(path=os.path.join(WORK, 't78_auto.png'), full_page=True)
        # 手動で作る
        await pg.click('#v-sg [data-sg-set="phow"][data-v="manual"]'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#v-sg')
        check('手動で作る：時刻表から1区間ずつ・区間を入れて計算する（行程の一覧は出さない）:', '時刻表から1区間ずつ組む' in t and '区間を入れて計算する' in t and 'この日に組める行程' not in t and '行く空港' not in t)
        await pg.click('#v-sg [data-sg-build]'); await pg.wait_for_timeout(600)
        check('手動から時刻表で組む画面へ:', await pg.evaluate("SG_PAGE") == 'build')
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data.pq")
        check('条件が保存される（作り方・行く空港）:', d['how'] == 'manual' and d['avoid'] == ['ITM'] and d['fresh'] is True)
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
