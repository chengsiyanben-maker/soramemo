import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 実績の確認：過ぎた予定（記録あり／乗った→記録帳／乗らなかった／あとで／確認しました）と、いまのポイントを合わせる（実績にする・控えにする・30日のお知らせ）
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
J = lambda n: (datetime.now(timezone.utc) + timedelta(hours=9) + timedelta(days=n)).strftime('%Y-%m-%d')
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
        d3, d1 = J(-3), J(-1)
        # 記録：3日前の羽田→那覇（ANA フレックス）
        await pg.evaluate(f"""() => {{ const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, F = __fake.db.flights, t = Date.parse('{d3}T08:00:00+09:00');
          Object.assign(F[0], {{ from_airport:h, to_airport:o, airline:'NH', flight_no:'NH461', fare:'ANA:E_FLEX', price:null, dep_at:new Date(t).toISOString(), arr_at:new Date(t + 9e6).toISOString() }});
          F.splice(1); }}""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.evaluate(f"""() => {{ const g = sgGet(), id = c => A.find(a => a.iata === c).id; g.car = 'ANA';
          g.plans = [{{ id:'p1', d:'{d3}', hm:'8:00', from:id('HND'), to:id('OKA'), car:'ANA', fare:'ANA:E_FLEX', no:'NH461' }},
                     {{ id:'p2', d:'{d3}', hm:'12:00', from:id('OKA'), to:id('HND'), car:'ANA', fare:'ANA:E_FLEX', no:'NH468', price:25000 }},
                     {{ id:'p3', d:'{d1}', hm:'7:00', from:id('HND'), to:id('ITM'), car:'ANA', fare:'ANA:E_FLEX', no:'NH15' }}];
          goTab('home'); renderPersonaCard(); }}""")
        await pg.wait_for_timeout(400)
        t = await pg.inner_text('#personaCard'); print('CARD', t[:400].replace('\n', ' | '))
        check('過ぎた予定を日ごとに確かめる:', '乗りましたか' in t and t.count('乗りましたか') == 2)
        check('記録のある便は「実績に入っています」:', '記録あり・実績に入っています' in t)
        await pg.locator('#personaCard .sgcf').first.screenshot(path=os.path.join(WORK, 't77_confirm.png'))
        pts0 = await pg.evaluate("sgYear().ANA.pts")
        await pg.click('#personaCard [data-sg-cf="flew:p2"]'); await pg.wait_for_timeout(1200)
        m = await pg.evaluate("__fake.db.manual_flights")
        check('乗った → 記録帳に入る（航空会社・運賃・金額は予定のもの）:', len(m) == 1 and m[0]['flown_on'] == d3 and m[0]['airline'] == 'NH' and m[0].get('fare') == 'ANA:E_FLEX' and m[0].get('price') == 25000)
        check('乗った便は実績に足される（+2,368）:', await pg.evaluate("sgYear().ANA.pts") == pts0 + 2368)
        check('乗った予定は予定から消える:', 'p2' not in await pg.evaluate("sgGet().plans.map(p => p.id)"))
        await pg.click('#personaCard [data-sg-cf="no:p3"]'); await pg.wait_for_timeout(500)
        check('乗らなかった → 予定から消える:', 'p3' not in await pg.evaluate("sgGet().plans.map(p => p.id)"))
        t = await pg.inner_text('#personaCard')
        check('記録だけの日は「確認しました」:', '確認しました' in t)
        await pg.click(f'#personaCard [data-sg-cf="ok:{d3}"]'); await pg.wait_for_timeout(500)
        check('確認しましたで、その日の予定を片づける:', await pg.evaluate("sgGet().plans.length") == 0 and '乗りましたか' not in await pg.inner_text('#personaCard'))
        await pg.evaluate(f"sgGet().plans.push({{ id:'p4', d:'{d1}', hm:'9:00', from:A.find(a => a.iata === 'HND').id, to:A.find(a => a.iata === 'FUK').id, car:'ANA', fare:'ANA:E_FLEX' }}); renderPersonaCard()"); await pg.wait_for_timeout(300)
        await pg.click('#personaCard [data-sg-cf="later:p4"]'); await pg.wait_for_timeout(500)
        check('あとで → きょうは出さない（予定は残る）:', '乗りましたか' not in await pg.inner_text('#personaCard') and await pg.evaluate("sgGet().plans[0].later") == J(0))
        # いまのポイントを合わせる
        rec = await pg.evaluate("sgYear().ANA.pts")
        await pg.evaluate("openShugyo('profile')"); await pg.wait_for_timeout(400)
        t = await pg.inner_text('#v-sg'); check('会員情報に「いまのポイントを合わせる」:', 'いまのポイントを合わせる' in t and 'そらメモの記録から' in t)
        await pg.fill('#sgSyP', '36200'); await pg.click('#v-sg [data-sg-sync]'); await pg.wait_for_timeout(500)
        check('サイトの数字を実績にする:', await pg.evaluate("sgYear().ANA.pts") == 36200 and await pg.evaluate("sgYear().ANA.rec.pts") == rec)
        t = await pg.inner_text('#v-sg'); check('ちがいを出す:', f"+{36200 - rec:,} PP" in t and 'サイトの数字を実績にしました' in t)
        d = await pg.evaluate("__fake.db.shugyo_prefs[0].data.sync.ANA")
        check('保存される（日付つき）:', d['pts'] == 36200 and d['at'] == J(0) and d['use'] is True)
        await pg.evaluate("sgGo('main')"); await pg.wait_for_timeout(300)
        check('修行のまとめ：合わせた数字と出どころ:', '36,200' in await pg.inner_text('#v-sg') and 'に合わせた数字' in await pg.inner_text('#v-sg'))
        await pg.screenshot(path=os.path.join(WORK, 't77_main.png'))
        await pg.evaluate("sgGo('profile')"); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-syuse="0"]'); await pg.click('#v-sg [data-sg-sync]'); await pg.wait_for_timeout(500)
        check('記録だけで数える（サイトの数字は控え）:', await pg.evaluate("sgYear().ANA.pts") == rec and await pg.evaluate("sgGet().sync.ANA.pts") == 36200)
        # 30日たったらお知らせ
        await pg.evaluate(f"sgGet().sync.ANA = {{ pts:36200, at:'{J(-40)}', use:true, recAt:{rec} }}; goTab('home'); renderPersonaCard()"); await pg.wait_for_timeout(400)
        check('30日たつとホームでお知らせ:', 'いまのポイントを合わせませんか' in await pg.inner_text('#personaCard'))
        print('errors', errs, 'fails', fails); await b.close()
        sys.exit(1 if fails or errs else 0)
asyncio.run(main())
