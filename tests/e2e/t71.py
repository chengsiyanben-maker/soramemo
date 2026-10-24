import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 表示の編集：下のタブ（出す・並び）、見方（隠す）、運用の空港（よく見る空港だけ）、運用の下・ホーム・成績のかたまり（出す・並び）。
# この端末だけに保存し、開き直しても残る。はじめに戻す・ひな形を選ぶと戻る。
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
        check('はじめは何も変えていない:', await pg.evaluate(LS) is None and await pg.evaluate(TABS) == 'home,book,log,ops,stats')
        check('マイページに入口:', await pg.locator('#dSettings [data-lo-open="top"]').count() == 1)

        # 運用：見方の右端の鉛筆から、その画面の編集へ
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        check('見方の右端に鉛筆:', await pg.locator('[data-lo-open="ops"]').count() == 1 and await pg.locator('#opsViews [data-vw]').count() == 7)
        await pg.click('[data-lo-open="ops"]'); await pg.wait_for_timeout(300)
        check('鉛筆で運用の編集が開く:', await pg.evaluate("$('dLayout').open && LO_PAGE === 'ops'"))
        for v in ['day', 'ontime', 'art']: await pg.click(f'[data-lo-view="ops:{v}"]')
        check('見方を隠す:', await pg.locator('#opsViews [data-vw]').count() == 4 and await pg.locator('#opsViews [data-vw="ops:day"]').count() == 0)
        for v in ['board', 'strip', 'photo']: await pg.click(f'[data-lo-view="ops:{v}"]')
        check('最後の1つは隠せない:', await pg.locator('[data-lo-view="ops:runway"]').is_disabled() and await pg.locator('#opsViews [data-vw]').count() == 1)
        for v in ['board', 'strip', 'photo']: await pg.click(f'[data-lo-view="ops:{v}"]')
        # 空港
        for a in ['HND', 'HIJ']: await pg.click(f'[data-lo-ap="{a}"]')
        aps = await pg.eval_on_selector_all('#opsAps [data-ops-ap]', 'e => e.map(x => x.dataset.opsAp)')
        check('よく見る空港だけ並ぶ:', 'HND' in aps and 'HIJ' in aps and len(aps) <= 3 and await pg.locator('#opsAps [data-ops-more]').count() == 1)
        # 運用の下：地図を隠す・特別塗装機を上へ
        await pg.click('[data-lo-blk="opsb:map"]'); await pg.click('[data-lo-mv="opsb:special:-1"]'); await pg.click('[data-lo-mv="opsb:special:-1"]')
        check('地図を隠す:', await pg.evaluate("$('opsBlocks').querySelector('[data-lo=\"opsb:map\"]').classList.contains('lo-off')"))
        check('特別塗装機がいちばん上:', await pg.evaluate("$('opsBlocks').firstElementChild.dataset.lo") == 'opsb:special')
        # 全体：成績のタブを隠し、運用を左へ
        await pg.click('[data-lo-page="top"]'); await pg.wait_for_timeout(200)
        await pg.click('[data-lo-tab="stats"]')
        for _ in range(3): await pg.click('[data-lo-tmv="ops:-1"]')
        check('タブ：成績を隠し、運用を左に:', await pg.evaluate(TABS) == 'ops,home,book,log')
        check('隠したタブはマイページから開ける:', '成績を開く' in (await pg.inner_text('#personaMore')))
        await pg.click('[data-lo-tab="book"]'); await pg.click('[data-lo-tab="log"]')
        check('タブは2つより減らせない:', await pg.evaluate(TABS) == 'ops,home' and await pg.locator('[data-lo-tab="ops"]').is_disabled())
        await pg.click('[data-lo-tab="book"]'); await pg.click('[data-lo-tab="log"]')
        # ホーム・成績
        await pg.click('[data-lo-page="home"]'); await pg.click('[data-lo-blk="home:recent"]')
        await pg.click('[data-lo-page="top"]'); await pg.click('[data-lo-page="stats"]')
        for _ in range(3): await pg.click('[data-lo-mv="stats:status:-1"]')
        check('ホーム：最近の印を隠す:', await pg.evaluate("document.querySelector('[data-lo=\"home:recent\"]').classList.contains('lo-off')"))
        check('成績：ステータスの目安がいちばん上:', await pg.evaluate("$('v-stats').querySelector('.lo').dataset.lo") == 'stats:status')
        # フライト・図鑑の見方
        await pg.click('[data-lo-page="top"]'); await pg.click('[data-lo-page="log"]'); await pg.click('[data-lo-view="log:alt"]')
        check('フライトの見方を隠す:', 'alt' in (await pg.evaluate(LS))['off']['log'])
        await pg.click('#dLayout [data-lo-page="top"]'); await pg.click('#dLayout [data-close]')

        # 開き直しても残る
        await pg.wait_for_timeout(500); await load()
        check('開き直してもタブが残る:', await pg.evaluate(TABS) == 'ops,home,book,log')
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1000)
        check('開き直しても見方が残る:', await pg.locator('#opsViews [data-vw]').count() == 4)
        check('開き直しても順番が残る:', await pg.evaluate("$('opsBlocks').firstElementChild.dataset.lo") == 'opsb:special' and await pg.evaluate("$('v-stats').querySelector('.lo').dataset.lo") == 'stats:status')
        check('ほかの空港を開ける:', True if await pg.click('[data-ops-more]') is None and await pg.locator('#opsAps [data-ops-ap]').count() == 14 else False)

        # はじめに戻す
        await pg.evaluate("openLayout('top', 'settings')"); await pg.click('[data-lo-reset]'); await pg.wait_for_timeout(300)
        check('はじめに戻す:', await pg.evaluate(LS) is None and await pg.evaluate(TABS) == 'home,book,log,ops,stats' and await pg.locator('#opsViews [data-vw]').count() == 7
              and await pg.evaluate("$('opsBlocks').firstElementChild.dataset.lo") == 'opsb:alerts' and not await pg.evaluate("document.querySelector('[data-lo=\"home:recent\"]').classList.contains('lo-off')"))
        # ひな形を選ぶと、その形になり、自分で変えた表示は戻る
        await pg.click('[data-lo-tab="stats"]')
        await pg.click('[data-lo-persona="spot"]'); await pg.wait_for_timeout(500)
        check('ひな形「撮影」を選ぶ:', await pg.evaluate(TABS) == 'ops,home,book,log' and await pg.evaluate(LS) is None and await pg.evaluate("PERSONA") == 'spot')
        check('使い方からの勧めは、自分で変えたら出さない:', await pg.evaluate("(() => { LAYOUT = { tabs:['home','ops'] }; const r = loCustom(); LAYOUT = null; return r; })()"))
        print('errors', errs + fails); srv.shutdown(); await b.close()
asyncio.run(main())
