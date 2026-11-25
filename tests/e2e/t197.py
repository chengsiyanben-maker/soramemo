# 乗る便の候補から1回で記録（11/25 23時05分・本人が貼った案の7番・checkin/flight-suggest）
#   1 フライトの「＋」：今日チェックインした空港の今日の運航情報から、これから出る便・いま着いた便を候補に並べる（欠航・出発済み・国際線は出さない）
#   2 押すと確認の1枚（便名・区間・時刻・機材）→「記録する」の1回で記録
#       これから出る便 → 乗る便として覚える／今日のその区間のフライトがある → 便名を付ける／なくてもうチェックインした → 日誌に今日の便（便名の列がない古いサーバーでも入る）
#   3 印のあとの「今日の便を記録」：シートで候補
#   4 電波がないときは候補なしで手入力へ（出発に今の空港を入れる）
#   5 過去の便：日付＋便名（数字だけでも）で区間と時刻を補う。同じ番号がいくつかあれば選ぶ。日誌に便名も残す
#   390・375 で撮る（docs/pm/shots-flight-suggest/）
import os, sys, json, shutil, re
from datetime import datetime, timedelta, timezone
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-flight-suggest')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
JST = timezone(timedelta(hours=9))
def hm(minutes):
    return (datetime.now(JST) + timedelta(minutes=minutes)).strftime('%H:%M')
def row(no, place, mins, kind='ok', ac=None, new=None):
    return {'time': hm(mins), 'newTime': hm(new) if new is not None else None, 'place': place, 'airline': no[:2], 'no': no, 'term': 'T1', 'kind': kind, 'gate': None, 'note': None, 'ac': ac}
NOWD = {'weather': None, 'taf': None, 'flights': {
    'dep': [row('JL509', 'CTS', 40, ac='738'), row('NH241', 'FUK', 70, kind='late', ac='772', new=85), row('JL999', 'OKA', 50, kind='cancel'), row('NH11', 'JFK', 60), row('JL301', 'FUK', -30, kind='done')],
    'arr': [row('JL116', 'ITM', -20, kind='done', ac='763', new=-18), row('NH58', 'OKA', -40, kind='done', ac='789'), row('NH999', 'CTS', 150)],
    'dc_date': None}}
TT = {'JAL': [['JL0509', 'HND', 'CTS', '08:00', '09:35', 0, '738'], ['JL0241', 'ITM', 'HND', '10:00', '11:05', 0, '767']],
      'ANA': [['NH0241', 'HND', 'FUK', '07:30', '09:20', 0, '772']]}
