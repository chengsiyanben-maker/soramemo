import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 修行：ポイントを自分で直せる欄と、確定・予約済みの見込みの2色の帯（11/25 PM・shugyo-manual-fix）
#   1便の内訳で運賃の種類・搭乗ボーナスを選び直し、確定の数を上書きできる。「自分で直した」の札・自動で数えた数・元に戻す。直しは shugyo_prefs の data.fix（便の記録は書き換えない）
import asyncio, json, re
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
JST = timezone(timedelta(hours=9)); NOW = datetime.now(JST); Y = NOW.year
J = lambda n: (NOW + timedelta(days=n)).strftime('%Y-%m-%d')
SHOT = os.environ.get('SORAMEMO_SHOT')   # 写真を残すフォルダ（なければ作業用フォルダ）
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo', device_scale_factor=2 if SHOT else 1)
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.persona','shugyo')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', lambda r: r.fulfill(status=200, body='[]', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        shot = lambda n, **k: pg.screenshot(path=os.path.join(SHOT or WORK, n), **k)
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        # 記録：今年の JAL 羽田⇄那覇 4便（セイバー 3便 1,676 FOP、最後の便は運賃なし＝推定でセイバー）
        await pg.evaluate(f"""() => {{ const h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id, F = __fake.db.flights; F.length = 0;
          const ts = [Date.UTC({Y}, 0, 10, 1), Date.UTC({Y}, 0, 11, 1), Date.UTC({Y}, 1, 3, 1), Date.now() - 3 * 864e5];
          ts.forEach((t, i) => F.push({{ id:301 + i, from_airport:i % 2 ? o : h, to_airport:i % 2 ? h : o, airline:'JL', flight_no:'JL90' + i, fare:i === 3 ? null : 'JAL:Y_SAVER', price:null, status:'verified', distance_km:1500,
            dep_at:new Date(t).toISOString(), arr_at:new Date(t + 9e6).toISOString() }})); }}""")
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.evaluate(f"""() => {{ const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.car = 'JAL'; g.goal.JAL = 'crystal';
          g.plans = [{{ id:'p1', d:'{J(5)}', hm:'07:00', from:h, to:o, car:'JAL', fare:'JAL:Y_SAVER', no:'JL903' }}, {{ id:'p2', d:'{J(6)}', hm:'18:00', from:o, to:h, car:'JAL', fare:'JAL:Y_SAVER', no:'JL918' }}]; g.drafts = []; }}""")
        await pg.evaluate("openShugyo('main')"); await pg.wait_for_timeout(700)
        check('はじめ：4便・6,704 FOP・推定 1便:', await pg.evaluate("[sgYear().JAL.pts, sgYear().JAL.n, sgYear().JAL.assumed]") == [6704, 4, 1])
        # 2色の帯：確定（実績）と予約済みの見込み（予定）。数字は足さない
        bar = await pg.evaluate("(() => { const b = document.querySelector('#v-sg .sgb-hero .sgb-bar:not(.thin)'), i = b.querySelectorAll('i'); return [i.length, i[0].style.width, i[1] && i[1].className, i[1] && i[1].style.left, i[1] && i[1].style.width, b.getAttribute('aria-label')]; })()")
        print('帯', bar)
        check('帯は2色（確定 22%・見込み 11%）:', bar[0] == 2 and bar[1] == '22%' and bar[2] == 'p' and bar[3] == '22%' and bar[4] == '11%' and '予約済みの見込み（予定）＋3,352' in bar[5])
        lg = await pg.inner_text('#v-sg .sgb-hero .sgb-lg')
        check('帯の下の札：確定 6,704・予約済みの見込み（予定）＋3,352（足した数は出さない）:', '確定 6,704' in lg and '予約済みの見込み（予定）＋3,352' in lg and '10,056' not in await pg.inner_text('#v-sg'))
        bg = await pg.evaluate("[getComputedStyle(document.querySelector('#v-sg .sgb-hero .sgb-bar i')).backgroundColor, getComputedStyle(document.querySelector('#v-sg .sgb-hero .sgb-bar i.p')).backgroundColor]")
        check('2色は違う色（見込みはうすい金色）:', bg[0] != bg[1] and bg[1] == 'rgb(233, 212, 155)')
        await shot('t199_road.png')
        # 1便ごと → 運賃が分からない便（いちばん新しい便）を押す → 直す
        await pg.click('#v-sg [data-sg-view="flights"]'); await pg.wait_for_timeout(300)
        await pg.locator('#v-sg [data-sg-fl]').first.click(); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg')
        check('内訳の下に「数を自分で直す」:', '数を自分で直す' in t and await pg.locator('#v-sg [data-sg-fixedit="1"]').count() == 1 and '便の記録を開く' in t)
        await pg.click('#v-sg [data-sg-fixedit="1"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#v-sg .sgb-fix')
        check('開くと運賃・搭乗ボーナス・確定の数（自動 1,676）:', await pg.locator('#sgFixFare').count() == 1 and await pg.evaluate("$('sgFixFare').value") == 'JAL:Y_SAVER' and '運賃どおり（200）' in t and '自動で数えた数：1,676 FOP' in t and await pg.evaluate("$('sgFixPts').placeholder") == '1676')
        check('ボーナスの選択肢は 運賃どおり・0・200・400:', await pg.evaluate("[...document.querySelectorAll('#v-sg [data-sg-fixb]')].map(b => b.dataset.sgFixb).join()") == ',0,200,400')
        await pg.select_option('#sgFixFare', 'JAL:Y_FLEX'); await pg.wait_for_timeout(300)
        check('運賃をフレックスにすると自動の数は 2,368（984×100%×2＋400）:', '自動で数えた数：2,368 FOP' in await pg.inner_text('#v-sg .sgb-fix'))
        check('保存する前は修行の数は変わらない:', await pg.evaluate("sgYear().JAL.pts") == 6704)
        await pg.fill('#sgFixPts', '2000')
        await pg.click('#v-sg [data-sg-fixb="0"]'); await pg.wait_for_timeout(300)
        check('ボーナス 0 で自動 1,968・入れかけの数は消えない:', '自動で数えた数：1,968 FOP' in await pg.inner_text('#v-sg .sgb-fix') and await pg.evaluate("$('sgFixPts').value") == '2000' and await pg.evaluate("document.querySelector('#v-sg [data-sg-fixb=\"0\"]').getAttribute('aria-pressed')") == 'true')
        await shot('t199_fix_edit.png', full_page=True)
        await pg.click('#v-sg [data-sg-fixsave]'); await pg.wait_for_timeout(500)
        fx = await pg.evaluate("__fake.db.shugyo_prefs[0].data.fix")
        check('保存：運賃・ボーナス・確定の数・日（キーは便の番号）:', fx == {'f304': {'fare': 'JAL:Y_FLEX', 'bonus': 0, 'pts': 2000, 'at': J(0)}})
        check('便の記録は書き換えない:', await pg.evaluate("__fake.db.flights.find(f => f.id === 304).fare") is None)
        check('修行の数：6,704 − 1,676 ＋ 2,000 ＝ 7,028・推定 0便:', await pg.evaluate("[sgYear().JAL.pts, sgYear().JAL.assumed]") == [7028, 0])
        t = await pg.inner_text('#v-sg')
        check('内訳：「自分で直した」・直した数 2,000・自動で数えた数 1,676・自分で選んだ運賃:', t.count('自分で直した') >= 2 and '2,000' in t and '1,676' in t and '自分で選んだ運賃' in t and '選んだ運賃とボーナスで数えた数' in t and '1,968' in t)
        await shot('t199_fix_done.png', full_page=True)
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(300)
        rows = await pg.evaluate("[...document.querySelectorAll('#v-sg [data-sg-fl]')].map(b => b.innerText.replace(/\\n/g, ' '))")
        print('行', rows[0])
        check('1便ごとの行にも札・＋2,000（直した便だけ）:', '自分で直した' in rows[0] and '＋2,000' in rows[0] and '（推定）' not in rows[0] and sum('自分で直した' in r for r in rows) == 1)
        await shot('t199_list.png')
        await pg.click('#v-sg [data-sg-view="road"]'); await pg.wait_for_timeout(300)
        check('道のりの大きな数字も 7,028・推定の便の札は消える:', '7,028' in await pg.inner_text('#v-sg .sgb-hero') and await pg.locator('#v-sg .sgb-est').count() == 0)
        # 開き直しても残る（サーバーから読み直す）
        await pg.evaluate("S.shugyo = null"); await pg.evaluate("__fake.login ? null : null")
        await pg.evaluate("(() => { S.shugyo = JSON.parse(JSON.stringify(__fake.db.shugyo_prefs[0].data)); })()")
        check('読み直しても直しは残る:', await pg.evaluate("sgYear().JAL.pts") == 7028)
        # 元に戻す
        await pg.click('#v-sg [data-sg-view="flights"]'); await pg.wait_for_timeout(300)
        await pg.locator('#v-sg [data-sg-fl]').first.click(); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-fixclear]'); await pg.wait_for_timeout(500)
        check('元に戻す：6,704・推定 1便・保存から消える:', await pg.evaluate("[sgYear().JAL.pts, sgYear().JAL.assumed]") == [6704, 1] and await pg.evaluate("__fake.db.shugyo_prefs[0].data.fix") == {} and '自分で直した' not in await pg.inner_text('#v-sg'))
        # ボーナスだけ直す（運賃の分かっている便）：確定の数は空 → 自動の数（セイバー 1,476 ＋ 400 ＝ 1,876）。推定の数は変わらない
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(300)
        await pg.locator('#v-sg [data-sg-fl]').nth(1).click(); await pg.wait_for_timeout(300)
        await pg.click('#v-sg [data-sg-fixedit="1"]'); await pg.wait_for_timeout(200)
        await pg.click('#v-sg [data-sg-fixb="400"]'); await pg.wait_for_timeout(200)
        await pg.click('#v-sg [data-sg-fixsave]'); await pg.wait_for_timeout(500)
        fx = await pg.evaluate("__fake.db.shugyo_prefs[0].data.fix")
        check('ボーナスだけ：保存はボーナスだけ・数は 6,904・推定 1便のまま:', list(fx.values())[0].keys() == {'bonus', 'at'} and await pg.evaluate("[sgYear().JAL.pts, sgYear().JAL.assumed]") == [6904, 1])
        t = await pg.inner_text('#v-sg')
        check('内訳の式：搭乗ボーナス（自分で選んだ）400 ＝ 1,876・札:', '搭乗ボーナス（自分で選んだ）' in t and '1,876' in t and '自分で直した' in t and '搭乗ボーナスを直しました' in t)
        # やめると何も変わらない
        await pg.click('#v-sg [data-sg-fixedit="1"]'); await pg.wait_for_timeout(200)
        await pg.fill('#sgFixPts', '99'); await pg.click('#v-sg [data-sg-fixedit="0"]'); await pg.wait_for_timeout(300)
        check('やめる：数は変わらない:', await pg.evaluate("sgYear().JAL.pts") == 6904)
        # おかしな数は保存しない
        await pg.click('#v-sg [data-sg-fixedit="1"]'); await pg.wait_for_timeout(200)
        await pg.fill('#sgFixPts', '50000'); await pg.click('#v-sg [data-sg-fixsave]'); await pg.wait_for_timeout(300)
        check('20,000 を超える数は保存しない（欄に戻る）:', await pg.evaluate("sgYear().JAL.pts") == 6904 and await pg.locator('#sgFixPts').count() == 1)
        await pg.click('#v-sg [data-sg-fixedit="0"]'); await pg.wait_for_timeout(200)
        # 予定がない・届いている：帯は1色
        await pg.click('#v-sg .sg-back'); await pg.wait_for_timeout(200)
        await pg.click('#v-sg [data-sg-view="road"]'); await pg.wait_for_timeout(200)
        await pg.evaluate("(() => { sgGet().plans = []; sgKeep(() => {}); })()"); await pg.wait_for_timeout(300)
        check('予定がないと帯は1色・札は出ない:', await pg.locator('#v-sg .sgb-hero .sgb-bar:not(.thin) i').count() == 1 and await pg.locator('#v-sg .sgb-lg').count() == 0)
        # 夜：金を使わない
        await pg.evaluate(f"""(() => {{ const g = sgGet(), h = A.find(a => a.iata === 'HND').id, o = A.find(a => a.iata === 'OKA').id; g.plans = [{{ id:'p1', d:'{J(5)}', hm:'07:00', from:h, to:o, car:'JAL', fare:'JAL:Y_SAVER', no:'JL903' }}]; document.documentElement.dataset.night = 'on'; sgKeep(() => {{}}); }})()"""); await pg.wait_for_timeout(300)
        nb = await pg.evaluate("getComputedStyle(document.querySelector('#v-sg .sgb-hero .sgb-bar i.p')).backgroundColor")
        check('夜の見込みは緑のうすい色（金でない）:', nb == 'rgba(74, 222, 128, 0.35)')
        await shot('t199_night.png')
        await pg.click('#v-sg [data-sg-view="flights"]'); await pg.wait_for_timeout(200)
        await pg.locator('#v-sg [data-sg-fl]').nth(1).click(); await pg.wait_for_timeout(300)
        await shot('t199_night_fix.png', full_page=True)
        print('errors', errs); await b.close()
        if errs: fails.append('errors')
    print('fails', fails); print('errors', fails if fails else [])
    sys.exit(1 if fails else 0)
asyncio.run(main())
