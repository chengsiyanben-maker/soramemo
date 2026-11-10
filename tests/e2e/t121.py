# 図鑑の空港ページのデータ欄（11/10 PM の指示・本人の決定「図鑑のデータ」）：供用開始・滑走路と出典の1行
#   行がない空港（成田・伊丹・番外編）は欄ごと出さない／羽田は年がないので滑走路だけ／「開港」と書かない／福岡のヘリポートは本数に数えない
#   サーバーの表（airport_facts）があれば、その値で上書きする
import os, sys, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-zukan-facts')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok, extra=''):
    print(label, ok, extra)
    if not ok: fails.append(label)
SEED = """() => { const id = i => A.find(a => a.iata === i).id, at = (y,m,d) => new Date(y,m-1,d,10).getTime();
  S.checkins = [['HND',2025,12,14],['CTS',2025,12,15],['FUK',2026,4,1],['ITM',2026,5,2],['NRT',2026,6,1]].map(([i,y,m,d]) => ({a:id(i), t:at(y,m,d), acc:20, term:null}));
  for(let k=0;k<5;k++) S.checkins.push({a:id('HND'), t:at(2026,1,1)+k*864e5*10, acc:20, term:null}); S.flights = []; save(); render(); }"""
NEW = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.zk.notice','new'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');"
async def open_app(b, h=844, night=False):
    c=await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2, timezone_id='Asia/Tokyo')
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.add_init_script(NEW)
    pg=await c.new_page(); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(500)
    await pg.evaluate(SEED); await pg.wait_for_timeout(300)
    if night: await pg.evaluate("document.documentElement.dataset.night = 'on'")
    await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(300)
    return c, pg, errs
async def ap(pg, iata):
    await pg.evaluate(f"openAirport(IATA.{iata}.id)"); await pg.wait_for_timeout(300)
    return await pg.evaluate("(() => { const b = document.querySelector('#dAirportBody'); const f = b.querySelector('#zkFacts'); return {all: b.innerText, facts: f ? f.innerText : null, cells: f ? [...f.querySelectorAll('.zk-facts > div')].map(x => x.innerText.replace(/\\s+/g, '')) : [], rw: f ? [...f.querySelectorAll('.zk-rw li')].map(x => x.innerText.replace(/\\s+/g, '')) : [], href: f && f.querySelector('.zk-src a') ? f.querySelector('.zk-src a').href : null}; })()")
