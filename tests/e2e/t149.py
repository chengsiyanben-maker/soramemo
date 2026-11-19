import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 飛行場・滑空場・ヘリポートの図鑑：種類の絞り込みと県名（11/20 本人「飛行場、滑空場、ヘリポートのフィルター機能、すべてに何県か表示して」・画面案 design/zukan-filter 1版 F1〜F3）
#   ピルは「すべて 75・飛行場 30・滑空場 33・ヘリポート 12」。基地は別の図鑑のまま。見方は「地方別・地図」。どちらも端末に覚える
#   県名は全部の枠に 13px 以上の薄いグレー（取っていない所も）。1つの種類に絞ったら枠の種類の札を外す
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(os.path.dirname(HERE), '..', 'docs', 'pm', 'shots-zukan-filter'); os.makedirs(SHOTS, exist_ok=True)
KAZO = (36.1311, 139.6017)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, h=844, init=''):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, geolocation={'latitude':KAZO[0],'longitude':KAZO[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1500)
    # 加須滑空場・ホンダエアポート・竜ヶ崎飛行場（2回）・東京ヘリポート を行った所にする
    await pg.evaluate("""(() => { const t = Date.now() - 864e5 * 30; S.checkins.push({a:2015, t}, {a:3002, t:t + 1e6}, {a:3004, t:t + 2e6}, {a:3004, t:t + 3e6}, {a:5006, t:t + 4e6}); for(const k in DIRTY) DIRTY[k] = true; goTab("book"); setBookSeg("air"); DIRTY.book = true; renderVisible(); window.scrollTo(0, 0); })()""")
    await pg.wait_for_timeout(600)
    return c, pg, errs
STATE = """(() => { const q = s => [...document.querySelectorAll(s)];
  return { pills: q("#zkxSeg [data-zxk]").map(b => [b.dataset.zxk, b.querySelector(".u").textContent, b.getAttribute("aria-pressed")]),
    tiles: q("#bookAir .zk-grid .zx-ap").length, num: (document.querySelector("#bookAir .zx-hero .num") || {}).textContent, u: (document.querySelector("#bookAir .zx-hero .u") || {}).textContent,
    lab: (document.querySelector("#bookAir .zx-hero .lab") || {}).textContent, rgs: q("#bookAir .zk-rg").map(x => x.dataset.rg),
    kinds: q("#bookAir .zk-grid .zx-ap").map(x => x.querySelector(".zx-k").textContent), kvis: q("#bookAir .zx-ap .zx-k").filter(x => x.offsetParent).length,
    dtag: q("#bookAir .zx-dtag").length, tsume: !!document.getElementById("zkxTsume"), map: !!document.querySelector("#bookAir .zx-bigmap"),
    view: q("#zkxViews [data-zxv]").map(b => [b.dataset.zxv, b.getAttribute("aria-selected")]) }; })()"""
PREFS = """(() => [...document.querySelectorAll("#bookAir .zk-grid .zx-ap")].map(x => { const p = x.querySelector(".zx-pf"), r = p.getBoundingClientRect(), t = x.getBoundingClientRect(), cs = getComputedStyle(p);
  return { id:+x.dataset.zka, pf:p.textContent, fs:parseFloat(cs.fontSize), vis:r.height > 0, inside:r.left >= t.left - 0.5 && r.right <= t.right + 0.5 && r.bottom <= t.bottom + 0.5, cut:p.scrollWidth > p.clientWidth + 1, col:cs.color }; }))()"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for hh in (844, 667):
            c, pg, errs = await page(b, hh)
            s = await pg.evaluate(STATE)
            check(f'{hh} はじめは「すべて」・地方別', s['pills'] == [['all', '75', 'true'], ['field', '30', 'false'], ['glider', '33', 'false'], ['heli', '12', 'false']] and s['view'] == [['region', 'true'], ['map', 'false']], s['pills'])
            check(f'{hh} すべて：75枠・4 / 75・種類の札が見える・扉の札あり・ツメあり', s['tiles'] == 75 and s['num'] == '4' and '75' in s['u'] and s['kvis'] == 75 and s['dtag'] == 8 and s['tsume'], [s['tiles'], s['num'], s['kvis'], s['dtag']])
            pr = await pg.evaluate(PREFS)
            truth = await pg.evaluate('Object.fromEntries(XA.map(a => [a.id, a.pref]))')
            check(f'{hh} 県名が全部の枠に出る（取っていない所も・データの県名と同じ）', len(pr) == 75 and all(x['vis'] and x['pf'] and x['pf'] == truth[str(x['id'])] for x in pr), [x for x in pr if not (x['vis'] and x['pf'])][:3])
            check(f'{hh} 県名の字は 13px 以上', all(x['fs'] >= 13 for x in pr), sorted({x['fs'] for x in pr}))
            check(f'{hh} 県名が枠からはみ出さない・切れない', all(x['inside'] and not x['cut'] for x in pr), [x['pf'] for x in pr if not (x['inside'] and not x['cut'])])
            check(f'{hh} 県名は薄いグレー（本文の色より薄い）', len({x['col'] for x in pr}) == 1 and pr[0]['col'] != 'rgb(0, 0, 0)', pr[0]['col'])
            if hh == 844: await pg.screenshot(path=os.path.join(SHOTS, 'f1-all-844.png'))
            # 横にはみ出さない
            ow = await pg.evaluate('document.documentElement.scrollWidth - innerWidth')
            check(f'{hh} 横にはみ出さない', ow <= 0, ow)
            # ヘリポートに絞る（F2）
            await pg.click('#zkxSeg [data-zxk="heli"]'); await pg.wait_for_timeout(400)
            s = await pg.evaluate(STATE)
            check(f'{hh} ヘリポート：12枠・1 / 12・頭は「ヘリポート」', s['tiles'] == 12 and s['num'] == '1' and '12' in s['u'] and 'ヘリポート' in s['lab'] and set(s['kinds']) == {'ヘリポート'}, [s['tiles'], s['num'], s['u'], s['lab']])
            check(f'{hh} ヘリポート：枠の種類の札を外す・扉の札なし', s['kvis'] == 0 and s['dtag'] == 0, [s['kvis'], s['dtag']])
            check(f'{hh} ヘリポート：中身のない地方は扉を出さず、ツメは押せない', '沖縄' not in s['rgs'] and '四国' not in s['rgs'] and await pg.evaluate('document.querySelector("#zkxTsume [data-zkj=\'沖縄\']").disabled'), s['rgs'])
            pr = await pg.evaluate(PREFS)
            check(f'{hh} ヘリポート：県名は出たまま', len(pr) == 12 and all(x['vis'] and x['pf'] for x in pr))
            check(f'{hh} ヘリポート：押したピルが選ばれた形', [x[2] for x in s['pills']] == ['false', 'false', 'false', 'true'])
            if hh == 844: await pg.screenshot(path=os.path.join(SHOTS, 'f2-heli-844.png'))
            if hh == 667: await pg.screenshot(path=os.path.join(SHOTS, 'f2-heli-667.png'))
            # 飛行場・滑空場の数
            await pg.click('#zkxSeg [data-zxk="field"]'); await pg.wait_for_timeout(300)
            s = await pg.evaluate(STATE)
            check(f'{hh} 飛行場：30枠・2 / 30', s['tiles'] == 30 and s['num'] == '2' and set(s['kinds']) == {'飛行場'}, [s['tiles'], s['num']])
            await pg.click('#zkxSeg [data-zxk="glider"]'); await pg.wait_for_timeout(300)
            s = await pg.evaluate(STATE)
            check(f'{hh} 滑空場：33枠・1 / 33', s['tiles'] == 33 and s['num'] == '1' and set(s['kinds']) == {'滑空場'}, [s['tiles'], s['num']])
            # 地図（F3）：同じピルが効く
            await pg.click('#zkxSeg [data-zxk="heli"]'); await pg.wait_for_timeout(300)
            await pg.click('#zkxViews [data-zxv="map"]'); await pg.wait_for_timeout(400)
            s = await pg.evaluate(STATE)
            m = await pg.evaluate('(() => ({ yet: document.querySelectorAll("#bookAir .zx-bigmap circle.my").length, got: document.querySelectorAll("#bookAir .zx-bigmap circle.mv").length, names:[...document.querySelectorAll("#bookAir .zx-bigmap text")].map(t => t.textContent), rows:[...document.querySelectorAll("#bookAir .zx-list .r")].map(r => r.querySelector(".pf").textContent), h4:(document.querySelector("#bookAir .zx-list h4") || {}).textContent }))()')
            check(f'{hh} 地図：ヘリポートだけ（行った1・まだ11）・名前は行った所', s['map'] and m['got'] == 1 and m['yet'] == 11 and m['names'] == ['東京'], m)
            check(f'{hh} 地図：まだの一覧に県名・見出しは11・畳んで5行（11/20 PM「5行だけ出して残り○か所で開く」）', m['h4'] == 'まだ 11' and len(m['rows']) == 5 and all(m['rows']), m['rows'][:3])
            check(f'{hh} 地図：ツメと地方の数を出さない', not s['tsume'] and not await pg.evaluate('!!document.querySelector("#bookAir .zx-hero .rg")'))
            ow = await pg.evaluate('document.documentElement.scrollWidth - innerWidth')
            check(f'{hh} 地図：横にはみ出さない', ow <= 0, ow)
            if hh == 844: await pg.screenshot(path=os.path.join(SHOTS, 'f3-heli-map-844.png'))
            await pg.click('#zkxSeg [data-zxk="all"]'); await pg.wait_for_timeout(300)
            m = await pg.evaluate('[document.querySelectorAll("#bookAir .zx-bigmap circle.mv").length, document.querySelectorAll("#bookAir .zx-list .r").length]')
            check(f'{hh} 地図：すべてに戻すと行った4つ（地図の中）・まだの一覧は畳んで5行', m == [4, 5], m)
            tiny = await pg.evaluate('[...document.querySelectorAll("#bookAir button")].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44).map(b => b.textContent.trim().slice(0, 12))')
            check(f'{hh} 地図：押せる所は44px 以上', not tiny, tiny)
            small = await pg.evaluate('[...document.querySelectorAll("#bookAir .zx-seg button, #bookAir .zx-seg .u, #bookAir .zx-lg, #bookAir .zx-list .pf, #bookAir .zx-pf")].filter(x => parseFloat(getComputedStyle(x).fontSize) < 12).length')
            check(f'{hh} 字が小さすぎない（ピルの数 12px・ほか 13px）', small == 0, small)
            # 覚える：開き直しても地図・ヘリポート
            await pg.click('#zkxSeg [data-zxk="heli"]'); await pg.wait_for_timeout(300)
            st = await pg.evaluate('[localStorage.getItem("soramemo.zkx.kind"), localStorage.getItem("soramemo.zkx.view")]')
            check(f'{hh} 端末に覚える', st == ['heli', 'map'], st)
            await pg.evaluate('setBookSeg("main"); DIRTY.book = true; renderVisible(); setBookSeg("air"); DIRTY.book = true; renderVisible()'); await pg.wait_for_timeout(300)
            s = await pg.evaluate(STATE)
            check(f'{hh} 開き直しても地図・ヘリポートのまま', s['map'] and [x[2] for x in s['pills']][3] == 'true')
            # 夜の画面
            await pg.click('#zkxViews [data-zxv="region"]'); await pg.wait_for_timeout(300)
            await pg.evaluate('document.documentElement.dataset.night = "on"'); await pg.wait_for_timeout(200)
            if hh == 844: await pg.screenshot(path=os.path.join(SHOTS, 'f2-heli-night-844.png'))
            await pg.evaluate('delete document.documentElement.dataset.night')
            # 変な値は「すべて」「地方別」に戻す
            await pg.evaluate('localStorage.setItem("soramemo.zkx.kind", "mil"); localStorage.setItem("soramemo.zkx.view", "x"); DIRTY.book = true; renderVisible()'); await pg.wait_for_timeout(300)
            s = await pg.evaluate(STATE)
            check(f'{hh} 知らない値は「すべて」「地方別」・基地は出さない', s['tiles'] == 75 and s['view'][0][1] == 'true' and '基地' not in ''.join(s['kinds']), [s['tiles'], s['view']])
            check(f'{hh} エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
