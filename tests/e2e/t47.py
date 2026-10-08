import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo'); await c.add_init_script("localStorage.setItem('soramemo.onboarded','1')")
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(400)
        # 羽田-新千歳（JAL セイバー・未選択）、羽田-那覇（ANA スタンダード）、旧運賃期間のANA、記録帳のJAL
        await pg.evaluate("""() => { const id=i=>A.find(a=>a.iata===i).id, T=s=>Date.parse(s);
          const fs=[{id:'a1',from:id('HND'),to:id('CTS'),dep:T('2026-06-01T08:00:00+09:00'),arr:T('2026-06-01T09:35:00+09:00'),km:km(BY[id('HND')],BY[id('CTS')]),airline:'JL',no:'JL501',fare:null,seat:null},
                    {id:'a2',from:id('HND'),to:id('OKA'),dep:T('2026-07-01T08:00:00+09:00'),arr:T('2026-07-01T11:00:00+09:00'),km:km(BY[id('HND')],BY[id('OKA')]),airline:'NH',no:'NH995',fare:'ANA:E_STD',seat:'12A'},
                    {id:'a3',from:id('HND'),to:id('FUK'),dep:T('2026-03-01T08:00:00+09:00'),arr:T('2026-03-01T10:00:00+09:00'),km:km(BY[id('HND')],BY[id('FUK')]),airline:'NH',no:'NH241',fare:null,seat:null}];
          localStorage.setItem('soramemo.v1', JSON.stringify(packS({checkins:[], flights:fs, manual:[{from:id('ITM'),to:id('CTS'),d:'2026-02-02',airline:'JL',fare:'JAL:Y_FLEX'}], demoClock:null}))); }""")
        await pg.wait_for_timeout(300); await pg.reload(); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(500)
        print('読み込み:', await pg.evaluate("JSON.stringify([S.flights.map(f=>[f.no,f.fare,f.seat]), S.manual.map(m=>[m.airline,m.fare])])"))
        r = await pg.evaluate("""() => { const s = statusSummary(2026), rows = statusRows().map(r => { const f = fareOf(r, r.t); return [BY[r.from].iata+'-'+BY[r.to].iata, Math.round(kmToMile(r.km)), f && f.table, f && f.id, f && f.rate, f && f.bonus]; }); return {s, rows}; }""")
        print('計算:', json.dumps(r, ensure_ascii=False))
        await pg.click('nav.tabs button[data-v=stats]'); await pg.wait_for_timeout(200)
        print('表示:', (await pg.inner_text('#statusBox')).replace('\n',' ')[:300])
        await pg.click('nav.tabs button[data-v=log]'); await pg.wait_for_timeout(200)
        # フライトの画面で運賃を選ぶ
        await pg.click('#flights .flight.tap >> nth=2'); await pg.wait_for_timeout(200)
        print('運賃の選択肢:', await pg.locator('#fFare option').count(), '| 選択中:', await pg.evaluate("$('fFare').value"), '| 座席:', await pg.inner_text('#fSeat'))
        await pg.select_option('#fFare', 'JAL:Y_FLEX'); await pg.click('#fSave'); await pg.wait_for_timeout(200)
        print('選んだ後:', await pg.evaluate("JSON.stringify(statusSummary(2026).jal)"))
        await pg.screenshot(path=os.path.join(WORK,'status.png'), full_page=False)
        print(errs); await b.close()
asyncio.run(main())
