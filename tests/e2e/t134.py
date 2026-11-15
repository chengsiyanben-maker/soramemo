import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用予想の見せ方 案A（11/15 本人「OK」・design/rotation-view の2版）
#   飛んだ便は1行にたたむ →「ここから予想」の帯 →「予想です。保証しません」。確からしさは 高い・中くらい・低い と3つの点＋回数（高いは5回以上）
#   出さない決まり：① 出発の時刻が過ぎた便 ② いま飛んでいる便とそれより前の便（運航情報にあっても）。いまの便が古いときは「JL148 からの予想」
#   844 と 667 の高さで、開いたときに予想の1便目が見える
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc)
JST = timezone(timedelta(hours=9))
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)      # 今日の 0時（日本時間）
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat()
today = base.strftime('%Y-%m-%d')
NOW1 = at(14, 50)        # 場面1：JL258 で飛んでいる 14時50分
NOW2 = at(20, 50)        # 場面2：JL148 のあと、JL599 で飛んでいる 20時50分（記録はまだ JL148 まで）

HIST = [{'day': today, 'callsign': cs, 'dep': d, 'arr': a, 'first': iso(*f), 'last': iso(*l), 'type': 'B738'} for cs, d, a, f, l in [
    ('JAL141', 'HND', 'HIJ', (7, 40), (9, 0)), ('JAL142', 'HIJ', 'HND', (9, 50), (11, 10)), ('JAL259', 'HND', 'HIJ', (11, 55), (13, 14)),
    ('JAL258', 'HIJ', 'HND', (14, 18), (14, 49))]]
V2 = {'reg': 'JA339J', 'src': 'reg', 'method': 'learn_hi', 'estimate': True, 'type': 'B738',
      'known': {'callsign': 'JAL258', 'dep': 'HIJ', 'arr': 'HND', 'first': iso(14, 18), 'last': iso(14, 49)}, 'next': [
    {'callsign': 'JAL147', 'dep': 'HND', 'arr': 'AOJ', 'time': '16:15', 'seen': None, 'share': None, 'src': 'livery'},
    {'callsign': 'JAL148', 'dep': 'AOJ', 'arr': 'HND', 'time': '18:35', 'seen': 12, 'share': 0.92, 'src': 'learn'},
    {'callsign': 'JAL599', 'dep': 'HND', 'arr': 'CTS', 'time': '20:30', 'seen': 10, 'share': 0.7, 'src': 'learn'},
    {'callsign': 'JAL502', 'dep': 'CTS', 'arr': 'HND', 'time': '07:30', 'seen': 5, 'share': 0.45, 'src': 'base'}]}
