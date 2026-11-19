import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# （11/19 運用タブは一覧＋専用ページになった。このテストは中身を前の形（見方のタブ）で確かめるので soramemo.ops.hub=0。一覧は t148）
# いつもより○分遅い（推定）（決定事項【11/17】案A・画面案 design/usual-late 2版 U1〜U5）
#   1 乗る便（時刻表にない便・飛行中）：見込みの時刻＋灰色の点線の札「いつもより32分遅い（推定）」＋箱の中の出典の1行。ODPT の出典は出さない
#   2 乗る便があるときは、ホームのシートの先頭（半券より上）にカード。844・667 で箱の中の出典の1行が下のタブ帯より上に見える
#   3 usual_late がまだないサーバー：foreign_late に切り替え、見込みがなければ「見込みはまだ出せません」（U1n）
#   4 門限（福岡22時）の10分前より遅い見込みは灰色の箱（U2b）。ダイバートは「いつもと違う空港」＋「いつもは 羽田」（U2c）。出発前はいつもの時刻（U2）
#   5 案内板：題「時刻表にない便」・凡例に出典・灰色の札（海外／日本）・いつもどおり・いつもの時刻はまだありません（U3）
#   6 機体のくわしく：着陸の見込みの箱といつもの時刻のカード（U4）
#   7 JAL・ANA の国際線（ODPT）は今までどおり（札も箱も出さない）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc); iso = lambda m: (now + timedelta(minutes=m)).isoformat()
JST = timezone(timedelta(hours=9)); today = now.astimezone(JST).strftime('%Y-%m-%d')
hm = lambda m: (now + timedelta(minutes=m)).astimezone(JST).strftime('%H:%M')
def at_jst(h, mi):   # 今日（日本時間）の h:mi
    d = now.astimezone(JST); return d.replace(hour=h, minute=mi, second=0, microsecond=0).isoformat()
LIVE = {
  'BA5':  {'flight':'BA5','found':True,'source':'route_estimate','dep':'LHR','arr':'HND','phase':'air','progress':0.97,'pos':{'lat':35,'lon':140,'alt_ft':9000,'kt':300,'at':iso(0)},'eta_pred':iso(20),'reg':'G-STBK','type':'B77W'},
  'BA7':  {'flight':'BA7','found':True,'source':'route_estimate','dep':'LHR','arr':'HND','phase':'air','progress':0.41,'pos':{'lat':60,'lon':90,'alt_ft':38000,'kt':480,'at':iso(0)},'eta_pred':None,'reg':'G-STBL','type':'B77W'},
  'BC13': {'flight':'BC13','found':True,'source':'route_estimate','dep':'HND','arr':'FUK','phase':'air','progress':0.62,'pos':{'lat':34,'lon':134,'alt_ft':37000,'kt':450,'at':iso(0)},'eta_pred':iso(60),'reg':'JA73NY','type':'B738'},
  'BA9':  {'flight':'BA9','found':True,'source':'route_estimate','dep':'LHR','arr':'HND','phase':'landed','progress':1,'ata':iso(-10),'reg':'G-STBK','type':'B77W'},
  'NH106':{'flight':'NH106','found':True,'source':'odpt','dep':'HND','arr':'LAX','std':iso(-240),'sta':iso(375),'phase':'air','progress':0.4,'pos':{'lat':45,'lon':170,'alt_ft':37000,'kt':560,'at':iso(0)},'eta_pred':iso(360),'reg':'JA791A','type':'B77W'},
}
# usual_late（データ担当 PR #118・移行185）と同じ形
U = lambda t, n: {'time':t, 'mins':int(t[:2])*60+int(t[3:]), 'n':n, 'dow':None, 'spread':10, 'weeks':8}
E = lambda at, landed=False, iata='HND', src='live': {'at':at, 'time':'', 'src':'track' if landed else src, 'landed':landed, 'iata':iata}
BASE = {'reason':None, 'source':'adsb.lol（ODbL）', 'note':'推定です。定刻や航空会社の発表ではありません', 'event':None, 'divert_to':None, 'curfew_near':None, 'late_min':None, 'kind':None}
USUAL = {
  'BA5':  {**BASE, 'arr':'HND', 'usual':U(hm(-12), 7), 'eta':E(iso(20)), 'late_min':32, 'kind':'late'},
  'BC13': {**BASE, 'arr':'FUK', 'usual':U('21:05', 8), 'eta':E(at_jst(21, 52), iata='FUK'), 'late_min':47, 'kind':'late', 'curfew_near':True},
  'BA9':  {**BASE, 'arr':'HND', 'usual':U(hm(-30), 8), 'eta':E(iso(-10), True, 'NRT'), 'event':'divert', 'divert_to':'NRT'},
  'BC21': {**BASE, 'arr':'FUK', 'usual':U('21:05', 8), 'eta':None},
  'NH106':{'flight':'NH106', 'reason':'odpt'},
}
FOREIGN = {'iata':'HND','planes':[
  {'kind':'arr','flight':'BA5','airline':'BA','other':'LHR','type':'B77W','status':'approach','km':40,'alt_ft':9000,'eta':iso(20),'usual':hm(-12),'usual_n':7,'late_min':32},
  {'kind':'arr','flight':'BC106','airline':'BC','other':'UKB','type':'B738','status':'approach','km':30,'alt_ft':6000,'eta':iso(15),'usual':hm(10),'usual_n':8},
  {'kind':'arr','flight':'QR812','airline':'QR','other':'DOH','type':'B77W','status':'approach','km':55,'alt_ft':12000,'eta':iso(25),'usual':None},
]}
BOARD = {'iata':'HND','now':iso(0),'hours':[{'h':h,'flights':2,'late':0,'cancel':0,'ref':0} for h in range(24)],
  'next_arr':[{'flight':'JL526','other':'CTS','sched':iso(5),'t':iso(23),'est':iso(23)}],'next_dep':[]}
