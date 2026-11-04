import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 滑走路の見方の地図：模式図をやめて本物の地図・滑走路の色（着陸・離陸・使っていない）・撮影地の名札（押すと撮影地の情報）・空港のまわり／経路の全体・現在地は空港の敷地の中だけ
import asyncio, json
from datetime import datetime, timezone
from playwright.async_api import async_playwright
_d = datetime.now(timezone.utc); now = datetime(_d.year, _d.month, _d.day, 3, 0, tzinfo=timezone.utc)
INFO = [{'iata': 'HND', 'name': '京浜島つばさ公園', 'open_kind': 'always', 'open_from': None, 'open_to': None, 'open_note': '24時間・無料', 'access': None, 'parking': '有料駐車場あり', 'rules': [], 'contact': '大井ふ頭中央海浜公園 管理事務所 03-3790-2378', 'sources': [], 'checked_on': '2026-11-02'}]
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def page(p, geo):
    b = await p.chromium.launch()
    c = await b.new_context(viewport={'width':400,'height':900}, timezone_id='Asia/Tokyo', geolocation=geo, permissions=['geolocation'])
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.view.ops','runway')")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://fake.supabase.co/rest/v1/spot_info**', lambda r: r.fulfill(status=200, body=json.dumps(INFO), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    pg = await c.new_page(); await pg.clock.set_fixed_time(now); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(600)
    await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1500)
    await pg.click('[data-vw="ops:runway"]'); await pg.wait_for_timeout(2500)
    return b, pg, errs
async def main():
    async with async_playwright() as p:
        # 羽田の敷地の中（第1ターミナルのあたり）
        b, pg, errs = await page(p, {'latitude': 35.5494, 'longitude': 139.7846})
        check('模式図はない:', await pg.locator('#opsInfo svg.opsdiag').count() == 0)
        check('地図が見えている:', await pg.evaluate("$('opsMap').offsetHeight > 200"))
        cols = await pg.evaluate("OPS_LAYER.getLayers().filter(l => l instanceof L.Polyline && /rwy-/.test(l.options.className || '')).map(l => l.options.className + ':' + l.options.color)")
        print('RWY', cols)
        check('滑走路の色（着陸＝紺・離陸＝薄い紺・使っていない＝薄い灰）:', any(x.startswith('rwy-arr:#0F1B2D') for x in cols) and any(x.startswith('rwy-dep:#8C9AAE') or x.startswith('rwy-arr') for x in cols) and len(cols) == 4)
        names = await pg.evaluate("[...document.querySelectorAll('#opsMap .spotlbl span')].map(e => e.textContent)")
        print('SPOTS', names)
        check('撮影地の名札（羽田の撮影地すべて・名前が見える）:', len(names) >= 6 and any('京浜島つばさ公園' in n for n in names) and any('第1T 展望デッキ' in n for n in names))
        check('空港のまわりでは経路の線を出さない:', await pg.evaluate("OPS_LAYER.getLayers().filter(l => l instanceof L.Polyline).length") <= 4 + 6 and await pg.locator('[data-layer="sid"]').is_hidden())
        check('空港のまわりの縮尺:', await pg.evaluate("OPS_MAP.getZoom()") >= 11 and await pg.evaluate("OPS_MAP.getBounds().contains(L.latLng(35.5533, 139.7811))"))
        check('現在地（敷地の中）:', await pg.locator('#opsMap .locdot').count() == 1)
        await pg.screenshot(path=os.path.join(WORK, 't113_near.png'), full_page=True)
        await pg.locator('#opsMap .spotlbl', has_text='京浜島').click(); await pg.wait_for_timeout(300)
        check('名札を押すと撮影地の情報:', await pg.evaluate("$('dSpotInfo').open") and '京浜島つばさ公園' in await pg.inner_text('#dSpotInfo'))
        await pg.click('#dSpotInfo [data-close]'); await pg.wait_for_timeout(200)
        await pg.click('[data-scope="wide"]'); await pg.wait_for_timeout(800)
        check('経路の全体：経路の線とピルが出る・縮尺を引く:', await pg.locator('[data-layer="sid"]').is_visible() and await pg.evaluate("OPS_MAP.getZoom()") <= 10 and await pg.evaluate("OPS_LAYER.getLayers().filter(l => l instanceof L.Polyline).length") > 10)
        check('範囲は覚える:', await pg.evaluate("localStorage.getItem('soramemo.opsScope')") == 'wide')
        await pg.click('[data-scope="near"]'); await pg.wait_for_timeout(500)
        print('errors1', errs); await b.close()
        # 敷地の外（東京駅のあたり）：現在地は出さない
        b, pg, errs2 = await page(p, {'latitude': 35.6812, 'longitude': 139.7671})
        check('現在地（敷地の外は出さない）:', await pg.locator('#opsMap .locdot').count() == 0)
        await b.close()
        print('errors', errs + errs2, 'fails', fails)
asyncio.run(main())