# 場面2：記録はまだ JL148（19:36 着）まで。予想は JL599（いま飛んでいる）→ 明日の JL502
V2B = {'reg': 'JA339J', 'src': 'reg', 'method': 'learn_hi', 'estimate': True,
       'known': {'callsign': 'JAL148', 'dep': 'AOJ', 'arr': 'HND', 'first': iso(18, 35), 'last': iso(19, 36)}, 'next': [
    {'callsign': 'JAL599', 'dep': 'HND', 'arr': 'CTS', 'time': '20:30', 'seen': 10, 'share': 0.7, 'src': 'learn'},
    {'callsign': 'JAL502', 'dep': 'CTS', 'arr': 'HND', 'time': '07:30', 'seen': 5, 'share': 0.45, 'src': 'base'}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for H in (844, 667):
            c = await b.new_context(viewport={'width': 390, 'height': H}, timezone_id='Asia/Tokyo')
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
            await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
            mode = {'v2': V2, 'hist': HIST, 'board': []}
            async def rpc(r):
                name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
                out = {'reg_history': mode['hist'], 'predict_rotation': {'reg': body.get('p_reg'), 'known': None, 'next': []},
                       'predict_rotation_v2': mode['v2'], 'predict_rotation_reg': {'reg': body.get('p_reg'), 'known': None, 'next': [], 'src': 'reg'},
                       'livery_board': mode['board']}.get(name, [])
                await r.fulfill(status=200, body=json.dumps(out), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
            await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
            await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}))
            await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
            pg = await c.new_page(); await pg.clock.set_fixed_time(NOW1); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
            await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
            tag = f'[{H}]'

            # 1. 機体の1日（A1）：飛んだ3便は1行・いまの便は飛行中・帯・予想。開いたときに予想の1便目が見える
            await pg.evaluate("openPlane('JA339J')"); await pg.wait_for_timeout(900)
            t = await pg.inner_text('#dPlane'); flat = t.replace('\n', ' ')
            check(tag + ' 飛んだ便は1行にたたむ:', '今日飛んだ 3便' in flat and await pg.locator('#dPlane li.flown').first.is_hidden())
            check(tag + ' いまの便は飛行中で「14:18 発」:', await pg.locator('#dPlane li.now').count() == 1 and '14:18' in await pg.inner_text('#dPlane li.now') and '飛行中' in await pg.inner_text('#dPlane li.now'))
            check(tag + ' 帯と保証しない:', 'ここから予想' in flat and '予想です。保証しません' in flat)
            preds = await pg.locator('#dPlane li.p').all_inner_texts()
            check(tag + ' 予想は4便（いまの便は出さない）:', len(preds) == 4 and not any('JL258' in x for x in preds))
            check(tag + ' 運航情報は縁の札:', 'JL147' in preds[0] and '運航情報' in preds[0])
            check(tag + ' 高い（12回）:', '高い' in preds[1] and '12回見た' in preds[1])
            check(tag + ' 中くらい（7割）:', '中くらい' in preds[2])
            check(tag + ' 低い・明日の区切り:', '低い' in preds[3] and '明日' in flat)
            check(tag + ' 割合の数字は画面に出さない:', '%' not in flat.split('近づいたら')[0])
            check(tag + ' 運航情報の出典:', '運航情報の出典：公共交通オープンデータセンター' in flat)
            box = await pg.locator('#dPlane li.p').first.bounding_box()
            check(tag + ' 開いたときに予想の1便目が見える:', box is not None and box['y'] + box['height'] <= H)
            await pg.screenshot(path=os.path.join(WORK, f't134_plane_{H}.png'))
            # 飛んだ便を開ける
            await pg.click('#dPlane [data-rot-fold]'); await pg.wait_for_timeout(100)
            check(tag + ' たたんだ行を開くと飛んだ便:', await pg.locator('#dPlane li.flown').first.is_visible() and await pg.get_attribute('#dPlane [data-rot-fold]', 'aria-expanded') == 'true')
            # 確からしさとは（A5）
            await pg.click('#dPlane [data-rot-conf]'); await pg.wait_for_timeout(150)
            s = await pg.inner_text('#dRotConf')
            check(tag + ' 確からしさのシート:', await pg.locator('#dRotConf').is_visible() and '5回以上' in s and '4割より少ない便は出しません' in s and '運航情報' in s and '保証しません' in s)
            if H == 844: await pg.screenshot(path=os.path.join(WORK, 't134_conf.png'))
            await pg.click('#dRotConf .btn1'); await pg.wait_for_timeout(100)
            check(tag + ' シートを閉じる:', not await pg.locator('#dRotConf').is_visible())
            await pg.evaluate("$('dPlane').close()")

            # 2. 出発の時刻が過ぎた便は出さない（① ）：16:15 の JL147 を 16:30 に見る
            await pg.clock.set_fixed_time(at(16, 30))
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL258', dep:'HIJ', arr:'HND', eta:null } }, {})", V2)
            check(tag + ' 過ぎた便を出さない:', 'JL147' not in h and 'JL148' in h)

            # 3. いまの便が古いとき（②・A6）：記録は JL148 まで、いま JL599 で飛んでいる
            await pg.clock.set_fixed_time(NOW2)
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL599', dep:'HND', arr:'CTS' } }, { reg:'JA339J', limit:2 })", V2B)
            body = h.split('ここから予想')[1].split('</ul>')[0]
            check(tag + ' いま飛んでいる便は予想に出さない:', 'class="p"' in body and 'いま飛んでいるので予想に出しません' in body and body.count('JL599') == 1)
            check(tag + ' 予想は明日の JL502 から:', 'JL502' in body and '明日' in body)
            check(tag + ' JL148 からの予想と書く:', 'いま飛んでいる JL599 が記録に入るまで' in h and 'JL148 からの予想を出しています' in h and '記録に入っている最後の便' in h)
            # 運航情報にあっても、いまの便より前の便は出さない
            v2c = json.loads(json.dumps(V2B)); v2c['next'].insert(0, {'callsign': 'JAL147', 'dep': 'HND', 'arr': 'AOJ', 'time': '19:50', 'seen': None, 'share': None, 'src': 'livery'})
            v2c['next'][1]['time'] = '20:30'
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL599', dep:'HND', arr:'CTS' } }, {})", v2c)
            check(tag + ' 運航情報の便でも、いまの便より前は出さない:', 'JL147' not in h)

            # 4. 確からしさの段：3回中3回は中くらい、5回以上で8割以上は高い、4割より少ない便とその先は出さない
            lv = await pg.evaluate("[predLevel({share:1, cnt:3}), predLevel({share:.85, cnt:5}), predLevel({share:.65, cnt:9}), predLevel({share:.45, cnt:9}), predLevel({plan:true})]")
            check(tag + ' 段の決まり:', lv == [2, 3, 2, 1, 0])
            v2d = json.loads(json.dumps(V2)); v2d['next'][1]['share'] = 0.3
            st = await pg.evaluate("d => predSteps(d).map(s => s.fl)", v2d)
            check(tag + ' 4割より少ない便とその先は出さない:', st == ['JL147'])
            # 予想が出ないとき
            h = await pg.evaluate("predictionHTML({ reg:'JA1', known:null, next:[], src:'reg' }, {}, {})")
            check(tag + ' 今日まだ見えていない:', '今日この機体はまだ見えていません' in h)
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", dict(V2B, next=[]))
            check(tag + ' 記録が足りない:', 'まだ記録が足りず予想できません' in h)

            # 5. 特別塗装機のくわしく（A4）：今日の足あと → この先（予想）。開いたときに予想の1便目が見える
            await pg.clock.set_fixed_time(NOW1)
            mode['v2'] = dict(V2, reg='JA894A', known=dict(V2['known'], callsign='ANA258'), next=[dict(n, callsign=n['callsign'].replace('JAL', 'ANA')) for n in V2['next']])
            mode['board'] = [{'reg': 'JA894A', 'now': {'at': iso(14, 49), 'lat': 34.6, 'lon': 135.2, 'alt_ft': 24000, 'callsign': 'ANA258', 'iata': None, 'phase': None, 'kt': 440},
                              'today': [{'cs': cs, 'dep': d, 'arr': a, 'first': iso(*f), 'last': iso(*l)} for cs, d, a, f, l in
                                        [('ANA141', 'HND', 'HIJ', (7, 40), (9, 0)), ('ANA142', 'HIJ', 'HND', (9, 50), (11, 10)), ('ANA259', 'HND', 'HIJ', (11, 55), (13, 14)), ('ANA258', 'HIJ', 'HND', (14, 18), (14, 49))]],
                              'last_day': today, 'arr30': {'HND': 20}}]
            await pg.evaluate("openSpecial('JA894A')"); await pg.wait_for_timeout(1200)
            t = (await pg.inner_text('#dSpecial')).replace('\n', ' ')
            check(tag + ' 足あとは1行にたたむ:', '今日飛んだ 3便' in t and await pg.locator('#dSpecial li.now').count() == 1)
            check(tag + ' この先（予想）:', 'この先（予想）' in t and '予想です。保証しません' in t and await pg.locator('#dSpecial li.p').count() == 4)
            check(tag + ' いまの便は予想に出さない（塗装機）:', not any('NH258' in x for x in await pg.locator('#dSpecial li.p').all_inner_texts()))
            box = await pg.locator('#dSpecial li.p').first.bounding_box()
            check(tag + ' 塗装機のくわしくで予想の1便目が見える:', box is not None and box['y'] + box['height'] <= H)
            await pg.screenshot(path=os.path.join(WORK, f't134_spb_{H}.png'))
            await pg.evaluate("$('dSpecial').close()")
            await c.close()
            check(tag + ' ページのエラーなし:', not errs)
            if errs: print(errs)
        await b.close()
    print('errors', fails)
asyncio.run(main())