fails = []; BODIES = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, plan=None, rpc_missing=False, width=390, height=844, view='board'):
    c = await b.new_context(viewport={'width':width,'height':height}, timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    reqs = []
    async def h(r):
        u = r.request.url; path = u.split('fake.supabase.co')[1].split('?')[0]; name = path.rsplit('/', 1)[-1]; reqs.append(name)
        body = None
        if name == 'usual_late':
            if rpc_missing: return await r.fulfill(status=404, body='{"code":"PGRST202"}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
            q = json.loads(r.request.post_data or '{}'); BODIES.append(q); body = USUAL.get(q.get('p_flight'))
        elif name == 'foreign_late': body = {'flight':'x','legs':[],'note':'推定です'}
        elif name == 'flight-live':
            f = u.split('flight=')[1].split('&')[0]; body = LIVE.get(f, {'flight':f, 'found':False})
        else: body = {'airport_board':BOARD, 'airport-foreign':FOREIGN, 'airport-traffic':{'planes':[], 'at':iso(0)}}.get(name, {} if '/functions/' in u else [])
        await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/rest/**', h); await c.route('https://fake.supabase.co/functions/**', h)
    init = "localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','HND'); localStorage.setItem('soramemo.view.ops','%s');" % view
    if plan: init += "localStorage.setItem('soramemo.plan', %s);" % json.dumps(json.dumps(plan))
    await c.add_init_script(init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true")
    return c, pg, errs, reqs
async def ride(b, no, dep, arr, airline, **kw):
    c, pg, errs, reqs = await page(b, plan={'intl':True, 'dep':dep, 'arr':arr, 'airline':airline, 'no':no, 'day':today}, **kw)
    await pg.evaluate("goTab('home')"); await pg.wait_for_selector('#rideCard:not([hidden])', timeout=8000); await pg.wait_for_timeout(300)
    return c, pg, errs, reqs, await pg.inner_text('#rideCard')
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); allerr = []
        # 1・2 飛行中・いつもより32分遅い
        for hgt in (844, 667):
            c, pg, errs, reqs, t = await ride(b, 'BA5', 'LHR', 'HND', 'BA', height=hgt)
            if hgt == 844:
                check('1 飛行中・羽田に着く見込み・見込みの時刻（ごろ）', '飛行中' in t and '羽田に着く見込み' in t and hm(20) in t and 'ごろ' in t, t[:200])
                check('1 灰色の点線の札「いつもより32分遅い（推定）」', await pg.locator('#rideCard .ultag').count() == 1 and 'いつもより32分遅い（推定）' in (await pg.evaluate("document.querySelector('#rideCard .ultag').textContent")))
                check('1 いつもは HH:MM ごろ', f'いつもは {hm(-12)} ごろ' in t, t[:300])
                check('1 箱の中に「推定・定刻や航空会社の発表ではありません・出典 adsb.lol（ODbL）」', 'adsb.lol（ODbL）' in (await pg.inner_text('#rideCard .ulbox .ulsrc')) and '定刻や航空会社の発表ではありません' in t)
                check('1 会社名と「時刻表にない便」の札', 'ブリティッシュ・エアウェイズ' in t and '時刻表にない便' in t)
                check('1 ODPT の出典は出さない', '公共交通オープンデータセンター' not in (await pg.evaluate("document.getElementById('rideCard').textContent")))
                check('1 札は橙・赤でない（点線の灰色）', await pg.evaluate("(() => { const s = getComputedStyle(document.querySelector('#rideCard .ultag')); return s.borderStyle === 'dashed' && s.backgroundColor === 'rgb(255, 255, 255)' })()"))
                check('1 長い説明は「出典と注意」の中', await pg.locator('#rideCard details.ulmore').count() == 1)
                check('1 usual_late を便名と日で呼ぶ', 'usual_late' in reqs and 'foreign_late' not in reqs, reqs)
                q = BODIES[-1] if BODIES else {}
                check('1 usual_late に p_flight・p_reg・p_day・p_arr を渡す', q.get('p_flight') == 'BA5' and q.get('p_reg') == 'G-STBK' and q.get('p_day') == today and q.get('p_arr') == 'HND' and 'p_land' in q, q)
            pos = await pg.evaluate("(() => { const top = document.getElementById('rideTop'), bp = document.getElementById('bpass'), card = document.getElementById('rideCard'); return { inTop: card.parentNode === top, before: !!(top.compareDocumentPosition(bp) & Node.DOCUMENT_POSITION_FOLLOWING) } })()")
            check(f'2 乗る便のカードはシートの先頭（半券より上）{hgt}', pos['inTop'] and pos['before'], pos)
            await pg.evaluate("document.getElementById('homeSheet').dataset.snap = 'half'"); await pg.wait_for_timeout(400)
            y = await pg.evaluate("(() => { const s = document.querySelector('#rideCard .ulsrc').getBoundingClientRect(), tb = document.querySelector('.tabbar, nav.tabs, #tabbar'); return { src: Math.round(s.bottom), tab: tb ? Math.round(tb.getBoundingClientRect().top) : null } })()")
            check(f'2 箱の中の出典の1行がタブ帯より上に見える {hgt}', y['tab'] is None or y['src'] <= y['tab'], y)
            await pg.screenshot(path=os.path.join(WORK, f't139_ride_{hgt}.png'))
            allerr += errs; await c.close()
        # 表示の編集で「乗る便」を隠したら、先頭にも出さない
        c, pg, errs, reqs, t = await ride(b, 'BA5', 'LHR', 'HND', 'BA')
        await pg.evaluate("document.querySelector('.lo[data-lo=\"home:ride\"]').classList.add('lo-off'); rideTop()")
        check('2 「乗る便」を隠すとカードは元の場所に戻り見えない', await pg.evaluate("document.getElementById('rideTop').hidden && !document.getElementById('rideCard').offsetParent"))
        # やめると先頭から消える
        await pg.evaluate("document.querySelector('.lo[data-lo=\"home:ride\"]').classList.remove('lo-off'); rideTop()")
        await pg.click('[data-ride-off]'); await pg.wait_for_timeout(400)
        check('2 やめると先頭の欄は空く', await pg.evaluate("document.getElementById('rideTop').hidden"))
        allerr += errs; await c.close()
        # 3 usual_late がまだない → foreign_late・見込みはまだ出せません
        c, pg, errs, reqs, t = await ride(b, 'BA7', 'LHR', 'HND', 'BA', rpc_missing=True)
        check('3 見込みはまだ出せません（U1n）', '見込みはまだ出せません' in t and 'いつもの時刻はまだありません' in t, t[:300])
        check('3 usual_late がないので foreign_late に切り替える', 'foreign_late' in reqs, reqs)
        check('3 札は出さない', await pg.locator('#rideCard .ultag').count() == 0)
        allerr += errs; await c.close()
        c, pg, errs, reqs, t = await ride(b, 'BA7', 'LHR', 'HND', 'BA')
        check('3 usual_late が null（この便は分からない）なら foreign_late は呼ばず U1n', '見込みはまだ出せません' in t and 'foreign_late' not in reqs, reqs)
        allerr += errs; await c.close()
        # 4 門限・ダイバート・出発前
        c, pg, errs, reqs, t = await ride(b, 'BC13', 'HND', 'FUK', 'BC')
        check('4 福岡の門限（22時）の10分前より遅い見込み（灰色の箱）', '門限（22時）の10分前より遅い見込み（推定）' in t and await pg.locator('#rideCard .ulcf').count() == 1, t[:400])
        check('4 いつもより47分遅い・スカイマーク', 'いつもより47分遅い' in t and 'スカイマーク' in t)
        await pg.screenshot(path=os.path.join(WORK, 't139_curfew.png')); allerr += errs; await c.close()
        c, pg, errs, reqs, t = await ride(b, 'BA9', 'LHR', 'HND', 'BA')
        check('4 ダイバート：いつもと違う空港・成田・いつもは 羽田', 'いつもと違う空港' in t and '成田' in t and 'いつもは 羽田' in t, t[:300])
        await pg.screenshot(path=os.path.join(WORK, 't139_divert.png')); allerr += errs; await c.close()
        c, pg, errs, reqs, t = await ride(b, 'BC21', 'HND', 'FUK', 'BC')
        check('4 出発前：いつもの時刻（福岡に着く 21:05・前の8週の8回から）', '出発前' in t and '福岡に着く' in t and '21:05' in t and '前の8週の8回から' in t, t[:300])
        check('4 出発前：出発の前の遅れと欠航は分かりません', '出発の前の遅れと欠航は分かりません' in t)
        await pg.screenshot(path=os.path.join(WORK, 't139_before.png')); allerr += errs; await c.close()
        # 7 JAL・ANA の国際線は今までどおり
        c, pg, errs, reqs, t = await ride(b, 'NH106', 'HND', 'LAX', 'NH')
        check('7 ODPT の国際線には箱も札も出さない', await pg.locator('#rideCard .ulbox, #rideCard .ultag').count() == 0 and '飛行中' in t and 'usual_late' not in reqs, reqs)
        allerr += errs; await c.close()
        # 5 案内板
        c, pg, errs, reqs = await page(b)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_selector('#opsBoard .bdseq.foreign', timeout=8000); await pg.wait_for_timeout(500)
        await pg.click('#opsBoard [data-board-dir="arr"]'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#opsBoard')
        check('5 題は「時刻表にない便（いま近くにいる便）」', '時刻表にない便（いま近くにいる便）' in t)
        check('5 題の下に凡例と出典', '点線の札はいつもの時刻との比べ（推定）' in t and 'adsb.lol（ODbL）' in t)
        lis = await pg.evaluate("[...document.querySelectorAll('#opsBoard .bdseq.foreign li')].map(li => li.innerText)")
        by = lambda k: next((x for x in lis if k in x), '')
        check('5 BA5：海外・20分後ごろ・いつもより32分遅い（推定）', '海外' in by('BA5') and f'{hm(20)}ごろ' in by('BA5') and 'いつもより32分遅い' in by('BA5'), by('BA5'))
        check('5 BC106：日本・いつもどおり', '日本' in by('BC106') and 'いつもどおり' in by('BC106'), by('BC106'))
        check('5 QR812：いつもの時刻はまだありません（札なし）', 'いつもの時刻はまだありません' in by('QR812'), by('QR812'))
        check('5 会社名は行に出さない', 'ブリティッシュ' not in by('BA5'))
        await pg.locator('#opsBoard .bdseq.foreign').scroll_into_view_if_needed(); await pg.screenshot(path=os.path.join(WORK, 't139_board.png'))
        allerr += errs; await c.close()
        # 6 機体のくわしく（撮る人の見方）
        c, pg, errs, reqs = await page(b, view='photo')
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(2500)
        html = await pg.evaluate("(f) => { FOREIGN = f; FOREIGN_AP = OPS_AP; const x = { fl:'BA5', dir:'arr', t:Date.now() + 20*60000, foreign:true, other:'LHR', type:'B77W', reg:'G-STBK', airline:'BA', status:'approach', km:40 }; return ulSpBox(x); }", FOREIGN)
        check('6 着陸の見込みの箱（いつもより32分遅い・いつもは・出典）', '着陸の見込み' in html and 'いつもより32分遅い' in html and 'いつもは' in html and 'adsb.lol' in html, html[:200])
        check('6 いつもの時刻（推定）のカード（数えた回数 7回）', 'いつもの時刻（推定）' in html and '7回' in html)
        allerr += errs; await c.close()
        await b.close()
        print('NG:', fails)
        print('errors', allerr if not fails else allerr + ['NG ' + f for f in fails])
asyncio.run(main())
