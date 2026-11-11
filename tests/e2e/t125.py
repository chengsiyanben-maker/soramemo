import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行の作り直し（11/11・画面案 design/shugyo-book 3版）：見方は道のり・1便ごと・月ごとの3つ。
# 道のり（大きな数字・1年の何割・2つの道・JGC は「記録分」と今の数を入れる形・入れたら届くか（推定））、1便の内訳、月ごとの年末の残り（回数は1行）、見方を選ぶの ON／OFF
import asyncio, json, re
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); NOW = datetime.now(JST); Y = NOW.year
J = lambda n: (NOW + timedelta(days=n)).strftime('%Y-%m-%d')
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        RT = [{'flight': 'JL903', 'std': '2026-01-01T00:00:00Z', 'cancelled': False}, {'flight': 'JL905', 'std': '2026-01-01T01:00:00Z', 'cancelled': True}]
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            await r.fulfill(status=200, body=json.dumps(RT if name == 'route_today' else []), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        # 記録：今年の JAL 羽田⇄那覇 セイバー 4便（1便 1,676 FOP）。1便目は前の年（Life Status だけに入る）
        await pg.evaluate(f"""() => {{ const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, F = __fake.db.flights; F.length = 0;
          const ts = [Date.UTC({Y - 1}, 5, 1, 1), Date.UTC({Y}, 0, 10, 1), Date.UTC({Y}, 0, 11, 1), Date.UTC({Y}, 1, 3, 1), Date.now() - 3 * 864e5];
          ts.forEach((t, i) => F.push({{ id:200 + i, from_airport:i % 2 ? h : o, to_airport:i % 2 ? o : h, airline:'JL', flight_no:'JL90' + i, fare:'JAL:Y_SAVER', price:null, status:'verified', distance_km:1500,
            dep_at:new Date(t).toISOString(), arr_at:new Date(t + 9e6).toISOString() }})); }}""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.evaluate(f"""() => {{ const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.car = 'JAL'; g.goal.JAL = 'crystal';
          g.plans = [{{ id:'p1', d:'{J(5)}', hm:'07:00', from:h, to:o, car:'JAL', fare:'JAL:Y_SAVER', no:'JL903' }}, {{ id:'p2', d:'{J(6)}', hm:'18:00', from:o, to:h, car:'JAL', fare:'JAL:Y_SAVER', no:'JL918' }}];
          g.drafts = []; }}""")
        await pg.evaluate("openShugyo('main')"); await pg.wait_for_timeout(700)
        t = await pg.inner_text('#v-sg'); print('E1', t[:900].replace('\n', ' | '))
        pts = await pg.evaluate("sgYear().JAL.pts"); n = await pg.evaluate("sgYear().JAL.n")
        check('実績は今年の記録した便だけ（4便・6,704 FOP）:', pts == 6704 and n == 4)
        check('見方のピルは 道のり・1便ごと・月ごと:', await pg.evaluate("[...document.querySelectorAll('#v-sg [data-sg-view]')].map(b => b.textContent).join()") == '道のり,1便ごと,月ごと')
        check('題の行：修行・ANA｜JAL・会員情報:', '修行' in t and '会員情報' in t and await pg.locator('#v-sg .sgb-hd [data-sg-set="car"]').count() == 2)
        check('大きな数字と目標・1年の何割:', '6,704' in t and '目標 クリスタル' in t and re.search(r'1年 \d+%（今日 \d+/\d+）', t) is not None and 'ポイント 22%' in t)
        check('2つの道は「あと ○」（FOP だけで あと 23,296・30回のうち あと 26回）:', re.search(r'あと\s*23,296', t) is not None and re.search(r'あと\s*26\s*回', t) is not None)
        check('JGC は「記録分」・記録した便から（前の年も入れて 5便×5＝25）:', '記録分' in t and '25' in t and '前の年の搭乗や JAL カードの分は入っていません' in t and await pg.evaluate("sgLS().v") == 25)
        check('入れたら届くか：予定は実績と分けて（推定）:', '予定の2便に乗ると' in t and '＋3,352' in t and '推定' in t and 'あと 19,944 FOP・あと 24回' in t)
        check('結論の一文は推定:', re.search(r'1年の \d+% が過ぎて、ポイントは 22%。予定の便に乗っても届きません（推定）', t) is not None)
        await pg.wait_for_timeout(500)
        check('次に乗る便：この路線の今日（2便・欠航 1便）:', '2便・欠航 1便' in await pg.inner_text('#sgNxRt'))
        await pg.screenshot(path=os.path.join(WORK, 't125_road.png'), full_page=True)
        # Life Status：今の数を入れる（入れた日より前の便は二重に数えない）
        await pg.click('#v-sg [data-sg-lsedit="1"]'); await pg.wait_for_timeout(200)
        d0 = J(-10); await pg.fill('#sgLsV', '1240'); await pg.fill('#sgLsD', d0)
        await pg.click('#v-sg [data-sg-lssave]'); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#v-sg')
        sv = await pg.evaluate("__fake.db.shugyo_prefs[0].data.lsIn")
        check('今の数を入れると保存（数と日）:', sv == {'v': 1240, 'at': d0})
        check('入れた数＋そのあとの便だけ（1便 5 → 1,245）・入れた日を出す:', await pg.evaluate("sgLS().v") == 1245 and f'{int(d0[5:7])}/{int(d0[8:])} に入れた 1,240 ＋ そのあとの便 1便 5' in t and '1,245' in t and '記録分' not in t)
        await pg.click('#v-sg [data-sg-lsedit="1"]'); await pg.wait_for_timeout(200)
        await pg.click('#v-sg [data-sg-lsclear]'); await pg.wait_for_timeout(300)
        check('入れた数を消すと記録した便だけに戻る:', await pg.evaluate("sgLS().v") == 25 and 'lsIn' not in await pg.evaluate("__fake.db.shugyo_prefs[0].data"))
        # 1便ごと → 1便の内訳
        await pg.click('#v-sg [data-sg-view="flights"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg')
        check('1便ごと：今年の4便（前の年は入らない）:', await pg.locator('#v-sg [data-sg-fl]').count() == 4 and '＋1,676' in t)
        await pg.locator('#v-sg [data-sg-fl]').first.click(); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg'); print('E2', t[:500].replace('\n', ' | '))
        check('内訳：984 × 75% → 738 × 2 → 1,476 ＋ 200 ＝ 1,676:', all(x in t for x in ['区間マイル', '984', '積算率 75%', '738', '1,476', '搭乗ボーナス', '200', '1,676']) and await pg.evaluate("SG_PAGE") == 'flight')
        check('内訳：回数 ＋1・JGC ＋5・運賃を選び直す:', '＋1' in t and '＋5' in t and await pg.locator('#v-sg [data-flight]').count() == 1)
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(300)
        check('戻ると1便ごとのまま:', await pg.evaluate("SG_PAGE") == 'main' and await pg.locator('#v-sg [data-sg-fl]').count() == 4)
        # 月ごと：12月31日の残り（回数は1行）・月末の残り・路線ごと
        await pg.click('#v-sg [data-sg-view="months"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg'); print('E3', t[:700].replace('\n', ' | '))
        check('年末の残り：実績のまま 23,296・予定まで 19,944（推定）:', '12月31日の残り（クリスタルまで・推定）' in t and '23,296' in t and '19,944' in t)
        rows = await pg.evaluate("[...document.querySelectorAll('#v-sg .sgb-end small.c')].map(x => x.textContent)")
        check('回数の残りは1行（回数 あと 26回 → 24回）:', rows == ['回数 あと 26回', '回数 あと 24回'])
        check('月末の残り：1月末 26,648（ひいた 3,352）・予定は別のカード:', '1月末' in t and '26,648' in t and 'ひいた 3,352' in t and await pg.locator('#v-sg .sgb-mc.p').count() >= 1)
        check('路線ごと：羽田 ⇄ 那覇 4回:', '羽田 ⇄ 那覇' in t and '4回' in t and '6,704' in t)
        await pg.screenshot(path=os.path.join(WORK, 't125_months.png'), full_page=True)
        # 見方を選ぶ：JGC を OFF → 道のりから消える。見方を OFF → ピルから消える。最後の1つは消せない
        await pg.click('#v-sg [data-sg-go="views"]'); await pg.wait_for_timeout(300)
        check('見方を選ぶ：はじめは全部 ON（JGC も ON）:', await pg.evaluate("[...document.querySelectorAll('#v-sg [data-sg-sw]')].every(b => b.getAttribute('aria-checked') === 'true')"))
        await pg.click('#v-sg [data-sg-sw="show.jgc"]'); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-sw="views.flights"]'); await pg.wait_for_timeout(300)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data")
        check('ON／OFF はサーバーに保存:', d['show']['jgc'] is False and d['views']['flights'] is False)
        await pg.click('#v-sg [data-sg-sw="views.months"]'); await pg.wait_for_timeout(200)
        await pg.click('#v-sg [data-sg-sw="views.road"]'); await pg.wait_for_timeout(200)
        check('見方は1つは残る:', await pg.evaluate("Object.values(sgShow().views).filter(Boolean).length") == 1)
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg')
        check('JGC を OFF にすると道のりに出ない・ピルは道のりだけ:', 'Life Status' not in t and await pg.evaluate("[...document.querySelectorAll('#v-sg [data-sg-view]')].map(b => b.textContent).join()") == '道のり')
        # 予定も計画もない人：一文と「計画を作る」
        await pg.evaluate("(() => { const g = sgGet(); g.plans = []; g.drafts = []; sgKeep(() => {}); })()"); await pg.wait_for_timeout(200)
        t = await pg.inner_text('#v-sg')
        check('空の人：一文と計画を作るだけ（予定の行は出ない）:', '乗る予定の便や、修行の計画を入れると' in t and '計画を作る' in t and '便に乗ると' not in t and 'ペース' in t)
        # ANA：道は1つ（PP）、JGC は出ない
        await pg.click('#v-sg [data-sg-set="car"][data-v="ANA"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg')
        check('ANA：PP の道1つ・JGC は出ない:', 'プレミアムポイントで' in t and 'Life Status' not in t and '30回' not in t)
        # 夜：金を使わない（予定のカードは点線の縁）
        await pg.evaluate("(() => { const g = sgGet(); g.car = 'JAL'; g.plans = [{ id:'p1', d:'" + J(5) + "', hm:'07:00', from:A.find(a => a.iata === 'HND').id, to:A.find(a => a.iata === 'OKA').id, car:'JAL', fare:'JAL:Y_SAVER', no:'JL903' }]; document.documentElement.dataset.night = 'on'; sgKeep(() => {}); })()"); await pg.wait_for_timeout(300)
        st = await pg.evaluate("(() => { const e = document.querySelector('#v-sg .sgb-next'), s = getComputedStyle(e); return [s.borderTopStyle, s.backgroundColor]; })()")
        check('夜：次に乗る便は点線の縁・金の地ではない:', st[0] == 'dashed' and st[1] != 'rgb(251, 246, 236)')
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
