import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行モード：下のタブに修行（運用の代わり）、ホームのカード（次に乗る便・運航の状況・その日の行程）、
# 修行のタブの中の行き来、フライトの見方「修行」（月ごと・金額を入れる）、成績の「修行のまとめ」（いちばん上）、気軽にでは隠す
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden).map(b => b.dataset.v).join(',')"
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        RT = [{'flight': 'NH469', 'std': iso(90), 'sta': iso(250), 'etd': iso(120), 'cancelled': False, 'aircraft': 'B789'}]
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            data = RT if name == 'route_today' else {'measured': 40, 'ontime': 34, 'cancelled': 1} if name == 'route_ontime' else []
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/airport-now**', lambda r: r.fulfill(status=200, body=json.dumps({'weather': None, 'taf': None, 'flights': None}), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        # 記録：羽田→那覇（ANA・金額あり）、那覇→羽田（ANA・金額なし）、40日前の羽田→那覇（ANA）
        await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, F = __fake.db.flights;
          Object.assign(F[0], { from_airport:h, to_airport:o, airline:'NH', flight_no:'NH461', fare:'ANA:E_FLEX', price:28700 });
          Object.assign(F[1], { from_airport:o, to_airport:h, airline:'NH', flight_no:'NH468', fare:'ANA:E_STD', price:null, dep_at:new Date(Date.now() - 40 * 864e5).toISOString(), arr_at:new Date(Date.now() - 40 * 864e5 + 9e6).toISOString() });
          Object.assign(F[2], { from_airport:h, to_airport:o, airline:'NH', flight_no:'NH463', fare:'ANA:E_STD', price:null }); }""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        check('修行：下のタブは ホーム・修行・フライト・成績:', await pg.evaluate(TABS) == 'home,sg,log,stats')
        # きょうの予定（往復）。行きは時刻表で30分遅れ
        await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, d = sgToday();
          sgGet().car = 'ANA'; sgGet().plans = [{ id:'p1', d, hm:'23:50', from:h, to:o, car:'ANA', fare:'ANA:E_FLEX', no:'NH469' }, { id:'p2', d, hm:'23:55', from:o, to:h, car:'ANA', fare:'ANA:E_FLEX', no:'NH470' }];
          goTab('home'); renderPersonaCard(); }""")
        await pg.wait_for_timeout(800)
        t = await pg.inner_text('#personaCard'); print('CARD', t.replace('\n', ' | ')[:500])
        check('ホーム：ポイントと目標:', 'PP' in t and '目標' in t and ('予定の便を乗ると' in t or '届く見込み' in t))
        check('ホーム：次に乗る便（きょう・便名・この便で）:', '次に乗る便' in t and 'きょう' in t and 'NH 469' in t and 'この便で' in t)
        check('ホーム：運航の状況と機材（航空会社の運航情報）:', '30分遅れ' in t and 'B789' in t and '運航情報' in t)
        check('ホーム：その日の行程と合計:', 'の行程' in t and 'この日の合計' in t and '2回' in t)
        await pg.locator('#personaCard').screenshot(path=os.path.join(WORK, 't73_home.png'))
        # 計画を作る → 修行のタブ（窓は開かない）
        await pg.click('#personaCard [data-sg-open="planner"]'); await pg.wait_for_timeout(400)
        check('計画を作るは修行のタブで開く:', await pg.evaluate("currentView()") == 'sg' and not await pg.evaluate("$('dShugyo').open") and '修行の計画を作る' in await pg.inner_text('#v-sg'))
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg')
        check('戻るとまとめ（閉じるはなく、会員情報がある）:', '年の修行' in t and '会員情報' in t and '閉じる' not in t)
        await pg.click('#v-sg [data-sg-go="year"]'); await pg.wait_for_timeout(200)
        await pg.click('nav.tabs button[data-v="sg"]'); await pg.wait_for_timeout(300)
        check('開いているときに修行のタブを押すとまとめに戻る:', await pg.evaluate("SG_PAGE") == 'main')
        await pg.click('#v-sg [data-sg-set="car"][data-v="JAL"]'); await pg.wait_for_timeout(300)
        check('タブの中で航空会社を切り替えられる:', await pg.evaluate("sgGet().car") == 'JAL' and 'FOP' in await pg.inner_text('#v-sg'))
        await pg.click('#v-sg [data-sg-set="car"][data-v="ANA"]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(WORK, 't73_tab.png'), full_page=True)
        check('窓の中身は空（id が重ならない）:', await pg.evaluate("$('dShugyoBody').innerHTML") == '')
        # フライトの見方「修行」
        await pg.click('nav.tabs button[data-v="log"]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#flights'); print('LOG', t.replace('\n', ' | ')[:400])
        check('フライト：見方は修行・月ごとにたまった・払った・1ポイントあたり:', await pg.evaluate("VIEW.log") == 'sg' and 'たまった' in t and '払った' in t and '1ポイントあたり' in t and '28,700' in t)
        check('フライト：金額のない便に「金額を入れる」:', '金額を入れる' in t)
        check('フライト：前の月はたたんである:', await pg.locator('#flights .sgmo[data-sglog]').count() >= 1)
        await pg.locator('#flights .sgled').screenshot(path=os.path.join(WORK, 't73_log.png'))
        await pg.click('#flights .sgprice'); await pg.wait_for_timeout(300)
        check('金額を入れるで便の窓が開く:', await pg.evaluate("$('dFlight').open"))
        await pg.evaluate("$('dFlight').close()")
        await pg.click('#flights [data-sglog]'); await pg.wait_for_timeout(300)
        check('たたんだ月を開ける:', 'たまった' in await pg.inner_text('#flights') and await pg.evaluate("SG_LOGOPEN") is not None)
        # 成績：修行のまとめがいちばん上
        await pg.click('nav.tabs button[data-v="stats"]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#sgSum'); print('SUM', t.replace('\n', ' | ')[:300])
        check('成績：修行のまとめ（月ごと・払った・1PPあたり・路線ごと）:', '月ごとのプレミアムポイント' in t and '払った' in t and '1PPあたり' in t and '路線ごと' in t)
        check('成績：まとめがパスポートより上:', await pg.evaluate("""() => { const a = document.querySelector('.lo[data-lo="stats:sgsum"]'), b = document.querySelector('.lo[data-lo="stats:passport"]'); return !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING); }"""))
        await pg.locator('#sgSum').screenshot(path=os.path.join(WORK, 't73_stats.png'))
        # 気軽にでは、修行のまとめは隠し、修行のタブもない。修行の画面は窓で開く
        await pg.evaluate("setPersona('casual', 'test')"); await pg.wait_for_timeout(500)
        check('気軽に：修行のまとめは隠す・修行のタブはない:', await pg.evaluate("document.querySelector('.lo[data-lo=\"stats:sgsum\"]').classList.contains('lo-off')") and 'sg' not in (await pg.evaluate(TABS)).split(','))
        await pg.evaluate("goTab('stats')"); await pg.wait_for_timeout(300)
        await pg.click('#v-stats .lo[data-lo="stats:status"] [data-sg-open="main"]'); await pg.wait_for_timeout(400)
        check('気軽に：修行の画面は窓で開く:', await pg.evaluate("$('dShugyo').open") and '閉じる' in await pg.inner_text('#dShugyo'))
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
