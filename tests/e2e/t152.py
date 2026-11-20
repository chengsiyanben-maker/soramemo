import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 日誌の1行と共有の画像も実際の時刻に（11/20 PM のおすすめ・report-small-1120 の「決めてほしいこと」）
#   実際の時刻がある便：日誌の1行の「○:○○ 発」と共有の画像（搭乗券の形）の「出発」を実際の出発の時刻に
#   ない便：今までどおりチェックインの時刻。共有の画像にチェックインの時刻は出さない（字を増やさない）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(os.path.dirname(HERE), '..', 'docs', 'pm', 'shots-actual-share'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
# 便7 羽田→新千歳：ODPT の実際の時刻（チェックインの出発の15分あと・80分）
ACT = """window.__flightsAct = fl => { const f7 = fl.find(x => x.id === 7);
  const d7 = Date.parse(f7.dep_at) + 15 * 6e4; f7.act_dep_at = new Date(d7).toISOString(); f7.act_arr_at = new Date(d7 + 80 * 6e4).toISOString(); f7.act_src = 'odpt'; };
  window.__txt = []; const ft = CanvasRenderingContext2D.prototype.fillText; CanvasRenderingContext2D.prototype.fillText = function(t, ...r){ window.__txt.push(String(t)); return ft.call(this, t, ...r); };"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, timezone_id='Asia/Tokyo')
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.route('https://cyberjapandata.gsi.go.jp/**', lambda r: r.abort())
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');" + ACT)
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
        await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1800)
        await pg.evaluate('(() => { goTab("log"); setLogSeg("list"); VIEW.log = "diary"; DIRTY.log = true; renderVisible(); window.scrollTo(0, 0); })()'); await pg.wait_for_timeout(600)
        exp = await pg.evaluate('(() => { const f = S.flights.find(x => x.id === 7), g = S.flights.find(x => x.id === 9); return { k7: fid(f), k9: fid(g), ad: hmOf(f.actDep), cd: hmOf(f.dep), d9: hmOf(g.dep), ok: !!f.actSrc && !g.actSrc }; })()')
        check('準備：便7は実際の時刻あり・便9はなし・時刻がずれている', exp['ok'] and exp['ad'] != exp['cd'], exp)
        ROW = '(k => { const r = document.querySelector(`#flights .fbrow[data-fbv="${k}"] .sub b`); return r ? r.textContent : null; })'
        r7 = await pg.evaluate(f'{ROW}({exp["k7"]!r})'); r9 = await pg.evaluate(f'{ROW}({exp["k9"]!r})')
        check('日誌：実際の時刻の便は1行の出発も実際の時刻', r7 == exp['ad'], [r7, exp['ad']])
        check('日誌：実際の時刻がない便は今までどおりチェックインの時刻', r9 == exp['d9'], [r9, exp['d9']])
        await pg.evaluate(f'document.querySelector(`#flights .fbrow[data-fbv="{exp["k7"]}"]`).scrollIntoView({{block:"center"}})'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, 'diary-row-act.png'))
        # くわしくの「この区間の便」の行も同じ関数（fbRowHTML）なのでそろう
        await pg.evaluate(f'fbOpenView({exp["k7"]!r})'); await pg.wait_for_timeout(500)
        v = await pg.evaluate(f'(() => {{ const r = document.querySelector(`#dFbView .fbrow[data-fbv="{exp["k7"]}"] .sub b`); return r ? r.textContent : null; }})()')
        check('くわしく：この区間の便の行も実際の時刻', v == exp['ad'], v)
        # 共有の画像
        for k, want, name in ((exp['k7'], exp['ad'], '実際の時刻の便'), (exp['k9'], exp['d9'], '実際の時刻がない便')):
            await pg.evaluate('window.__txt = []')
            await pg.evaluate(f'fbOpenShare({k!r})'); await pg.wait_for_timeout(700)
            tx = await pg.evaluate('window.__txt')
            i = tx.index('出発') if '出発' in tx else -1
            got = tx[i + 1] if i >= 0 and i + 1 < len(tx) else None
            check(f'共有の画像：{name}の「出発」は {want}', got == want, [got, want])
            check(f'共有の画像：{name}にチェックインの時刻の行は出さない', not any('チェックイン' in t for t in tx), [t for t in tx if 'チェックイン' in t])
            if k == exp['k7']: await pg.screenshot(path=os.path.join(SHOTS, 'share-act.png'))
            await pg.evaluate('document.getElementById("dFbShare").close()'); await pg.wait_for_timeout(200)
        check('エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
