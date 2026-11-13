import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 経営の見回り（11/13）の直し
#   K2〜K4：押せる範囲が44px 以上（エアライン経営とは・会社名・役職の「選ぶ」・持っている／買う）。見た目の大きさは変えない（選ぶは除く）
#           広げた範囲が、上の「スタンプラリー／エアライン経営」の切り替えにかぶらない
#   K5：「収益を受け取る」が押せないときは、押せない理由をボタンの字にする
#   K6：会社を開くときは路線・機体の一覧を描かず、路線・機体を開いたときに描く（描いた中身は前と同じ）
#   偽のサーバー（fake_sb.js）とデモを使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
# 要素の見た目の箱と、上下に広げた所を押したとき一番上に来る要素がその要素か
HIT = """(sel => { const e = document.querySelector(sel); if(!e) return null; const r = e.getBoundingClientRect(), x = r.left + r.width / 2;
  const at = y => { const h = document.elementFromPoint(x, y); return !!h && (h === e || e.contains(h)); };
  let top = r.top, bot = r.bottom; while(top > r.top - 12 && at(top - 1)) top--; while(bot < r.bottom + 12 && at(bot)) bot++;
  return { h: Math.round(r.height), hit: Math.round(bot - top) }; })"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo')
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
        await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(1500)
        await pg.evaluate('openMyPage()'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(1200)
        await pg.evaluate('goTab("home")'); await pg.wait_for_timeout(400)
        # K6：会社を開いた時点では、路線・機体の一覧はまだ描かない
        await pg.evaluate('$("coRoutes").innerHTML = ""; $("coFleet").innerHTML = ""')
        await pg.click('#modeSw [data-mode=game]'); await pg.wait_for_timeout(500)
        check('会社が開く', await pg.evaluate('currentView()') == 'co')
        check('会社を開いた時点では路線・機体の一覧を描かない', await pg.evaluate('$("coRoutes").innerHTML === "" && $("coFleet").innerHTML === "" && FLEET_LATER === true'))
        # K2・K3
        for name, sel, want_h in [('エアライン経営とは', '#gameNote summary', 32), ('会社名', '#coName', 37)]:
            m = await pg.evaluate(HIT, sel)
            check(f'{name}：押せる範囲 44px 以上', m and m['hit'] >= 44, m)
            check(f'{name}：見た目の高さは前のまま（{want_h}px）', m and m['h'] == want_h, m)
        m = await pg.evaluate(HIT, '#modeSw [data-mode=game]')
        check('上の切り替えは、広げた範囲にかぶられない', m and m['hit'] >= m['h'], m)
        await pg.evaluate('document.querySelector("#coRoles select").scrollIntoView({block:"center"})')
        m = await pg.evaluate(HIT, '#coRoles select')
        check('役職の「選ぶ」：押せる範囲 44px 以上', m and m['hit'] >= 44, m)
        # K5：押せないときの字
        t = await pg.evaluate('[$("coCollect").disabled, $("coCollect").textContent]')
        check('受け取れないときは、理由がボタンの字にある', t[0] and t[1] in ('まだ貯まっていません', '路線ができると貯まります'), t)
        await pg.evaluate('(CO_LOCAL ? CO_LOCAL.last = Date.now() - 864e5 : 0); CO.last = Date.now() - 864e5; renderCompany()')
        t = await pg.evaluate('[$("coCollect").disabled, $("coCollect").textContent]')
        check('貯まったら押せて、額が出る', (not t[0]) and t[1].startswith('受け取る'), t)
        await pg.click('#coCollect'); await pg.wait_for_timeout(300)
        t = await pg.evaluate('[$("coCollect").disabled, $("coCollect").textContent]')
        check('受け取ったあとは押せず、理由が出る', t[0] and t[1] == 'まだ貯まっていません', t)
        # K6：路線・機体を開くと描く
        await pg.evaluate('window.scrollTo(0,0)'); await pg.click('nav.tabs button[data-v=routes]'); await pg.wait_for_timeout(300)
        check('路線を開くと路線の一覧を描く', await pg.evaluate('$("coRoutes").innerHTML.length > 0 && FLEET_LATER === false'))
        await pg.click('nav.tabs button[data-v=fleet]'); await pg.wait_for_timeout(300)
        check('機体を開くと機体の一覧を描く', await pg.evaluate('$("coTabs").innerHTML.length > 0 && $("coFleet").innerHTML.length > 0'))
        # K4
        for i in range(2):
            m = await pg.evaluate(HIT, f'.cseg.fmode button:nth-child({i+1})')
            check(f'持っている／買う（{i+1}つ目）：押せる範囲 44px 以上・見た目は 42px のまま', m and m['hit'] >= 44 and m['h'] == 42, m)
        await pg.click('.cseg.fmode button:nth-child(2)'); await pg.wait_for_timeout(200)
        check('「買う」を押すと買う一覧に変わる', await pg.evaluate('CO_TAB !== "have"'))
        # 会社に戻って、また機体を開いても中身が古くならない（会社で描き直した印が残る）
        await pg.click('nav.tabs button[data-v=co]'); await pg.wait_for_timeout(200)
        await pg.evaluate('CO.cash += 1; DIRTY.game = true; renderVisible()')
        await pg.click('nav.tabs button[data-v=fleet]'); await pg.wait_for_timeout(200)
        check('会社で描き直したあと機体を開くと、描き直す', await pg.evaluate('FLEET_LATER === false'))
        check('エラーなし', not errs, errs)
        await b.close()
asyncio.run(main())
print('errors', fails)
