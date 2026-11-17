import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 図鑑の飛行場・滑空場（決定事項【11/17】・design/zukan-airfields）の残り
#   「番外編」の言葉は使わない（基地の図鑑は「基地」・空港ページの説明・実績の見出し・記録の選ぶ欄）
#   夜の小さな地図で滑空場は四角（昼は今までどおり丸だけ）
#   入口は黒いカードのすぐ下・「ほかの図鑑・実績」の行も残す（PR #75 のまま）・ヘリポートの札はデータが入ったので出す
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(WORK, 'zukan_air_shots'); os.makedirs(SHOTS, exist_ok=True)
KAZO = (36.1311, 139.6017)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, h=844):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, geolocation={'latitude':KAZO[0],'longitude':KAZO[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1500)
    # 行った所：加須滑空場・大利根滑空場（近くで重なる→滑空場の数の丸）・竜ヶ崎飛行場・妻沼滑空場・東京ヘリポート・羽田
    await pg.evaluate("""(() => { const t = Date.now() - 864e5 * 30; S.checkins.push({a:2015, t}, {a:2014, t:t + 1e6}, {a:3002, t:t + 2e6}, {a:2017, t:t + 3e6}, {a:1001, t:t + 4e6}, {a:IATA.HND.id, t:t + 5e6}); for(const k in DIRTY) DIRTY[k] = true; goTab("book"); })()""")
    await pg.wait_for_timeout(700)
    return c, pg, errs
VIS = """(() => [...document.querySelectorAll('#zkBody .zxmap :is(circle,rect)')].filter(e => getComputedStyle(e).display !== 'none').reduce((m, e) => { const k = e.tagName + '.' + [...e.classList].filter(c => c !== 'zd' && c !== 'zn').join('.'); m[k] = (m[k] || 0) + 1; return m; }, {}))()"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c, pg, errs = await page(b)
        # 夜の四角：昼は丸だけ・夜は滑空場が四角
        day = await pg.evaluate(VIS)
        check('昼の小さな地図：四角はない（今までどおり丸だけ）', not any(k.startswith('rect') for k in day), day)
        n_gl = await pg.evaluate("zkxList().filter(a => a.kind === 'glider' && a.lat > 30.5 && a.lon > 128.4).length")
        await pg.evaluate('document.documentElement.dataset.night = "on"'); await pg.wait_for_timeout(300)
        night = await pg.evaluate(VIS)
        sq = sum(v for k, v in night.items() if k.startswith('rect'))
        check('夜の小さな地図：滑空場は四角（まだの点も行った丸も）', sq >= n_gl - 3 and night.get('rect.my', 0) > 20 and night.get('rect.mv', 0) >= 1, night)
        gl_circle = await pg.evaluate("[...document.querySelectorAll('#zkBody .zxmap circle.zd')].filter(e => getComputedStyle(e).display !== 'none').length")
        check('夜の小さな地図：滑空場の丸は隠れる', gl_circle == 0, gl_circle)
        lg = await pg.evaluate("[...document.querySelectorAll('#zkBody .zx-kd i')].map(i => [i.className, getComputedStyle(i).display, getComputedStyle(i).borderRadius])")
        g = [x for x in lg if x[0] == 'k-glider']; f = [x for x in lg if x[0] == 'k-field']
        check('夜の凡例：滑空場は四角・飛行場は丸で見える', g and g[0][1] != 'none' and g[0][2] == '2px' and f and f[0][1] != 'none' and f[0][2] != '2px', lg)
        el = await pg.query_selector('#zkBody .zx-entry'); await el.screenshot(path=os.path.join(SHOTS, '01-entry-night.png'))
        await pg.evaluate('delete document.documentElement.dataset.night'); await pg.wait_for_timeout(300)
        await el.screenshot(path=os.path.join(SHOTS, '02-entry-day.png'))
        # 入口・ヘリポートの札（データが入ったので出す）
        e = await pg.inner_text('#zkBody .zx-entry')
        check('入口：黒いカードのすぐ下・内訳にヘリポート', await pg.evaluate('!!document.querySelector("#zkBody .zk-hero + .zx-entry")') and 'ヘリポート' in e, e.replace('\n', ' '))
        # ほかの図鑑・実績：飛行場の行が残る・基地の図鑑は「基地」
        await pg.click('#bookMain [data-zkseg="others"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#bookOthers')
        check('ほかの図鑑・実績：「番外編」の字がない・「基地」の行・飛行場の図鑑の行', '番外編' not in t and '基地' in t and '飛行場・滑空場・ヘリポートの図鑑' in t.replace('\n', ''), t.replace('\n', ' ')[:200])
        await pg.screenshot(path=os.path.join(SHOTS, '03-others.png'))
        await pg.click('#bookOthers [data-zkseg="extra"]'); await pg.wait_for_timeout(300)
        h = await pg.inner_text('#bookExtra .book-head h2')
        check('基地の図鑑の題は「基地」', h == '基地', h)
        await pg.click('#bookExtra [data-zkseg="others"]'); await pg.wait_for_timeout(200)
        # 実績の見出し
        cats = await pg.evaluate('[...new Set(ACH.map(x => x.cat))]')
        check('実績の見出しに「番外編」がない', not any('番外編' in x for x in cats), [x for x in cats if '番外' in x or x in ('基地', '滑空場', '飛行場')])
        await pg.evaluate("setBookSeg('ach'); renderVisible()"); await pg.wait_for_timeout(300)
        a = await pg.inner_text('#bookAch')
        check('実績の画面：飛行場・滑空場の実績のまとまりが残り、「番外編」の字がない', '飛行場・滑空場の実績' in a and '番外編' not in a, a[:120].replace('\n', ' '))
        # 空港ページの説明（滑空場・基地）
        r = await pg.evaluate("""(() => { const out = []; for(const id of [2015, 1001, 3002]){ openAirport(id); const d = document.querySelector('#dAirport') || document.body; out.push(d.innerText); } return out; })()""")
        check('空港ページ：「番外編」の字がない（滑空場・基地・飛行場）', all('番外編' not in x for x in r) and '滑空場' in r[0], [x[:60].replace('\n', ' ') for x in r])
        # 記録の選ぶ欄
        og = await pg.evaluate("[...document.querySelectorAll('optgroup')].map(o => o.label).filter(l => /番外|滑空|基地|自衛隊|飛行場|ヘリ/.test(l))")
        check('選ぶ欄の見出し：「番外編」がない', not any('番外編' in x for x in og), og)
        # 文書の全体（見える字）
        body = await pg.evaluate("document.body.innerText")
        check('画面の字に「番外編」がない', '番外編' not in body)
        check('エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
