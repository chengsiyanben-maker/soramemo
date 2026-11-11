import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 表示の編集（11/8 全部乗せ＋フィルター）：下のタブ（出す・隠す、2〜5こ）、見方（隠す）、運用の空港（よく見る空港だけ）、運用の下・ホーム・成績のかたまり（出す・隠す）。
# 開き直しても残る。全部乗せに戻すと全部出る。並べ替えは1月の公開のあと（いまの画面にはない）
# 読み込み直しを確かめるため、ファイルとしてではなく小さなサーバーから開く（file:// だと最初の読み込み直しで保存が消えることがある）
import asyncio, json, threading, http.server, socketserver, functools
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': [{'h': h, 'flights': 10, 'late': 0, 'cancel': 0, 'ref': 0} for h in range(24)],
         'next_arr': [{'flight': 'NH212', 'other': 'LHR', 'sched': iso(25), 't': iso(25), 'intl': True, 'aircraft': 'B789'}],
         'next_dep': [{'flight': 'JL903', 'other': 'OKA', 'sched': iso(30), 't': iso(30), 'aircraft': 'A359'}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WORK)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/index_server_test.html'
TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden).map(b => b.dataset.v).join(',')"
LS = "JSON.parse(localStorage.getItem('soramemo.layout') || 'null')"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            await r.fulfill(status=200, body=json.dumps(BOARD if name == 'airport_board' else []), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{"planes":[]}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        async def load():
            await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
            await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await load()
        check('はじめは何も変えていない（前からの人は「気軽に」：ホーム・図鑑・フライト）:', await pg.evaluate(LS) is None and await pg.evaluate(TABS) == 'home,book,log')
        check('マイページに入口:', await pg.locator('#dSettings [data-lo-open="top"]').count() == 1)

        # 運用：見方の右端の鉛筆から、表示の編集（運用の見方の所）へ
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        check('見方の右端に鉛筆:', await pg.locator('[data-vs-open="ops"]').count() == 1 and await pg.locator('#opsViews [data-vw]').count() == 7)
        await pg.click('[data-vs-open="ops"]'); await pg.wait_for_timeout(300)
        check('鉛筆で運用の見方のシートが開く:', await pg.evaluate("$('dViews').open && VS.k === 'ops'"))
        for v in ['day', 'ontime', 'art']: await pg.click(f'#dViews [data-vs-sw="{v}"]')
        check('見方を隠す:', await pg.locator('#opsViews [data-vw]').count() == 4 and await pg.locator('#opsViews [data-vw="ops:day"]').count() == 0)
        for v in ['board', 'strip', 'photo']: await pg.click(f'#dViews [data-vs-sw="{v}"]')
        check('最後の1つは隠せない:', await pg.locator('#dViews [data-vs-sw="runway"]').is_disabled() and await pg.locator('#opsViews [data-vw]').count() == 1)
        for v in ['board', 'strip', 'photo']: await pg.click(f'#dViews [data-vs-sw="{v}"]')
        await pg.evaluate("$('dViews').close(); openLayout('ops', 'screen')"); await pg.wait_for_timeout(300)
        # 空港
        for a in ['HND', 'HIJ']: await pg.click(f'[data-lo-ap="{a}"]')
        aps = await pg.eval_on_selector_all('#opsAps .aplist [data-ops-ap]', 'e => e.map(x => x.dataset.opsAp)')
        check('よく見る空港が、空港を選ぶ画面のいちばん上に並ぶ:', aps == ['HND', 'HIJ'] and await pg.locator('#opsAps .apgrid [data-ops-ap]').count() == 14)
        # 運用の下：地図を隠す
        await pg.click('[data-lo-blk="opsb:map"]')
        check('地図を隠す:', await pg.evaluate("$('opsBlocks').querySelector('[data-lo=\"opsb:map\"]').classList.contains('lo-off')"))
        # タブ：隠れている運用のタブを出す（成績は隠れたまま）
        await pg.click('[data-lo-tab="ops"]')
        check('タブ：運用を出す（成績は隠れたまま）:', await pg.evaluate(TABS) == 'home,book,log,ops')
        check('隠したタブはマイページから開ける:', await pg.locator('#personaMore [data-persona-open="stats"]').count() == 1)
        await pg.click('[data-lo-tab="book"]'); await pg.click('[data-lo-tab="log"]')
        check('タブは2つより減らせない:', await pg.evaluate(TABS) == 'home,ops' and await pg.locator('[data-lo-tab="ops"]').is_disabled())
        await pg.click('[data-lo-tab="book"]'); await pg.click('[data-lo-tab="log"]'); await pg.click('[data-lo-tab="sg"]')
        check('タブは5つまで出せる:', await pg.evaluate(TABS) == 'home,ops,book,log,sg' and await pg.locator('[data-lo-tab="sg"]').get_attribute('aria-pressed') == 'true')
        await pg.click('[data-lo-tab="sg"]')
        # ホーム・成績のかたまり
        await pg.click('[data-lo-blk="home:recent"]'); await pg.click('[data-lo-blk="stats:status"]')
        check('ホーム：最近の印を隠す:', await pg.evaluate("document.querySelector('[data-lo=\"home:recent\"]').classList.contains('lo-off')"))
        # フライトの隠れていた見方を出す
        await pg.click('[data-lo-view="log:year"]')
        check('フライトの隠れていた見方（年のまとめ）を出す:', 'year' not in (await pg.evaluate(LS))['off'].get('log', []))
        await pg.click('#dLayout [data-close]')

        # 開き直しても残る
        await pg.wait_for_timeout(500); await load()
        check('開き直してもタブが残る:', await pg.evaluate(TABS) == 'home,ops,book,log')
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1000)
        check('開き直しても見方が残る:', await pg.locator('#opsViews [data-vw]').count() == 4)
        check('開き直してもかたまりが残る:', await pg.evaluate("$('opsBlocks').querySelector('[data-lo=\"opsb:map\"]').classList.contains('lo-off')"))
        await pg.click('#opsApBtn'); await pg.fill('#opsApQ', 'oka'); await pg.wait_for_timeout(200)
        check('空港を3レターで探せる:', await pg.eval_on_selector_all('#opsAps [data-ops-ap]', 'e => e.map(x => x.dataset.opsAp)') == ['OKA'])
        await pg.click('#opsAps [data-ops-ap="OKA"]'); await pg.wait_for_timeout(600)
        check('選ぶと閉じて、その空港の運用:', not await pg.evaluate("$('dOpsAp').open") and await pg.evaluate("OPS_AP") == 'OKA')
        await pg.evaluate("setOpsAirport('HND')"); await pg.wait_for_timeout(400)

        # 全部乗せに戻す（11/8：ひな形に戻すのではなく、全部出す）
        await pg.evaluate("openLayout('top', 'settings')"); await pg.click('[data-lo-reset]'); await pg.click('[data-lo-reset-yes]'); await pg.wait_for_timeout(300)
        check('全部乗せに戻す:', await pg.evaluate(LS) is None and await pg.evaluate("PERSONA") == 'all' and await pg.evaluate(TABS) == 'home,book,log,ops,sg' and await pg.locator('#opsViews [data-vw]').count() == 7
              and not await pg.evaluate("document.querySelector('[data-lo=\"home:recent\"]').classList.contains('lo-off')"))
        check('ひな形を選ぶ所はない:', await pg.locator('#dLayout [data-lo-persona]').count() == 0 and await pg.locator('button[data-persona]').count() == 0)
        check('使い方からの勧めは、自分で変えたら出さない:', await pg.evaluate("(() => { LAYOUT = { tabs:['home','ops'] }; const r = loCustom(); LAYOUT = null; return r; })()"))
        print('errors', errs + fails); srv.shutdown(); await b.close()
asyncio.run(main())
