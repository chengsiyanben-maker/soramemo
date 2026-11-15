import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 海外の空港の止まり具合（決定事項【11/15】案A・画面案 design/world-ops の W1〜W5）
#   1 案内板の国際線の便にピンの札（FAA のいちばん重いもの1つ）。過ぎた便・着いた便には出さない。便の数の札は便の列に出さない
#   2 「行き先の海外の空港のいま」の欄：出す空港だけ（FAA があるか欠航・30分以上の遅れ）・断り書きは太字・note を出す・国内線では出さない
#   3 札・欄の行を押すとくわしく（わけ・終わる見込み・今日の便の数・断り書き）
#   4 乗る便のカードに1行（FAA・便の数）。着いた便には出さない
#   5 取れないとき（関数が空・失敗）は何も出さない。滑走路の見方では読まない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, collections
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
now = datetime.now(timezone.utc); iso = lambda m: (now + timedelta(minutes=m)).isoformat()
BOARD = {'iata':'NRT','now':iso(0),'hours':[{'h':h,'flights':2,'late':0,'cancel':0,'ref':0} for h in range(24)],
  'next_arr':[{'flight':'JL61','other':'LAX','sched':iso(-20),'t':iso(-20),'actual':iso(-20),'intl':True},
              {'flight':'NH7','other':'SFO','sched':iso(30),'t':iso(30),'intl':True,'aircraft':'B789'},
              {'flight':'NH862','other':'ICN','sched':iso(50),'t':iso(50),'intl':True},
              {'flight':'JL501','other':'CTS','sched':iso(40),'t':iso(40)}],
  'next_dep':[{'flight':'JL62','other':'LAX','sched':iso(35),'t':iso(35),'intl':True},
              {'flight':'NH861','other':'ICN','sched':iso(15),'t':iso(15),'intl':True},
              {'flight':'NH1','other':'HNL','sched':iso(55),'t':iso(55),'intl':True}]}
NOTE = '出典：FAA NAS Status。運航の判断には使えません。遅れることがあります。便の数は JAL・ANA の運航情報（ODPT）から数えたものです'
WOPS = {'source':'FAA NAS Status','note':NOTE,'airports':[
  {'iata':'LAX','faa':[{'kind':'delay_dep','reason':'VOLUME','starts':None,'ends':None,'avg_delay':20,'max_delay':35,'trend':'increasing','since':iso(-50)},
                       {'kind':'ground_stop','label':'地上待機中','reason':'WEATHER / LOW CEILINGS','reason_ja':'天候（低い雲）','starts':None,'ends':iso(60),'avg_delay':None,'max_delay':None,'trend':None,'since':iso(-30)}],'flights':8,'cancelled':0,'late30':2,'feed_at':iso(-3),'note':'出典：FAA NAS Status。運航の判断には使えません。遅れることがあります'},
  {'iata':'SFO','faa':[{'kind':'gdp','reason':'WEATHER / WIND','starts':None,'ends':iso(120),'avg_delay':45,'max_delay':90,'trend':None,'since':iso(-90)}],'flights':4,'cancelled':0,'late30':0},
  {'iata':'ICN','faa':[],'flights':14,'cancelled':3,'late30':2,'note':'便の数は JAL・ANA の運航情報（ODPT）から数えたものです'},
  {'iata':'HNL','faa':[],'flights':6,'cancelled':0,'late30':0},
  {'iata':'CTS','faa':[],'flights':1,'cancelled':1,'late30':0}]}
