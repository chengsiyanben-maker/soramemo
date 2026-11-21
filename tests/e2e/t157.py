import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 改善担当の見回り（11/21）の撮る人の直し：
#  5 特別塗装機の欄は「羽田に着く・羽田を出る」。いま飛んでいない・3時間以内の予定があるときは「いまは飛んでいません。3時間以内の予定」（「見つかっていません」は出さない）
# 10 0時〜日の出は「日の出前（日の出 ○時○分ごろ）」、日の入り〜24時は「日の入り後」
#  9 滑走路の地図の撮影地の印は、見た目 12px のまま押せる範囲を 44px に
import asyncio, json, threading, http.server, socketserver, functools
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
PLANS = [
  {'flight':'JL565','livery':'トゥンクトゥンクJET','dep':'HND','arr':'CTS','std':iso(80),'sta':iso(170),'cancelled':False,'atd':None},
  {'flight':'NH24','livery':'ポケモンジェット 青','dep':'ITM','arr':'HND','std':iso(30),'sta':iso(100),'cancelled':False,'atd':None},
  {'flight':'JL999','livery':'遠い予定','dep':'HND','arr':'OKA','std':iso(300),'sta':iso(450),'cancelled':False,'atd':None},
  {'flight':'JL777','livery':'欠航の便','dep':'HND','arr':'FUK','std':iso(60),'sta':iso(160),'cancelled':True,'atd':None},
]
OTHER = [{'reg':'JA8089','name':'ほかの空港の塗装機','airline':'JAL','callsign':'JAL3001','lat':34.7,'lon':135.4,'alt_ft':20000,'iata':None,'phase':None,'src':'x','at':iso(-1),'kind':'special'}]
fails = []
def check(label, ok, extra=''):
    print(label, ok, extra if not ok else '')
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WORK)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/index_server_test.html'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', bypass_csp=True)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            body = PLANS if name == 'livery_plans_upcoming' else OTHER if name == 'special_now' else []
            await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{"planes":[]}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate("setOpsAirport('HND'); goTab('ops')"); await pg.wait_for_timeout(1800)
        if await pg.evaluate("$('v-ops').dataset.hub === 'list'"): await pg.evaluate("opsHubOpen('photo')"); await pg.wait_for_timeout(1200)

        # ---- 5 特別塗装機：いま羽田に着く・出る機体はない。3時間以内の予定は2便（到着1・出発1）
        sp = await pg.inner_text('#opsSpecial')
        check('5 見出しは「羽田に着く・羽田を出る特別塗装機」:', '羽田に着く・羽田を出る特別塗装機' in sp, sp[:120])
        check('5 予定があるときは「いまは飛んでいません。3時間以内の予定」:', 'いまは飛んでいません。3時間以内の予定' in sp, sp[:200])
        check('5 予定があるときは「見つかっていません」を出さない:', '見つかっていません' not in sp.split('いま飛んでいる特別塗装機')[0], sp[:200])
        head = sp.split('いま飛んでいる特別塗装機')[0]
        check('5 羽田を出る便（JL565・札幌へ・出発の予定）も入る:', 'JL565' in head and '出発の予定' in head, head)
        check('5 羽田に着く便（NH24・到着の予定）も入る:', 'NH24' in head and '到着の予定' in head, head)
        check('5 3時間より先・欠航の便は入らない:', 'JL999' not in head and 'JL777' not in head, head)
        check('5 予定は時刻の順（出発 80分後の JL565 が到着 100分後の NH24 より先）:', head.find('JL565') < head.find('NH24'))
        check('5 いま飛んでいる特別塗装機（3機まで）は畳まずに開く:', await pg.evaluate("!!document.querySelector('#opsSpecial details.spnow[open]')"))
        await pg.locator('#opsSpecial').scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(WORK, 't157_special_plans_390.png'))
        # 予定も飛んでいる機体もないとき
        none = await pg.evaluate("(() => { const keep = SP_PLANS; SP_PLANS = []; const h = spInboundHTML(); SP_PLANS = keep; return h; })()")
        check('5 何もないときは「この3時間に羽田に着く・羽田を出る特別塗装機は、いまは見つかっていません。」:', 'この3時間に羽田に着く・羽田を出る特別塗装機は、いまは見つかっていません。' in none, none[:300])
        # 着陸に向かっている機体があるときは、それを先に、予定は「3時間以内の予定」の小見出しの下
        both = await pg.evaluate("""(() => { SPECIAL.set('JA819A', { reg:'JA819A', name:'ポケモンジェット 赤', airline:'ANA', callsign:'ANA18', iata:'HND', phase:'arr', lat:35.45, lon:139.9, kind:'special' });
            const h = spInboundHTML(); SPECIAL.delete('JA819A'); return h; })()""")
        check('5 飛んでいる機体があるときは先に出し、予定は小見出しの下:', 'ポケモンジェット 赤' in both and '>3時間以内の予定<' in both and 'いまは飛んでいません' not in both and both.find('ポケモンジェット 赤') < both.find('3時間以内の予定'), both[:400])
        dep = await pg.evaluate("""(() => { SPECIAL.set('JA01XX', { reg:'JA01XX', name:'離陸の塗装機', airline:'JAL', callsign:'JAL1', iata:'HND', phase:'dep', lat:35.5, lon:139.8, kind:'special' });
            const h = spInboundHTML(); SPECIAL.delete('JA01XX'); return h; })()""")
        check('5 羽田を離陸したところの機体も入る:', '離陸の塗装機' in dep and '離陸したところ' in dep, dep[:300])

        # ---- 10 日の出前・日の入り後
        r = await pg.evaluate("""(() => { const T = s => Date.parse(s), c = [35.5494, 139.7798];
          return { a:spNightWord(T('2026-11-21T05:41:00+09:00')), b:spNightWord(T('2026-11-21T19:30:00+09:00')), z:spNightWord(T('2026-11-21T00:10:00+09:00')),
                   la:lightWord('night', T('2026-11-21T05:41:00+09:00')), lb:lightWord('night', T('2026-11-21T22:00:00+09:00')), lc:lightWord('back', T('2026-11-21T10:00:00+09:00')),
                   line:spNightLine(T('2026-11-21T05:41:00+09:00'), c), line2:spNightLine(T('2026-11-21T21:00:00+09:00'), c) }; })()""")
        check('10 5時41分は「日の出前」:', r['a'] == '日の出前', r)
        check('10 0時10分も「日の出前」:', r['z'] == '日の出前', r)
        check('10 19時30分は「日の入り後」:', r['b'] == '日の入り後', r)
        check('10 光の言葉（夜）も時刻で分ける・昼の言葉はそのまま:', r['la'] == '日の出前' and r['lb'] == '日の入り後' and r['lc'] == '順光', r)
        check('10 見出しは「日の出前（日の出 06:xxごろ）」:', r['line'].startswith('日の出前（日の出 <b>06:') and r['line'].endswith('ごろ）'), r['line'])
        check('10 夜は「日の入り後」のまま:', r['line2'] == '日の入り後', r['line2'])
        # 撮る人の見出しの1行が、5時41分には「日の出前」を出す（renderPhoto の facts）
        src = await pg.evaluate("renderPhoto.toString()")
        check('10 撮る人の見出しは夜のとき spNightLine を使う:', 'spNightLine(' in src)

        # ---- 9 撮影地の印の押せる範囲
        hit = await pg.evaluate("""(() => { const d = document.createElement('div'); d.className = 'spotlbl'; d.innerHTML = '<i></i><span>展望デッキ</span>'; d.style.cssText = 'position:fixed;left:100px;top:100px;width:12px;height:12px'; document.body.appendChild(d);
          const i = getComputedStyle(d.querySelector('i')), a = getComputedStyle(d.querySelector('i'), '::after'), s = getComputedStyle(d.querySelector('span'), '::after');
          const out = { iw:i.width, aw:a.width, ah:a.height, sh:s.height }; d.remove(); return out; })()""")
        check('9 印の見た目は 12px のまま:', hit['iw'] == '12px', hit)
        check('9 印の押せる範囲は 44×44:', hit['aw'] == '44px' and hit['ah'] == '44px', hit)
        check('9 名札の押せる高さは 44:', hit['sh'] == '44px', hit)

        check('JS のエラーなし:', not errs, errs)
        await b.close()
asyncio.run(main())
print('errors', fails)
