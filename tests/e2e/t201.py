import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用予想の小さな足し（11/26 PM の指示・Gemini 22往復目の考え方を機体の運用予想に当てはめたもの。docs/pm/yosoku-gemini-1126.md）
#   1 確からしさの回数：数字を太く。データ担当が seen_of（分母・重みなし）を返したら「12回中11回」、返さないうちは「11回見た」。時刻表の予想は回数を出さない
#   3・8 根拠の1行：どの便から（記録の最後の時刻）・前の何日の記録から（learn_hi は42日、ほかは60日）・先の便ほど外れやすい
#   4 外れたとき：いま飛んでいる便が予想の1便目と違う（同じころ・前後90分）ときは、隠さず「当時の予想」と並べ、この先は外れやすいと書く
#   どれも「予想です。保証しません」は今のまま。偽のサーバー（fake_sb.js）を使い、本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc)
JST = timezone(timedelta(hours=9))
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat()
ms = lambda h, m: int(at(h, m).timestamp() * 1000)
today = base.strftime('%Y-%m-%d')
V2 = {'reg': 'JA339J', 'src': 'reg', 'method': 'learn_hi', 'estimate': True, 'type': 'B738',
      'known': {'callsign': 'JAL148', 'dep': 'AOJ', 'arr': 'HND', 'first': iso(18, 35), 'last': iso(19, 36)}, 'next': [
    {'callsign': 'JAL599', 'dep': 'HND', 'arr': 'CTS', 'time': '20:30', 'seen': 12, 'share': 0.92, 'src': 'learn'},
    {'callsign': 'JAL502', 'dep': 'CTS', 'arr': 'HND', 'time': '07:30', 'seen': 5, 'share': 0.62, 'src': 'learn'}]}
HIST = [{'day': today, 'callsign': cs, 'dep': d, 'arr': a, 'first': iso(*f), 'last': iso(*l), 'type': 'B738'} for cs, d, a, f, l in [
    ('JAL147', 'HND', 'AOJ', (16, 15), (17, 30)), ('JAL148', 'AOJ', 'HND', (18, 35), (19, 36)), ('JAL517', 'HND', 'CTS', (20, 40), (20, 49))]]
