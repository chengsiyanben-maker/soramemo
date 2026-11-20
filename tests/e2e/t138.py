import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# （11/19 運用タブは一覧＋専用ページになった。このテストは中身を前の形（見方のタブ）で確かめるので soramemo.ops.hub=0。一覧は t148）
# 運用タブを空港と機体に分ける（決定事項【11/16】・design/ops-split 2版の A1・A2・A3・Q2・V1・V1c・V3）
#   1 上は1行：空港の側は「空港｜機体」＋空港のピル＋ⓘ＋共有。機体の側は探す欄＋ⓘ。選んだあとは「‹ 戻る」＋登録記号＋共有
#   2 機体の側のはじめの見方は「最近見た」。飛んでいる特別塗装機（地上の機体は入れない）と撮る人への入口
#   3 機体を選ぶとタブの中に機体の1日（シートは開かない）。844 と 667 で予想の1便目が見える。帯の下線は外れる
#   4 鉛筆のシートで「空港｜機体」を切り替え。鉛筆と選んだ見方が画面の中
#   5 「機体」を出す OFF で切り替えが消え、運用は空港だけ。シートの「機体 隠し中」から戻せる
#   6 機体の側では空港の物（気象通報・案内板・機体の位置）を読まない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, collections
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); _d = datetime.now(timezone.utc)
base = datetime(_d.year, _d.month, _d.day, tzinfo=JST)
at = lambda h, m: (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)
iso = lambda h, m: at(h, m).isoformat(); today = base.strftime('%Y-%m-%d'); NOW = at(14, 50)
HIST = [{'day': today, 'callsign': cs, 'dep': d, 'arr': a, 'first': iso(*f), 'last': iso(*l), 'type': 'B738'} for cs, d, a, f, l in [
    ('JAL141', 'HND', 'HIJ', (7, 40), (9, 0)), ('JAL142', 'HIJ', 'HND', (9, 50), (11, 10)), ('JAL323', 'HND', 'FUK', (14, 18), (14, 49))]]
V2 = {'reg': 'JA339J', 'src': 'reg', 'method': 'learn_hi', 'estimate': True, 'type': 'B738',
      'known': {'callsign': 'JAL323', 'dep': 'HND', 'arr': 'FUK', 'first': iso(14, 18), 'last': iso(14, 49)}, 'next': [
    {'callsign': 'JAL332', 'dep': 'FUK', 'arr': 'HND', 'time': '17:00', 'seen': 12, 'share': 0.92, 'src': 'learn'},
    {'callsign': 'JAL117', 'dep': 'HND', 'arr': 'ITM', 'time': '20:00', 'seen': 7, 'share': 0.7, 'src': 'learn'}]}
