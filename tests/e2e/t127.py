import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 近くの空港（11/11・11/12 の決定。画面案 design/near-airfields 5版・review-5）
#   民間空港と飛行場・滑空場・ヘリポートを分けずに近い順。基地は出さない。判定（印）の決まりは今のまま
#   パタパタは先頭が民間空港でコードがあるときだけ。「ほか」は 20km。20km 以内に民間空港がなければ、いちばん近い民間空港を1つ足す
#   「飛行場・滑空場・ヘリポートも出す」（はじめ ON）：ホームに出すもの・表示の編集。かたまりの数（4/4）には入れない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(WORK, 'near_shots'); os.makedirs(SHOTS, exist_ok=True)
KAZO = (36.1311, 139.6017); RYU = (35.9063, 140.2422); TOKYO = (35.6812, 139.7671); YAO = (34.6267, 135.6020); KAWAGOE = (35.9251, 139.4858); ITAMI = (34.7855, 135.4382); IRUMA = (35.8580, 139.4100)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, geo, h=844, shots=False, init=''):
    c = await b.new_context(viewport={'width':390,'height':h}, device_scale_factor=2 if shots else 1, geolocation={'latitude':geo[0],'longitude':geo[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1500)
    try: await pg.wait_for_function('HOME_NEAR && HOME_NEAR.others', timeout=8000)
    except Exception: pass
    await pg.wait_for_timeout(500)
    return c, pg, errs
async def info(pg):
    return await pg.evaluate("""(() => ({ name:$('nearName').textContent, label:$('nearLabel').textContent, flap:$('nearCode').textContent, tag:$('nearTag').hidden ? '' : $('nearTag').textContent,
      more:$('nearMore').hidden ? '' : $('nearMore').textContent.trim(), dist:$('nearDist').textContent, state:$('bpass').dataset.state,
      others:HOME_NEAR.others.map(o => o.a.name), civ:HOME_NEAR.civ ? HOME_NEAR.civ.a.name : null }))()""")
async def full(pg):
    await pg.click('#nearMore'); await pg.wait_for_timeout(700)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 0. 近い順の中身（地図を開かずに nearest だけ）
        c, pg, errs = await page(b, KAZO)
        r = await pg.evaluate("(() => { const n = nearest({lat:35.8900, lon:139.4100}); return [n.a.name, n.within, n.others.map(o => o.a.kind || 'civ')]; })()")
        check('入間基地から約3.5km：基地は並びに出さない（先頭も一覧も）', 'mil' not in r[2] and '基地' not in r[0], r)
        r = await pg.evaluate("(() => { const n = nearest({lat:35.8580, lon:139.4100}); return [n.a.name, n.within, n.others.map(o => o.a.kind || 'civ')]; })()")
        check('入間基地の判定範囲の中：印の決まりは今のまま（基地）・一覧に基地は出さない', r[0] == '入間基地' and r[1] and 'mil' not in r[2], r)
        r = await pg.evaluate("(() => { const n = nearest({lat:35.5494, lon:139.7798}); return [n.a.name, n.within, n.civ]; })()")
        check('羽田の中：判定は今のまま（羽田・範囲の中）・民間空港を足さない', r[0] == '東京国際空港（羽田）' and r[1] and r[2] is None, r)
        r = await pg.evaluate("(() => { const n = nearest({lat:%f, lon:%f}); return [n.a.name, n.others.map(o => o.a.name), n.others.every(o => o.km <= 20), n.civ && n.civ.a.name]; })()" % KAZO)
        check('加須駅：先頭は加須滑空場（範囲の外でも近い順の先頭）', r[0] == '加須滑空場', r)
        check('加須駅：ほかは 20km 以内だけ・6つ', r[2] and len(r[1]) == 6, r[1])
        check('加須駅：20km 以内に民間空港がないので調布空港を1つ足す（数に入れない）', r[3] == '調布空港', r[3])
        r = await pg.evaluate("(() => { const n = nearest({lat:%f, lon:%f}); return [n.a.name, n.a.kind, n.others.map(o => o.a.name)]; })()" % TOKYO)
        check('東京駅：東京ヘリポートが先頭・羽田は「ほか」', r[0] == '東京ヘリポート' and r[1] == 'heli' and any('羽田' in x for x in r[2]), r)
        r = await pg.evaluate("(() => { const n = nearestBase({lat:%f, lon:%f}); return n.a.name; })()" % KAZO)
        check('判定の決まり（nearestBase）は今のまま：加須駅は滑空場ではなく民間空港', '滑空場' not in r, r)
        r = await pg.evaluate("XA.filter(a => a.kind === 'heli').length")
        check('ヘリポートが12か所', r == 12, r)
        check('並び：エラーなし', not errs, errs); await c.close()

        # 1. 加須駅（範囲の外・先頭が滑空場）844
        c, pg, errs = await page(b, KAZO, shots=True)
        i = await info(pg)
        check('加須：見出し「いちばん近い」・札「滑空場」・パタパタなし', i['label'] == 'いちばん近い' and i['tag'] == '滑空場' and not i['flap'], i)
        check('加須：ピル「ほか6つ」', i['more'] == 'ほか6つ', i['more'])
        check('加須：判定範囲の外・ここから 6.xkm', '判定範囲の外' in i['dist'] and '6.' in i['dist'], i['dist'])
        check('加須：最初の位置では一覧を出さない', not await pg.is_visible('#nearList'))
        await pg.screenshot(path=os.path.join(SHOTS, '01-kazo-844.png'))
        top0 = await pg.evaluate('$("homeSheet").getBoundingClientRect().top')
        await full(pg)
        check('加須：ピルを押すと引き上げた位置で一覧が出る', await pg.evaluate('$("homeSheet").dataset.snap') == 'full' and await pg.is_visible('#nearList'))
        check('加須：引き上げた位置のピルは「閉じる」', (await pg.inner_text('#nearMore')).strip() == '閉じる')
        h = await pg.inner_text('#nearList .nlh')
        check('加須：見出し「ほかに 20km 以内 6つ」（review-5 の3）', 'ほかに 20km 以内 6つ' in h, h)
        rows = await pg.evaluate('[...document.querySelectorAll("#nearList .nrow2")].map(x => x.innerText.replace(/\\s+/g, " "))')
        check('加須：844 は3行＋民間空港の行（2段目に「民間空港でいちばん近い」）', len(rows) == 4 and '民間空港でいちばん近い' in rows[-1] and '調布空港' in rows[-1], rows)
        await pg.screenshot(path=os.path.join(SHOTS, '02-kazo-full-844.png'))
        await pg.click('[data-near-all]'); await pg.wait_for_timeout(400)
        n = await pg.evaluate('document.querySelectorAll("#dNear .nrow2").length')
        check('加須：すべてで6つ＋民間空港1つ', n == 7, n)
        check('加須：すべての題の下「加須滑空場のほか・6つ・近い順」', '加須滑空場のほか ・ 6つ ・ 近い順' in await pg.inner_text('#dNear h3'))
        await pg.screenshot(path=os.path.join(SHOTS, '03-kazo-all-844.png'))
        await pg.click('#dNear .nrow2'); await pg.wait_for_timeout(500)
        check('加須：行を押すとその飛行場のページ', await pg.evaluate('$("dAirport").open && !$("dNear").open') and '大利根滑空場' in await pg.inner_text('#dAirportBody'))
        await pg.evaluate('$("dAirport").close()')
        await pg.click('#nearMore'); await pg.wait_for_timeout(700)
        t1 = await pg.evaluate('$("homeSheet").getBoundingClientRect().top')
        check(f'加須：閉じると最初の位置に戻る（{round(top0)} → {round(t1)}）', abs(t1 - top0) < 2 and (await pg.inner_text('#nearMore')).strip() == 'ほか6つ')
        tiny = await pg.evaluate('[...document.querySelectorAll("#nearMore,#nearList button")].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44).map(b => b.textContent)')
        check('加須：押せる所は44px 以上', not tiny, tiny)
        check('加須：エラーなし', not errs, errs); await c.close()

        # 2. 667・740 の引き上げた位置：一覧は1行＋民間空港の行・一覧の下とタブ帯のあいだ 12px 以上（review-5 の2）
        for hh in (667, 740):
            c, pg, errs = await page(b, KAZO, h=hh, shots=True)
            await pg.screenshot(path=os.path.join(SHOTS, f'01-kazo-{hh}.png'))
            await full(pg)
            n = await pg.evaluate('document.querySelectorAll("#nearList .nrow2").length')
            gap = await pg.evaluate('document.querySelector("nav.tabs .in").getBoundingClientRect().top - $("nearList").getBoundingClientRect().bottom')
            check(f'{hh}：引き上げた位置の一覧は1行＋民間空港の行', n == 2, n)
            check(f'{hh}：一覧の下とタブ帯のあいだ 12px 以上（{round(gap)}px）', gap >= 12, gap)
            await pg.screenshot(path=os.path.join(SHOTS, f'02-kazo-full-{hh}.png'))
            check(f'{hh}：エラーなし', not errs, errs); await c.close()

        # 3. 竜ヶ崎飛行場の中：半券はその飛行場・琥珀・「飛行場・滑空場の図鑑に入ります」
        c, pg, errs = await page(b, RYU, shots=True)
        i = await info(pg)
        check('竜ヶ崎：判定範囲の中で札「飛行場」', i['state'] == 'in' and i['tag'] == '飛行場' and '判定範囲の中' in i['dist'], i)
        check('竜ヶ崎：「飛行場・滑空場の図鑑に入ります」（review-5 の6）', '飛行場・滑空場の図鑑に入ります' in i['dist'], i['dist'])
        await pg.screenshot(path=os.path.join(SHOTS, '04-ryugasaki-844.png'))
        check('竜ヶ崎：エラーなし', not errs, errs); await c.close()

        # 4. 東京駅：東京ヘリポートが先頭・札「ヘリポート」・パタパタなし
        c, pg, errs = await page(b, TOKYO, shots=True)
        i = await info(pg)
        check('東京駅：先頭は東京ヘリポート・札「ヘリポート」・パタパタなし', i['name'] == '東京ヘリポート' and i['tag'] == 'ヘリポート' and not i['flap'], i)
        await pg.screenshot(path=os.path.join(SHOTS, '05-tokyo-heli-844.png'))
        # 「飛行場・滑空場・ヘリポートも出す」を OFF：羽田が先頭・パタパタ HND
        await pg.click('[data-he-open]'); await pg.wait_for_timeout(500)
        t = await pg.inner_text('#dHomeEdBody')
        check('ホームに出すもの：半券の下に「飛行場・滑空場・ヘリポートも出す」（はじめ ON）', '飛行場・滑空場・ヘリポートも出す' in t and await pg.evaluate('document.querySelector("#dHomeEdBody [data-nearx]").getAttribute("aria-checked")') == 'true')
        await pg.screenshot(path=os.path.join(SHOTS, '06-home-edit-nearx-844.png'))
        await pg.click('#dHomeEdBody [data-nearx]'); await pg.wait_for_timeout(500)
        check('OFF にすると保存（LAYOUT.nearx = 0）', await pg.evaluate('LAYOUT && LAYOUT.nearx === 0'))
        await pg.evaluate('$("dHomeEd").close()'); await pg.wait_for_timeout(400)
        i = await info(pg)
        check('OFF：先頭は羽田・パタパタ HND・札なし', '羽田' in i['name'] and i['flap'] == 'HND' and not i['tag'], i)
        check('OFF：並びは民間空港だけ', await pg.evaluate('HOME_NEAR.others.every(o => !o.a.kind)'))
        await pg.screenshot(path=os.path.join(SHOTS, '07-tokyo-civonly-844.png'))
        # 表示の編集のホームのカード：4/4 のまま（数に入れない）・行がある
        await pg.evaluate('openLayout("home", "settings")'); await pg.wait_for_timeout(500)
        hc = await pg.inner_text('[data-lo-sec="home"]')
        check('表示の編集：ホームのカードに行がある・数は○/4 のまま（数に入れない）', '飛行場・滑空場・ヘリポートも出す' in hc and '/4' in hc.replace('\n', '') and '/5' not in hc.replace('\n', ''), hc[:200])
        await pg.screenshot(path=os.path.join(SHOTS, '08-layout-nearx-844.png'))
        await pg.click('#dLayout [data-nearx]'); await pg.wait_for_timeout(400)
        check('表示の編集で ON に戻すと LAYOUT.nearx がなくなる', await pg.evaluate('!(LAYOUT && "nearx" in LAYOUT)'))
        check('東京駅：エラーなし', not errs, errs); await c.close()

        # 5. 八尾空港の近く：先頭が飛行場で、民間空港を1つ足す →「近くの民間空港」
        c, pg, errs = await page(b, YAO, shots=True)
        i = await info(pg)
        check('八尾の近く：先頭は八尾空港（飛行場）', i['name'] == '八尾空港' and i['tag'] == '飛行場', i)
        check('八尾の近く：20km 以内に伊丹・関西がないときのピル', i['more'] in ('近くの民間空港', 'ほか1つ', 'ほか2つ') , i)
        await pg.screenshot(path=os.path.join(SHOTS, '09-yao-844.png'))
        check('八尾：エラーなし', not errs, errs); await c.close()

        # 6. 伊丹の近く：民間空港が先頭ならパタパタ
        c, pg, errs = await page(b, ITAMI)
        i = await info(pg)
        check('伊丹の近く：パタパタ ITM・札なし', i['flap'] == 'ITM' and not i['tag'], i)
        check('伊丹：エラーなし', not errs, errs); await c.close()
        # 7. 図鑑の飛行場・滑空場（design/zukan-airfields 3版）：入口・別の図鑑・重なる行った丸は数の入った1つ
        for hh in (844, 667):
            c, pg, errs = await page(b, KAZO, h=hh, shots=True)
            await pg.evaluate("""(() => { const t = Date.now() - 864e5 * 30; S.checkins.push({a:2015, t}, {a:3002, t:t + 1e6}, {a:3004, t:t + 2e6}, {a:3004, t:t + 3e6}, {a:IATA.HND.id, t:t + 4e6}); for(const k in DIRTY) DIRTY[k] = true; goTab("book"); })()""")
            await pg.wait_for_timeout(600)
            e = await pg.inner_text('#zkBody .zx-entry')
            check(f'{hh} 図鑑：黒いカードのすぐ下に入口（もう1つの図鑑・3 / 75）', await pg.evaluate('!!document.querySelector("#zkBody .zk-hero + .zx-entry")') and '飛行場・滑空場の図鑑' in e and '3' in e and '/ 75' in e, e.replace('\n', ' '))
            if hh == 844:
                m = await pg.evaluate('[document.querySelectorAll("#zkBody .zxmap .mv").length, [...document.querySelectorAll("#zkBody .zxmap .mn")].map(x => x.textContent)]')
                check('844 図鑑：関東の3つは数の入った1つの丸（review-3 の1）', m[0] == 1 and m[1] == ['3'], m)
                check('844 図鑑：入口の内訳に飛行場・滑空場・ヘリポート', all(x in e for x in ['飛行場 2', '滑空場 1', 'ヘリポート 0']), e)
            else:
                check('667 図鑑：入口は1行の形（地図と内訳を外す）', not await pg.is_visible('#zkBody .zxmap') and not await pg.is_visible('#zkBody .zx-kd'))
            await pg.screenshot(path=os.path.join(SHOTS, f'10-zukan-entry-{hh}.png'))
            check(f'{hh} 図鑑：86 の数は変わらない（1 / 86）', (await pg.inner_text('#bookProg')).strip() == '1')
            await pg.click('#zkBody .zx-entry'); await pg.wait_for_timeout(600)
            check(f'{hh} 飛行場の図鑑：開く・地方の扉と枠・ツメ', await pg.evaluate('!$("bookAir").hidden && document.querySelectorAll("#bookAir .zk-rg").length == 8 && document.querySelectorAll("#bookAir .zk-ap").length == 75') and await pg.is_visible('#zkxTsume'))
            check(f'{hh} 飛行場の図鑑：四国のツメは押せない', await pg.evaluate('document.querySelector("#zkxTsume [data-zkj=\'四国\']").disabled'))
            await pg.screenshot(path=os.path.join(SHOTS, f'11-airbook-{hh}.png'))
            await pg.click('#zkxTsume [data-zkj="関東"]'); await pg.wait_for_timeout(900)
            d = await pg.evaluate('(() => { const r = document.querySelector("#zkxrg-関東 .zk-door").getBoundingClientRect(); return [Math.round(r.top), document.querySelector("#zkxTsume .on") && document.querySelector("#zkxTsume .on").dataset.zkj]; })()')
            check(f'{hh} 飛行場の図鑑：ツメで関東へ飛び、扉が上に止まる', d[1] == '関東' and d[0] < 80, d)
            got = await pg.evaluate('[...document.querySelectorAll("#zkxrg-関東 .zk-ap:not(.no)")].map(x => x.getAttribute("aria-label"))')
            check(f'{hh} 飛行場の図鑑：行った3つ（加須・ホンダ・竜ヶ崎 2回）', len(got) == 3 and any('竜ヶ崎飛行場' in x and '2回' in x for x in got), got)
            await pg.screenshot(path=os.path.join(SHOTS, f'12-airbook-kanto-{hh}.png'))
            ov = await pg.evaluate('[...document.querySelectorAll("#bookAir .zx-nm, #bookAir .zx-k")].filter(x => { if(x.classList.contains("zx-k")) return x.getBoundingClientRect().height > 26 || x.scrollWidth > x.clientWidth + 1; const r = document.createRange(); r.selectNodeContents(x); return r.getBoundingClientRect().height > x.getBoundingClientRect().height + 8; }).map(x => x.textContent)')
            check(f'{hh} 飛行場の図鑑：名前が枠で切れない', not ov, ov)
            tiny = await pg.evaluate('[...document.querySelectorAll("#bookAir button, #zkBody .zx-entry")].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44).map(b => b.textContent.trim().slice(0, 12))')
            check(f'{hh} 飛行場の図鑑：押せる所は44px 以上', not tiny, tiny)
            await pg.evaluate('document.documentElement.dataset.night = "on"'); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(SHOTS, f'13-airbook-kanto-night-{hh}.png'))
            await pg.evaluate('delete document.documentElement.dataset.night')
            check(f'{hh} 図鑑：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
