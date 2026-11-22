import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ホームの撮影カードの切り替え（11/22 本人「離陸じゃなくて、他のやつを表示できるような機能にしてほしい」）
#   ピル（着陸・離陸・特別塗装機・遅れ）・はじめは近い方・端末に覚える・「推定・出典 i」・「運用を見る ›」は選んだものの専用ページへ
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc); now = datetime(_d.year, _d.month, _d.day, 3, 0, tzinfo=timezone.utc)   # 日本時間の昼12時
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-home-card-switch')); os.makedirs(SHOTS, exist_ok=True)
HRS = [{'h': h, 'flights': 40 if 6 <= h <= 22 else 0, 'late': 3 if h in (8, 10) else 0, 'cancel': 1 if h == 9 else 0, 'ref': 1} for h in range(24)]
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': HRS,
  'next_arr': [{'flight': 'JL500', 'other': 'ITM', 'sched': iso(5), 'est': iso(50), 't': iso(50), 'aircraft': 'B738'},
               {'flight': 'NH212', 'other': 'LHR', 'sched': iso(25), 't': iso(25), 'intl': True, 'aircraft': 'B789'},
               {'flight': 'JL123', 'other': 'ITM', 'sched': iso(70), 't': iso(70), 'aircraft': 'B763'}],
  'next_dep': [{'flight': 'NH50', 'other': 'CTS', 'sched': iso(-15), 'actual': iso(-8), 't': iso(-8), 'aircraft': 'B772', 'takeoff': iso(8), 'takeoff_src': 'calc', 'taxi': 16},
               {'flight': 'NH106', 'other': 'LAX', 'sched': iso(15), 't': iso(15), 'intl': True, 'aircraft': 'B77W', 'takeoff': iso(31), 'takeoff_src': 'calc', 'taxi': 16}]}
PLANS = [{'flight': 'JL123', 'livery': 'ミッキー塗装', 'dep': 'ITM', 'arr': 'HND', 'std': iso(0), 'sta': iso(70), 'cancelled': False, 'atd': None},
         {'flight': 'NH99', 'livery': '出発した塗装', 'dep': 'HND', 'arr': 'CTS', 'std': iso(-30), 'sta': iso(60), 'cancelled': False, 'atd': iso(-25)},
         {'flight': 'NH77', 'livery': '欠航の塗装', 'dep': 'HND', 'arr': 'FUK', 'std': iso(40), 'sta': iso(150), 'cancelled': True, 'atd': None},
         {'flight': 'JL9', 'livery': 'あしたの塗装', 'dep': 'HND', 'arr': 'OKA', 'std': iso(60 * 20), 'sta': iso(60 * 23), 'cancelled': False, 'atd': None}]
