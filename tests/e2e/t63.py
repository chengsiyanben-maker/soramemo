import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 撮る人の見方：注目の機体・機体のくわしく・撮影条件と天気・近づいたら知らせる
import asyncio, json
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
# 時刻は昼の12時（日本時間）に固定する（深夜は滑走路が1本になり、撮影地から見える機体が変わるため）
_d = datetime.now(timezone.utc); now = datetime(_d.year, _d.month, _d.day, 3, 0, tzinfo=timezone.utc)
iso = lambda m: (now + timedelta(minutes=m)).isoformat()
HRS = [{'h': h, 'flights': [0,0,0,0,0,2,30,48,52,50,44,46,48,44,42,46,48,50,52,48,40,30,20,6][h], 'late': (h % 5 == 0) * 2, 'cancel': 0, 'ref': 1} for h in range(24)]
BOARD = {'iata': 'HND', 'now': iso(0), 'hours': HRS,
  'next_arr': [{'flight': 'JL500', 'other': 'ITM', 'sched': iso(5), 't': iso(5), 'aircraft': 'B738'}, {'flight': 'NH212', 'other': 'LHR', 'sched': iso(25), 't': iso(25), 'intl': True, 'aircraft': 'B789'}],
  'next_dep': [{'flight': 'NH106', 'other': 'LAX', 'sched': iso(15), 't': iso(15), 'intl': True, 'aircraft': 'B77W'}, {'flight': 'JL903', 'other': 'OKA', 'sched': iso(30), 'est': iso(48), 't': iso(48), 'aircraft': 'A359'}, {'flight': 'BC101', 'other': 'UKB', 'sched': iso(40), 't': iso(40), 'aircraft': 'B738'}]}
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); c=await b.new_context(viewport={'width':400,'height':860}, timezone_id='Asia/Tokyo')
        await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1')")
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        async def rpc(r):
            name = r.request.url.rsplit('/', 1)[-1]
            await r.fulfill(status=200, body=json.dumps(BOARD if name == 'airport_board' else []), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        await c.route('https://fake.supabase.co/rest/v1/rpc/**', rpc)
        FG = {'planes': [{'flight': 'TG660', 'airline': 'TG', 'other': 'BKK', 'kind': 'arr', 'status': 'approach', 'km': 40, 'alt_ft': 6000, 'type': 'A359'}]}
        await c.route('https://fake.supabase.co/functions/v1/airport-foreign**', lambda r: r.fulfill(status=200, body=json.dumps(FG), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        NOWD = {'weather': {'time': iso(-10), 'wdir': 340, 'wspd': 12, 'wgst': None, 'vis_m': 10000, 'vis_plus': True, 'sky': '晴れ', 'ceil_ft': None, 'temp': 16, 'dewp': 14, 'low_ft': 1800, 'layers': [{'cover': 'FEW', 'base': 1800}, {'cover': 'SCT', 'base': 4500}]},
          'taf': {'periods': [{'from': int(now.timestamp()) - 3600, 'to': int(now.timestamp()) + 86400, 'kind': 'base', 'wdir': 340, 'wspd': 10, 'sky': '晴れ', 'low_ft': 2500, 'prob': None, 'wgst': None, 'vis_m': 10000, 'ceil_ft': None}]}, 'flights': None}
        await c.route('https://fake.supabase.co/functions/v1/airport-now**', lambda r: r.fulfill(status=200, body=json.dumps(NOWD), content_type='application/json', headers={'Access-Control-Allow-Origin':'*'}))
        pg=await c.new_page(); await pg.clock.set_fixed_time(now); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '')[:300]))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load'); await pg.wait_for_timeout(600)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(800)
        await pg.evaluate("localStorage.setItem('soramemo.view.ops', 'photo')")
        await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(1800)
        await pg.click('[data-vw="ops:photo"]'); await pg.wait_for_timeout(1200)
        t = await pg.inner_text('#opsPhoto'); print('PHOTO', t.replace('\n', ' | '))
        check('注目の機体のカード:', await pg.locator('#opsPhoto .sphero').count() == 1)
        check('注目だけ（B738 は出ない）:', 'NH212' in t and 'TG660' in t and 'JL500' not in t and 'BC101' not in t)
        # 撮影地ごとの絞り込み
        n_spots = await pg.locator('#opsPhoto [data-spspot]').count()
        check('撮影地のボタンが並ぶ:', n_spots >= 3)
        sel = await pg.inner_text('#opsPhoto .spsel'); print('SEL', sel.replace('\n', ' | '))
        check('選んでいる撮影地と見える線:', '見える：' in sel)
        before = await pg.locator('#opsPhoto .sprow').count()
        btns = pg.locator('#opsPhoto [data-spspot]:not([disabled])')
        names = [await btns.nth(i).get_attribute('data-spspot') for i in range(await btns.count())]
        await btns.nth(len(names) - 1).click(); await pg.wait_for_timeout(200)
        check('撮影地を変えると選び直される:', names[-1] in await pg.inner_text('#opsPhoto .spsel') and await pg.evaluate("localStorage.getItem('soramemo.photoSpot.HND')") == names[-1])
        await btns.nth(0).click(); await pg.wait_for_timeout(200)
        # 羽田の着陸：来た方面で1本に絞る（伊丹＝南西→34L、新千歳＝北→34R、出発地が分からなければ2本のまま）
        rws = await pg.evaluate("""() => { const op = { arr:['34L','34R'], dep:['05','34R'] };
          return [spRwsOf({ dir:'arr', other:'ITM', fl:'X1' }, op), spRwsOf({ dir:'arr', other:'CTS', fl:'X2' }, op), spRwsOf({ dir:'arr', other:'ZZZ', fl:'X3' }, op), spRwsOf({ dir:'dep', other:'ITM', fl:'X4' }, op),
            spRwsOf({ dir:'arr', other:'FUK', fl:'X5' }, { arr:['22','23'], dep:[] }), spRwsOf({ dir:'arr', other:'LAX', fl:'X6' }, { arr:['16L','16R'], dep:[] }),
            spRwsOf({ dir:'dep', other:'CTS', fl:'X7' }, { arr:['22','23'], dep:['16L','16R'] }), spRwsOf({ dir:'dep', other:'FUK', fl:'X8' }, { arr:['22','23'], dep:['16L','16R'] }), spRwsOf({ dir:'dep', other:'ZZZ', fl:'X9' }, op)]; }""")
        print('RWS', rws)
        ln = await pg.evaluate("""() => { const keep = OPS_AP; OPS_AP = 'CTS';
          SP_LEARN.set('CTS', { at:Date.now(), d:{ rows:[{ dir:'arr', rwy:'01R', sec:4, n:80 }, { dir:'arr', rwy:'01L', sec:4, n:6 }, { dir:'dep', rwy:'01L', sec:4, n:20 }, { dir:'dep', rwy:'01R', sec:4, n:15 }] } });
          const op = { arr:['01L','01R'], dep:['01L','01R'] }; const r = [spRwsOf({ dir:'arr', other:'HND', fl:'Y1' }, op), spRwsOf({ dir:'dep', other:'HND', fl:'Y2' }, op)];
          OPS_AP = keep; return r; }""")
        print('LEARN', ln)
        nr = await pg.evaluate("""() => { const keep = OPS_AP; OPS_AP = 'NRT'; const r = [spRwsOf({ dir:'arr', other:'CTS', fl:'Z1' }, { arr:['34L','34R'], dep:[] }), spRwsOf({ dir:'arr', other:'FUK', fl:'Z2' }, { arr:['16L','16R'], dep:[] }), spRwsOf({ dir:'arr', other:'CTS', fl:'Z3' }, { arr:['16L','16R'], dep:[] })]; OPS_AP = keep; return r; }""")
        print('NRT', nr); check('成田も来た方面で絞る:', nr[0]['rws'] == ['34R'] and nr[1]['rws'] == ['16R'] and nr[2]['rws'] == ['16L'])
        ph = await pg.evaluate("""() => predictionHTML({ src:'reg', known:{ callsign:'ANA21', dep:'HND', arr:'ITM', last:new Date().toISOString() }, next:[{ callsign:'ANA30', dep:'ITM', arr:'HND', time:'13:05', seen:4, share:0.8 }] })""")
        check('全機の運用の予想（呼び出し符号を便名に）:', 'NH21' in ph and 'NH30' in ph and '13:05ごろ' in ph and '80%（4回）' in ph and '全機の位置の記録' in ph)
        check('学習した使い分けで絞る（8割以上・30機以上だけ）:', ln[0] == {'rws': ['01R'], 'side': False, 'learn': 93} and ln[1]['rws'] == ['01L', '01R'])
        check('来た方面で滑走路を絞る:', rws[0] == {'rws': ['34L'], 'side': True} and rws[1]['rws'] == ['34R'] and rws[2] == {'rws': ['34L', '34R'], 'side': False} and rws[3] == {'rws': ['05'], 'side': True} and rws[6]['rws'] == ['16L'] and rws[7]['rws'] == ['16R'] and rws[8] == {'rws': ['05', '34R'], 'side': False} and rws[4]['rws'] == ['22'] and rws[5]['rws'] == ['16L'])
        check('天気の札:', '雲底 1,800ft' in t and 'ベイパー 出やすい' in t)
        await pg.click('[data-spfilter="all"]'); await pg.wait_for_timeout(200)
        check('すべてで B738 も出る:', 'JL500' in await pg.inner_text('#opsPhoto'))
        await pg.click('[data-spfilter="dep"]'); await pg.wait_for_timeout(200)
        t2 = await pg.inner_text('#opsPhoto .splist2'); check('離陸だけ:', 'NH106' in t2 and 'NH212' not in t2)
        await pg.locator('#opsPhoto .sprow').first.click(); await pg.wait_for_timeout(300)
        check('機体のくわしく:', await pg.evaluate("$('dSpotFl').open") and '離陸' in await pg.inner_text('#dSpotFl'))
        td = await pg.inner_text('#dSpotFl'); check('管制の場面（離陸する機体はグランドから）:', 'いまの管制の場面' in td and '東京グランド' in td and '121.70' in td)
        await pg.screenshot(path=os.path.join(WORK, 't63_detail.png'))
        await pg.click('#dSpotFl [data-atc]'); await pg.wait_for_timeout(200)
        ta = await pg.inner_text('#dAtc'); check('いま聞く周波数:', await pg.evaluate("$('dAtc').open") and '118.10' in ta and 'ATIS' in ta and '128.80' in ta and '航空路誌' in ta)
        await pg.click('#dAtc [data-atctab="arr"]'); await pg.wait_for_timeout(100)
        check('着陸を聞く：アプローチ:', '東京アプローチ' in await pg.inner_text('#dAtc') and '119.10' in await pg.inner_text('#dAtc'))
        await pg.screenshot(path=os.path.join(WORK, 't63_atc.png'), full_page=True)
        await pg.click('#dAtc [data-close]'); await pg.wait_for_timeout(100)
        sc = await pg.evaluate("""() => { const c = opsDef().center; const at = (d, alt) => ({ lat:c[0] + d / 111, lon:c[1], alt_ft:alt });
          return [atcScene({ dir:'arr' }, at(60, 9000)).k, atcScene({ dir:'arr' }, at(10, 2000)).k, atcScene({ dir:'arr' }, at(200, 35000)).k, atcScene({ dir:'dep' }, at(6, 1500)).k, atcScene({ dir:'dep' }, at(40, 12000)).k]; }""")
        print('SCENE', sc); check('場面の推定:', sc == ['app', 'twr', 'cruise', 'twr', 'dep'])
        await pg.click('#dSpotFl .spx'); await pg.wait_for_timeout(200)
        check('閉じる:', not await pg.evaluate("$('dSpotFl').open"))
        await pg.locator('#opsPhoto [data-spcond]').last.click(); await pg.wait_for_timeout(800)
        tc = await pg.inner_text('#dSpotCond'); print('COND', tc[:300].replace('\n', ' | '))
        check('撮影条件と天気:', await pg.evaluate("$('dSpotCond').open") and '1,800' in tc and '4,500ft' in tc and '日の出' in tc and 'これから' in tc)
        check('撮影地の地図:', await pg.locator('#dSpotCond svg.spmap circle').count() >= 2)
        await pg.screenshot(path=os.path.join(WORK, 't63_cond.png'), full_page=True)
        await pg.click('#dSpotCond [data-close]'); await pg.wait_for_timeout(200)
        # 知らせの設定（端末の通知の申し込みは置き換えて、送る中身だけ確かめる）
        await pg.evaluate("window.pushOK = () => true; syncPush = async (a, f, s, spot) => { window.__spot = spot; localStorage.setItem('soramemo.pushSpot', JSON.stringify(spot)); return true; }")
        await pg.click('#opsPhoto [data-sppush]'); await pg.wait_for_timeout(300)
        check('知らせの設定:', await pg.evaluate("$('dSpotPush').open"))
        await pg.click('[data-spkind="special"]'); await pg.click('[data-spkind="reg"]'); await pg.wait_for_timeout(100)
        await pg.fill('#spRegs', 'ja01xj, bad JA873A'); await pg.click('[data-splead="10"]'); await pg.wait_for_timeout(100)
        await pg.click('[data-spsave]'); await pg.wait_for_timeout(300)
        sp = await pg.evaluate('window.__spot'); print('SPOT', sp)
        check('保存した中身:', sp and sp['iata'] == 'HND' and sp['kinds'] == ['special', 'reg'] and sp['regs'] == ['JA01XJ', 'JA873A'] and sp['lead'] == 10)
        await pg.click('[data-spfilter="pick"]'); await pg.wait_for_timeout(200)
        n = pg.locator('#opsPhoto .spnote'); check('10分前に知らせるボタン:', '10分前' in await n.inner_text())
        await n.click(); await pg.wait_for_timeout(300)
        sp = await pg.evaluate('window.__spot'); print('SPOT2', sp)
        check('便を知らせに足す:', len(sp['flights']) == 1 and sp['kinds'] == ['special', 'reg'])
        check('取り消しに変わる:', '取り消す' in await pg.locator('#opsPhoto .spnote').inner_text())
        await pg.click('[data-sppush]'); await pg.wait_for_timeout(200); await pg.click('[data-spoff]'); await pg.wait_for_timeout(300)
        check('すべてやめる:', (await pg.evaluate('window.__spot'))['iata'] is None)
        print('errors', errs, 'fails', fails); await b.close()
asyncio.run(main())
