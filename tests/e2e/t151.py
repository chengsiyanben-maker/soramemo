import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 図鑑とフライトの小さい直し（11/20 PM のおすすめ・report-zukan-filter-app と report-flight-actual-app の「決めてほしいこと」）
#   図鑑：地図の見方の「まだ」の一覧は5行だけ出し、「残り○か所 ›」で全部開く。種類や見方を変えたら畳み直す
#   フライト：実際の時刻がある便は、くわしくの「出発・到着」も実際の時刻。下に小さくチェックインの時刻を1行（取り先は「空の上」の箱に出ているので重ねない）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(os.path.dirname(HERE), '..', 'docs', 'pm', 'shots-small-1120'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
# 便7 羽田→新千歳：ODPT の実際の時刻（チェックインの出発の15分あと・80分）
ACT = """window.__flightsAct = fl => { const f7 = fl.find(x => x.id === 7);
  const d7 = Date.parse(f7.dep_at) + 15 * 6e4; f7.act_dep_at = new Date(d7).toISOString(); f7.act_arr_at = new Date(d7 + 80 * 6e4).toISOString(); f7.act_src = 'odpt'; };"""
async def page(b, init):
    c = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.abort())
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1800)
    return c, pg, errs
YET = '(() => [document.querySelectorAll("#bookAir .zx-list .r").length, (document.querySelector("#bookAir .zx-list h4") || {}).textContent || "", (document.getElementById("zkxYetMore") || {}).textContent || ""])()'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- 図鑑 ----
        c, pg, errs = await page(b, "localStorage.setItem('soramemo.zkx.view','map');")
        await pg.evaluate('(() => { goTab("book"); setBookSeg("air"); DIRTY.book = true; renderVisible(); window.scrollTo(0, 0); })()'); await pg.wait_for_timeout(600)
        total = await pg.evaluate('zkxCounts().list.filter(a => !zkxCounts().xv.has(a.id)).length')
        y = await pg.evaluate(YET)
        check('図鑑：はじめは5行だけ・「残り○か所」', y[0] == 5 and f'まだ {total}' in y[1] and f'残り{total - 5}か所' in y[2], [total, y])
        h = await pg.evaluate('document.getElementById("zkxYetMore").getBoundingClientRect().height')
        check('図鑑：「残り」のボタンは押しやすい高さ（44px 以上）', h >= 44, h)
        await pg.evaluate('document.getElementById("zkxYetMore").scrollIntoView({block:"center"})'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, 'zukan-yet-5.png'))
        await pg.click('#zkxYetMore'); await pg.wait_for_timeout(400)
        y = await pg.evaluate(YET)
        check('図鑑：押すと全部開く・ボタンは消える', y[0] == total and y[2] == '', y)
        foc = await pg.evaluate('document.activeElement === document.querySelectorAll("#bookAir .zx-list .r")[5]')
        check('図鑑：開いたら6行目に移る（キーボードで続けて読める）', foc, foc)
        await pg.click('#zkxSeg [data-zxk="glider"]'); await pg.wait_for_timeout(400)
        y = await pg.evaluate(YET); g = await pg.evaluate('zkxCounts().list.filter(a => a.kind === "glider" && !zkxCounts().xv.has(a.id)).length')
        check('図鑑：種類を変えると畳み直す（滑空場）', y[0] == min(5, g) and (g <= 5 or f'残り{g - 5}か所' in y[2]), [g, y])
        await pg.click('#zkxSeg [data-zxk="all"]'); await pg.click('#zkxViews [data-zxv="region"]'); await pg.wait_for_timeout(400)
        n = await pg.evaluate('[document.querySelectorAll("#bookAir .zx-list").length, document.querySelectorAll("#bookAir .zk-grid .zx-ap").length]')
        check('図鑑：地方別の見方は今までどおり（一覧なし・枠は全部）', n[0] == 0 and n[1] == await pg.evaluate('zkxCounts().list.length'), n)
        await pg.evaluate('localStorage.setItem("soramemo.zkx.view","region")')
        check('図鑑：エラーなし', not errs, errs); await c.close()
        # ---- フライト ----
        c, pg, errs = await page(b, ACT)
        await pg.evaluate('(() => { goTab("log"); setLogSeg("list"); VIEW.log = "diary"; DIRTY.log = true; renderVisible(); window.scrollTo(0, 0); })()'); await pg.wait_for_timeout(600)
        exp = await pg.evaluate('(() => { const f = S.flights.find(x => x.id === 7), g = S.flights.find(x => x.id === 9); return { k7: fid(f), k9: fid(g), ad: hmOf(f.actDep), aa: hmOf(f.actArr), cd: hmOf(f.dep), ca: hmOf(f.arr), d9: hmOf(g.dep), a9: hmOf(g.arr) }; })()')
        await pg.evaluate(f'fbOpenView({exp["k7"]!r})'); await pg.wait_for_timeout(500)
        t = await pg.evaluate('(() => { const d = document.getElementById("dFbView"); return { times: [...d.querySelectorAll(".fvhead .times b")].map(x => x.textContent), src: (d.querySelector(".fvhead .fvsrc") || {}).textContent || "", fs: d.querySelector(".fvhead .fvsrc") ? parseFloat(getComputedStyle(d.querySelector(".fvhead .fvsrc")).fontSize) : 0 }; })()')
        check('フライト：実際の時刻の便はくわしくの出発・到着も実際の時刻', t['times'] == [exp['ad'], exp['aa']], [t, exp])
        check('フライト：下に1行だけチェックインの時刻（取り先は空の上の箱にある）', t['src'] == f'チェックイン {exp["cd"]}〜{exp["ca"]}', t['src'])
        check('フライト：その1行は小さい字（12px）', t['fs'] == 12, t['fs'])
        await pg.screenshot(path=os.path.join(SHOTS, 'flight-view-act.png'))
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        await pg.evaluate(f'fbOpenView({exp["k9"]!r})'); await pg.wait_for_timeout(500)
        t = await pg.evaluate('(() => { const d = document.getElementById("dFbView"); return [[...d.querySelectorAll(".fvhead .times b")].map(x => x.textContent), !!d.querySelector(".fvhead .fvsrc")]; })()')
        check('フライト：実際の時刻がない便は今までどおり（チェックインの時刻・1行なし）', t == [[exp['d9'], exp['a9']], False], t)
        check('フライト：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