SPNOW = [{'reg': 'JA8089', 'name': '鬼滅ジェット', 'airline': 'ANA', 'kind': 'livery', 'callsign': 'ANA77', 'iata': 'HND', 'phase': 'arr', 'lat': 35.5, 'lon': 139.9}]
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        calls = []
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; calls.append(name)
            body = BOARD if name == 'airport_board' else PLANS if name == 'livery_plans_upcoming' else SPNOW if name == 'special_now' else []
            await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        pg=await c.new_page(); await pg.clock.set_fixed_time(now); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("setPersona('spot', 'test')"); await pg.wait_for_timeout(1500)   # 撮影の構成（運用タブを先に開く＝いまの運用が分かる）
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300)
        await pg.evaluate("renderPersonaCard()"); await pg.wait_for_timeout(1000)
        card = pg.locator('#personaCard')
        async def shot(name):   # 写真はスマホの画面（390×844）のまま。シートを広げてカードを上へ
            if await pg.get_attribute('#homeSheet', 'data-snap') != 'full': await pg.click('#homeSheet .grab'); await pg.wait_for_timeout(500)
            await pg.evaluate("(() => { const b = document.querySelector('#homeSheet .sbody'), c = $('personaCard'); b.scrollTop += c.getBoundingClientRect().top - b.getBoundingClientRect().top - 8; })()"); await pg.wait_for_timeout(150)
            await pg.screenshot(path=os.path.join(SHOTS, name))
        tabs = await pg.evaluate("[...document.querySelectorAll('#personaCard [data-pctab]')].map(b => b.textContent + ':' + b.getAttribute('aria-selected'))")
        print('TABS', tabs)
        check('ピルは4つ（着陸・離陸・特別塗装機・遅れ）:', [t.split(':')[0] for t in tabs] == ['着陸', '離陸', '特別塗装機', '遅れ'])
        check('はじめは近い方（離陸 NH50 が8分後）:', tabs[1].endswith('true') and sum(t.endswith('true') for t in tabs) == 1)
        t = await card.inner_text(); print('DEP', t.replace('\n', ' | '))
        check('離陸：NH50 が大きく・あと NH106:', await pg.locator('#personaCard .sphero').count() == 1 and 'NH50' in t and 'NH106' in t and 'NH212' not in t)
        check('長い注意書きはたたむ（1行だけ）:', await pg.locator('#pcInfo').is_hidden() and '推定・出典' in t and '表示する機体：' not in t)
        check('ページが横にはみ出さない:', await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        await shot('02_dep.png')
        # 着陸
        await pg.click('#personaCard [data-pctab="arr"]'); await pg.wait_for_timeout(200)
        t = await card.inner_text(); print('ARR', t.replace('\n', ' | '))
        check('着陸：NH212 が大きく（B738 の JL500 は注目でない）:', 'NH212' in t and 'NH50' not in t and 'JL500' not in t and '着陸' in t)
        check('着陸：滑走路（推定）:', '滑走路 ' in t and '（推定）' in t)
        check('選んだものを端末に覚える:', await pg.evaluate("localStorage.getItem('soramemo.home.spTab')") == 'arr')
        check('押したピルにフォーカス:', await pg.evaluate("document.activeElement && document.activeElement.dataset.pctab") == 'arr')
        await shot('01_arr.png')
        # 推定・出典 i
        await pg.click('#personaCard [data-pcinfo]'); await pg.wait_for_timeout(100)
        ti = await pg.inner_text('#pcInfo')
        check('i で注意書きが開く:', await pg.locator('#pcInfo').is_visible() and '表示する機体' in ti and '公共交通オープンデータセンター' in ti and '保証しません' in ti and await pg.get_attribute('#personaCard [data-pcinfo]', 'aria-expanded') == 'true')
        await shot('05_info.png')
        await pg.click('#personaCard [data-pcinfo]'); await pg.wait_for_timeout(100)
        # 特別塗装機
        await pg.evaluate("SPECIAL_AT = 0; SP_PLANS = []; SPECIAL.clear()"); n0 = calls.count('livery_plans_upcoming')   # 運用タブで読んだ分は捨てる
        await pg.click('#personaCard [data-pctab="sp"]'); await pg.wait_for_timeout(800)
        t = await card.inner_text(); print('SP', t.replace('\n', ' | '))
        check('特別塗装機を選んだら読む:', calls.count('livery_plans_upcoming') == n0 + 1 and 'special_now' in calls)
        check('特別塗装機：いま着陸に向かっている機体が先:', '鬼滅ジェット' in t and 'いま' in t and '着陸に向かっている' in t and t.index('鬼滅ジェット') < t.index('ミッキー塗装'))
        check('特別塗装機：今日このあとの予定（出発済み・欠航・あしたは出ない）:', 'ミッキー塗装' in t and 'JL123' in t and '出発した塗装' not in t and '欠航の塗装' not in t and 'あしたの塗装' not in t)
        await shot('03_sp.png')
        hub = await pg.get_attribute('#personaCard [data-pchub]', 'data-pchub'); check('特別塗装機の「運用を見る」は特別塗装機のページへ:', hub == 'special')
        await pg.evaluate("SP_PLANS = []; SPECIAL.clear(); renderPersonaCard()"); await pg.wait_for_timeout(500)
        t = await card.inner_text(); check('特別塗装機がないとき「今日はありません」:', '今日はありません' in t)
        await shot('03b_sp_none.png')
        # 遅れ
        await pg.click('#personaCard [data-pctab="late"]'); await pg.wait_for_timeout(200)
        t = await card.inner_text(); print('LATE', t.replace('\n', ' | '))
        check('遅れ：今日の数（遅れ6・欠航1）:', '7\n便' in t and '遅れ 6便・欠航 1便' in t)
        check('遅れ：いちばん大きいもの（JL500 45分）:', 'いちばん大きい遅れ' in t and 'JL500' in t and '45' in t)
        await shot('04_late.png')
        pl = await pg.evaluate("""() => [pcLate({ hours:[{ late:2, cancel:1 }], bad:[{ dir:'dep', flight:'NH1', other:'CTS', late:20, cancelled:false }, { dir:'arr', flight:'JL2', other:'FUK', late:95, cancelled:false }, { dir:'dep', flight:'NH3', other:'OKA', late:null, cancelled:true }] }),
          pcLate({ hours:[{ late:0, cancel:1 }], bad:[{ dir:'dep', flight:'NH3', other:'OKA', late:null, cancelled:true }] }), pcLate(null)]""")
        print('PCLATE', pl)
        check('遅れ：bad があればそこから（いちばん大きい遅れ・なければ欠航）:', pl[0]['n'] == 3 and pl[0]['top']['fl'] == 'JL2' and pl[0]['top']['m'] == 95 and pl[1]['top']['cancel'] is True and pl[2] is None)
        check('遅れ：0便のとき:', '今日は遅れ・欠航の便はありません' in await pg.evaluate("(() => { const d = JSON.parse(JSON.stringify(PC_LAST.d)); d.hours.forEach(h => { h.late = 0; h.cancel = 0; }); return spHomeHTML(PC_LAST.ap, PC_LAST.def, d); })()"))
        # 覚えたものは開き直しても残る
        await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300); await pg.evaluate("renderPersonaCard()"); await pg.wait_for_timeout(1000)
        check('開き直しても遅れのまま:', await pg.get_attribute('#personaCard [data-pctab="late"]', 'aria-selected') == 'true')
        await pg.screenshot(path=os.path.join(SHOTS, '06_home_late.png'))
        # 運用を見る › は遅れのページへ
        await pg.click('#personaCard [data-pchub]'); await pg.wait_for_timeout(1200)
        check('運用を見る › で遅れの専用ページ:', await pg.evaluate("currentView()") == 'ops' and await pg.evaluate("OPS_PAGE") == 'late' and await pg.locator('#opsLate').is_visible())
        # 着陸・離陸は撮る人のページへ
        await pg.evaluate("localStorage.setItem('soramemo.home.spTab', 'dep'); opsHubBack(); goTab('home')"); await pg.wait_for_timeout(600)
        await pg.evaluate("renderPersonaCard()"); await pg.wait_for_timeout(800)
        await pg.click('#personaCard [data-pchub]'); await pg.wait_for_timeout(1200)
        check('離陸の「運用を見る ›」は撮る人のページ:', await pg.evaluate("OPS_PAGE") == 'photo')
        print('errors', errs, 'fails', fails); await b.close()
asyncio.run(main())
