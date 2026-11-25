import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行：Gemini の案の小さい3つ（11/26 PM・shugyo-gemini-small）
#   2：記録した便1つで外す予定は1つだけ（同じ日に同じ区間を2回乗る予定で、1便だけ記録しても残りの予定は見込みに残る）
#   3：根拠の1行（区間マイル × 積算率 × 2 ＋ 搭乗ボーナス ＝ ポイント（目安））を、次に乗る便・予定と計画・路線を入れて計算する に出す
#   9：月ごとの「12月31日の残り」に、今年あと何日と、届くための月あたり（1か月以内は1週間あたり）の目安
import asyncio, math
from datetime import datetime, timedelta, timezone, date
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); NOW = datetime.now(JST); Y = NOW.year
J = lambda n: (NOW + timedelta(days=n)).strftime('%Y-%m-%d')
SHOT = os.environ.get('SORAMEMO_SHOT')
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2 if SHOT else 1)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        shot = lambda n, **k: pg.screenshot(path=os.path.join(SHOT or WORK, n), **k)
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        # 記録：今年1月の JAL 羽田⇄那覇 2便（セイバー 1,676×2）＋ 2日前の羽田→伊丹 1便 ＋ 今日の羽田→伊丹 1便（どちらもセイバー）
        await pg.evaluate(f"""() => {{ const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, i = A.find(a => a.iata === 'ITM').id, F = __fake.db.flights; F.length = 0;
          const L = [[Date.UTC({Y}, 0, 10, 1), h, o], [Date.UTC({Y}, 0, 11, 1), o, h], [Date.parse('{J(-2)}T07:30:00+09:00'), h, i], [Date.parse('{J(0)}T00:01:00+09:00'), h, i]];
          L.forEach(([t, f, to], k) => F.push({{ id:401 + k, from_airport:f, to_airport:to, airline:'JL', flight_no:'JL10' + k, fare:'JAL:Y_SAVER', price:null, status:'verified', distance_km:500,
            dep_at:new Date(t).toISOString(), arr_at:new Date(t + 36e5).toISOString() }})); }}""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        # 予定：今日の羽田→伊丹を2便（07:00・15:00）、2日前の羽田→伊丹を2便、5日後の羽田→那覇を1便
        await pg.evaluate(f"""() => {{ const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, i = A.find(a => a.iata === 'ITM').id; g.car = 'JAL'; g.goal.JAL = 'crystal'; g.drafts = [];
          const P = (id, d, hm, f, t) => ({{ id, d, hm, from:f, to:t, car:'JAL', fare:'JAL:Y_SAVER', no:null }});
          g.plans = [P('t2', '{J(0)}', '15:00', h, i), P('t1', '{J(0)}', '07:00', h, i), P('y1', '{J(-2)}', '07:00', h, i), P('y2', '{J(-2)}', '19:00', h, i), P('f1', '{J(5)}', '08:00', h, o)]; }}""")
        await pg.evaluate("openShugyo('main')"); await pg.wait_for_timeout(700)
        # ---- 2：二重に数えない・数えすぎて消さない ----
        fut = await pg.evaluate("sgFuture().map(p => p.id)")
        check('今日の予定2便のうち、記録した1便ぶん（早い 07:00）だけ外れ、15:00 は見込みに残る:', fut == ['t2', 'f1'])
        past = await pg.evaluate("sgPast().map(x => x.p.id + ':' + x.done)")
        check('2日前の予定2便も、記録1便ぶん（07:00）だけ「実績に入っています」:', past == ['y1:true', 'y2:false'])
        P = await pg.evaluate("(() => { const Y = sgYear(); return [Y.JAL.n, sgPlanSum('JAL', Y).n]; })()")
        check('実績 4便・予定 2便（実績と予定で同じ便を二重に数えない）:', P == [4, 2])
        t = await pg.inner_text('#v-sg')
        check('確認の札：記録あり1つと「乗った」ボタン1つ:', t.count('記録あり・実績に入っています') == 1 and await pg.locator('#v-sg [data-sg-cf^="flew:"]').count() == 1)
        # ---- 3：根拠の1行 ----
        why = await pg.evaluate("(() => { const L = sgLeg('JAL', A.find(a => a.iata === 'HND').id, A.find(a => a.iata === 'ITM').id, 'JAL:Y_SAVER', Date.now()); return [L.mi, L.pts]; })()")
        mi, pts = why; exp = f"根拠 {mi:,}マイル × 75% × 2 ＋ 200 ＝ {pts:,}（目安）"
        check(f'式の数がポイントと合う（{mi}×75%×2＋200＝{pts}）:', round(mi * 0.75) * 2 + 200 == pts)
        nx = await pg.inner_text('#v-sg .sgb-next')
        check('次に乗る便（今日 15:00 の羽田→伊丹）に根拠の1行:', exp in nx)
        await pg.locator('#v-sg .sgb-next').screenshot(path=os.path.join(SHOT or WORK, 't206_road_next.png'))
        await pg.evaluate("sgGo('plan')"); await pg.wait_for_timeout(400)
        n = await pg.locator('#v-sg .sgpd .sgwhy').count(); t = await pg.inner_text('#v-sg')
        check('予定と計画：予定2便それぞれに根拠の1行（那覇は 984マイル ＝ 1,676）:', n == 2 and exp in t and '根拠 984マイル × 75% × 2 ＋ 200 ＝ 1,676（目安）' in t)
        await pg.locator('#v-sg .sgpd').first.screenshot(path=os.path.join(SHOT or WORK, 't206_plan.png'))
        await pg.evaluate("sgGo('quick')"); await pg.wait_for_timeout(400)
        q = await pg.inner_text('#v-sg .sg-res .sgwhy')
        print('計算', q)
        check('路線を入れて計算する：結果に根拠の1行（目安）:', q.startswith('FOP の根拠 984マイル × ') and q.endswith('（目安）'))
        await pg.click('#v-sg [data-sg-set="qside"][data-v="round"]')
        await pg.wait_for_timeout(300)
        check('往復では「片道。往復はこの2倍」と書く:', '（片道。往復はこの2倍）' in await pg.inner_text('#v-sg .sg-res .sgwhy'))
        await pg.locator('#v-sg .sg-res').screenshot(path=os.path.join(SHOT or WORK, 't206_quick.png'))
        # ---- 9：今年あと何日・月あたりの目安 ----
        await pg.evaluate("sgGo('main')"); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-view="months"]'); await pg.wait_for_timeout(400)
        days = (date(Y, 12, 31) - NOW.date()).days + 1
        cur = await pg.evaluate("sgYear().JAL.pts"); left = 30000 - cur
        if days > 31: per, v = '月あたり', math.ceil(left / (days / (365.25 / 12)) / 100) * 100
        elif days > 7: per, v = '1週間あたり', math.ceil(left / (days / 7) / 100) * 100
        else: per, v = '', left
        pc = await pg.inner_text('#v-sg .sgb-end .sgb-pace')
        print('目安', pc)
        check(f'今年あと {days}日・{per or "あと"} {v:,} FOP（目安）:', f'今年あと {days}日' in pc and f'{v:,} FOP' in pc and (per in pc) and pc.endswith('（目安）') and 'FOP だけで' in pc)
        await pg.evaluate("document.querySelector('#v-sg .sgb-end').scrollIntoView({ block:'start' })"); await pg.locator('#v-sg .sgb-end').screenshot(path=os.path.join(SHOT or WORK, 't206_months_end.png'))
        # 届いていると目安は出さない・別の年は出さない
        check('別の年は出さない:', await pg.evaluate(f"sgPace(1000, {Y + 1})") is None)
        await pg.evaluate("(() => { sgGet().goal.JAL = 'crystal'; sgGet().sync = { JAL:{ pts:31000, n:null, at:sgToday(), use:true, recAt:0 } }; sgKeep(() => {}); })()"); await pg.wait_for_timeout(300)
        check('届いているときは目安の行なし:', await pg.locator('#v-sg .sgb-end .sgb-pace').count() == 0)
        # ANA：「FOP だけで」は付けない・単位は PP
        await pg.evaluate("(() => { const g = sgGet(); g.sync = {}; g.car = 'ANA'; sgKeep(() => {}); })()"); await pg.wait_for_timeout(300)
        pa = await pg.inner_text('#v-sg .sgb-end .sgb-pace') if await pg.locator('#v-sg .sgb-end .sgb-pace').count() else ''
        check('ANA：PP の目安・「FOP だけで」なし:', ' PP' in pa and 'FOP' not in pa)
        print('errors', errs); await b.close()
        if errs: fails.append('errors')
    print('fails', fails); print('errors', fails if fails else [])
    sys.exit(1 if fails else 0)
asyncio.run(main())
