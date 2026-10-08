import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 羽田の今の運用：運用の推定、気象通報の表示、手での切り替え、通報が読めないとき
import asyncio, json
from playwright.async_api import async_playwright
MET={'id':'RJTT','time':'2026-10-08T07:00:00Z','raw':'METAR RJTT 080700Z 18015KT 9999 FEW030 24/16 Q1018','wdir':180,'wspd':15,'wgst':None,'vis_m':10000,'vis_plus':True}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        state={'ok':True}
        async def metar(r):
            if state['ok']: await r.fulfill(status=200, body=json.dumps(MET), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
            else: await r.fulfill(status=503, body='{"error":"unavailable"}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/functions/v1/metar**', metar)
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        cases = await pg.evaluate("""() => { const T = s => new Date(s), e = (m, t) => estimateHaneda(m, T(t)).mode; return [
          e({wdir:40, wspd:4, vis_m:10000}, '2026-10-08T13:00:00+09:00'), e({wdir:180, wspd:15, vis_m:10000}, '2026-10-08T13:00:00+09:00'),
          e({wdir:180, wspd:15, vis_m:10000}, '2026-10-08T16:00:00+09:00'), e({wdir:180, wspd:15, vis_m:3000}, '2026-10-08T16:00:00+09:00'),
          e({wdir:180, wspd:5, vis_m:10000}, '2026-10-08T16:00:00+09:00'), e(null, '2026-10-08T16:00:00+09:00') ]; }""")
        print('推定:', cases)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
        lines = "document.querySelectorAll('#opsMap path.leaflet-interactive').length"
        # 未加入（無料）
        await pg.click('#opsOpen'); await pg.wait_for_timeout(3000)
        print('無料 通報:', await pg.inner_text('#opsWx'))
        print('無料 理由:', (await pg.inner_text('#opsInfo')).split('\n')[1])
        print('無料 線の数:', await pg.evaluate(lines), '| 案内:', await pg.is_visible('#opsJoin'), '| 凡例:', await pg.inner_text('#opsLegend'))
        await pg.click('[data-ops=city]'); await pg.wait_for_timeout(300); print('無料でも手動切り替え:', (await pg.inner_text('#opsInfo')).split('\n')[0])
        await pg.click('#opsJoin'); await pg.wait_for_timeout(300); print('くわしく見る → 設定:', await pg.evaluate("$('dSettings').open"), '|', (await pg.inner_text('#plusInfo'))[:60])
        await pg.click('#closeSettings')
        # 加入中
        await pg.evaluate('PLUS = true'); await pg.click('#opsOpen'); await pg.wait_for_timeout(2000)
        print('＋ 通報:', await pg.inner_text('#opsWx'))
        print('＋ 理由:', (await pg.inner_text('#opsInfo')).split('\n')[1])
        print('＋ 線の数:', await pg.evaluate(lines), '| 案内:', await pg.locator('#opsJoin').count())
        await pg.click('#dOps [data-close]')
        # 通報が読めないとき
        state['ok']=False; await pg.click('#opsOpen'); await pg.wait_for_timeout(1500)
        print('通報なし:', await pg.inner_text('#opsWx'), '|', (await pg.inner_text('#opsInfo')).split('\n')[0])
        print(errs); await b.close()
asyncio.run(main())
