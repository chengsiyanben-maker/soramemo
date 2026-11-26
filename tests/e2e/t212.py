import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 案内板の「これから着く便」を時刻表に（11/26 本人の指示・design/board-timetable 案A 到着）
#   列（定刻／変更・便名・出発地（経由）・機材・ゲート・状況）、状況（定刻・遅れ・到着済み・欠航・推定）、「いま」の線、遅れの黄色、欠航の札、
#   状況が変わったときだけパタパタ、動きを減らす設定では動かさない、出発の欄は今のまま。写真は 390・375（昼・暗い色）を docs/pm/shots-arr-timetable へ
import asyncio, json, shutil
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-arr-timetable')) if os.environ.get('SORAMEMO_SHOTS') == '1' else WORK
os.makedirs(SHOTS, exist_ok=True)
STATE = {'nh52_late': False}
def board(kind):
    arr = [
        {'flight': 'JL502', 'other': 'CTS', 'sched': iso(-14), 'actual': iso(-18), 'aircraft': 'A359', 'intl': False, 't': iso(-18), 'gate': '16'},
        {'flight': 'NH240', 'other': 'FUK', 'sched': iso(-8), 'actual': iso(-2), 'aircraft': 'B789', 'intl': False, 't': iso(-2), 'gate': '60'},
        {'flight': 'JL904', 'other': 'OKA', 'sched': iso(3), 'est': iso(28), 'aircraft': 'A359', 'intl': False, 't': iso(28), 'gate': '14'},
        {'flight': 'NH52', 'other': 'CTS', 'sched': iso(8), 'aircraft': 'B772', 'intl': False, 't': iso(8), 'gate': '63', **({'est': iso(33)} if STATE['nh52_late'] else {})},
        {'flight': 'BC514', 'other': 'UKB', 'sched': iso(28), 'predicted': iso(29), 'aircraft': 'B738', 'intl': False, 't': iso(29)},
        {'flight': 'NH1794', 'other': 'ISG', 'sched': iso(43), 'aircraft': 'B738', 'intl': False, 't': iso(43), 'via': 'MMY'},
        {'flight': 'NH106', 'other': 'LAX', 'sched': iso(55), 'aircraft': 'B77W', 'intl': True, 't': iso(55)},
        {'flight': 'JL120', 'other': 'ITM', 'sched': iso(70), 'aircraft': 'B763', 'intl': False, 't': iso(70)},
    ]
    if kind == 'intl': arr = [f for f in arr if f['intl']]
    if kind == 'dom': arr = [f for f in arr if not f['intl']]
    bad = [{'dir': 'arr', 'flight': 'JL432', 'other': 'MYJ', 'sched': iso(13), 'cancelled': True, 'intl': False, 'aircraft': 'B738'},
           {'dir': 'arr', 'flight': 'JL999', 'other': 'KIX', 'sched': iso(-300), 'cancelled': True, 'intl': False},          # 幅の外（5時間前）は出さない
           {'dir': 'dep', 'flight': 'JL433', 'other': 'MYJ', 'sched': iso(20), 'cancelled': True, 'intl': False},           # 出発の欠航は到着の時刻表に出さない
           {'dir': 'arr', 'flight': 'JL904', 'other': 'OKA', 'sched': iso(3), 'est': iso(28), 'late': 25, 'cancelled': False, 'intl': False}]
    return {'iata': 'HND', 'now': iso(0), 'hours': [{'h': h, 'flights': 0, 'late': 0, 'cancel': 0, 'ref': 0} for h in range(24)], 'bad': bad, 'next_arr': arr,
            'next_dep': [{'flight': 'JL555', 'other': 'KIX', 'sched': iso(30), 'intl': False, 't': iso(30)}]}
res = []
def check(name, ok, extra=''):
    res.append((name, bool(ok))); print(('OK  ' if ok else 'NG  ') + name + (f'  {extra}' if extra and not ok else ''))