fails = []
def check(label, ok, detail=''):
    print(label, ok, detail if not ok else '')
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for H in (844, 667):
            c = await b.new_context(viewport={'width': 390, 'height': H}, timezone_id='Asia/Tokyo')
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
            await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
            mode = {'v2': V2, 'hist': HIST}
            async def rpc(r):
                name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
                out = {'reg_history': mode['hist'], 'predict_rotation': {'reg': body.get('p_reg'), 'known': None, 'next': []},
                       'predict_rotation_v2': mode['v2'], 'predict_rotation_reg': {'reg': body.get('p_reg'), 'known': None, 'next': [], 'src': 'reg'},
                       'livery_board': []}.get(name, [])
                await r.fulfill(status=200, body=json.dumps(out), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
            await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
            await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}))
            await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
            pg = await c.new_page(); await pg.clock.set_fixed_time(at(19, 50)); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
            await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
            tag = f'[{H}]'

            # 1 回数：数字は太く、分母がないうちは「12回見た」、seen_of があれば「14回中12回」
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", V2)
            check(tag + ' 回数の数字は太い:', '<b>12</b>回見た' in h, h[:300])
            v = json.loads(json.dumps(V2)); v['next'][0]['seen_of'] = 14; v['next'][1]['seen_of'] = 3
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", v)
            check(tag + ' 分母があれば「14回中12回」:', '14回中<b>12</b>回' in h and 'aria-label="確からしさ 高い・14回中12回"' in h)
            check(tag + ' 分母が回数より小さいときは使わない:', '<b>5</b>回見た' in h and '3回中' not in h)
            tt = {'reg': 'JA1', 'src': 'odpt', 'known': {'flight': 'JL148', 'dep': 'AOJ', 'arr': 'HND', 'std': iso(18, 35), 'sta': iso(19, 36), 'phase': 'landed'},
                  'next': [{'flight': 'JL599', 'dep': 'HND', 'arr': 'CTS', 'std': iso(20, 30), 'seen': 20, 'of': 22, 'share': 0.9, 'seen_of': 30}]}
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", tt)
            check(tag + ' 時刻表の予想は回数を出さない:', '回見た' not in h and '回中' not in h and '高い' in h)

            # 3・8 根拠の1行
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", V2)
            check(tag + ' 根拠は便と時刻と42日:', 'class="rbasis"' in h and 'JL148（19:36 着）から、前の42日の記録で続いた便をたどっています' in h)
            check(tag + ' 先の便ほど外れやすい:', '先の便ほど外れやすくなります' in h)
            check(tag + ' 保証しないは今のまま:', '予想です。保証しません' in h)
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", tt)
            check(tag + ' 時刻表の予想は60日:', '前の60日の記録' in h)
            v = json.loads(json.dumps(V2)); v['next'] = [{'callsign': 'JAL599', 'dep': 'HND', 'arr': 'CTS', 'time': '20:30', 'seen': None, 'share': None, 'src': 'livery'}]
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", v)
            check(tag + ' 運航情報の便だけなら航空会社の予定から:', '運航情報の便は、航空会社の予定から' in h and '日の記録' not in h)
            h = await pg.evaluate("d => predictionHTML(d, {}, {})", dict(V2, next=[]))
            check(tag + ' 予想がないときは根拠を出さない:', 'rbasis' not in h)

            # 4 外れたとき：予想は 20:30 の JL599、いま 20:40 発の JL517 で飛んでいる
            await pg.clock.set_fixed_time(at(20, 50))
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL517', dep:'HND', arr:'CTS', t:%d } }, {})" % ms(20, 40), V2)
            check(tag + ' いま実際は・当時の予想と並べる:', 'class="skip miss"' in h and 'いま実際は <b>JL517</b>' in h and '当時の予想：20:30 JL599</small>' in h)
            check(tag + ' 機体の入れ替えなどで変わる:', '機体の入れ替えなどで変わることがあります' in h)
            check(tag + ' この先は外れやすいと書く:', 'いま飛んでいる JL517 は予想と違いました' in h and 'この先は外れやすくなっています' in h)
            check(tag + ' いま飛んでいるので…の行は重ねない:', 'いま飛んでいるので予想に出しません' not in h)
            check(tag + ' 予想の便そのものは出さない（過ぎた）:', h.count('JL599') == 1 and 'JL502' in h)
            # 時刻が離れている（前後90分より外）・時刻が分からないときは外れと言わない
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL517', dep:'HND', arr:'CTS', t:%d } }, {})" % ms(22, 30), V2)
            check(tag + ' 時刻が離れていれば外れと言わない:', 'miss' not in h and 'いま飛んでいるので予想に出しません' in h)
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL517', dep:'HND', arr:'CTS' } }, {})", V2)
            check(tag + ' 出発の時刻が分からなければ外れと言わない:', 'miss' not in h)
            # 当たっているときは今までどおり
            h = await pg.evaluate("d => predictionHTML(d, { live:{ fl:'JL599', dep:'HND', arr:'CTS', t:%d } }, {})" % ms(20, 32), V2)
            check(tag + ' 当たっているときは外れの行なし:', 'miss' not in h and 'いま飛んでいるので予想に出しません' in h)

            # 機体の1日：記録（reg_history）で JL517 が飛んでいる → 外れの行・根拠・この先は外れやすい
            await pg.evaluate("openPlane('JA339J')"); await pg.wait_for_timeout(900)
            t = (await pg.inner_text('#dPlane')).replace('\n', ' ')
            check(tag + ' 機体の1日に外れの行:', await pg.locator('#dPlane li.skip.miss').count() == 1 and '当時の予想：20:30 JL599' in t, t[:400])
            check(tag + ' 機体の1日に根拠:', '根拠' in t and 'から、前の42日の記録で続いた便をたどっています' in t)
            box = await pg.locator('#dPlane li.p').first.bounding_box()
            check(tag + ' 予想の1便目が画面の中:', box is not None and box['y'] + box['height'] <= H, box)
            await pg.screenshot(path=os.path.join(WORK, f't201_plane_miss_{H}.png'))
            # シートの説明
            await pg.click('#dPlane [data-rot-conf]'); await pg.wait_for_timeout(150)
            s = await pg.inner_text('#dRotConf')
            check(tag + ' シートに根拠と外れたとき:', '根拠と外れたとき' in s and '当時の予想' in s and '先の便ほど外れやすくなります' in s)
            await pg.click('#dRotConf .btn1'); await pg.evaluate("$('dPlane').close()")
            # 夜の画面でも読める（色は変数）
            await pg.evaluate("document.documentElement.dataset.night = 'on'; openPlane('JA339J')"); await pg.wait_for_timeout(900)
            col = await pg.evaluate("getComputedStyle(document.querySelector('#dPlane .rbasis')).color")
            check(tag + ' 夜は根拠の字が明るい:', col in ('rgb(167, 176, 188)',), col)
            if H == 844: await pg.screenshot(path=os.path.join(WORK, 't201_plane_night.png'))
            await c.close()
            check(tag + ' ページのエラーなし:', not errs, errs)
        await b.close()
    print('errors', fails)
asyncio.run(main())