async def main():
    allerr = []
    async with async_playwright() as p:
        b=await p.chromium.launch()
        c, pg, errs = await open_app(b)
        check('組み立てで82空港の値が入っている:', await pg.evaluate("Object.keys(AIRPORT_FACTS).length") == 82)
        r = await ap(pg, 'CTS')
        check('新千歳：供用開始 1988年・滑走路 2本:', r['cells'] == ['供用開始1988年', '滑走路2本'], str(r['cells']))
        check('新千歳：A・B の長さ×幅:', r['rw'] == ['A3,000m×60m', 'B3,000m×60m'], str(r['rw']))
        check('出典の1行と国土交通省の PDF へのリンク:', '出典：国土交通省『空港一覧』を加工して作成' in r['facts'] and r['href'] == 'https://www.mlit.go.jp/koku/content/002021263.pdf', str(r['href']))
        check('「開港」とは書かない:', '開港' not in r['all'])
        check('データ欄は押した回数の下:', await pg.evaluate("(() => { const d = document.querySelector('#dAirportBody .zk-dl:not(.zk-facts)'), f = document.querySelector('#zkFacts'); return !!d && !!f && d.getBoundingClientRect().bottom <= f.getBoundingClientRect().top; })()"))
        await pg.screenshot(path=os.path.join(SHOTS, '01-844-cts.png'))
        r = await ap(pg, 'HND')
        check('羽田：年がないので滑走路だけ（4本・横いっぱい）:', r['cells'] == ['滑走路4本'] and await pg.evaluate("document.querySelector('#zkFacts .zk-facts > div').classList.contains('w')"), str(r['cells']))
        check('羽田：A〜D の4行:', len(r['rw']) == 4 and r['rw'][2] == 'C3,360m×60m', str(r['rw']))
        await pg.screenshot(path=os.path.join(SHOTS, '02-844-hnd.png'))
        r = await ap(pg, 'FUK')
        check('福岡：ヘリポートは本数に数えない（2本）・補足を添える:', r['cells'] == ['供用開始1972年', '滑走路2本'] and len(r['rw']) == 4 and '奈多地区（ヘリポート）' in r['rw'][2], str(r['rw']))
        for i in ['NRT', 'ITM', 'NGO', 'KIX']:
            r = await ap(pg, i)
            check(f'{i}：会社管理の空港は欄ごと出さない（出典も）:', r['facts'] is None and '出典' not in r['all'] and '供用開始' not in r['all'])
        await pg.screenshot(path=os.path.join(SHOTS, '03-844-itm.png'))
        x = await pg.evaluate("(() => { const a = XA[0]; if(!a) return null; openAirport(a.id); return !document.querySelector('#zkFacts') && !document.querySelector('#dAirportBody').innerText.includes('供用開始'); })()")
        check("番外編は欄ごと出さない:", x is True, str(x))
        r = await ap(pg, 'WKJ')
        check('まだの空港にも出す（稚内 1960年・1本）:', r['cells'] == ['供用開始1960年', '滑走路1本'] and r['rw'] == ['2,200m×45m'], str(r))
        await pg.screenshot(path=os.path.join(SHOTS, '04-844-wkj-yet.png'))
        r = await ap(pg, 'CTS')
        await pg.evaluate("document.querySelector('#zkFacts').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '01b-844-cts-facts.png'))
        lk = await pg.evaluate("(() => { const a = document.querySelector('#zkFacts .zk-src a'); const s = getComputedStyle(a); return [a.target, a.rel, s.textDecorationLine]; })()")
        check('リンクは別のタブで開き、下線つき:', lk[0] == '_blank' and 'noopener' in lk[1] and 'underline' in lk[2], str(lk))
        allerr += errs; await c.close()
        # 667 と夜
        c, pg, errs = await open_app(b, h=667)
        await ap(pg, 'HND'); await pg.evaluate("document.querySelector('#zkFacts').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
        over = await pg.evaluate("[...document.querySelectorAll('#zkFacts *')].filter(x => x.getBoundingClientRect().right > innerWidth + 0.5).length")
        check('667：はみ出さない:', over == 0, str(over))
        await pg.screenshot(path=os.path.join(SHOTS, '05-667-hnd.png'))
        allerr += errs; await c.close()
        c, pg, errs = await open_app(b, night=True)
        await ap(pg, 'CTS'); await pg.evaluate("document.querySelector('#zkFacts').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(SHOTS, '06-844-cts-night.png'))
        allerr += errs; await c.close()
        # サーバーの表があれば上書きする
        shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_server_test.html'))
        open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
        c = await b.new_context(viewport={'width':390,'height':844}); await c.add_init_script(NEW)
        await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
        pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(600)
        await pg.evaluate("__fake.db.airport_facts = [{airport_id: IATA.CTS.id, opened_year: 1990, runways: [{name:'A', length_m:3100, width_m:60}], source_ref: 'https://www.mlit.go.jp/koku/content/002021999.pdf（令和9年1月1日現在）'}]")
        await pg.evaluate("openAirport(IATA.CTS.id)"); await pg.wait_for_timeout(500)
        f = await pg.inner_text('#zkFacts')
        check('サーバーの値で上書き（1990年・3,100m）:', '1990' in f and '3,100' in f and await pg.evaluate("document.querySelector('#zkFacts .zk-src a').href") == 'https://www.mlit.go.jp/koku/content/002021999.pdf', f)
        await pg.evaluate("ZK_FACTS_LOADED = false; delete __fake.db.airport_facts"); await pg.evaluate("openAirport(IATA.HND.id)"); await pg.wait_for_timeout(400)
        check('表がないときは組み立ての値のまま（羽田 4本）:', '4' in await pg.inner_text('#zkFacts .zk-facts'))
        allerr += [e for e in errs]; await c.close()
        await b.close()
    print('fails', fails)
    print('errors', fails + allerr)
asyncio.run(main())