fails = []
def ok(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)
async def waitjs(pg, expr, timeout=15000):
    for _ in range(timeout // 100):
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(100)
    return False
async def page(p, w, h):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=2)
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1');")
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.route('https://fake.supabase.co/functions/v1/airport-now**', lambda r: r.fulfill(status=200, body=json.dumps(NOWD), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
    async def rpc(r):
        name = r.request.url.rsplit('/', 1)[-1]; body = json.loads(r.request.post_data or '{}')
        if name == 'plan_timetable': data = {'date': body.get('p_date'), 'operator': body.get('p_operator'), 'f': TT.get(body.get('p_operator'), [])}
        elif name == 'flight_facts': data = [{'f': x['f'], 'd': x['d'], 'a': x['a'], 'atd': x['d'] + 'T08:04:00+09:00', 'ata': x['d'] + 'T09:31:00+09:00', 'reg': 'JA301J', 'cancelled': False} for x in body]
        else: data = None
        await r.fulfill(status=200, body=json.dumps(data), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_server_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await waitjs(pg, 'S.checkins.length >= 1'); await pg.wait_for_timeout(1000)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    # 今日、羽田でチェックインした（サーバーにも入れておく）
    await pg.evaluate("""(() => { const h = A.find(a => a.iata === 'HND').id; __fake.db.checkins.push({airport_id:h, terminal_id:null, created_at:new Date(Date.now() - 30*60e3).toISOString(), accuracy_m:20}); })()""")
    await pg.evaluate('reload()'); await pg.wait_for_timeout(800)
    return b, c, pg, errs
ID = "A.find(a => a.iata === '%s').id"
async def open_book(pg):
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); FSUG.cache.clear(); goTab('log'); setLogSeg('list')"); await pg.wait_for_timeout(300)
    await pg.click('#flAdd'); await pg.wait_for_timeout(700)
async def main():
    allerrs = []
    async with async_playwright() as p:
        for (w, h) in [(390, 844), (375, 667)]:
            sz = f'{w}x{h}'
            b, c, pg, errs = await page(p, w, h)
            # 1 候補
            await open_book(pg)
            t = await pg.inner_text('#fsugBook')
            nos = await pg.evaluate("FSUG.list.map(x => x.dir + ':' + x.no)")
            ok(not await pg.is_hidden('#fsugBook') and 'これから出る便' in t and 'いま着いた便' in t, f'{sz} 1 フライトの「＋」で今日の便の候補が上に出る')
            ok(nos == ['dep:JL509', 'dep:NH241', 'arr:JL116', 'arr:NH58'], f'{sz} 1 欠航・出発済み・国際線・まだ遠い到着は出さない（{nos}）')
            tags = await pg.evaluate("[...document.querySelectorAll('#fsugBook .altag')].map(x => x.className + ':' + x.textContent)")
            ok(tags[0] == 'altag jl:JL' and 'altag nh:NH' in tags, f'{sz} 1 航空会社の記号は小さな札（{tags[:2]}）')
            await pg.evaluate("$('fsugBook').scrollIntoView({block:'start'})"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(SHOTS, f'book-{w}.png'))
            # 2 これから出る便 → 乗る便として記録（1回）
            await pg.click('#fsugBook [data-fsug="0"]'); await pg.wait_for_timeout(300)
            ct = await pg.inner_text('#dFsugBody')
            ok(await pg.evaluate("$('dFsug').open") and '509' in ct and '新千歳' in ct and '738' in ct and NOWD['flights']['dep'][0]['time'] in ct, f'{sz} 2 確認に便名・区間・時刻・機材が入っている')
            ok(await pg.evaluate("document.querySelectorAll('#dFsugBody [data-fsug-go]').length") == 1 and 'チェックインすると' in ct, f'{sz} 2 確認は「記録する」1つ・乗る便の説明')
            await pg.screenshot(path=os.path.join(SHOTS, f'confirm-dep-{w}.png'))
            await pg.click('[data-fsug-go]'); await pg.wait_for_timeout(400)
            plan = await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.plan') || 'null')")
            ok(plan and plan['no'] == 'JL509' and plan['from'] == await pg.evaluate(ID % 'HND') and plan['to'] == await pg.evaluate(ID % 'CTS') and not await pg.evaluate("$('dFsug').open"), f'{sz} 2 1回で乗る便として記録（{plan}）')
            tt = await pg.evaluate("$('smToast') ? $('smToast').textContent : ''"); ok('JL509' in tt, f'{sz} 2 記録の札（{tt}）')
            # 2 いま着いた便：今日の伊丹→羽田のフライトがある → 便名を付ける
            await pg.evaluate("""(() => { const db = __fake.db; db.flights.push({id:901, from_airport:%s, to_airport:%s, dep_at:new Date(Date.now() - 100*60e3).toISOString(), arr_at:new Date(Date.now() - 31*60e3).toISOString(), distance_km:400, status:'provisional', airline:null, flight_no:null}); })()""" % (await pg.evaluate(ID % 'ITM'), await pg.evaluate(ID % 'HND')))
            await pg.evaluate('reload()'); await pg.wait_for_timeout(600)
            await open_book(pg)
            await pg.click('#fsugBook [data-fsug="2"]'); await pg.wait_for_timeout(300)
            ct = await pg.inner_text('#dFsugBody'); ok('便名を付けます' in ct and '116' in ct, f'{sz} 2 いま着いた便：今日のフライトに便名を付ける確認')
            await pg.screenshot(path=os.path.join(SHOTS, f'confirm-arr-{w}.png'))
            await pg.click('[data-fsug-go]'); await pg.wait_for_timeout(800)
            lr = await pg.evaluate('window.__lastRpc || null'); ok(lr and lr['p_flight_id'] == 901 and lr['p_flight_no'] == 'JL116', f'{sz} 2 1回で便名が付く（{lr}）')
            # 2 いま着いた便：フライトがなく、もうチェックインした → 日誌（便名の列がないサーバーでも入る）
            await pg.evaluate('window.__mfNoCol = true'); await open_book(pg)
            await pg.click('#fsugBook [data-fsug="3"]'); await pg.wait_for_timeout(300)
            ct = await pg.inner_text('#dFsugBody'); ok('日誌に今日の便として残します' in ct, f'{sz} 2 フライトがない到着は日誌に残す確認')
            n0 = await pg.evaluate('__fake.db.manual_flights.length')
            await pg.click('[data-fsug-go]'); await pg.wait_for_timeout(800)
            mf = await pg.evaluate('__fake.db.manual_flights.slice(-1)[0] || null')
            ok(await pg.evaluate('__fake.db.manual_flights.length') == n0 + 1 and mf['from_airport'] == await pg.evaluate(ID % 'OKA') and mf['airline'] == 'NH', f'{sz} 2 日誌に入る（便名の列がないときは外して）（{mf}）')
            await pg.evaluate('window.__mfNoCol = false')
            # 3 印のあとの「今日の便を記録」
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); FSUG.cache.clear(); goTab('home')"); await pg.wait_for_timeout(300)
            await pg.evaluate("showStamp(BY[%s], Date.now(), false, null, null, false)" % await pg.evaluate(ID % 'HND')); await pg.wait_for_timeout(600)
            ok(await pg.evaluate("!!document.querySelector('#dStamp [data-fsug-open]')"), f'{sz} 3 印の画面に「今日の便を記録」')
            await pg.click('#dStamp [data-fsug-open]'); await pg.wait_for_timeout(800)
            st = await pg.inner_text('#dFsugBody')
            ok(await pg.evaluate("$('dFsug').open") and 'これから出る便' in st and '509' in st, f'{sz} 3 シートで候補が出る')
            await pg.screenshot(path=os.path.join(SHOTS, f'stamp-sheet-{w}.png'))
            await pg.click('#dFsugBody [data-fsug="1"]'); await pg.wait_for_timeout(300)
            ok('241' in await pg.inner_text('#dFsugBody') and await pg.evaluate("!!document.querySelector('#dFsugBody [data-fsug-back]')"), f'{sz} 3 シートから確認へ（戻るもある）')
            await pg.click('[data-fsug-back]'); await pg.wait_for_timeout(500)
            ok('これから出る便' in await pg.inner_text('#dFsugBody'), f'{sz} 3 戻ると候補の一覧')
            # 4 電波がない
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
            await c.set_offline(True); await open_book(pg)
            t = await pg.inner_text('#fsugBook'); mfrom = await pg.evaluate("$('mFrom').value")
            ok('電波がないため、候補は出せません' in t and mfrom == str(await pg.evaluate(ID % 'HND')), f'{sz} 4 電波がないときは候補なしで手入力へ（出発 {mfrom}）')
            await pg.screenshot(path=os.path.join(SHOTS, f'offline-{w}.png'))
            await c.set_offline(False)
            # 5 過去の便：日付＋数字だけの便名
            past = (datetime.now(JST) - timedelta(days=10)).strftime('%Y-%m-%d')
            await pg.evaluate(f"$('mFrom').value = ''; $('mTo').value = ''; $('mAirline').value = ''; $('mDate').value = '{past}'")
            await pg.fill('#mNo', '509'); await pg.dispatch_event('#mNo', 'change'); await pg.wait_for_timeout(900)
            r = await pg.evaluate("({f: $('mFrom').value, t: $('mTo').value, al: $('mAirline').value, no: $('mNo').value, hint: $('mNoHint').textContent})")
            ok(r['f'] == str(await pg.evaluate(ID % 'HND')) and r['t'] == str(await pg.evaluate(ID % 'CTS')) and r['al'] == 'JL' and r['no'] == 'JL509', f'{sz} 5 数字だけの便名で区間と航空会社を補う（{r}）')
            ok('08:00→09:35' in r['hint'] and '今の時刻表から' in r['hint'] and 'JA301J' in r['hint'], f'{sz} 5 時刻・機材とその日の記録（{r["hint"]}）')
            await pg.evaluate("$('mNoHint').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(SHOTS, f'past-{w}.png'))
            n0 = await pg.evaluate('__fake.db.manual_flights.length')
            await pg.click('#mAdd'); await pg.wait_for_timeout(700)
            mf = await pg.evaluate('__fake.db.manual_flights.slice(-1)[0] || null')
            ok(await pg.evaluate('__fake.db.manual_flights.length') == n0 + 1 and mf['flight_no'] == 'JL509' and mf['flown_on'] == past, f'{sz} 5 日誌に便名も残す（{mf}）')
            # 5 同じ番号がいくつか → 選ぶ
            await pg.evaluate("$('mAirline').value = ''"); await pg.fill('#mNo', '241'); await pg.dispatch_event('#mNo', 'change'); await pg.wait_for_timeout(900)
            n = await pg.evaluate("document.querySelectorAll('#mNoPick [data-mno-pick]').length")
            ok(n == 2 and not await pg.is_hidden('#mNoPick'), f'{sz} 5 同じ番号の便は選ぶ（{n}つ）')
            await pg.click('#mNoPick [data-mno-pick="1"]'); await pg.wait_for_timeout(600)
            r = await pg.evaluate("({f: $('mFrom').value, t: $('mTo').value, al: $('mAirline').value})")
            ok(r['f'] == str(await pg.evaluate(ID % 'HND')) and r['t'] == str(await pg.evaluate(ID % 'FUK')) and r['al'] == 'NH', f'{sz} 5 選んだ便で補う（{r}）')
            # 5 電波がないとき
            await c.set_offline(True); await pg.fill('#mNo', '509'); await pg.dispatch_event('#mNo', 'change'); await pg.wait_for_timeout(400)
            ok('電波がないため補えませんでした' in await pg.inner_text('#mNoHint'), f'{sz} 5 電波がないときの文')
            await c.set_offline(False)
            allerrs += errs; await b.close()
    print('errors', allerrs if not fails else fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
