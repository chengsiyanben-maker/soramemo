import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# フライトの「空の上」を実際の飛行時間に・地図に実際の飛行ルート（11/20 PM・data/flight-actual 移行187 の列 act_dep_at・act_arr_at・act_src）
#   act_src があれば act_arr_at − act_dep_at、なければチェックインの時刻の差で「目安」。合計に推定（adsb・timetable）か目安を含むと「（推定を含む）」
#   地図：track がある区間はその線（なければ今の弧）。出典に adsb.lol（ODbL）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(os.path.dirname(HERE), '..', 'docs', 'pm', 'shots-flight-actual'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
# 便7 羽田→新千歳（チェックインの差 120分）：ODPT の実際の時刻で 80分
# 便8 新千歳→羽田（117分）：機体の位置からの推定で 90分・航跡あり
# 便9 羽田→那覇（150分）：実際の時刻なし（目安 150分）
ACT = """window.__flightsAct = fl => { const f7 = fl.find(x => x.id === 7), f8 = fl.find(x => x.id === 8);
  const d7 = Date.parse(f7.dep_at) + 15 * 6e4; f7.act_dep_at = new Date(d7).toISOString(); f7.act_arr_at = new Date(d7 + 80 * 6e4).toISOString(); f7.act_src = 'odpt';
  const d8 = Date.parse(f8.dep_at) + 10 * 6e4; f8.act_dep_at = new Date(d8).toISOString(); f8.act_arr_at = new Date(d8 + 90 * 6e4).toISOString(); f8.act_src = 'adsb';
  f8.track = [[42.77, 141.69], [42.2, 141.9], [41.0, 141.7], [39.5, 141.6], [37.6, 140.9], [36.4, 140.4], [35.55, 139.79]]; };"""
async def page(b, init, h=844):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.abort())
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1800)
    return c, pg, errs