SPECIAL = [{'reg': 'JA05RK', 'name': 'ジンベエジェット', 'airline': 'JTA', 'callsign': 'JTA9', 'kind': 'livery', 'lat': 30.1, 'lon': 129.0, 'alt_ft': 34000, 'iata': None, 'phase': None},
           {'reg': 'JA228J', 'name': 'J-AIR 創立30周年記念機', 'airline': 'J-AIR', 'callsign': 'JAL2205', 'kind': 'livery', 'lat': 34.0, 'lon': 133.0, 'alt_ft': 21000, 'iata': None, 'phase': None},
           {'reg': 'JA01XJ', 'name': 'A350 1号機', 'airline': 'JAL', 'callsign': None, 'kind': 'livery', 'lat': 35.55, 'lon': 139.78, 'alt_ft': 0, 'iata': None, 'phase': None},
           {'reg': 'JA8089', 'name': 'スターアライアンス塗装', 'airline': 'ANA', 'callsign': 'ANA1', 'kind': 'alliance', 'lat': 35.0, 'lon': 136.0, 'alt_ft': 30000, 'iata': None, 'phase': None}]
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, height=844, side='ap', recent=None):
    c = await b.new_context(viewport={'width': 390, 'height': height}, timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    reqs = []
    async def h(r):
        u = r.request.url; path = u.split('fake.supabase.co')[1].split('?')[0]; name = path.rsplit('/', 1)[-1]; reqs.append(name)
        body = {'reg_history': HIST, 'predict_rotation_v2': V2, 'predict_rotation': {'reg': 'JA339J', 'known': None, 'next': []},
                'predict_rotation_reg': {'reg': 'JA339J', 'known': None, 'next': [], 'src': 'reg'}, 'special_now': SPECIAL,
                'inbound_aircraft': {'found': True, 'reg': 'JA339J', 'dep': 'HND', 'arr': 'FUK'}, 'airport-traffic': {'planes': [], 'at': iso(14, 50)}}.get(name, {} if '/functions/' in u else [])
        await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/rest/**', h); await c.route('https://fake.supabase.co/functions/**', h)
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.fulfill(status=404, body=''))
    init = ("localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
            "localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND'); localStorage.setItem('soramemo.view.ops','photo'); localStorage.setItem('soramemo.ops.side','%s');" % side)
    if recent is not None: init += "localStorage.setItem('soramemo.ops.recent', %s);" % json.dumps(json.dumps(recent))
    await c.add_init_script(init)
    pg = await c.new_page(); await pg.clock.set_fixed_time(NOW); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true")
    return c, pg, errs, reqs
VIS = "(sel => { const e = document.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 ? { l: Math.round(r.left), r: Math.round(r.right), t: Math.round(r.top), b: Math.round(r.bottom) } : null })"
async def vis(pg, sel): return await pg.evaluate(VIS + "(%s)" % json.dumps(sel))
async def inview(pg, sel, maxb=None):
    v = await vis(pg, sel); W = await pg.evaluate('innerWidth'); H = maxb or await pg.evaluate('innerHeight')
    return bool(v) and v['l'] >= 0 and v['r'] <= W and v['b'] <= H, v
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); allerr = []
        os.makedirs(os.path.join(WORK, 'shots-ops-split'), exist_ok=True)
        for H in (844, 667):
            tag = f'[{H}]'
            c, pg, errs, reqs = await page(b, H, recent=['JA339J'])
            await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(900)
            # 1 空港の側：上は1行
            row = await pg.evaluate("(() => { const ids = ['opsSide','opsApBtn','opsInfoBtn','opsShare','opsPlQ','opsPlBack','opsPlReg']; const o = {}; for(const i of ids){ const e = document.getElementById(i); const r = e.getBoundingClientRect(); o[i] = r.width > 0 ? Math.round(r.top + r.height / 2) : null; } return o; })()")
            ys = [row[k] for k in ('opsSide', 'opsApBtn', 'opsInfoBtn', 'opsShare')]
            check(tag + ' 空港の側：「空港｜機体」・空港・ⓘ・共有が1行', None not in ys and max(ys) - min(ys) <= 4, row)
            check(tag + ' 空港の側：探す欄・戻る・登録記号は出さない', row['opsPlQ'] is None and row['opsPlBack'] is None and row['opsPlReg'] is None, row)
            check(tag + ' 横にはみ出さない', await pg.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            ok, v = await inview(pg, '#opsAside .vwedit'); check(tag + ' 空港の側：鉛筆が画面の中', ok, v)
            ok, v = await inview(pg, '#opsViews [aria-selected="true"]'); check(tag + ' 空港の側：選んだ見方（撮る人）が画面の中', ok, v)
            t = await pg.inner_text('#opsViews'); check(tag + ' 空港の側の見方は7つ（撮る人を含む・案2）', all(x in t for x in ['案内板', '1日の山', '滑走路', '定時', '空の道すじ', '短冊', '撮る人']), t)
            if H == 844: await pg.screenshot(path=os.path.join(WORK, 'shots-ops-split', f'01-ap-{H}.png'))
            # 2 機体の側
            reqs.clear(); await pg.click('[data-ops-side="plane"]'); await pg.wait_for_timeout(700)
            row = await pg.evaluate("(() => { const o = {}; for(const i of ['opsSide','opsPlQ','opsInfoBtn','opsApBtn','opsShare']){ const r = document.getElementById(i).getBoundingClientRect(); o[i] = r.width > 0 ? Math.round(r.top + r.height / 2) : null; } return o; })()")
            check(tag + ' 機体の側：「空港｜機体」・探す欄・ⓘが1行、空港のピルと共有は出さない', row['opsPlQ'] and abs(row['opsPlQ'] - row['opsSide']) <= 4 and abs(row['opsInfoBtn'] - row['opsSide']) <= 4 and row['opsApBtn'] is None and row['opsShare'] is None, row)
            check(tag + ' 機体の側のはじめの見方は「最近見た」', (await pg.inner_text('#opsPViews [aria-selected="true"]')).strip() == '最近見た')
            t = await pg.inner_text('#opsPRecent')
            check(tag + ' 最近見た機体に JA339J', '最近見た機体' in t and 'JA339J' in t, t[:120])
            check(tag + ' いま飛んでいる特別塗装機：地上とアライアンスは入れない（飛行中 2機）', '飛行中 2機' in t and 'ジンベエジェット' in t and 'A350 1号機' not in t and 'スターアライアンス' not in t, t)
            check(tag + ' 撮る人への入口（案2）', '撮影地から見える機体' in t and '撮る人へ' in t)
            check(tag + ' 機体の側では空港の物（気象通報・案内板・機体の位置）を読まない', not any(n in reqs for n in ('metar', 'airport_board', 'airport-traffic')), dict(collections.Counter(reqs)))
            check(tag + ' 空港の側の中身は隠れる', await vis(pg, '#opsViews') is None and await vis(pg, '#opsMap') is None)
            if H == 844: await pg.screenshot(path=os.path.join(WORK, 'shots-ops-split', f'02-plane-{H}.png'))
            # 3 機体を選ぶ → タブの中に機体の1日
            await pg.click('#opsPRecent [data-plane="JA339J"]'); await pg.wait_for_timeout(1200)
            check(tag + ' シートは開かない（タブの中に出す）', not await pg.evaluate("document.getElementById('dPlane').open"))
            t = await pg.inner_text('#opsPlDay'); check(tag + ' 機体の1日（ここから予想・予想です。保証しません）', 'ここから予想' in t and '保証しません' in t, t[:160])
            row = await pg.evaluate("(() => { const o = {}; for(const i of ['opsSide','opsPlBack','opsPlReg','opsShare','opsPlQ','opsInfoBtn']){ const r = document.getElementById(i).getBoundingClientRect(); o[i] = r.width > 0 ? Math.round(r.top + r.height / 2) : null; } return o; })()")
            check(tag + ' 選んだあと：戻る・登録記号・共有が1行、探す欄とⓘは出さない', row['opsPlBack'] and abs(row['opsPlReg'] - row['opsSide']) <= 4 and abs(row['opsShare'] - row['opsSide']) <= 4 and row['opsPlQ'] is None and row['opsInfoBtn'] is None, row)
            check(tag + ' 登録記号のピルに JA339J', (await pg.inner_text('#opsPlReg')).strip() == 'JA339J')
            check(tag + ' 見方の帯の下線は外れる', await pg.evaluate("!document.querySelector('#opsPViews [aria-selected=\"true\"]')"))
            tab = await pg.evaluate("document.querySelector('nav.tabs').getBoundingClientRect().top")
            ok, v = await inview(pg, '#opsPlDay .rtl li.p', tab)
            check(tag + ' 予想の1便目が下のタブ帯の上に見える', ok, (v, tab))
            await pg.screenshot(path=os.path.join(WORK, 'shots-ops-split', f'03-plane-day-{H}.png'))
            await pg.click('#opsPlBack'); await pg.wait_for_timeout(300)
            check(tag + ' 戻るで最近見たへ', await vis(pg, '#opsPRecent .opsprow') is not None and await vis(pg, '#opsPlDay') is None)
            # 便名で探す
            await pg.fill('#opsPlQ', 'JL 323'); await pg.press('#opsPlQ', 'Enter'); await pg.wait_for_timeout(1000)
            check(tag + ' 便名で探すと機体の1日', (await pg.inner_text('#opsPlReg')).strip() == 'JA339J' and await vis(pg, '#opsPlDay') is not None)
            await pg.click('#opsPViews [data-vw="opsp:special"]'); await pg.wait_for_timeout(500)
            check(tag + ' 機体を選んでいるとき帯を押すとその見方（特別塗装機）', await vis(pg, '#opsPlDay') is None and await vis(pg, '#opsPSpecial') is not None and 'ジンベエジェット' in await pg.evaluate("document.getElementById('opsPSpecial').textContent"))
            # 4 鉛筆のシート
            await pg.click('#opsPside .vwedit'); await pg.wait_for_timeout(300)
            t = await pg.inner_text('#dViews'); check(tag + ' 機体の側の鉛筆：運用の見方・機体の2つと「機体」を出す', '運用の見方' in t and '最近見た' in t and '特別塗装機' in t and '「機体」を出す' in t, t[:200])
            await pg.click('#dViews [data-vs-side="ops"]'); await pg.wait_for_timeout(200)
            t = await pg.inner_text('#dViews'); check(tag + ' シートの中で空港に切り替え（7つ）', '案内板' in t and '撮る人' in t and '「機体」を出す' not in t)
            await pg.click('#dViews [data-vs-side="opsp"]'); await pg.wait_for_timeout(200)
            # 5 「機体」を出す OFF
            await pg.click('#dViews [data-vs-plane]'); await pg.wait_for_timeout(500)
            t = await pg.inner_text('#dViews'); check(tag + ' OFF：シートに「隠し中」と戻し方', '隠し中' in t and 'ここか、マイページの「表示の編集」' in t, t[:200])
            await pg.click('#dViews [data-close]'); await pg.wait_for_timeout(500)
            check(tag + ' OFF：切り替えが消え、空港の側だけ', await vis(pg, '#opsSide') is None and await vis(pg, '#opsApBtn') is not None and await vis(pg, '#opsPside') is None)
            ok, v = await inview(pg, '#opsAside .vwedit'); check(tag + ' OFF：鉛筆が画面の中', ok, v)
            if H == 844: await pg.screenshot(path=os.path.join(WORK, 'shots-ops-split', f'05-off-{H}.png'))
            await pg.evaluate("openPlane('JA339J')"); await pg.wait_for_timeout(600)
            check(tag + ' OFF：機体の1日は前のシートで開く', await pg.evaluate("document.getElementById('dPlane').open"))
            await pg.evaluate("document.getElementById('dPlane').close()")
            await pg.click('#opsAside .vwedit'); await pg.wait_for_timeout(300)
            await pg.click('#dViews [data-vs-side="opsp"]'); await pg.wait_for_timeout(200)
            await pg.click('#dViews [data-vs-plane]'); await pg.wait_for_timeout(300)
            await pg.click('#dViews [data-close]'); await pg.wait_for_timeout(400)
            check(tag + ' ON に戻すと切り替えが戻る', await vis(pg, '#opsSide') is not None)
            # 表示の編集
            await pg.evaluate("openLayout('opsp', 'screen')"); await pg.wait_for_timeout(300)
            t = await pg.inner_text('#dLayout'); check(tag + ' 表示の編集：運用（空港）と運用（機体）に分かれる', '運用（空港）' in t and '運用（機体）' in t and '「機体」を出す' in t, t[:300])
            await pg.click('#dLayout [data-lo-plane]'); await pg.wait_for_timeout(300)
            check(tag + ' 表示の編集の同じ行で OFF', not await pg.evaluate('opsPlaneOn()') and '「機体」を隠しています' in await pg.inner_text('#dLayout'))
            await pg.click('#dLayout [data-lo-filter="off"]'); await pg.wait_for_timeout(200)
            check(tag + ' 「隠しているもの」に「機体」を出すの行', await pg.evaluate("!!document.querySelector('#dLayout [data-lo-plane]')"))
            await pg.click('#dLayout [data-lo-plane]'); await pg.wait_for_timeout(200)
            check(tag + ' 戻せる', await pg.evaluate('opsPlaneOn()'))
            allerr += errs; await c.close()
        # 最近見た機体がない人（A2e）・開き直しても機体の側を覚えている
        c, pg, errs, reqs = await page(b, 844, side='plane', recent=[])
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(900)
        t = await pg.inner_text('#opsPRecent')
        check('最近見た機体がない人には説明（機体を1機ずつ追う）', '機体を1機ずつ追う' in t and 'JA339J' in t, t[:120])
        check('開き直しても機体の側', await pg.evaluate("document.getElementById('v-ops').dataset.side") == 'plane')
        await pg.screenshot(path=os.path.join(WORK, 'shots-ops-split', '04-plane-empty-844.png'))
        await pg.click('[data-ops-photo]'); await pg.wait_for_timeout(600)
        check('撮る人へで空港の側の撮る人', await pg.evaluate("document.getElementById('v-ops').dataset.side") == 'ap' and (await pg.inner_text('#opsViews [aria-selected=\"true\"]')).strip() == '撮る人')
        allerr += errs; await c.close()
        await b.close()
        print('fails', fails)
        print('errors', allerr if not fails else fails + allerr)
asyncio.run(main())
