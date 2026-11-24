import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 空港のピン止め（決定事項【11/19】・画面案 design/pin 4版）
#   近くの空港のカード（K1）・ピン止めした直後のシート（K4）・「ピン止め中 ›」で知らせ（K1s）・外す＋元に戻す（K4u）・2回目からの帯（K4t）
#   ホームの「ピン止めした空港」（K1h・はじめ ON）・空港のページ（K2）・運用タブの1行（K7）・空港を選ぶシート（K8）・知らせの画面（K5・K6）
#   今の申し込みはそのままピン止めに移す（K9・上限12を超えてもそのまま）。知らせの送り手は今の push-subscribe（ピン止めから作る）
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(WORK, 'shots-pin'); os.makedirs(SHOTS, exist_ok=True)
HND = (35.5494, 139.7798); TOKYO = (35.6812, 139.7671)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, geo, h=844, shots=False, init=''):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2 if shots else 1, geolocation={'latitude':geo[0],'longitude':geo[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1'); localStorage.setItem('soramemo.persona','all');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1500)
    try: await pg.wait_for_function('HOME_NEAR && HOME_NEAR.others', timeout=8000)
    except Exception: pass
    await pg.wait_for_timeout(500)
    return c, pg, errs
PINS = "JSON.parse(localStorage.getItem('soramemo.pins') || 'null')"
# 届く端末のふりをして、push-subscribe に送る中身を控える
FAKE_OK = "pinDeliver = () => 'ok'; window.__sent = []; syncPush = async (airports, flights, sp, spot, ga) => { window.__sent.push({ airports, sp, spot: spot && spot.iata, ga: ga && ga.airports }); return true; };"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. 羽田の中：はじめてのピン止め（届かない端末 → K4 のシート）
        for H in (844, 667):
            c, pg, errs = await page(b, HND, h=H, shots=True)
            tag = f'[{H}]'
            t = await pg.inner_text('#nearPin')
            check(tag + ' K1：いちばん近い（羽田）の右に「ピン止め」（していない形）', 'ピン止め' in t and 'ピン止め中' not in t, t)
            r = await pg.evaluate("(() => { const a = $('nearPin').getBoundingClientRect(), b = $('nearLabel').getBoundingClientRect(), s = $('checkin').getBoundingClientRect(); return { same: Math.abs((a.top + a.height / 2) - (b.top + b.height / 2)) < 8, inCard: a.right <= s.left + 1, h: Math.round(a.height) }; })()")
            check(tag + ' K1：札は見出しの行・半券に重ならない', r['same'] and r['inCard'], r)
            check(tag + ' K1h：ピン止めが0のときは「ピン止めした空港」を出さない', await pg.evaluate("$('pinHome').hidden"))
            if H == 844: await pg.screenshot(path=os.path.join(SHOTS, '01-K1-not-844.png'))
            await pg.click('#nearPin .pinpill'); await pg.wait_for_timeout(500)
            check(tag + ' K4：はじめては「羽田をピン止めしました」のシート', await pg.is_visible('#dPin') and '羽田をピン止めしました' in await pg.inner_text('#dPin'))
            sw = await pg.evaluate("[...document.querySelectorAll('#dPin [data-pin-kind]')].map(x => [x.dataset.pinKind, x.getAttribute('aria-checked'), x.disabled])")
            check(tag + ' K4：はじめは特別塗装機だけ ON・4つのスイッチ', sw[0] == ['sp', 'true', False] and [x[1] for x in sw[1:]] == ['false', 'false', 'false'] and len(sw) == 4, sw)
            t = await pg.inner_text('#dPin')
            check(tag + ' K4：羽田は門限なしの書き方・推定の断り・取り消す', '門限はありません' in t and '推定です。保証しません。' in t and '取り消す' in t, '')
            ov = await pg.evaluate("(() => { const d = $('dPin'), r = d.getBoundingClientRect(); return { fit: r.bottom <= innerHeight + 1, over: [...d.querySelectorAll('*')].filter(e => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible' && !['INPUT'].includes(e.tagName)).length, small: [...d.querySelectorAll('button')].filter(e => { const q = e.getBoundingClientRect(); return q.width > 0 && q.height < 36; }).map(e => e.textContent.trim()) }; })()")
            check(tag + ' K4：シートの中ではみ出し・小さすぎる押す所なし', ov['over'] == 0 and not ov['small'], ov)
            await pg.screenshot(path=os.path.join(SHOTS, f'02-K4-{H}.png'))
            await pg.click('#dPin .pindone'); await pg.wait_for_timeout(300)
            v = await pg.evaluate(PINS)
            check(tag + ' 保存：羽田・特別塗装機 ON', v == [{'k':'HND','sp':True,'dl':False,'ga':False}], v)
            t = await pg.inner_text('#nearPin')
            check(tag + ' K1：ピン止めしたら「ピン止め中」', 'ピン止め中' in t, t)
            check(tag + ' K1h：「ピン止めした空港 1」がホームに出る', await pg.evaluate("!$('pinHome').hidden") and 'ピン止めした空港 1' in await pg.evaluate("$('pinHome').textContent"))
            if H == 844: await pg.screenshot(path=os.path.join(SHOTS, '03-K1-on-844.png'))
            # 「ピン止め中 ›」→ 知らせ（K1s）
            await pg.click('#nearPin .pinpill'); await pg.wait_for_timeout(400)
            t = await pg.inner_text('#dPin')
            check(tag + ' K1s：「ピン止め中 ›」で羽田の知らせ・外すボタン', '羽田の知らせ' in t and '羽田のピン止めを外す' in t, '')
            await pg.click('#dPin [data-pin-kind="dl"]'); await pg.wait_for_timeout(300)
            v = await pg.evaluate(PINS)
            check(tag + ' K1s：遅れ・欠航・ダイバートを ON にすると保存', v and v[0]['dl'] is True, v)
            check(tag + ' K1s：届かない端末では ON の行に「届きません」', '届きません' in await pg.inner_text('#dPin'))
            await pg.screenshot(path=os.path.join(SHOTS, f'04-K1s-{H}.png'))
            # 外す → 元に戻す（K4u）
            await pg.click('#dPin [data-pin-remove]'); await pg.wait_for_timeout(400)
            check(tag + ' K4u：外すと帯「元に戻す」', await pg.is_visible('.pinband') and '元に戻す' in await pg.inner_text('.pinband'))
            check(tag + ' 外したらピン止めは空', await pg.evaluate(PINS) == [])
            if H == 844: await pg.screenshot(path=os.path.join(SHOTS, '05-K4u-844.png'))
            await pg.click('.pinband [data-pin-undo]'); await pg.wait_for_timeout(300)
            v = await pg.evaluate(PINS)
            check(tag + ' 元に戻すと前の知らせのまま戻る', v and v[0]['k'] == 'HND' and v[0]['dl'] is True, v)
            check(tag + ' エラーなし', not errs, errs); await c.close()

        # 2. 東京駅：近くの一覧の丸（K1o）と、2回目からの帯（K4t）。届く端末のふり：送る中身をピン止めから作る
        c, pg, errs = await page(b, TOKYO, shots=True, init="localStorage.setItem('soramemo.pins', JSON.stringify([{k:'HND',sp:true,dl:true,ga:false}])); localStorage.setItem('soramemo.pins.first','1');")
        await pg.evaluate(FAKE_OK)
        await pg.click('#nearMore'); await pg.wait_for_timeout(700)
        r = await pg.evaluate("[...document.querySelectorAll('#nearList .nrw')].map(x => [x.querySelector('.nrow2 b').textContent, x.querySelector('.nrpin').getAttribute('aria-pressed')])")
        check('K1o：一覧の各行の右にピンの丸（羽田はしている）', r and any('羽田' in x[0] and x[1] == 'true' for x in r) and all(len(x) == 2 for x in r), r)
        await pg.screenshot(path=os.path.join(SHOTS, '06-K1o-844.png'))
        # 先頭の東京ヘリポート（3レターなし）を黒いカードの札からピン止め（2回目からは帯）
        await pg.click('#nearPin .pinpill'); await pg.wait_for_timeout(500)
        check('K4t：2回目からはシートでなく帯「○○をピン止めしました｜知らせの設定」', not await pg.is_visible('#dPin') and await pg.is_visible('.pinband') and '知らせの設定' in await pg.inner_text('.pinband'), await pg.inner_text('.pinband'))
        await pg.screenshot(path=os.path.join(SHOTS, '07-K4t-844.png'))
        v = await pg.evaluate(PINS); k = v[-1]['k']
        check('ヘリポートの鍵は「#番号」・特別塗装機は OFF（知らせを出せない）', k.startswith('#') and v[-1]['sp'] is False, v)
        sent = await pg.evaluate("window.__sent")
        check('送る中身：遅れ・特別塗装機は羽田だけ（3レターのない所は送らない）', sent and sent[-1]['airports'] == ['HND'] and sent[-1]['sp'] == ['HND'], sent)
        await pg.click('[data-pin-open="%s"]' % k); await pg.wait_for_timeout(300)
        sw = await pg.evaluate("[...document.querySelectorAll('#dPin [data-pin-kind]')].map(x => x.disabled)")
        check('ヘリポートの知らせ：4つとも出せない（理由つき）', sw == [True]*4 and '3レターのない飛行場' in await pg.inner_text('#dPin'), sw)
        await pg.evaluate("$('dPin').close()")
        # 一覧の羽田の丸を押すと外れる（元に戻せる）
        await pg.click('#nearList [data-pin-remove="HND"]'); await pg.wait_for_timeout(400)
        check('K1o：している丸を押すと外れる・帯「元に戻す」', '元に戻す' in await pg.inner_text('.pinband') and all(x['k'] != 'HND' for x in await pg.evaluate(PINS)))
        await pg.click('.pinband [data-pin-undo]'); await pg.wait_for_timeout(300)
        # 空港のページ（K2）
        await pg.evaluate("openAirport(IATA.HND.id); $('dAirport').showModal()"); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#dAirportBody .pinap')
        check('K2：空港のページに「ピン止め中」と「羽田の知らせ」・ON の札', 'ピン止め中' in t and '羽田の知らせ' in t and '✓ 特別塗装機' in t and '✓ 遅れ・欠航・ダイバート' in t and 'ほか' in t, t)
        await pg.screenshot(path=os.path.join(SHOTS, '08-K2-844.png'))
        await pg.click('#dAirportBody .pinapc'); await pg.wait_for_timeout(300)
        check('K2：「羽田の知らせ」を押すとシート', await pg.is_visible('#dPin') and '羽田の知らせ' in await pg.inner_text('#dPin'))
        await pg.click('#dPin [data-pin-kind="ga"]'); await pg.wait_for_timeout(300)
        sent = await pg.evaluate("window.__sent")
        check('ゴーアラウンドを ON：ga.airports に羽田', sent[-1]['ga'] == ['HND'], sent[-1])
        await pg.evaluate("$('dPin').close(); $('dAirport').close()")
        # 運用タブ（K7）と空港を選ぶシート（K8）
        await pg.evaluate("localStorage.setItem('soramemo.view.ops','photo')"); await pg.evaluate("goTab('ops')"); await pg.wait_for_timeout(900)
        r = await pg.evaluate("pinLineHTML('HND')")
        check('K7：運用の1行「羽田はピン止め中・特別塗装機・遅れ・ゴーアラウンドが ON」', '羽田はピン止め中' in r and '特別塗装機・遅れ・ゴーアラウンドが ON' in r, r)
        r = await pg.evaluate("pinLineHTML('ITM')")
        check('K7：していない空港は「伊丹をピン止めして知らせを受ける」', '伊丹をピン止めして知らせを受ける' in r, r)
        await pg.click('#opsApBtn'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#opsAps')
        check('K8：空港を選ぶシートの先頭に「ピン止めした空港」', t.strip().startswith('ピン止めした空港') and '羽田' in t.split('\n')[1:4].__str__(), t[:60])
        await pg.screenshot(path=os.path.join(SHOTS, '09-K8-844.png'))
        await pg.evaluate("$('dOpsAp').close()")
        check('東京駅：エラーなし', not errs, errs); await c.close()

        # 3. 今の申し込みをピン止めに移す（K9）・上限12を超えてもそのまま（K9b）・知らせの画面（K5・K6）
        old = ['HND','NRT','ITM','KIX','CTS','FUK','OKA','NGO','SDJ','HIJ','KMJ','KOJ','ISG']
        init = "localStorage.setItem('soramemo.pushSpecial', %s); localStorage.setItem('soramemo.pushAirports', %s); localStorage.setItem('soramemo.pushGa', %s);" % (json.dumps(json.dumps(old)), json.dumps(json.dumps(['HND','ISG'])), json.dumps(json.dumps({'airports':['HND'],'kinds':['plane'],'quiet':False,'gap':3})))
        for H in (844, 667):
            c, pg, errs = await page(b, HND, h=H, shots=True, init=init)
            v = await pg.evaluate(PINS)
            check(f'[{H}] K9：前の申し込み13空港をそのままピン止めに（特別塗装機・遅れ・ゴーアラウンドもそのまま）', v and len(v) == 13 and v[0] == {'k':'HND','sp':True,'dl':True,'ga':True} and next(x for x in v if x['k'] == 'ISG')['dl'] is True, v[:2])
            await pg.evaluate("pinListOpen()"); await pg.wait_for_timeout(400)
            t = await pg.inner_text('#dPins')
            check(f'[{H}] K5：知らせの画面「ピン止めした空港 13 / 12」と続けている旨・乗る便', '13 / 12' in t and '13空港をそのまま続けています' in t and '乗る便' in t, '')
            check(f'[{H}] K5：羽田のカードに ON の札（特別塗装機・遅れ・ゴーアラウンド）', '✓ 特別塗装機' in t and '✓ ゴーアラウンド' in t, '')
            await pg.screenshot(path=os.path.join(SHOTS, f'10-K5-{H}.png'))
            await pg.fill('#pinQ', '大分'); await pg.wait_for_timeout(200)
            await pg.click('#pinQOut [data-pin-add]'); await pg.wait_for_timeout(300)
            check(f'[{H}] K9b：上限を超えているあいだは新しく足せない（帯で知らせる）', len(await pg.evaluate(PINS)) == 13 and '12空港まで' in await pg.inner_text('.pinband'))
            await pg.click('#dPins [data-pin-page="ISG"]'); await pg.wait_for_timeout(300)
            t = await pg.inner_text('#dPins')
            sw = await pg.evaluate("Object.fromEntries([...document.querySelectorAll('#dPins [data-pin-kind]')].map(x => [x.dataset.pinKind, x.disabled]))")
            check(f'[{H}] K6n：石垣は欠航などだけの書き方・ゴーアラウンドと撮影は出せない（薄く理由）', '石垣は欠航・ダイバート・引き返しだけ' in t and sw.get('ga') is True and sw.get('spot') is True and sw.get('sp') is False, sw)
            await pg.screenshot(path=os.path.join(SHOTS, f'11-K6n-{H}.png'))
            await pg.click('#dPins [data-pin-back]'); await pg.wait_for_timeout(200)
            check(f'[{H}] K6 → 戻ると一覧', '13 / 12' in await pg.inner_text('#dPins'))
            check(f'[{H}] エラーなし', not errs, errs); await c.close()

        # 4. マイページの入口とホームに出すもの（K1h：はじめ ON の行）
        c, pg, errs = await page(b, HND, init="localStorage.setItem('soramemo.pins', JSON.stringify([{k:'HND',sp:true,dl:false,ga:false}]));")
        await pg.click('#openSettings'); await pg.wait_for_timeout(400)
        check('マイページ：「知らせ」のタイル（1 / 12 空港）', '1/ 12 空港' in (await pg.inner_text('#mpTiles [data-pins-open]')).replace('\n',''))
        await pg.click('#mpTiles [data-pins-open]'); await pg.wait_for_timeout(300)
        check('マイページ → 知らせ（戻るは「マイページ」）', await pg.is_visible('#dPins') and 'マイページ' in await pg.inner_text('#dPins .mp-back'))
        await pg.evaluate("$('dPins').close(); $('dSettings').close()")
        r = await pg.evaluate("LO_BLOCKS.home.map(x => x[0])")
        check('ホームに出すもの：「ピン止めした空港」の行がある（はじめ ON）', 'pins' in r and not await pg.evaluate("loOff('home').has('pins')"), r)
        check('マイページ：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('fails', fails)
asyncio.run(main())
