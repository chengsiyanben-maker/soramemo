import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用タブの「定時率」と「空の道（航跡アート）」、フライトの画面の「この路線の定時率」、航跡の巡航の部分を点線にする
from datetime import datetime, timedelta, timezone
import asyncio, json, math
from playwright.async_api import async_playwright

def enc(pts):
    out, la0, lo0 = '', 0, 0
    def e(v):
        v = ~(v << 1) if v < 0 else v << 1; s = ''
        while v >= 0x20: s += chr((0x20 | (v & 0x1f)) + 63); v >>= 5
        return s + chr(v + 63)
    for la, lo in pts:
        a, b = round(la * 1e4), round(lo * 1e4); out += e(a - la0) + e(b - lo0); la0, lo0 = a, b
    return out
# 羽田（35.5533, 139.7811）から出ていく線・入ってくる線
TR = [{'d': 1, 'p': enc([(35.55 + i * .01, 139.78 + i * .012 * k) for i in range(30)]), 'a': [0] * 30} for k in (1, -1, .3)]
TR += [{'d': 0, 'p': enc([(35.2 + i * .012, 139.5 + i * .01) for i in range(30)]), 'a': [0] * 30}]
AO = {'iata': 'HND', 'days': 30, 'from': '2026-09-19', 'to': '2026-10-18', 'flights': 900, 'measured': 610, 'ontime': 512, 'cancelled': 3,
      'routes': [{'arr': 'CTS', 'flights': 120, 'measured': 90, 'ontime': 81, 'cancelled': 0}, {'arr': 'FUK', 'flights': 110, 'measured': 80, 'ontime': 60, 'cancelled': 1}]}
RO = {'dep': 'HND', 'arr': 'CTS', 'days': 30, 'flights': 130, 'measured': 96, 'ontime': 80, 'cancelled': 2}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.view.ops','ontime')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        calls=[]
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}'); calls.append((name, body))
            data = {'airport_ontime': AO, 'route_ontime': RO, 'airport_tracks': TR if body.get('p_iata') == 'HND' else []}.get(name)
            if data is None: await r.fulfill(status=404, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}); return
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        for n in ('airport_ontime', 'route_ontime', 'airport_tracks'): await c.route(f'https://fake.supabase.co/rest/v1/rpc/{n}', rpc)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_selector('#opsOntime:not([hidden])', timeout=8000)
        t = await pg.inner_text('#opsOntime')
        print('定時率:', '84%' in t.replace('\n', ''), '| 路線:', await pg.locator('#opsOntime .otlist li').count(), '| 福岡は黄色:', await pg.locator('#opsOntime .otlist i.mid').count() == 1)
        await pg.click('[data-vw="ops:art"]')   # 見方の切り替え：空の道すじ
        await pg.wait_for_selector('#opsArt:not([hidden]) canvas', timeout=8000)
        lit = await pg.evaluate("""() => { const cv = document.getElementById('artCv'), d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data; let n = 0;
          for(let i = 0; i < d.length; i += 4) if(d[i] > d[i + 2] + 30) n++; return n; }""")
        print('空の道 出発の線（橙）が描かれた:', lit > 20, '|', (await pg.inner_text('#opsArt .artnav span')))
        await pg.locator('#opsArt').screenshot(path=os.path.join(WORK,'t55_art.png')); print('次の日は押せない（昨日まで）:', await pg.is_disabled('#opsArt [aria-label="次の日"]'))
        await pg.click('#opsArt [aria-label="前の日"]'); await pg.wait_for_timeout(600)
        days = [x[1].get('p_day') for x in calls if x[0] == 'airport_tracks']
        print('前の日を読みにいく:', len(days) >= 2 and days[-1] < days[0], '| 空の日でも枠は残る:', await pg.is_visible('#opsArt'))
        mn = await pg.get_attribute('#artDate', 'min')
        await pg.fill('#artDate', mn); await pg.dispatch_event('#artDate', 'change'); await pg.wait_for_timeout(600)
        days = [x[1].get('p_day') for x in calls if x[0] == 'airport_tracks']
        print('日を選んで記録の最初の日まで:', days[-1] == mn and mn == '2026-10-18')
        cold = []
        await c.route('https://fake.supabase.co/functions/v1/cold-tracks**', lambda r: (cold.append(r.request.url), r.fulfill(status=200, body=json.dumps(TR), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))[1])
        await pg.evaluate("(async () => { ART = { iata:null }; const t = await loadArt('KIX', addDay(jstToday(), -420)); window.__cold = t.length; })()"); await pg.wait_for_timeout(800)
        print('古い日はファイル置き場から読む:', len(cold) == 1 and 'iata=KIX' in cold[0] and await pg.evaluate('window.__cold') == len(TR))
        await pg.click('#opsArt [aria-label="次の日"]'); await pg.wait_for_timeout(600)
        await pg.click('#artShare'); await pg.wait_for_selector('#dShare[open]', timeout=5000)
        print('共有の画像:', (await pg.get_attribute('#shareImg', 'src') or '')[:22])
        await pg.evaluate("document.getElementById('dShare').close()")
        # 航跡を線に分ける（120km以上離れた点のあいだは点線）
        segs = await pg.evaluate("trackSegs([[35.55,139.78],[35.7,139.9],[35.9,140.0],[42.6,141.6],[42.77,141.69]]).map(([s, g]) => s.length + (g ? '点線' : '線'))")
        print('航跡の分け方:', segs)
        # フライトの画面：この路線の定時率
        await pg.evaluate("""() => { const f = { id:1, from:A.find(a => a.iata === 'HND').id, to:A.find(a => a.iata === 'CTS').id, dep:Date.now() - 86400000, arr:Date.now() - 86400000 + 5400000, km:820, airline:'JL', no:'JL501', status:'with_flight_no' };
          S.flights.push(f); openFlight(fid(f)); }""")
        await pg.wait_for_selector('#fOntime:not([hidden])', timeout=5000)
        print('この路線:', (await pg.inner_text('#fOntime'))[:40])
        print('errors', errs); await b.close()
asyncio.run(main())