FOREIGN = {'iata':'NRT','planes':[]}
LIVE = {'flight':'JL62','found':True,'source':'odpt','dep':'NRT','arr':'LAX','std':iso(35),'sta':iso(35+600),'phase':'sched','etd':iso(35)}
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, view='board', wops=WOPS, live=LIVE, plan=None, width=390, height=844):
    c = await b.new_context(viewport={'width':width,'height':height}, timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    reqs = []
    async def h(r):
        u = r.request.url; path = u.split('fake.supabase.co')[1].split('?')[0]; name = path.rsplit('/', 1)[-1]; reqs.append(path)
        if name == 'world_airport_ops' and wops == 'fail': return await r.fulfill(status=500, body='{}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        body = {'airport_board':BOARD, 'airport-foreign':FOREIGN, 'world_airport_ops':wops, 'flight-live':live, 'airport-traffic':{'planes':[], 'at':iso(0)}}.get(name, {} if '/functions/' in u else [])
        await r.fulfill(status=200, body=json.dumps(body), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
    await c.route('https://fake.supabase.co/rest/**', h); await c.route('https://fake.supabase.co/functions/**', h)
    init = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.opsAirport','NRT'); localStorage.setItem('soramemo.view.ops','%s');" % view
    if plan: init += "localStorage.setItem('soramemo.plan', %s);" % json.dumps(json.dumps(plan))
    await c.add_init_script(init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); OPS_PICKED = true")
    return c, pg, errs, reqs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); allerr = []
        # 1〜3 案内板
        c, pg, errs, reqs = await page(b)
        reqs.clear(); await pg.evaluate("goTab('ops')"); await pg.wait_for_selector('#opsBoard .bdseq', timeout=8000); await pg.wait_for_timeout(500)
        check('案内板で world_airport_ops を1回読む', collections.Counter(reqs)['/rest/v1/rpc/world_airport_ops'] == 1, dict(collections.Counter(reqs)))
        await pg.click('#opsBoard [data-board-dir="arr"]'); await pg.wait_for_timeout(200)
        lis = await pg.evaluate("[...document.querySelectorAll('#opsBoard .bdseq:not(.foreign) li')].map(li => ({t: li.innerText, tag: li.querySelector('.wobtn') ? li.querySelector('.wobtn').innerText : ''}))")
        by = lambda k: next((x for x in lis if k in x['t']), {'t':'', 'tag':''})
        check('SFO から着く便に「到着の間引き中 FAA」の札', '到着の間引き中' in by('NH7')['tag'] and 'FAA' in by('NH7')['tag'], by('NH7'))
        check('着いた便（LAX）には札を出さない', by('JL61')['t'] != '' and by('JL61')['tag'] == '', by('JL61'))
        check('便の数の札（ICN 欠航）は便の列に出さない', by('NH862')['tag'] == '' and '欠航3便' not in by('NH862')['t'], by('NH862'))
        check('国内線の便に札を出さない', by('JL501')['tag'] == '', by('JL501'))
        t = await pg.inner_text('#opsBoard')
        check('札があるときはピンの説明の1行', 'ピンの札は、行き先の空港全体のようすです' in t)
        await pg.click('#opsBoard [data-board-dir="dep"]'); await pg.wait_for_timeout(200)
        lis = await pg.evaluate("[...document.querySelectorAll('#opsBoard .bdseq:not(.foreign) li')].map(li => ({t: li.innerText, tag: li.querySelector('.wobtn') ? li.querySelector('.wobtn').innerText : ''}))")
        check('LAX へ出る便には、いちばん重い「地上待機中」（出発の遅れより重い）', '地上待機中' in by('JL62')['tag'] and '出発の遅れ' not in by('JL62')['tag'], by('JL62'))
        check('HNL（何もない）には札なし', by('NH1')['tag'] == '', by('NH1'))
        # 2 欄
        box = await pg.evaluate("(() => { const w = document.querySelector('#opsBoard .wobox'); return w ? { t: w.innerText, rows: [...w.querySelectorAll('.worow')].map(r => r.innerText), b: [...w.querySelectorAll('.wonote b')].map(x => x.innerText) } : null })()")
        check('「行き先の海外の空港のいま」の欄がある', bool(box) and '行き先の海外の空港のいま' in box['t'], box)
        names = [r.split('\n')[0] for r in (box or {}).get('rows', [])]
        check('欄は出す空港だけ（LAX・SFO・ICN。HNL と国内の CTS は出さない）', any('ロサンゼルス' in n for n in names) and any('サンフランシスコ' in n for n in names) and any('仁川' in n for n in names) and not any('ホノルル' in n for n in names) and not any('札幌' in n or 'CTS' in n for n in names), names)
        check('重いものが先（ロサンゼルスが1行目）', bool(names) and 'ロサンゼルス' in names[0], names)
        icn = next((r for r in (box or {}).get('rows', []) if '仁川' in r), '')
        check('ICN の行に便の数の札「今日 欠航3便」', '今日 欠航3便' in icn, icn)
        lax = next((r for r in (box or {}).get('rows', []) if 'ロサンゼルス' in r), '')
        check('LAX の行に「○時○分まで見込み」', 'まで見込み' in lax, lax)
        check('断り書きは欄の中に太字', bool(box) and any('運航の判断には使えません' in x for x in box['b']), box and box['b'])
        check('「○時○分 更新」は feed_at から', bool(box) and ' 更新' in box['t'], box and box['t'][:40])
        check('出典の note を出す', bool(box) and 'FAA NAS Status' in box['t'] and 'ODPT' in box['t'])
        # 押せる範囲
        hit = await pg.evaluate("(() => { const b = document.querySelector('#opsBoard .wobtn'); const r = b.getBoundingClientRect(); const a = getComputedStyle(b, '::after'); return { h: parseFloat(a.height), w: r.width } })()")
        check('札の押せる範囲は高さ 44px', hit['h'] >= 44, hit)
        rh = await pg.evaluate("Math.min(...[...document.querySelectorAll('#opsBoard .worow')].map(r => r.getBoundingClientRect().height))")
        check('欄の行は高さ 44px 以上', rh >= 44, rh)
        await pg.evaluate("document.querySelector('#opsBoard .wobox').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(WORK, 't133_board.png'))
        # 3 くわしく
        await pg.evaluate("document.querySelector('#opsBoard .bdseq').scrollIntoView({block:'center'})")
        await pg.click('#opsBoard .bdseq li .wobtn'); await pg.wait_for_timeout(300)
        st = await pg.evaluate("(() => { const d = document.getElementById('dWorldAp'); return { open: d.open, t: d.innerText } })()")
        check('札を押すとくわしくが開く（LAX・地上待機中・FAA の発表）', st['open'] and 'ロサンゼルス' in st['t'] and '地上待機中' in st['t'] and 'FAA の発表' in st['t'], st['t'][:120])
        check('くわしくに わけ・終わる見込み・遅れの向き・ほかの発表・今日の便', all(k in st['t'] for k in ['わけ', 'WEATHER / LOW CEILINGS', '天候（低い雲）', '発表の時刻', '終わる見込み', '現地', 'ほかの発表', '出発の遅れ', '今日の JAL・ANA の便']), st['t'])
        check('くわしくにも断り書き', 'この便のことではありません' in st['t'] and '運航の判断には使えません' in st['t'])
        await pg.screenshot(path=os.path.join(WORK, 't133_sheet_lax.png'))
        await pg.click('#dWorldAp [data-close]'); await pg.wait_for_timeout(200)
        await pg.evaluate("[...document.querySelectorAll('#opsBoard .worow')].find(r => r.innerText.includes('仁川')).click()"); await pg.wait_for_timeout(300)
        st = await pg.evaluate("document.getElementById('dWorldAp').innerText")
        check('仁川のくわしく：欠航 3便・JAL・ANA の便から・空港の発表はありません', '欠航' in st and 'JAL・ANA の便から' in st and 'ありません' in st and 'FAA の発表' not in st, st[:200])
        check('仁川のくわしくの出典は空港ごとの note（FAA の字が出ない）', 'FAA' not in st and 'ODPT' in st, st[-120:])
        await pg.screenshot(path=os.path.join(WORK, 't133_sheet_icn.png'))
        await pg.evaluate("document.getElementById('dWorldAp').close()")
        # 国内線
        await pg.click('#opsBoard [data-board-kind="dom"]'); await pg.wait_for_timeout(600)
        t = await pg.inner_text('#opsBoard')
        check('国内線では欄も札も出さない', '行き先の海外の空港のいま' not in t and 'ピンの札' not in t)
        allerr += errs; await c.close()
        # 667 の幅
        c, pg, errs, reqs = await page(b, width=375, height=667)
        await pg.evaluate("goTab('ops')"); await pg.wait_for_selector('#opsBoard .wobox', timeout=8000); await pg.wait_for_timeout(300)
        ov = await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        check('375 の幅で横にはみ出さない', ov)
        await pg.evaluate("document.querySelector('#opsBoard .bdseq').scrollIntoView({block:'start'}); scrollBy(0, -120)"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(WORK, 't133_board_667.png'))
        allerr += errs; await c.close()
        # 5 取れないとき・滑走路の見方
        for w, label in [([], '空'), ('fail', '失敗'), ({'source':'FAA NAS Status','note':NOTE,'airports':[]}, '空港なし')]:
            c, pg, errs, reqs = await page(b, wops=w)
            await pg.evaluate("goTab('ops')"); await pg.wait_for_selector('#opsBoard .bdseq', timeout=8000); await pg.wait_for_timeout(400)
            t = await pg.inner_text('#opsBoard')
            check(f'取れないとき（{label}）は札も欄も出さない', '行き先の海外の空港のいま' not in t and await pg.locator('#opsBoard .wobtn').count() == 0 and 'これから' in t)
            allerr += errs; await c.close()
        c, pg, errs, reqs = await page(b, view='runway')
        reqs.clear(); await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(2000)
        check('滑走路の見方では world_airport_ops を読まない', '/rest/v1/rpc/world_airport_ops' not in reqs, reqs)
        allerr += errs; await c.close()
        # 4 乗る便のカード
        today = (now + timedelta(hours=9)).date().isoformat()
        c, pg, errs, reqs = await page(b, plan={'intl':True,'dep':'NRT','arr':'LAX','airline':'JL','no':'JL62','day':today})
        await pg.evaluate("goTab('home')"); await pg.wait_for_selector('#rideCard .woline', timeout=8000)
        t = await pg.inner_text('#rideCard')
        check('乗る便：到着地ロサンゼルスで地上待機中（FAA・○時○分まで見込み）', '到着地ロサンゼルスで地上待機中' in t and '（FAA・' in t and 'まで見込み' in t, t)
        check('乗る便：いまの発表の断り・出典に FAA', '着くころには変わっていることがあります' in t and 'FAA（アメリカ連邦航空局）の発表' in t)
        await pg.locator('#rideCard').screenshot(path=os.path.join(WORK, 't133_ride_faa.png'))
        await pg.click('#rideCard .woline'); await pg.wait_for_timeout(300)
        check('乗る便の1行を押すとくわしく', await pg.evaluate("document.getElementById('dWorldAp').open"))
        allerr += errs; await c.close()
        live2 = dict(LIVE, arr='ICN', flight='NH861')
        c, pg, errs, reqs = await page(b, live=live2, plan={'intl':True,'dep':'NRT','arr':'ICN','airline':'NH','no':'NH861','day':today})
        await pg.evaluate("goTab('home')"); await pg.wait_for_selector('#rideCard .woline', timeout=8000)
        t = await pg.inner_text('#rideCard')
        check('乗る便：到着地ソウル（仁川）：今日の欠航 3便（JAL・ANA）・空港全体の数', '到着地ソウル（仁川）：今日の欠航 3便' in t and '（JAL・ANA）' in t and '空港全体の数です。この便のことではありません' in t, t)
        await pg.locator('#rideCard').screenshot(path=os.path.join(WORK, 't133_ride_cnt.png'))
        allerr += errs; await c.close()
        live3 = dict(LIVE, phase='landed', ata=iso(-5))
        c, pg, errs, reqs = await page(b, live=live3, plan={'intl':True,'dep':'NRT','arr':'LAX','airline':'JL','no':'JL62','day':today})
        await pg.evaluate("goTab('home')"); await pg.wait_for_selector('#rideCard .rv', timeout=8000); await pg.wait_for_timeout(300)
        check('着いた便には1行を出さない', await pg.locator('#rideCard .woline').count() == 0 and '到着しました' in await pg.inner_text('#rideCard'))
        allerr += errs; await c.close()
        await b.close()
        print('errors', allerr + fails)
asyncio.run(main())