async def view(pg, v):
    await pg.evaluate(f'(() => {{ goTab("log"); setLogSeg("list"); VIEW.log = "{v}"; DIRTY.log = true; renderVisible(); window.scrollTo(0, 0); }})()'); await pg.wait_for_timeout(600)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c, pg, errs = await page(b, ACT)
        f = await pg.evaluate('S.flights.map(f => [f.id, f.actSrc, fbMin(f)])')
        check('読み込み：実際の時刻の列を読む（便7 odpt 80分・便8 adsb 90分・便9 なし 150分）', sorted(f) == [[7, 'odpt', 80], [8, 'adsb', 90], [9, None, 150]], f)
        bad = await pg.evaluate('[fbActOf({act_src:"odpt", act_dep_at:"2026-11-01T10:00:00Z", act_arr_at:"2026-11-01T09:00:00Z"}).actSrc, fbActOf({act_src:"x", act_dep_at:"2026-11-01T10:00:00Z", act_arr_at:"2026-11-01T11:00:00Z"}).actSrc, fbActOf({}).actSrc, fbActOf({act_src:"timetable", act_dep_at:"2026-11-01T10:00:00Z", act_arr_at:"2026-11-01T11:05:00Z"}).actSrc]')
        check('おかしな値（到着が前・知らない取り先・空）は使わない／時刻表は使う', bad == [None, None, None, 'timetable'], bad)
        # 日誌
        await view(pg, 'diary')
        rows = await pg.evaluate('[...document.querySelectorAll("#flights .fbrow")].map(r => [r.dataset.fbv, r.querySelector(".r").innerText.replace(/\\s+/g, "")])')
        check('日誌：3便', len(rows) == 3, rows)
        tx = ' '.join(x[1] for x in rows)
        check('日誌：1時間20分・1時間30分・2時間30分', '1時間20分' in tx and '1時間30分' in tx and '2時間30分' in tx, rows)
        mey = await pg.evaluate('[...document.querySelectorAll("#flights .fbrow")].filter(r => r.querySelector(".fbmeyasu")).map(r => r.querySelector(".r").innerText.replace(/\\s+/g, ""))')
        check('日誌：「目安」は実際の時刻がない便（2時間30分）だけ', len(mey) == 1 and '2時間30分' in mey[0], mey)
        fs = await pg.evaluate('parseFloat(getComputedStyle(document.querySelector("#flights .fbmeyasu")).fontSize)')
        check("「目安」は小さい字（12〜13px・1行のほかの補足と同じ）", 12 <= fs <= 13, fs)
        yr = await pg.evaluate('document.querySelector("#fbYr .yrnums").innerText.replace(/\\s+/g, "")')
        check('年の帯：空の上 5時間20分（80＋90＋150）・（推定を含む）', '5時間20分' in yr and '（推定を含む）' in yr, yr)
        await pg.screenshot(path=os.path.join(SHOTS, 'diary-844.png'))
        # くわしく
        k = await pg.evaluate('(() => { const r = [...document.querySelectorAll("#flights .fbrow")]; return r.map(x => x.dataset.fbv); })()')
        txt = []
        for key in k:
            await pg.click(f'#flights .fbrow[data-fbv="{key}"]'); await pg.wait_for_timeout(500)
            txt.append(await pg.evaluate('(() => { const d = [...document.querySelectorAll("dialog[open]")].pop(); return d ? d.innerText.replace(/\\s+/g, "") : ""; })()'))
            await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
        jt = ' '.join(txt)
        check('くわしく：取り先の説明（運航情報・機体の位置（推定）・目安）', '航空会社の運航情報から' in jt and '機体の位置から（推定）' in jt and '目安・チェックインの時刻から' in jt, [t[:80] for t in txt])
        # 年のまとめ
        await view(pg, 'year')
        t = await pg.evaluate('document.querySelector("#flights .fbtiles").innerText.replace(/\\s+/g, "")')
        check('年のまとめ：空の上 5時間20分・（推定を含む）', '5時間20分' in t and '（推定を含む）' in t, t)
        await pg.screenshot(path=os.path.join(SHOTS, 'year-844.png'))
        # 地図（SVG の版。地図の画像は読ませない）
        await view(pg, 'map')
        m = await pg.evaluate('(() => { const ps = [...document.querySelectorAll("#map path[data-n]")]; return { n: ps.length, track: ps.filter(p => p.dataset.track).map(p => (p.getAttribute("d").match(/L/g) || []).length), cred: document.querySelector("#flights .mcred").textContent }; })()')
        check('地図：区間は2つ（羽田⇄新千歳・羽田⇄那覇）・航跡の線は1本（7点＝L が6つ）', m['n'] == 2 and m['track'] == [6], m)
        check('地図：出典に航跡 adsb.lol（ODbL）', 'adsb.lol（ODbL）' in m['cred'], m['cred'])
        await pg.screenshot(path=os.path.join(SHOTS, 'map-844.png'))
        sel = await pg.evaluate('(() => { const b = document.querySelector("#flights [data-fbrt]"); b.click(); return 1; })()'); await pg.wait_for_timeout(500)
        st = await pg.evaluate('(() => { const s = document.querySelector("#flights .fbsel"); return s ? s.innerText.replace(/\\s+/g, "") : ""; })()')
        check('地図：区間を選ぶと空の上の合計（羽田⇄新千歳 2時間50分 または 羽田⇄那覇 2時間30分）', '2時間50分' in st or '2時間30分' in st, st[:120])
        check('エラーなし', not errs, errs); await c.close()
        # 実際の時刻がない人：今までどおり・「推定を含む」はチェックインの目安でも出る
        c, pg, errs = await page(b, '')
        await view(pg, 'diary')
        yr = await pg.evaluate('document.querySelector("#fbYr .yrnums").innerText.replace(/\\s+/g, "")')
        n = await pg.evaluate('document.querySelectorAll("#flights .fbmeyasu").length')
        m0 = await pg.evaluate('S.flights.map(f => fbMin(f)).reduce((a, b) => a + b, 0)')
        check('実際の時刻なし：全部の便に「目安」・合計はチェックインの差（120＋117＋150）', n == 3 and m0 == 387, [n, m0])
        await view(pg, 'map')
        m = await pg.evaluate('[document.querySelectorAll("#map path[data-track]").length, document.querySelector("#flights .mcred").textContent]')
        check('実際の時刻なし：地図は今の弧・出典は国土地理院だけ', m[0] == 0 and 'adsb' not in m[1], m)
        check('実際の時刻なし：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
