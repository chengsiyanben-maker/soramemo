import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 窓側の席ガイド・機体と運航の実績・空のカレンダー（年間まとめを全員に）
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
            data = []
            if name == 'flight_facts':
                data = [{'f': x['f'], 'd': x['d'], 'a': x['a'], 'reg': ['JA01XJ', 'JA301J', 'JA301J'][i % 3], 'type': ['A359', 'B738', 'B738'][i % 3],
                         'ata': '2026-10-18T03:00:00Z', 'ata_src': 'odpt', 'arr_delay': 3, 'cancelled': False, 'diverted_to': 'NGO' if i == 1 else None} for i, x in enumerate(body.get('p', []))]
            await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
        # 窓側の席ガイド：羽田→伊丹は富士山が右側、伊丹→羽田は左側
        g = await pg.evaluate("""() => { const d = Date.parse('2026-10-20T09:00:00+09:00');
          return [seatGuide(IATA.HND, IATA.ITM, d, null, null), seatGuide(IATA.ITM, IATA.HND, d, null, null)]; }""")
        print('羽田→伊丹 富士山は右:', '富士山' in g[0]['R'], '| 伊丹→羽田 富士山は左:', '富士山' in g[1]['L'])
        # 便名を記録したフライトを3便（羽田→伊丹・伊丹→羽田・羽田→伊丹）
        await pg.evaluate("""() => { const h = IATA.HND.id, i = IATA.ITM.id, t0 = Date.parse('2026-10-16T09:00:00+09:00');
          [[h, i, 'JL101'], [i, h, 'JL102'], [h, i, 'JL103']].forEach(([a, b, no], k) => S.flights.push({ id:100 + k, from:a, to:b, dep:t0 + k * 864e5, arr:t0 + k * 864e5 + 3900000, km:400, airline:'JL', no, status:'with_flight_no' }));
          FACTS_KEY = ''; }""")
        await pg.evaluate("openFlight(fid(S.flights.find(f => f.id === 100)))"); await pg.wait_for_selector('#fSeatGuide:not([hidden])', timeout=5000)
        print('フライトの画面の席ガイド:', '右側' in (await pg.inner_text('#fSeatGuide')) and '富士山' in (await pg.inner_text('#fSeatGuide')))
        await pg.locator('#fSeatGuide').screenshot(path=os.path.join(WORK, 't58_seat.png'))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 実績：毎日の記録を読み込んでから
        await pg.evaluate("goTab('stats')"); await pg.wait_for_timeout(1500)
        done = await pg.evaluate("[...achState().done.keys()].filter(k => ['sp1','ty3','same2','dv1','ot10'].includes(k))")
        print('実績:', sorted(done))
        # 空のカレンダーと年間まとめ（そらメモ＋なし）
        await pg.evaluate("goTab('log'); setLogSeg('year')"); await pg.wait_for_timeout(500)
        cal = await pg.locator('#yrPlus .skycal rect.f').count()
        print('空のカレンダー（飛んだ日）:', cal >= 3, '| 年間まとめ:', '年のまとめ' in (await pg.inner_text('#yrPlus')))
        print('カレンダーを今月まで送る:', await pg.evaluate("(() => { const s = document.querySelector('#yrPlus .skycal'); return s.scrollLeft > 0; })()")); await pg.locator('#yrPlus .skycal').screenshot(path=os.path.join(WORK, 't58_cal.png'))
        print('errors', errs); await b.close()
asyncio.run(main())
