import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 運用タブの見回りの直し（11/13 の全体の見回り。運用予想担当）
#   1 選んでいる見方の分だけ読む（開いたときの通信の本数）・livery_board は1回・見方を変えても3分以内の結果を使う・ログインしていない人とデモは flight_alerts を読まない
#   2 気象通報が届くまでは風の欄「読み込み中」・札を出さない
#   3 見方の帯ははじめ左端から。選んだ見方が外のときだけ送る
#   4 「ほかの向き」の丸いボタンは開けば押せる
#   5 案内板の長い行き先は切らない・到着／出発・すべて／国内線／国際線・原文・くわしく は押せる範囲 44px
#   6 「滑走路」に戻したときの最初の変化が速い
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, collections
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc); iso = lambda m: (now + timedelta(minutes=m)).isoformat()
SPECIAL = [{'reg':'JA819A','name':'ポケモンジェット 赤','airline':'ANA','callsign':'ANA18','lat':35.45,'lon':139.9,'alt_ft':3000,'iata':'HND','phase':'arr','src':'x','at':iso(-1),'kind':'special'},
           {'reg':'JA8089','name':'スターアライアンス塗装','airline':'ANA','callsign':'ANA21','lat':34.0,'lon':135.0,'alt_ft':30000,'iata':None,'phase':None,'src':'x','at':iso(-1),'kind':'alliance'}]
LBOARD = [{'reg':'JA819A','now':{'at':iso(-1),'lat':35.45,'lon':139.9,'alt_ft':3000,'callsign':'ANA18','iata':'HND','phase':'arr','kt':180},
   'today':[{'cs':'ANA18','dep':'ITM','arr':'HND','first':iso(-60),'last':iso(-1),'sch':False}],'last_day':str((now + timedelta(hours=9)).date()),'arr30':{'HND':9}}]
BOARD = {'iata':'HND','now':iso(0),'hours':[{'h':h,'flights':2,'late':0,'cancel':0,'ref':0} for h in range(24)],
  'next_arr':[{'flight':'NH7','other':'SFO','sched':iso(30),'t':iso(30),'intl':True,'aircraft':'B789'},{'flight':'JL501','other':'CTS','sched':iso(40),'t':iso(40)}],
  'next_dep':[{'flight':'JL502','other':'CTS','sched':iso(20),'t':iso(20)}]}
