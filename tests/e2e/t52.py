import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo', device_scale_factor=2); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        print('件数: 民間', await pg.evaluate('A.length'), '| 番外編', await pg.evaluate("JSON.stringify({mil:XA.filter(a=>a.kind=='mil').length, glider:XA.filter(a=>a.kind=='glider').length, field:XA.filter(a=>a.kind=='field').length})"), '| 実績', await pg.evaluate('ACH.length'))
        # 判定：新千歳の範囲内で千歳基地のほうが近い地点、範囲外で千歳基地の範囲内の地点
        print('新千歳の範囲内:', await pg.evaluate("nearest({lat:42.7855, lon:141.6770}).a.name"), '| 千歳基地の範囲:', await pg.evaluate("nearest({lat:42.8050, lon:141.6550}).a.name"), '| 入間のフェンス外:', await pg.evaluate("nearest({lat:35.8580, lon:139.4100}).a.name"))
        await pg.click('#openSettings'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(200)
        # 羽田 → 入間基地 → 妻沼滑空場 → 羽田 の順にデモでチェックイン
        for v in ['t:HND-T1', 'a:1010', 'a:2017', 'a:3002', 'a:89', 'a:5']:
            await pg.select_option('#demoAirport', v); await pg.click('#checkin'); await pg.wait_for_timeout(700)
            body = (await pg.inner_text('#dStamp')).replace('\n',' ')
            print(v, '→', body[:40], '| 注意:', ('基地の中には入れません' in body), ('滑走路や河川敷' in body), ('格納庫' in body), '| 守り神:', await pg.locator('#dStamp .meet').count())
            if v == 'a:1010': await pg.screenshot(path=os.path.join(WORK,'x_mil.png'))
            await pg.click('#dStamp [data-close]')
        print('フライト:', await pg.evaluate("JSON.stringify(S.flights.map(f=>[BY[f.from].name,BY[f.to].name]))"))
        print('空港の数（民間）:', await pg.evaluate('visited().size'), '| 番外編:', await pg.evaluate('visitedExtra().size'))
        st = await pg.evaluate("(() => { const s = achState(); return ['mil1','gl1','fd1','ap1','ap5'].map(id => id + ':' + s.done.has(id)); })()"); print('実績:', st)
        await pg.click('nav.tabs button[data-v=book]'); await pg.wait_for_timeout(300)
        print('図鑑の進み:', await pg.inner_text('#bookProg'))
        await pg.click('#v-book [data-seg=extra]'); await pg.wait_for_timeout(200)
        print('番外編:', [t for t in (await pg.inner_text('#bookExtra')).split('\n') if '/' in t][-2:])
        await pg.locator('#bookExtra h2').scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(WORK,'x_book.png'))
        print(errs); await b.close()
asyncio.run(main())
