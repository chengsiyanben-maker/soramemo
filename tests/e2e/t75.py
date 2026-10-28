import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 計画を作る：時刻表から行程を探す（乗り継ぎは各社の決まりを守る）・組む・案として残す・予定に入れる。計画は実績・予定にまぜない
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
        calls = []
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}'); calls.append(name)
            data = {'date': D, 'operator': 'ANA', 'until': '2027-03-27', 'f': TT} if name == 'plan_timetable' and body.get('p_operator') == 'ANA' and body.get('p_date') == D else \
                   {'date': body.get('p_date'), 'operator': body.get('p_operator'), 'until': '2027-03-27', 'f': []} if name == 'plan_timetable' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(900)
        # 乗り継ぎの決まり
        m = await pg.evaluate("[sgMct('ANA','ANA','HND'), sgMct('ANA','ANA','ITM'), sgMct('ANA','ANA','OKA'), sgMct('ANA','ANA','FUK'), sgMct('JAL','JAL','HND'), sgMct('JAL','JAL','OKA'), sgMct('JAL','JAL','CTS'), sgMct('ANA','JAL','NRT'), sgMct('JAL','ANA','FUK')]")
        check('乗り継ぎの決まり（ANA 羽田35・伊丹25・那覇30・ほか20、JAL 羽田30・那覇30・ほか20、またぐと成田50・ほか30）:', m == [35, 25, 30, 20, 30, 30, 20, 50, 30])
        before = await pg.evaluate("[sgYear().ANA.pts, sgFuture().length]")
        # 計画を作る（修行のタブ）
        await pg.evaluate(f"sgGet().car = 'ANA'; sgGet().pq = {{ d:'{D}', home:'HND', start:'05:30', end:'22:00', mode:'pts', fare:{{ ANA:'ANA:E_FLEX' }} }}; openShugyo('find')"); await pg.wait_for_timeout(800)
        t = await pg.inner_text('#v-sg'); print('FIND', t[:700].replace('\n', ' | '))
        check('計画を作るは時刻表から探す画面:', await pg.evaluate("SG_PAGE") == 'find' and 'この日に組める行程' in t and 'plan_timetable' in calls)
        check('いちばんたまるのは 羽田⇄那覇 2往復 +9,472:', '羽田⇄那覇 2往復' in t and '+9,472' in t and 'いちばんたまる' in t)
        legs = await pg.evaluate("SG_FIND.R.list[0].legs.map(f => f.no).join()")
        check('決まりより短い乗り継ぎ（那覇で20分の NH468）は組まない:', legs == 'NH991,NH994,NH469,NH472' and all('NH468' not in ','.join(x) for x in await pg.evaluate("SG_FIND.R.list.map(r => r.legs.map(f => f.no))")))
        check('羽田の乗り継ぎは35分以上（12:20着 → 13:15発）:', await pg.evaluate("SG_FIND.R.list.every(r => r.legs.slice(1).every((f, i) => f.d - r.legs[i].a >= sgMct('ANA', 'ANA', f.dep)))"))
        check('帰っていたい時刻までに羽田へ戻る:', await pg.evaluate("SG_FIND.R.list.every(r => r.legs[r.legs.length - 1].arr === 'HND' && r.back <= 22 * 60)"))
        await pg.locator('#v-sg #sgFindRes').screenshot(path=os.path.join(WORK, 't74_find.png'))
        # ねらいを回数に
        await pg.click('#v-sg [data-sg-set="pmode"][data-v="count"]'); await pg.wait_for_timeout(500)
        check('ねらいを変えると並びが変わる（回数）:', await pg.evaluate("sgGet().pq.mode") == 'count' and await pg.evaluate("SG_FIND.R.list[0].n") == await pg.evaluate("SG_FIND.R.maxN"))
        await pg.click('#v-sg [data-sg-set="pmode"][data-v="pts"]'); await pg.wait_for_timeout(500)
        # 行程を開いて組む
        await pg.click('#v-sg [data-sg-res="0"]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#v-sg')
        check('組む画面：4区間・乗り継ぎと決まり・羽田に戻る:', await pg.evaluate("SG_PAGE") == 'build' and '那覇で乗り継ぎ 1時間05分（ANA の決まり 30分以上）' in t and '羽田で乗り継ぎ 55分（ANA の決まり 35分以上）' in t and '18:55に羽田着' in t)
        await pg.click('#v-sg [data-sg-pop]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg'); print('BUILD', t[:900].replace('\n', ' | '))
        check('次の便は16:30から（那覇の決まり30分）:', '4区間目：那覇から' in t and '16:30から乗れます（決まり 30分）' in t)
        check('決まりより短い便は出さず、理由を一行で:', '1便は、乗り継ぎが決まり（30分）より短いので出していません' in t and '16:20発 NH 468' in t and await pg.locator('#v-sg [data-sg-add^="NH468|"]').count() == 0)
        check('その日に羽田へ帰れない便に印:', 'その日に羽田へ帰る便はありません' in t)
        await pg.click('#v-sg [data-sg-bf="home"]'); await pg.wait_for_timeout(300)
        check('羽田へ帰る便だけにできる:', await pg.locator('#v-sg [data-sg-add^="NH1765|"]').count() == 0 and await pg.locator('#v-sg [data-sg-add^="NH470|"]').count() == 1)
        await pg.click('#v-sg [data-sg-add^="NH470|"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg .sgbar')
        check('計画のかたまり：この行程の分 +9,472・19:15に羽田着:', '計画' in t and '+9,472' in t and '19:15に羽田着' in t)
        await pg.screenshot(path=os.path.join(WORK, 't74_build.png'), full_page=True)
        # 案として残す
        await pg.click('#v-sg [data-sg-savedraft]'); await pg.wait_for_timeout(400)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0] && __fake.db.shugyo_prefs[0].data")
        check('案として残すと保存される（予定には入らない）:', d and len(d.get('drafts', [])) == 1 and d['drafts'][0]['pts'] == 9472 and len(d.get('plans', [])) == 0)
        check('計画は実績・予定にまざらない:', await pg.evaluate("[sgYear().ANA.pts, sgFuture().length]") == before)
        # 予定に入れる
        await pg.click('#v-sg [data-sg-buildplan]'); await pg.wait_for_timeout(400)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data")
        check('予定に入れる：4便・便名と出発時刻つき:', len(d['plans']) == 4 and d['plans'][0]['no'] == 'NH991' and d['plans'][0]['hm'] == '6:15' and d['plans'][3]['no'] == 'NH470')
        # 残した案を開く
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(600)
        check('探す画面の下に残した案:', '残した案' in await pg.inner_text('#v-sg'))
        await pg.click('#v-sg [data-sg-draft]'); await pg.wait_for_timeout(500)
        check('残した案を開くと組む画面に戻る:', await pg.evaluate("SG_PAGE") == 'build' and await pg.evaluate("SG_BUILD.legs.length") == 4)
        # 時刻表の出ていない先の日
        await pg.evaluate("sgGet().pq.d = '2027-05-01'; sgGo('find')"); await pg.wait_for_timeout(600)
        check('時刻表がまだ出ていない日は、そう出す:', 'まだ出ていません' in await pg.inner_text('#v-sg'))
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