FOREIGN = {'iata':'HND','planes':[]}
METAR = {'wdir':330,'wspd':12,'vis_m':9999,'time':iso(-20)}
ALERTS = [{'kind':'delay_dep','flight':'JL123','dep':'HND','arr':'ITM','at':iso(-10),'message':'機材の到着遅れのため、約30分遅れて出発します。定刻 10:00 → 10:30（航空会社の運航情報）'}]
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, mode, view='runway', metar_wait=0.0):
    c = await b.new_context(viewport={'width':390,'height':844}, timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    reqs = []
    async def h(r):
        u = r.request.url; path = u.split('fake.supabase.co')[1].split('?')[0]; name = path.rsplit('/', 1)[-1]; reqs.append(path)
        if name == 'metar' and metar_wait: await asyncio.sleep(metar_wait)
        body = {'special_now':SPECIAL, 'livery_board':LBOARD, 'airport_board':BOARD, 'airport-foreign':FOREIGN, 'metar':METAR, 'flight_alerts':ALERTS, 'airport-traffic':{'planes':[], 'at':iso(0)}}.get(name, {} if '/functions/' in u else [])
        await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/rest/**', h); await c.route('https://fake.supabase.co/functions/**', h)
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND'); localStorage.setItem('soramemo.view.ops','%s');" % view)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    if mode == 'login': await pg.evaluate('__fake.login()')
    if mode == 'demo': await pg.evaluate("$('toggleDemo').click()")
    await pg.wait_for_timeout(1500); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true")
    reqs.clear()
    return c, pg, errs, reqs
OTHER_VIEWS = ['/rest/v1/rpc/airport_ontime', '/rest/v1/rpc/airport_tracks', '/rest/v1/rpc/airport_yesterday', '/rest/v1/rpc/airport_board', '/functions/v1/airport-foreign']
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); allerr = []
        # 1. 通信の本数（滑走路で開く）
        for mode in ['anon', 'demo', 'login']:
            c, pg, errs, reqs = await page(b, mode)
            await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(2500)
            n = collections.Counter(reqs)
            check(f'{mode}：滑走路で開くと、ほかの見方の分（定時・空の道すじ・昨日・案内板・海外）を読まない', not any(n[x] for x in OTHER_VIEWS), dict(n))
            check(f'{mode}：livery_board は1回だけ（いま飛んでいる特別塗装機の分）', n['/rest/v1/rpc/livery_board'] == 1, n['/rest/v1/rpc/livery_board'])
            check(f'{mode}：同じ呼び出しが2回以上ない', all(v == 1 for v in n.values()), dict(n))
            lim = 9 if mode == 'login' else 7   # ログインは flight_alerts と通知の鍵（push-subscribe。デモで呼ばないのはチェックイン担当の直し）が増える
            check(f'{mode}：開いたときの本数は{lim}本以下（前は17本）', len(reqs) <= lim, len(reqs))
            if mode == 'login':
                check('ログイン：flight_alerts を読み、遅れ・欠航のタイルとお知らせが出る', n['/rest/v1/rpc/flight_alerts'] == 1 and await pg.locator('#opsDelayTile').count() == 1 and 'JL123' in await pg.inner_text('#opsAlerts'))
            else:
                check(f'{mode}：flight_alerts を読まない・遅れ・欠航のタイルとお知らせを出さない', n['/rest/v1/rpc/flight_alerts'] == 0 and await pg.locator('#opsDelayTile').count() == 0 and await pg.evaluate("$('opsAlerts').hidden"))
            sp = await pg.inner_text('#opsSpecial')
            check(f'{mode}：羽田に来る特別塗装機は今までどおり出る', 'ポケモンジェット 赤' in sp and '着陸に向かっている' in sp, sp[:80])
            if mode == 'anon':
                # 見方を変えると、その見方の分だけ読む。戻っても3分以内は読み直さない
                reqs.clear(); await pg.click('[data-vw="ops:board"]'); await pg.wait_for_timeout(1200)
                n = collections.Counter(reqs)
                check('案内板にすると airport_board と海外の便を1回ずつ読む', n['/rest/v1/rpc/airport_board'] == 1 and n['/functions/v1/airport-foreign'] == 1, dict(n))
                check('案内板にすると機体の位置の読み込みを止める', await pg.evaluate("TRAFFIC_TIMER === null"))
                reqs.clear(); await pg.click('[data-vw="ops:strip"]'); await pg.wait_for_timeout(800)
                await pg.click('[data-vw="ops:day"]'); await pg.wait_for_timeout(800)
                n = collections.Counter(reqs)
                check('短冊・1日の山にしても案内板・海外の便を読み直さない（1日の山は昨日だけ読む）', n['/rest/v1/rpc/airport_board'] == 0 and n['/functions/v1/airport-foreign'] == 0 and n['/rest/v1/rpc/airport_yesterday'] == 1, dict(n))
                reqs.clear(); await pg.click('[data-vw="ops:board"]'); await pg.wait_for_timeout(800)
                await pg.click('[data-vw="ops:runway"]'); await pg.wait_for_timeout(800)
                n = collections.Counter(reqs)
                check('案内板・滑走路に戻しても、3分以内は読み直さない（機体の位置だけ読み直す）', set(n) <= {'/functions/v1/airport-traffic'}, dict(n))
                reqs.clear(); await pg.click('[data-vw="ops:ontime"]'); await pg.wait_for_timeout(800)
                check('定時を選んだときだけ airport_ontime を読む', collections.Counter(reqs)['/rest/v1/rpc/airport_ontime'] == 1, reqs)
                reqs.clear(); await pg.click('[data-vw="ops:art"]'); await pg.wait_for_timeout(800)
                check('空の道すじを選んだときだけ airport_tracks を読む', collections.Counter(reqs)['/rest/v1/rpc/airport_tracks'] == 1, reqs)
            allerr += errs; await c.close()
        # 2. 気象通報が届くまで
        c, pg, errs, reqs = await page(b, 'anon', metar_wait=1.5)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(500)
        w = await pg.inner_text('#opsInfo .otiles .otile'); tag = await pg.locator('#opsInfo .opssrc').count()
        check('届く前：風の欄は「読み込み中」・「気象通報なし」と書かない', '読み込み中' in w and '気象通報なし' not in await pg.inner_text('#opsInfo'), w)
        check('届く前：運用の札（風から推定）を出さない', tag == 0, tag)
        await pg.wait_for_timeout(2000)
        w = await pg.inner_text('#opsInfo .otiles .otile'); tag = await pg.inner_text('#opsInfo .opssrc')
        check('届いたあと：風の値と札「風から推定」', '12' in w and '330' in w and tag == '風から推定', [w, tag])
        allerr += errs; await c.close()
        c, pg, errs, reqs = await page(b, 'anon')
        await pg.route('https://fake.supabase.co/functions/v1/metar**', lambda r: r.fulfill(status=500, body='{}', headers={'Access-Control-Allow-Origin':'*'}))
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1500)
        check('読めなかったとき：「気象通報なし」と札「気象通報なし（仮の表示）」（「風から推定」と言わない）', '気象通報なし' in await pg.inner_text('#opsInfo .otiles') and await pg.inner_text('#opsInfo .opssrc') == '気象通報なし（仮の表示）')
        allerr += errs; await c.close()
        # 3. 見方の帯
        c, pg, errs, reqs = await page(b, 'anon')
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1200)
        r = await pg.evaluate("(() => { const el = $('opsViews'), f = el.querySelector('[data-vw]').getBoundingClientRect(); return [el.scrollLeft, Math.round(f.left)]; })()")
        check('滑走路で開いても帯は左端から（案内板が見える）', r[0] == 0 and r[1] >= 0, r)
        await pg.evaluate("$('opsViews').scrollLeft = 300; document.querySelector('[data-vw=\"ops:photo\"]').click()"); await pg.wait_for_timeout(600)
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(300); await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1000)
        r = await pg.evaluate("(() => { const el = $('opsViews'), b = el.querySelector('[aria-selected=\"true\"]').getBoundingClientRect(), e = el.getBoundingClientRect(); return [b.left >= e.left - 1 && b.right <= e.right + 1, el.scrollLeft]; })()")
        check('撮る人（右端）を選んで開くと、撮る人が見えるところまで送る', r[0] and r[1] > 0, r)
        allerr += errs; await c.close()
        # 4・5・6
        c, pg, errs, reqs = await page(b, 'login')
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1500)
        n = await pg.evaluate("document.querySelectorAll('#opsInfo .opsmdc .chip').length")
        await pg.click('#opsInfo .opsmd summary'); await pg.wait_for_timeout(200)
        await pg.click('#opsInfo .opsmdc [data-ops="south"]'); await pg.wait_for_timeout(300)
        check('「ほかの向き」を開くと丸いボタンに名前があり押せる（南風）', n >= 3 and await pg.evaluate("OPS_MODE") == 'south' and await pg.locator('#opsInfo .opsmdc [data-ops="south"]').get_attribute('aria-pressed') == 'true')
        await pg.click('#opsInfo .opsmdc [data-ops="auto"]'); await pg.wait_for_timeout(300)
        HIT = """(sel => { const e = document.querySelector(sel); e.scrollIntoView({ block:'center' }); const r = e.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
          const at = (x, y) => { const t = document.elementFromPoint(x, y); return !!t && (t === e || e.contains(t)); };
          return { w:Math.round(r.width), h:Math.round(r.height), v:at(cx, cy - 21) && at(cx, cy + 21), hz:at(cx - 21, cy) && at(cx + 21, cy) }; })"""
        r = await pg.evaluate(HIT + "('#opsInfo .opswhy summary')")
        check('「くわしく」：見た目の高さは今のまま・押せる範囲は縦 44px', r['h'] < 30 and r['v'], r)
        r = await pg.evaluate(HIT + "('#opsAlerts .fwraw summary')")
        check('「原文」：押せる範囲は 44×44', r['w'] < 44 and r['v'] and r['hz'], r)
        await pg.click('[data-vw="ops:board"]'); await pg.wait_for_selector('#opsBoard .bdseq', timeout=5000); await pg.wait_for_timeout(300)
        r = await pg.evaluate("(() => { const b = [...document.querySelectorAll('#opsBoard .bdseq b')].find(x => x.textContent.includes('サンフランシスコ')); return b ? [b.textContent, b.scrollHeight <= b.clientHeight + 1, b.scrollWidth <= b.clientWidth + 1] : null; })()")
        check('案内板：「サンフランシスコから」を切らない（2行まで折る）', r and r[1] and r[2], r)
        for sel in ['[data-board-dir="arr"]', '[data-board-dir="dep"]', '[data-board-kind="all"]', '[data-board-kind="dom"]', '[data-board-kind="intl"]']:
            r = await pg.evaluate(HIT + "('#opsBoard %s')" % sel.replace('"', '\\"'))
            check(f'案内板 {sel}：見た目の高さは今のまま・押せる範囲は縦 44px', r['h'] < 30 and r['v'], r)
        await pg.click('#opsBoard [data-board-dir="dep"]'); await pg.wait_for_timeout(200)
        check('「出発」を押すと出発の便になる', 'これから出る便' in await pg.inner_text('#opsBoard'))
        await pg.screenshot(path=os.path.join(WORK, 't130_board.png'))
        r = await pg.evaluate("""(() => { const t0 = performance.now(); document.querySelector('[data-vw="ops:runway"]').click(); const t1 = performance.now();
          return [t1 - t0, !$('opsInfo').classList.contains('ovoff'), $('opsBoard').classList.contains('ovoff')]; })()""")
        check('滑走路に戻すと、押した直後に滑走路の中身が出る（同じ処理の中で 100ms 未満）', r[0] < 100 and r[1] and r[2], r)
        await pg.wait_for_timeout(600)
        check('地図はそのあと描き直す（地図が見えて大きさがある）', await pg.evaluate("opsMapShown() && !!OPS_CUR"))
        allerr += errs; await c.close()
        check('画面のエラーなし', not allerr, allerr)
        await b.close()
    print('errors', fails)
asyncio.run(main())
