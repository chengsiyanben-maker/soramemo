import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 案をくらべる（P3）・年末までの道のり（P4）：案は計画として別に出し、実績・予定とまぜない。案を足したときの届く日。案を予定に入れる。乗れる日
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
J = lambda n: (datetime.now(timezone.utc) + timedelta(hours=9) + timedelta(days=n)).strftime('%Y-%m-%d')
D1, D2, D3, D4 = J(7), J(10), J(12), J(14)
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        # 記録：羽田→那覇・那覇→羽田・羽田→那覇（ANA フレックス、今年）
        await pg.evaluate("""() => { const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, F = __fake.db.flights, t = Date.now() - 20 * 864e5;
          [[h, o], [o, h], [h, o]].forEach(([a, b], i) => Object.assign(F[i], { from_airport:a, to_airport:b, airline:'NH', flight_no:'NH46' + i, fare:'ANA:E_FLEX', price:i ? null : 30000,
            dep_at:new Date(t + i * 864e5).toISOString(), arr_at:new Date(t + i * 864e5 + 9e6).toISOString() })); }""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        leg = lambda no, dep, arr, d, a: f"{{ no:'{no}', dep:'{dep}', arr:'{arr}', d:{d}, a:{a}, ac:null }}"
        rt = lambda n, start: ', '.join(leg(f'NH{900+i}', 'HND' if i % 2 == 0 else 'OKA', 'OKA' if i % 2 == 0 else 'HND', start + i * 170, start + i * 170 + 150) for i in range(n))
        await pg.evaluate(f"""() => {{ const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.car = 'ANA'; g.goal.ANA = 30000;
          g.plans = [0, 1, 2, 3].map(i => ({{ id:'p' + i, d:'{D1}', hm:(6 + i * 3) + ':00', from:i % 2 ? o : h, to:i % 2 ? h : o, car:'ANA', fare:'ANA:E_FLEX', no:'NH' + (500 + i) }}));
          g.drafts = [{{ id:'dA', d:'{D2}', car:'ANA', fare:'ANA:E_FLEX', home:'HND', start:'05:00', end:'23:59', legs:[{rt(8, 300)}], pts:0 }},
                      {{ id:'dB', d:'{D3}', car:'ANA', fare:'ANA:E_FLEX', home:'HND', start:'05:00', end:'23:59', legs:[{rt(2, 400)}], pts:0 }}];
          g.days = ['{D4}']; }}""")
        before = await pg.evaluate("[sgYear().ANA.pts, sgFuture().length, sgPlanSum('ANA', sgYear()).pts]")
        print('実績・予定の数', before)
        # P3 案をくらべる
        await pg.evaluate("openShugyo('compare')"); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#v-sg'); print('CMP', t[:700].replace('\n', ' | '))
        check('くらべる：2つの案を表で（案A 8区間・案B 2区間）:', '2つの案' in t and '案A' in t and '案B' in t and '+18,944' in t and '+4,736' in t)
        check('くらべる：計画の印と「まだ予定ではありません」:', '計画' in t and 'まだ予定ではありません' in t)
        check('効き：実績と予定に案Aを足すと届く・案Bでは届かない:', f"に届く" in t and '年内は届かない' in t)
        r = await pg.evaluate("(() => { const Y = sgYear(), g = sgGoal('ANA', Y); return [sgReachWith(g, Y, sgDraftItems(sgDrafts('ANA')[0])).d, sgReachWith(g, Y, []).d || null]; })()")
        check('案Aを足すと、案Aの日に届く（予定だけでは届かない）:', r == [D2, None])
        check('くらべても実績・予定は変わらない:', await pg.evaluate("[sgYear().ANA.pts, sgFuture().length, sgPlanSum('ANA', sgYear()).pts]") == before)
        await pg.locator('#v-sg .sgcmp').screenshot(path=os.path.join(WORK, 't76_compare.png'))
        # P4 年末までの道のり
        await pg.evaluate("sgGo('road')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#v-sg'); print('ROAD', t[-600:].replace('\n', ' | '))
        check('道のり：実績（記録だけ）・予定・案を別々に:', 'きょうまで' in t and '記録した便だけ' in t and '予定だけなら' in t and '予定に案Aも足すと' in t and '予定に案Bも足すと' in t)
        check('道のり：予定の日と案の日がカレンダーに:', await pg.locator(f'#v-sg [data-sg-day="{D1}"].pp').count() == 1 and await pg.locator(f'#v-sg [data-sg-day="{D2}"].pd').count() == 1 and await pg.locator(f'#v-sg [data-sg-day="{D4}"].fr').count() == 1)
        check('道のり：予定の行（羽田⇄那覇 2往復 +9,472）:', '羽田⇄那覇 2往復' in t and '+9,472' in t)
        await pg.screenshot(path=os.path.join(WORK, 't76_road.png'), full_page=True)
        d5 = J(16)
        await pg.click(f'#v-sg [data-sg-day="{d5}"]'); await pg.wait_for_timeout(300)
        check('日付を押すと乗れる日になる:', d5 in await pg.evaluate("sgGet().days"))
        await pg.click('#v-sg [data-sg-roadfind]'); await pg.wait_for_timeout(400)
        check('乗れる日の案を作る → 探す画面（その日）:', await pg.evaluate("SG_PAGE") == 'find' and await pg.evaluate("sgGet().pq.d") == D4)
        # 案Aを予定に入れる
        await pg.evaluate("sgGo('compare')"); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-d2plan="dA"]'); await pg.wait_for_timeout(400)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data")
        check('案Aを予定に入れると、予定に8便・案から消える:', len([x for x in d['plans'] if x['d'] == D2]) == 8 and [x['id'] for x in d['drafts']] == ['dB'] and bool(d['plans'][-1]['hm']) and '翌' not in d['plans'][-1]['hm'])
        check('予定に入れたあとの結論（予定だけで届く）:', await pg.evaluate("(() => { const Y = sgYear(); return sgReachWith(sgGoal('ANA', Y), Y, []).d; })()") == D2)
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