ROWS = "[...document.querySelectorAll('#opsBoard .bdtt .tt')].map(li => ({ f: li.dataset.tt, cls: li.className, st: li.querySelector('[data-k=st]').textContent, chg: li.querySelector('.chg').textContent, chgY: !li.querySelector('.chg').classList.contains('ok2'), t: li.innerText, go: li.querySelectorAll('.fch.go').length }))"
async def setup(p, w, h, reduce=False, hub=False, palette=None):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo', reduced_motion='reduce' if reduce else 'no-preference', device_scale_factor=2 if os.environ.get('SORAMEMO_SHOTS') == '1' else 1)
    init = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
    if not hub: init += "localStorage.setItem('soramemo.ops.hub','0'); localStorage.setItem('soramemo.layout', JSON.stringify({tabs:['home','book','log','ops','stats'], off:{home:[],book:[],log:[],ops:[],stats:['sgsum']}})); localStorage.setItem('soramemo.view.ops','board');"
    await c.add_init_script(init)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE, 'fake_sb.js'), content_type='application/javascript'))
    async def rpc(r):
        name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
        data = board(body.get('p_kind', 'all')) if name == 'airport_board' else []
        await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin': '*'})
    await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
    await c.route('https://fake.supabase.co/functions/v1/**', lambda r: r.fulfill(status=200, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
    if palette: await pg.evaluate(f"document.documentElement.setAttribute('data-palette', '{palette}')")
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(500)
    return b, pg, errs
async def main():
    async with async_playwright() as p:
        b, pg, errs = await setup(p, 390, 844)
        await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_selector('#opsBoard .bdtt .tt', timeout=8000); await pg.wait_for_timeout(300)
        rows = await pg.evaluate(ROWS); by = {r['f']: r for r in rows}
        head = await pg.evaluate("[...document.querySelectorAll('#opsBoard .bdtt .cols span')].map(s => s.innerText.replace(/\\n/g, ''))")
        check('1 列は 定刻変更・便名・出発地・機材・ゲート・状況', head == ['定刻変更', '便名', '出発地', '機材', 'ゲート', '状況'], head)
        check('2 定刻の順（欠航の JL432 は bad から足す・幅の外と出発の欠航は出さない）', [r['f'] for r in rows] == ['JL502', 'NH240', 'JL904', 'NH52', 'JL432', 'BC514', 'NH1794', 'NH106', 'JL120'], [r['f'] for r in rows])
        check('3 到着済み（実際の時刻・薄い字）', by['JL502']['st'] == '到着済み' and 's-gone' in by['JL502']['cls'] and by['JL502']['chg'] and not by['JL502']['chgY'], by['JL502'])
        check('4 遅れ（黄色の変更の時刻）', by['JL904']['st'] == '遅れ' and 's-late' in by['JL904']['cls'] and by['JL904']['chgY'] and by['JL904']['chg'], by['JL904'])
        check('5 定刻（変更の時刻なし・ゲート 63）', by['NH52']['st'] == '定刻' and by['NH52']['chg'] == '' and '63' in by['NH52']['t'], by['NH52'])
        check('6 欠航の札（ゲートは —）', by['JL432']['st'] == '欠航' and 's-x' in by['JL432']['cls'] and '—' in by['JL432']['t'], by['JL432'])
        check('7 推定（機体の位置からの見込みだけ）', by['BC514']['st'] == '推定' and 's-est' in by['BC514']['cls'], by['BC514'])
        check('8 経由（宮古経由）・国際線の札', '宮古経由' in by['NH1794']['t'] and 'ロサンゼルス' in by['NH106']['t'] and '国際線' in by['NH106']['t'], (by['NH1794']['t'], by['NH106']['t']))
        order = await pg.evaluate("[...document.querySelectorAll('#opsBoard .bdtt .ttl > li')].map(li => li.classList.contains('nowl') ? 'NOW' : li.classList.contains('hrl') ? 'H' : li.dataset.tt)")
        o2 = [x for x in order if x != 'H']   # 時の区切りは今の時刻しだいで入る所が変わるので外して比べる
        check('9 「いま」の線は過ぎた便と次の便のあいだ（1本だけ）', o2.count('NOW') == 1 and o2.index('NOW') + 1 == o2.index('JL904') and o2.index('NOW') == o2.index('NH240') + 1, order)
        cap = await pg.inner_text('#opsBoard .bdtt .bcap')
        check('10 頭の数：今日の欠航（到着の欠航だけ・今日の bad 全部）2便', '到着' in cap and '欠航 2便' in cap.replace('\n', ''), cap)
        st = await pg.evaluate("(() => { const c = s => getComputedStyle(document.querySelector(s)); return { bg: c('#opsBoard .bdtt').backgroundColor, late: c('#opsBoard .bdtt .tt[data-tt=JL904] .c-st').color, x: c('#opsBoard .bdtt .tt[data-tt=JL432] [data-k=st]').backgroundColor, sch: c('#opsBoard .bdtt .sch').fontSize } })()")
        check('11 紺の地・遅れは黄の字・欠航は黄の札', st['bg'] == 'rgb(14, 30, 54)' and st['late'] == 'rgb(255, 210, 63)' and st['x'] == 'rgb(255, 210, 63)', st)
        check('12 はじめて出したときは動かさない', all(r['go'] == 0 for r in rows) and await pg.locator('#opsBoard .bdtt .flash').count() == 0)
        # 横にはみ出さない（390）
        ov = await pg.evaluate("(() => { const b = document.querySelector('#opsBoard .bdtt').getBoundingClientRect(); return [b.left, b.right, document.documentElement.scrollWidth, innerWidth] })()")
        check('13 横にはみ出さない（390）', ov[0] >= 0 and ov[1] <= ov[3] and ov[2] <= ov[3], ov)
        # 状況が変わった（NH52 が遅れに）→ その行の状況と変更の時刻だけパタパタ
        STATE['nh52_late'] = True
        await pg.evaluate("BOARD_AT = 0; renderBoard()"); await pg.wait_for_timeout(500)
        rows2 = await pg.evaluate(ROWS); by2 = {r['f']: r for r in rows2}
        check('14 変わった行だけパタパタ（状況と変更の時刻の字）', by2['NH52']['st'] == '遅れ' and by2['NH52']['go'] >= 4 and 'flash' in by2['NH52']['cls'] and all(r['go'] == 0 for r in rows2 if r['f'] != 'NH52'), [(r['f'], r['go']) for r in rows2])
        await pg.evaluate("BOARD_AT = 0; renderBoard()"); await pg.wait_for_timeout(400)
        check('15 変わらなければ次は動かさない', all(r['go'] == 0 for r in await pg.evaluate(ROWS)))
        # 国内線だけ：国際線の便は出さない
        await pg.click('#opsBoard [data-board-kind="dom"]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#opsBoard .bdtt')
        check('16 国内線だけ：国際線の便は出さない', 'ロサンゼルス' not in t and '松山' in t)
        await pg.click('#opsBoard [data-board-kind="all"]'); await pg.wait_for_timeout(500)
        # 出発の欄は今のまま
        await pg.click('#opsBoard [data-board-dir="dep"]'); await pg.wait_for_timeout(200)
        check('17 出発の欄は今のまま（時刻表にしない）', await pg.locator('#opsBoard .bdtt').count() == 0 and '関西へ' in await pg.inner_text('#opsBoard .bdseq'))
        await pg.click('#opsBoard [data-board-dir="arr"]'); await pg.wait_for_timeout(200)
        check('18 到着に戻すと時刻表', await pg.locator('#opsBoard .bdtt .tt').count() == 9)
        STATE['nh52_late'] = False
        check('19 エラーなし（390）', not errs, errs); await b.close()
        # 動きを減らす設定：変わっても字を置き換えるだけ
        b, pg, errs = await setup(p, 375, 667, reduce=True)
        await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_selector('#opsBoard .bdtt .tt', timeout=8000); await pg.wait_for_timeout(300)
        STATE['nh52_late'] = True
        await pg.evaluate("BOARD_AT = 0; renderBoard()"); await pg.wait_for_timeout(400)
        r = {x['f']: x for x in await pg.evaluate(ROWS)}['NH52']
        check('20 動きを減らす設定：字は変わるが動かない', r['st'] == '遅れ' and r['go'] == 0 and 'flash' not in r['cls'], r)
        ov = await pg.evaluate("(() => { const b = document.querySelector('#opsBoard .bdtt').getBoundingClientRect(); const d = [...document.querySelectorAll('#opsBoard .bdtt .c-dst b')].map(x => x.scrollHeight <= x.clientHeight + 2); return [b.left, b.right, document.documentElement.scrollWidth, innerWidth, d.filter(Boolean).length, d.length] })()")
        check('21 横にはみ出さない（375）・出発地の名前は切れない', ov[0] >= 0 and ov[1] <= ov[3] and ov[2] <= ov[3] and ov[4] == ov[5], ov)
        STATE['nh52_late'] = False
        check('22 エラーなし（375）', not errs, errs); await b.close()
        # 写真：ふだんの一覧（ハブ）から開いた形で 390・375、明るい色と暗い色（案内板の色）
        for w, h in ((390, 844), (375, 667)):
            for pal in (None, 'board'):
                b, pg, errs = await setup(p, w, h, hub=True, palette=pal)
                await pg.evaluate("goTab('home'); goTab('ops')"); await pg.wait_for_timeout(800)
                await pg.evaluate("document.querySelector('[data-ohub=\"board\"]').click()"); await pg.wait_for_timeout(900)
                await pg.wait_for_selector('#opsBoard .bdtt .tt', timeout=8000); await pg.wait_for_timeout(400)
                await pg.evaluate("document.querySelector('#opsBoard .bdtt').scrollIntoView({block:'start'}); scrollBy(0, -70)"); await pg.wait_for_timeout(300)
                await pg.screenshot(path=os.path.join(SHOTS, f'arr-{w}{"-dark" if pal else ""}.png'))
                if not pal:
                    await pg.locator('#opsBoard .bdtt').screenshot(path=os.path.join(SHOTS, f'arr-{w}-card.png'))
                check(f'23 写真 {w}{" 暗い色" if pal else ""}：エラーなし', not errs, errs); await b.close()
    bad = [n for n, ok in res if not ok]
    print('errors', bad)
asyncio.run(main())
