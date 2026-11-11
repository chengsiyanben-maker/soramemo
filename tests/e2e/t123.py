import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# フライトの作り直し（11/11 本人「すべてOK」・画面案 design/flight-book 4版）
#   見方は日誌・地図・年のまとめの3つ／車などの移動は便・空の上・距離に入れず別に数える／日誌は年をまたいで1本／
#   年を選ぶとその年の頭へ／1便のくわしい所と画像で共有（登録記号ははじめ ON・座席ははじめ OFF）／古い見方の id は読むときに直す
import asyncio
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.persona','all');"
async def start(b, h=844, extra=""):
    c = await b.new_context(viewport={'width':390,'height':h}, timezone_id='Asia/Tokyo')
    await c.add_init_script(INIT + extra)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WEB,'index.html')); await pg.wait_for_function('typeof render === "function"'); await pg.wait_for_timeout(700)
    return c, pg, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c, pg, errs = await start(b)
        await pg.evaluate('openMyPage()'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(800)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(400)
        check('見方は日誌・地図・年のまとめの3つ:', await pg.evaluate("[...document.querySelectorAll('#logViews [data-vw]')].map(x=>x.textContent).join(',')") == '日誌,地図,年のまとめ')
        check('はじめは日誌:', await pg.evaluate("VIEW.log") == 'diary')
        check('上の段（そらメモ・マイページ）が見える・シートはない:', await pg.locator('header.top').is_visible() and await pg.locator('#logSheet').count() == 0)
        # 車などの移動（デモの長崎→福岡）
        info = await pg.evaluate("""(() => { const y = FB_Y, fs = S.flights.filter(f => new Date(f.dep).getFullYear() === y), car = fs.filter(isCar), fly = fs.filter(f => !isCar(f));
          return { car: car.length, fly: fly.length, km: Math.round(fly.reduce((x, f) => x + f.km, 0)), allCar: S.flights.filter(isCar).length, focusKm: Math.round(focusKm()), flyKm: Math.round(S.flights.filter(f => !isCar(f)).reduce((x, f) => x + f.km, 0)),
            hsFl: +$('hsFl').textContent, nFly: S.flights.filter(f => !isCar(f)).length, routes: routes().size, flyRoutes: new Set(S.flights.filter(f => !isCar(f)).map(f => [f.from, f.to].sort((a,b)=>a-b).join('-'))).size }; })()""")
        print(info)
        check('デモに車などの移動が1つ:', info['allCar'] == 1)
        yrtxt = await pg.inner_text('#fbYr')
        check('上の数：便の数は車などを入れない:', f"{info['fly']}\n便" in yrtxt or f"{info['fly']}便" in yrtxt.replace('\n', ''))
        check('上の数：距離は車などを入れない:', f"{info['km']:,}" in yrtxt)
        if info['car']: check('上に「車など 1（…km）は別に数えています」:', '車など 1' in yrtxt and '別に数えています' in yrtxt)
        check('距離（focusKm）・路線・ホームの便の数も車などを入れない:', info['focusKm'] == info['flyKm'] and info['routes'] == info['flyRoutes'] and info['hsFl'] == info['nFly'])
        # 日誌の行：車などは会社の帯なし・点線の札・空の上なし
        if not info['car']: await pg.evaluate("fbGoYear(new Date(S.flights.find(isCar).dep).getFullYear())"); await pg.wait_for_timeout(300)
        row = pg.locator('#flights .fbrow[data-g="CAR"]').first
        check('車などの行がある:', await row.count() == 1)
        rt = await row.inner_text()
        check('車などの行：札「車など」・空の上なし・距離:', '車など' in rt and '空の上なし' in rt and 'km' in rt and '発' not in rt)
        check('車などの行：会社の帯なし:', await row.evaluate("e => getComputedStyle(e, '::before').backgroundColor") in ('rgba(0, 0, 0, 0)', 'transparent'))
        mh = await pg.evaluate("[...document.querySelectorAll('#flights .fbmh')].map(x=>x.innerText.replace(/\\n/g,' ')).find(t => t.includes('車など'))")
        check('月の見出しに「○便・車など 1」:', bool(mh) and '便・車など 1' in mh)
        # 便の行：日付が左・出発の時刻と便名・時間と距離
        r0 = await pg.locator('#flights .fbrow:not([data-g="CAR"])').first.inner_text()
        check('便の行：○時間○分・km・発:', '時間' in r0 or '分' in r0) ; check('便の行：発と km:', '発' in r0 and 'km' in r0)
        # 年をまたぐ：2つ以上の年があるように、前の年に記録帳の便を足す
        await pg.evaluate("""(() => { const y = new Date(S.flights[0].dep).getFullYear() - 1; const h = A.find(a=>a.iata==='HND').id, o = A.find(a=>a.iata==='OKA').id;
          S.manual.push({from:h, to:o, d:`${y}-03-10`, airline:'JL'}, {from:o, to:h, d:`${y}-03-12`, airline:'JL'}); save(); render(); })()""")
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(300)
        ys = await pg.evaluate("fbYears(FB_ES)")
        print('years', ys)
        check('記録のある年が2つ以上:', len(ys) >= 2)
        old = ys[-1]
        check('日誌は1本：前の年の帯（便の数・まとめ ›）がある:', await pg.locator(f'#fbY-{old}').count() == 1 and 'まとめ' in await pg.inner_text(f'#fbY-{old}'))
        check('前の年の月の見出しに小さく年:', await pg.evaluate(f"[...document.querySelectorAll('#flights .fbmh[data-y=\"{old}\"]')].some(x => x.innerText.includes('{old}年'))"))
        check('年の終わりに「○年の便はここまで」:', f'{old}年の便はここまで' in await pg.inner_text('#flights'))
        # 年を選ぶ：その年の頭へ飛ぶ（日誌は消えない）
        await pg.click('[data-fbyears]'); await pg.wait_for_timeout(300)
        check('年を選ぶの一覧が開く:', await pg.evaluate("$('dFbYears').open") and await pg.locator('#dFbYears [data-fbypick]').count() == len(ys))
        await pg.click(f'#dFbYears [data-fbypick="{old}"]'); await pg.wait_for_timeout(500)
        top = await pg.evaluate(f"$('fbY-{old}').getBoundingClientRect().top - $('fbMiniBar').getBoundingClientRect().bottom")
        check('選んだ年の頭まで送った（帯が上の細い帯のすぐ下）:', -4 <= top <= 60)
        check('上の年がその年になる:', f'{old}年' in await pg.inner_text('#fbYr') and f'{old}年' in await pg.inner_text('#fbMiniBar'))
        # 上に止まるのは年の字と ‹ › だけの細い帯（月の見出しを隠さない・review-app-1 の2）
        mini = await pg.evaluate("""(() => { const m = $('fbMini'), r = $('fbMiniBar').getBoundingClientRect(); return { shown: !m.hidden && getComputedStyle(m).visibility === 'visible', h: Math.round(r.height), top: Math.round(r.top), nums: !!$('fbMiniBar').querySelector('.yrnums'), btn: $('fbMiniBar').querySelectorAll('[data-fby]').length }; })()""")
        print('細い帯', mini)
        check('送ると細い帯が上に止まる（高さ56px以下・便や km は出さない・‹ › あり）:', mini['shown'] and mini['h'] <= 56 and -1 <= mini['top'] <= 1 and not mini['nums'] and mini['btn'] == 2)
        await pg.evaluate("window.scrollBy(0, 220)"); await pg.wait_for_timeout(300)
        hid = await pg.evaluate("""(() => { const b = $('fbMiniBar').getBoundingClientRect().bottom; const hs = [...document.querySelectorAll('#flights .fbmh')].filter(h => { const r = h.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
          return { vis: hs.length, under: hs.filter(h => h.getBoundingClientRect().top < b - 2 && h.getBoundingClientRect().bottom > 0).length }; })()""")
        print('月の見出し', hid)
        check('月の見出しが細い帯の下に隠れない（見えている見出しが帯と重ならない）:', hid['under'] == 0 or hid['vis'] > hid['under'])
        check('新しい年の便も続けて残っている（日誌は1本）:', await pg.evaluate(f"document.querySelectorAll('#flights .fbmh:not([data-y=\"{old}\"])').length") > 0)
        await pg.evaluate("window.scrollTo(0, 0)"); await pg.wait_for_timeout(300)
        check('上へ戻すと上の年も新しい年に戻る:', f'{ys[0]}年' in await pg.inner_text('#fbYr'))
        check('いちばん上では細い帯を出さない（大きいカードだけ）:', await pg.evaluate("$('fbMini').hidden"))
        # 年の帯を押すと年のまとめ（その年だけ）
        await pg.click(f'#fbY-{old}'); await pg.wait_for_timeout(300)
        yt = await pg.inner_text('#flights')
        check('年の帯 → 年のまとめ（その年）:', await pg.evaluate("VIEW.log") == 'year' and f'{old}年' in await pg.inner_text('#fbYr') and '路線' in yt and '月ごとの便の数' in yt)
        await pg.click('#fbYr [data-fby]:not([disabled]) >> nth=-1'); await pg.wait_for_timeout(300)
        check('› で新しい年へ（年のまとめは選んだ年だけ）:', await pg.evaluate("FB_Y") == ys[ys.index(old) - 1])
        # 地図：太さ＝回数・区間を押すとその区間
        await pg.click('[data-vw="log:map"]'); await pg.wait_for_timeout(500)
        await pg.evaluate("fbGoYear(new Date(S.flights.find(isCar).dep).getFullYear())"); await pg.wait_for_timeout(400)   # 車などのある年
        dash = await pg.evaluate("(() => { const i = document.querySelector('#flights .fblg i.dash'); return i ? getComputedStyle(i).backgroundImage : 'なし'; })()")
        check('地図：凡例の「車など」は点線（実線でない）:', 'repeating-linear-gradient' in dash)
        check('地図：太さの凡例と乗った区間:', '太さ＝回数' in await pg.inner_text('#flights') and await pg.locator('#flights [data-fbrt]').count() > 0)
        n1 = await pg.evaluate("Math.max(...[...document.querySelectorAll('#map path[data-n]')].map(p => +p.dataset.n))")
        w = await pg.evaluate("(() => { const ps = [...document.querySelectorAll('#map path[data-n]')]; const a = ps.reduce((m, p) => +p.dataset.n < +m.dataset.n ? p : m, ps[0]), b = ps.reduce((m, p) => +p.dataset.n > +m.dataset.n ? p : m, ps[0]); return [+a.dataset.n, +b.dataset.n, +a.getAttribute('stroke-width'), +b.getAttribute('stroke-width')]; })()")
        print('線の太さ', w)
        check('地図：何度も乗った区間ほど太い:', w[0] == w[1] or w[3] > w[2])
        await pg.locator('#flights .fbrts [data-fbrt]').first.click(); await pg.wait_for_timeout(400)
        check('区間を押すと、その区間の回数・距離・便:', await pg.locator('#flights .fbsel').count() == 1 and '回数' in await pg.inner_text('#flights .fbsel'))
        # 1便のくわしい所と画像で共有
        await pg.click('[data-vw="log:diary"]'); await pg.wait_for_timeout(300)
        key = await pg.evaluate("""(() => { const f = [...S.flights].reverse().find(x => !isCar(x)); f.no = 'JL924'; f.airline = 'JL'; f.seat = '25K'; FACTS.set(factKey(f), { reg:'JA751A', type:'B77W' }); save(); render(); return fid(f); })()""")
        await pg.evaluate("goTab('log')"); await pg.wait_for_timeout(300)
        await pg.click(f'#flights [data-fbv="{key}"]'); await pg.wait_for_timeout(500)
        vt = await pg.inner_text('#dFbView')
        check('1便：コード・出発・到着・空の上・距離・区間マイル:', await pg.evaluate("$('dFbView').open") and '出発' in vt and '到着' in vt and '空の上' in vt and 'マイル' in vt)
        check('1便：機体と座席:', 'JA751A' in vt and '25K' in vt)
        check('1便：この区間の便:', 'この区間の便' in vt)
        await pg.click('#dFbView [data-fvshare]'); await pg.wait_for_timeout(700)
        check('画像で共有：登録記号ははじめ ON:', await pg.get_attribute('[data-fbsw="reg"]', 'aria-checked') == 'true')
        check('画像で共有：座席ははじめ OFF:', await pg.get_attribute('[data-fbsw="seat"]', 'aria-checked') == 'false')
        st = await pg.inner_text('#dFbShare')
        check('画像で共有：ロゴは入らない・ON にすると 25K席:', '会社のロゴは入りません' in st and '25K席' in st)
        await pg.click('[data-fbsw="seat"]'); await pg.wait_for_timeout(500)
        check('座席を押すと ON:', await pg.get_attribute('[data-fbsw="seat"]', 'aria-checked') == 'true')
        await pg.click('[data-fbsw="reg"]'); await pg.wait_for_timeout(500)
        check('登録記号を押すと OFF:', await pg.get_attribute('[data-fbsw="reg"]', 'aria-checked') == 'false')
        # 券の下の1行目：長い機種名でも、字を小さくせず座席 → 登録記号の順に外す（「非公式アプリ」は別の行で折れない）
        lines = await pg.evaluate("""(async () => { const s = { ...FB_SHARE, type:'B777-300ER（とても長い機種名の見本）', reg:'JA751A', seat:'103K', showReg:true, showSeat:true };
          const cv = await fbPassCard(s); return cv.width; })()""")
        check('長い機種名でも券が描ける:', lines == 1080)
        await pg.click('#fbShareGo'); await pg.wait_for_timeout(600)
        check('共有するで共有の窓へ:', await pg.evaluate("$('dShare').open") and not await pg.evaluate("$('dFbShare').open"))
        await pg.evaluate("$('dShare').close()")
        # ✎ で便の窓 → 車などにすると便から外れる
        await pg.click(f'#flights [data-fbv="{key}"]'); await pg.wait_for_timeout(400)
        before = await pg.evaluate("S.flights.filter(f => !isCar(f)).length")
        await pg.click('#fvEdit'); await pg.wait_for_timeout(300)
        check('✎ で便の窓（車などのスイッチ）:', await pg.evaluate("$('dFlight').open") and await pg.locator('#fCar').count() == 1 and not await pg.is_checked('#fCar'))
        st0 = await pg.evaluate("(() => { const y = new Date(S.flights.find(f => fid(f) === %r).dep).getFullYear(); return [statusRows().length, JSON.stringify(statusSummary(y))]; })()" % key)
        await pg.check('#fCar'); await pg.wait_for_timeout(300)
        st1 = await pg.evaluate("(() => { const y = new Date(S.flights.find(f => fid(f) === %r).dep).getFullYear(); return [statusRows().length, JSON.stringify(statusSummary(y)), statusRows().some(r => isCar(r.ref))]; })()" % key)
        print('成績の目安', st0, st1)
        check('車などにした便は成績の目安・修行に数えない（statusRows から外れ、目安の数が変わる）:', st1[0] == st0[0] - 1 and st1[1] != st0[1] and not st1[2])
        check('車などにすると便の数が1つ減る:', await pg.evaluate("S.flights.filter(f => !isCar(f)).length") == before - 1 and await pg.locator(f'#flights .fbrow[data-fbv="{key}"][data-g="CAR"]').count() == 1)
        await pg.uncheck('#fCar'); await pg.wait_for_timeout(300); await pg.evaluate("$('dFlight').close()")
        check('戻すと便に戻る:', await pg.evaluate("S.flights.filter(f => !isCar(f)).length") == before)
        # ＋ で記録帳、もどる
        await pg.click('#flAdd'); await pg.wait_for_timeout(300)
        check('＋ で記録帳の入力:', not await pg.evaluate("$('lsBook').hidden") and await pg.evaluate("$('lsList').hidden"))
        await pg.click('#fbBack'); await pg.wait_for_timeout(200)
        check('もどるで日誌:', await pg.evaluate("$('lsBook').hidden") and not await pg.evaluate("$('lsList').hidden"))
        check('横のはみ出しなし:', await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        await c.close()
        # 古い見方の id は読むときに直す（案内板→日誌、高度→年のまとめ）。表示の編集の古い id も
        for oldv, newv in [('board', 'diary'), ('cal', 'diary'), ('sg', 'diary'), ('alt', 'year'), ('month', 'year'), ('map', 'map')]:
            c2, pg2, e2 = await start(b, extra=f"localStorage.setItem('soramemo.view.log','{oldv}');")
            check(f'古い見方 {oldv} → {newv}:', await pg2.evaluate("VIEW.log") == newv)
            errs += e2; await c2.close()
        c3, pg3, e3 = await start(b, extra="localStorage.setItem('soramemo.layout', JSON.stringify({off:{log:['sg','board','map','cal','month','alt','text','route']}}));")
        check('古い off（8つ隠す）でも新しい見方は出る（地図だけ隠したまま）:', await pg3.evaluate("viewsShown('log').map(x=>x[0]).join(',')") == 'diary,year')
        errs += e3; await c3.close()
        await b.close()
        print('errors', errs + fails)
asyncio.run(main())
