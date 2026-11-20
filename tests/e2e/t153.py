import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行の年と月の区切りは日本時間（11/20 候補1）。端末の時計の地域が日本でなくても、日本時間の 1月1日 0時で年が変わる。
# 時計を日本時間 2027-01-01 00:30（＝世界時 2026-12-31 15:30）に止め、東京・世界時・ロサンゼルスの3つの地域で同じ数になるかを見る。
import asyncio, json
from playwright.async_api import async_playwright
NOW = '2026-12-31T15:30:00Z'   # 2026-12-31T15:30:00Z ＝ 日本時間 2027-01-01 00:30
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def run(p, tz):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':390,'height':844}, timezone_id=tz)
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.clock.install(time=NOW)
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.clock.run_for(800)
    # 記録：JAL 羽田→那覇。出発が日本時間 12/31 23:00（世界時 14:00）と、日本時間 1/1 0:00（世界時 15:00）の2便（修行は出発の日で数える）
    await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, F = __fake.db.flights; F.length = 0;
      [Date.UTC(2026, 11, 31, 14), Date.UTC(2026, 11, 31, 15)].forEach((t, i) => F.push({ id:300 + i, from_airport:h, to_airport:o, airline:'JL', flight_no:'JL90' + i, fare:'JAL:Y_SAVER', price:20000, status:'verified', distance_km:1500,
        dep_at:new Date(t).toISOString(), arr_at:new Date(t + 9e6).toISOString() })); }""")
    await pg.evaluate('__fake.login()'); await pg.clock.run_for(1200)
    await pg.evaluate("""() => { const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.car = 'JAL'; g.goal.JAL = 'crystal';
      g.plans = [{ id:'p1', d:'2027-01-02', hm:'07:00', from:o, to:h, car:'JAL', fare:'JAL:Y_SAVER', no:'JL918' }]; g.drafts = []; }""")
    r = await pg.evaluate("""() => { const Y = sgYear(), Y0 = sgYear(2026), M = sgMoney(Y);
      return { now:[sgNowY(), sgNowM()], y:Y.y, n:Y.JAL.n, m0:Y.months[0].n, m11:Y.months[11].n, n0:Y0.JAL.n, m011:Y0.months[11].n, md:sgMD('2027-01-01'), wd:sgWD('2027-01-01'), wd2:sgWD('2027-01-02'),
        mSpent:M.mSpent, past:sgYearPast(2027).md, days:[...Y.days.keys()] }; }""")
    print(tz, r)
    check(f'[{tz}] 今年は日本時間で 2027・1月:', r['now'] == [2027, 0] and r['y'] == 2027)
    check(f'[{tz}] 日本時間 1/1 0:00 の便は 2027年の1月に入る（12/31 23:00 の便は入らない）:', r['n'] == 1 and r['m0'] == 1 and r['m11'] == 0 and r['days'] == ['2027-01-01'])
    check(f'[{tz}] 2026年には 12/31 23:00 の便だけ（12月）:', r['n0'] == 1 and r['m011'] == 1)
    check(f'[{tz}] 日付と曜日は日本の暦（2027-01-01 は 1/1 金・1/2 は 土）:', r['md'] == '1/1' and r['wd'] == '金' and r['wd2'] == '土' and r['past'] == '1/1')
    check(f'[{tz}] 今月の使った額は 2027年1月の便だけ:', r['mSpent'] == 20000)
    # 画面：道のりの「次に乗る便」とホームの修行のカードの日付
    await pg.evaluate("openShugyo('main')"); await pg.clock.run_for(800)
    t = await pg.inner_text('#v-sg')
    check(f'[{tz}] 道のりの題は 2027年・次に乗る便は 1月2日（土）:', '1月2日（土）' in t and '07:00発' in t)
    box = await pg.evaluate("""async () => { const d = document.createElement('div'); document.body.appendChild(d); await renderShugyoCard(d); const s = d.innerText; d.remove(); return s; }""")
    check(f'[{tz}] ホームの修行のカード：2027年の修行・次の便は 2日 1月 土:', '2027年の修行' in box and '2\n1月 土' in box)
    if tz == 'Asia/Tokyo':   # 11/20 乗り継ぎは JAL の公式の値：空港を移るのは JAL だけ伊丹⇔関西 175分（ANA は 180分のまま）
        x = await pg.evaluate("[sgXfer('ITM','KIX','JAL'), sgXfer('KIX','ITM','JAL'), sgXfer('ITM','KIX','ANA'), sgXfer('HND','NRT','JAL'), sgXfer('CTS','OKD','JAL'), sgNextAps('ITM', 600, 'JAL').map(v => v.join()).join('|'), sgNextAps('ITM', 600, 'ANA').map(v => v.join()).join('|')]")
        print(x)
        check('乗り継ぎ：JAL の伊丹⇔関西は 175分・ANA は 180分・羽田⇔成田 180・新千歳⇔丘珠 150:', x[:5] == [175, 175, 180, 180, 150] and x[5] == 'ITM,620|KIX,775|UKB,770' and x[6] == 'ITM,625|KIX,780|UKB,770')
    check(f'[{tz}] エラーなし:', not errs)
    if errs: print(errs[:3])
    await b.close()
async def main():
    async with async_playwright() as p:
        for tz in ['Asia/Tokyo', 'UTC', 'America/Los_Angeles']: await run(p, tz)
asyncio.run(main())
print('errors', fails)
