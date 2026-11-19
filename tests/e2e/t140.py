import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 近くの空港の小さな直し3つ（11/17 18時05分の PM の指示・review-app-1 の5・review-app-2 の4と5）
#   1. 図鑑の関東で「大利根」が2つ → 同じ短い名前が2つあるときだけ正式な名前（大利根滑空場・大利根飛行場）
#   2. 東京駅で東京ヘリポートの名札が「いまここ」への点線にかかる → 点線にかからない側に置く（点線が縦のときは今のまま）
#   3. 夜の札が地の色と同じで読めない → 一覧の札と図鑑の札は濃い札に明るい字（4.5:1 以上）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(WORK, 'near_fix_shots'); os.makedirs(SHOTS, exist_ok=True)
KAZO = (36.1311, 139.6017); TOKYO = (35.6812, 139.7671); YAO = (34.6267, 135.6020)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, geo, h=844, night=False):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, geolocation={'latitude':geo[0],'longitude':geo[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1500)
    try: await pg.wait_for_function('HOME_NEAR && HOME_NEAR.others', timeout=8000)
    except Exception: pass
    if night: await pg.evaluate('document.documentElement.dataset.night = "on"')
    await pg.wait_for_timeout(600)
    return c, pg, errs
# 名札の四角と、空港といまここを結ぶ点線（地図の上の位置）が重なるか
LABEL = """(() => { const ap = document.querySelector('#homeMap .hm-ap'), r = ap.getBoundingClientRect(), mt = $('homeMap').getBoundingClientRect();
  const a = HOME_MAP.latLngToContainerPoint([HOME_NEAR.a.lat, HOME_NEAR.a.lon]), m = HOME_MAP.latLngToContainerPoint([HOME_POS.lat, HOME_POS.lon]);
  let hit = 0; for(let i = 1; i <= 200; i++){ const x = mt.left + a.x + (m.x - a.x) * i / 200, y = mt.top + a.y + (m.y - a.y) * i / 200; if(x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) hit++; }
  return { hit, left: ap.classList.contains('l'), dx: Math.round(m.x - a.x), dy: Math.round(m.y - a.y), lab: [Math.round(r.left), Math.round(r.right)], W: Math.round(mt.width) }; })()"""
# 字と、その後ろの色（透明でない一番近い祖先）のコントラスト比
CONTRAST = """(sel => [...document.querySelectorAll(sel)].filter(x => x.offsetParent).map(x => {
  const rgb = s => { const m = s.match(/[\\d.]+/g).map(Number); return { c: m.slice(0, 3), a: m.length > 3 ? m[3] : 1 }; };
  const L = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  let e = x, bg = null; while(e){ const b = rgb(getComputedStyle(e).backgroundColor); if(b.a > .5){ bg = b.c; break; } e = e.parentElement; }
  bg = bg || [255, 255, 255]; const fg = rgb(getComputedStyle(x).color).c, l1 = L(fg), l2 = L(bg);
  return Math.round((Math.max(l1, l2) + .05) / (Math.min(l1, l2) + .05) * 10) / 10; }))"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. 図鑑：同じ短い名前が2つあるときだけ正式な名前
        c, pg, errs = await page(b, KAZO)
        r = await pg.evaluate("[zkxShort(XA.find(a => a.name === '大利根滑空場')), zkxShort(XA.find(a => a.name === '大利根飛行場')), zkxShort(XA.find(a => a.name === '加須滑空場')), zkxShort(XA.find(a => a.name === '東京ヘリポート'))]")
        check('図鑑の名前：大利根は2つとも正式な名前・ほかは今までどおり短い名前', r == ['大利根滑空場', '大利根飛行場', '加須', '東京'], r)
        await pg.evaluate("""(() => { const t = Date.now() - 864e5 * 30; S.checkins.push({a:2014, t}, {a:IATA.HND.id, t:t + 1e6}); for(const k in DIRTY) DIRTY[k] = true; goTab("book"); })()""")
        await pg.wait_for_timeout(600); await pg.click('#zkBody .zx-entry'); await pg.wait_for_timeout(600)
        await pg.click('#zkxTsume [data-zkj="関東"]'); await pg.wait_for_timeout(900)
        nm = await pg.evaluate('[...document.querySelectorAll("#zkxrg-関東 .zx-nm")].map(x => x.textContent)')
        check('図鑑の関東：「大利根」だけの枠がない・正式な名前が2つ', '大利根' not in nm and '大利根滑空場' in nm and '大利根飛行場' in nm, [x for x in nm if '大利根' in x])
        ov = await pg.evaluate('[...document.querySelectorAll("#zkxrg-関東 .zx-ap")].filter(x => /大利根/.test(x.textContent)).map(x => { const n = x.querySelector(".zx-nm"); return n.scrollHeight <= n.clientHeight + 3 && x.scrollWidth <= x.clientWidth + 1; })')
        check('図鑑の関東：正式な名前は「大利根／滑空場」の2行で収まる', ov and all(ov), ov)
        el = await pg.query_selector('#zkxrg-関東 .zk-grid'); await el.screenshot(path=os.path.join(SHOTS, '01-airbook-kanto.png'))
        # 3b. 夜の図鑑：まだの枠と行った枠の札
        await pg.evaluate('document.documentElement.dataset.night = "on"'); await pg.wait_for_timeout(300)
        cr = await pg.evaluate(CONTRAST, '#zkxrg-関東 .zx-ap.no .zx-k')
        cr2 = await pg.evaluate(CONTRAST, '#zkxrg-関東 .zx-ap:not(.no) .zx-k')
        check(f'夜の図鑑：まだの枠の札が 4.5:1 以上（最小 {min(cr) if cr else "-"}）', cr and min(cr) >= 4.5, sorted(set(cr)))
        check(f'夜の図鑑：行った枠の札も 4.5:1 以上（最小 {min(cr2) if cr2 else "-"}）', cr2 and min(cr2) >= 4.5, sorted(set(cr2)))
        await el.screenshot(path=os.path.join(SHOTS, '02-airbook-kanto-night.png'))
        check('図鑑：エラーなし', not errs, errs); await c.close()

        # 2. 東京駅：引き上げた地図・最初の位置とも、東京ヘリポートの名札が点線にかからない
        for h in (844, 667):
            c, pg, errs = await page(b, TOKYO, h=h)
            r = await pg.evaluate(LABEL)
            check(f'東京駅 {h}：最初の位置で名札が点線にかからない', r['hit'] == 0, r)
            await pg.click('#nearMore'); await pg.wait_for_timeout(900)
            r = await pg.evaluate(LABEL)
            check(f'東京駅 {h}：引き上げた位置で名札が点線にかからない', r['hit'] == 0, r)
            check(f'東京駅 {h}：名札は地図の中', r['lab'][0] >= 0 and r['lab'][1] <= r['W'], r)
            await pg.screenshot(path=os.path.join(SHOTS, f'03-tokyo-full-{h}.png'))
            check(f'東京駅 {h}：エラーなし', not errs, errs); await c.close()
        # 点線が縦のとき（加須・八尾）は今までどおり、名札は点線にかからない
        for nmx, g in (('加須', KAZO), ('八尾', YAO)):
            c, pg, errs = await page(b, g)
            await pg.click('#nearMore'); await pg.wait_for_timeout(900)
            r = await pg.evaluate(LABEL)
            check(f'{nmx}：引き上げた位置で名札が点線にかからない', r['hit'] == 0, r)
            check(f'{nmx}：エラーなし', not errs, errs); await c.close()

        # 3a. 夜の一覧：白いカードの上でも札が読める
        c, pg, errs = await page(b, KAZO, night=True)
        await pg.click('#nearMore'); await pg.wait_for_timeout(900)
        cr = await pg.evaluate(CONTRAST, '#nearList .nrow2 .t')
        check(f'夜の一覧：札が 4.5:1 以上（最小 {min(cr) if cr else "-"}）', cr and min(cr) >= 4.5, cr)
        await pg.screenshot(path=os.path.join(SHOTS, '04-kazo-full-night.png'))
        await pg.click('[data-near-all]'); await pg.wait_for_timeout(700)
        cr = await pg.evaluate(CONTRAST, '#dNear .nrow2 .t')
        check(f'夜の「すべて」：札が 4.5:1 以上（最小 {min(cr) if cr else "-"}）', cr and min(cr) >= 4.5, cr)
        check('夜：エラーなし', not errs, errs); await c.close()
        # 昼の札の色は今までどおり
        c, pg, errs = await page(b, KAZO)
        await pg.click('#nearMore'); await pg.wait_for_timeout(900)
        bg = await pg.evaluate('getComputedStyle(document.querySelector("#nearList .nrow2 .t.gl")).backgroundColor')
        check('昼の一覧：滑空場の札の色は今までどおり（#D7EAF6）', bg == 'rgb(215, 234, 246)', bg)
        check('昼：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
