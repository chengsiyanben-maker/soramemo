import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ホーム 3版（改善案 improve-1106 v3）の4つの状態：範囲の中・範囲の外・ログインしていない・デモ。と、引き上げた位置
#   出し分けの順番：ログインしていない ＞ 判定範囲の外 ＞ 範囲の中
#   地図は自分と空港が両方入る縮尺（入らないほど遠いときは端に矢印と距離）
#   字は13px以上（単位だけ12px）・色の濃さ4.5:1以上・押せる所は44px以上・最後の行がタブ帯にもぐらない
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio
from playwright.async_api import async_playwright
SHOTS = os.path.join(WORK, 'home_v3_shots'); os.makedirs(SHOTS, exist_ok=True)
HND = (35.5494, 139.7798); OUT = (35.62, 139.70); FAR = (33.0, 142.2)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
# 見えている字の大きさ・色の濃さ、押せる所の大きさを数える（ホームの上の段・搭乗券・数字の帯・案内）
MEASURE = r"""(() => {
  const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return [.2126 * f(m[0]) + .7152 * f(m[1]) + .0722 * f(m[2]), m[3] == null ? 1 : m[3]]; };
  const bgOf = el => { for(let e = el; e; e = e.parentElement){ const c = getComputedStyle(e).backgroundColor; if(c && !/rgba\(0, 0, 0, 0\)|transparent/.test(c) && lum(c)[1] > .5) return c; } return "rgb(255,255,255)"; };
  const ratio = (a, b) => { const x = lum(a)[0], y = lum(b)[0]; return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const roots = [".topzone", "#bpass", "#homeStrip", "#homeGate", "#homeMap .hm-ap", "#homeMap .hm-mel", "#homeEdge"].map(s => document.querySelector(s)).filter(Boolean);
  const small = [], low = [], tiny = [];
  for(const r of roots){
    const w = document.createTreeWalker(r, NodeFilter.SHOW_TEXT);
    for(let n; n = w.nextNode();){ const t = n.textContent.trim(); if(!t) continue; const el = n.parentElement, cs = getComputedStyle(el), bx = el.getBoundingClientRect();
      if(!bx.width || cs.visibility === "hidden" || el.closest("[hidden]") || el.closest(".bt")) continue;
      const fs = parseFloat(cs.fontSize); if(fs < 13 && !(fs >= 12 && /^[\/\d.,km%]+$/.test(t.replace(/\s/g, "")))) small.push(t + ":" + fs);
      if(!el.closest(".hm-ap,.hm-mel,.flap") && ratio(cs.color, bgOf(el)) < 4.5) low.push(t + ":" + ratio(cs.color, bgOf(el)).toFixed(2)); } }
  for(const b of document.querySelectorAll(".topzone button, #bpass button, #homeStrip button, #homeGate button, #homeMap .leaflet-control-zoom a")){
    const r = b.getBoundingClientRect(); if(!r.width || b.closest("[hidden]")) continue;
    if(r.height < 38 || (r.height < 44 && !b.closest("#modeSw"))) tiny.push((b.id || b.textContent.trim()) + ":" + Math.round(r.width) + "x" + Math.round(r.height)); }
  const nav = document.querySelector("nav.tabs .in").getBoundingClientRect().top, last = ["#homeGate", "#homeStrip", "#bpass"].map(s => document.querySelector(s)).find(e => e && !e.hidden);
  return { small, low, tiny, under: last.getBoundingClientRect().bottom > nav, sheetTop: document.getElementById("homeSheet").getBoundingClientRect().top };
})()"""
async def page(b, geo, login=False, init='', shots=False):
    c = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2 if shots else 1, geolocation={'latitude':geo[0],'longitude':geo[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(400)
    if login: await pg.evaluate('__fake.login()')
    await pg.wait_for_timeout(1500)
    return c, pg, errs
async def state(pg): return await pg.evaluate('$("bpass").dataset.state')
async def measure(pg, name):
    m = await pg.evaluate(MEASURE)
    check(name + '：13px 未満の字なし（単位の12pxは除く）', not m['small'], m['small'])
    check(name + '：色の濃さ4.5:1 未満の字なし', not m['low'], m['low'])
    check(name + '：押せる所は44px 以上（切り替えは38px のピルを44px の帯に）', not m['tiny'], m['tiny'])
    check(name + '：最後の行がタブ帯にもぐらない', not m['under'])
    return m
# 地図の上で、自分と空港の両方が見える所（上の段の下・シートの上）にあるか
RATIO_OF = """(sel => { const e = document.querySelector(sel), cs = getComputedStyle(e);
  const rgb = c => c.match(/[\\d.]+/g).map(Number), mix = (f, b) => { const a = f[3] == null ? 1 : f[3]; return [0, 1, 2].map(i => f[i] * a + b[i] * (1 - a)); };
  let bg = [255, 255, 255]; const chain = []; for(let x = e; x; x = x.parentElement){ const c = getComputedStyle(x).backgroundColor; if(!/rgba\\(0, 0, 0, 0\\)|transparent/.test(c)) chain.push(rgb(c)); }
  for(const c of chain.reverse()) bg = mix(c, bg);
  const L = v => { const f = x => { x /= 255; return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }; return .2126 * f(v[0]) + .7152 * f(v[1]) + .0722 * f(v[2]); };
  const a = L(mix(rgb(cs.color), bg)), b = L(bg); return (Math.max(a, b) + .05) / (Math.min(a, b) + .05); })"""
INVIEW = """(() => { const box = $('homeMap').getBoundingClientRect(), top = document.querySelector('.topzone').getBoundingClientRect().bottom, bot = $('homeSheet').getBoundingClientRect().top;
  const pt = ll => HOME_MAP.latLngToContainerPoint(ll), ok = p => p.x >= 0 && p.x <= box.width && p.y >= top && p.y <= bot;
  return { ap: ok(pt([HOME_NEAR.a.lat, HOME_NEAR.a.lon])), me: ok(pt([HOME_POS.lat, HOME_POS.lon])), edge: !!$('homeEdge') && !$('homeEdge').hidden }; })()"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. 範囲の中（ログイン中・羽田）
        c, pg, errs = await page(b, HND, login=True, shots=True)
        check('範囲の中：形', await state(pg) == 'in', await state(pg))
        check('範囲の中：空港名と「判定範囲の中」', '東京国際空港' in await pg.inner_text('#nearName') and '判定範囲の中' in await pg.inner_text('#nearDist'))
        check('範囲の中：半券は琥珀で「右へ引いて印をもらう」', '右へ引いて' in await pg.inner_text('#stubSub') and not await pg.evaluate('$("checkin").classList.contains("off")'))
        check('範囲の中：数字の帯が出て、ログインの案内は出ない', await pg.is_visible('#homeStrip') and not await pg.is_visible('#homeGate'))
        check('範囲の中：上の段は「マイページ」', (await pg.inner_text('#openSettings')).strip() == 'マイページ')
        check('範囲の中：上の段は1段（切り替えとマイページが同じ高さ）', abs(await pg.evaluate("$('modeSw').getBoundingClientRect().top - $('openSettings').getBoundingClientRect().top")) < 6)
        check('範囲の中：デモ中のピルは出ない', not await pg.is_visible('#demoPill'))
        m = await measure(pg, '範囲の中')
        check(f'範囲の中：最初の位置で地図は450px 以上（{round(m["sheetTop"])}px）', m['sheetTop'] >= 450)
        await pg.screenshot(path=os.path.join(SHOTS, '01-home-in.png'))
        # 押すだけ → 確かめ → やめる
        await pg.click('#checkin'); await pg.wait_for_timeout(300)
        check('範囲の中：押すと「印をもらいますか」', await pg.evaluate('$("dCkConfirm").open') and '印をもらいますか' in await pg.inner_text('#dCkConfirm'))
        await pg.click('#dCkConfirm button[value=no]'); await pg.wait_for_timeout(200)
        # 引き上げる
        await pg.click('#hsUp'); await pg.wait_for_timeout(600)
        check('引き上げ：シートは2段の上の位置', await pg.evaluate('$("homeSheet").dataset.snap') == 'full')
        check('引き上げ：数字は3枚のカード', await pg.evaluate("getComputedStyle($('homeStrip')).display") == 'grid')
        check('引き上げ：最近の印の見出しに図鑑へのピル', await pg.is_visible('#recentBook'))
        o = await pg.evaluate('''(() => { const st = $("homeStrip").getBoundingClientRect(), rc = document.querySelector('[data-lo="home:recent"]').getBoundingClientRect(); return { strip: st.bottom, recent: rc.top }; })()''')
        check('引き上げ：最近の印は3枚の数字のすぐ下', 0 <= o['recent'] - o['strip'] <= 40, o)
        rb = await pg.evaluate(RATIO_OF + "('#recentBook')")
        check(f'引き上げ：「図鑑 ›」の色の濃さ4.5:1 以上（{rb:.2f}）', rb >= 4.5)
        await pg.screenshot(path=os.path.join(SHOTS, '02-home-open.png'))
        await pg.click('#homeSheet .grab'); await pg.wait_for_timeout(500)
        check('つまみを押すと最初の位置へ（2段だけ）', await pg.evaluate('$("homeSheet").dataset.snap') == 'half')
        top0 = await pg.evaluate('$("homeSheet").getBoundingClientRect().top')
        # 引き上げ → 中をいちばん下まで送る → つまみで下げる：最初の位置に戻り、半券が見える（前は送った量だけ下へずれて消えた）
        await pg.click('#hsUp'); await pg.wait_for_timeout(500)
        await pg.evaluate('(b => { b.scrollTop = b.scrollHeight; })(document.querySelector("#homeSheet .sbody"))'); await pg.wait_for_timeout(200)
        await pg.click('#homeSheet .grab'); await pg.wait_for_timeout(600)
        t1 = await pg.evaluate('$("homeSheet").getBoundingClientRect().top'); ck = await pg.evaluate('$("checkin").getBoundingClientRect().bottom')
        check(f'送ってから下げても最初の位置（{round(top0)} → {round(t1)}）で、半券が見える', abs(t1 - top0) < 2 and ck < 844, ck)
        await pg.click('#hsUp'); await pg.wait_for_timeout(500)
        await pg.evaluate('(b => { b.scrollTop = 400; })(document.querySelector("#homeSheet .sbody"))')
        g = await pg.evaluate('document.querySelector("#homeSheet .grab").getBoundingClientRect().top')
        await pg.mouse.move(195, g + 10); await pg.mouse.down(); await pg.mouse.move(195, g + 300, steps=8); await pg.mouse.up(); await pg.wait_for_timeout(600)
        t2 = await pg.evaluate('$("homeSheet").getBoundingClientRect().top')
        check(f'送ってからつまみを引き下げても最初の位置（{round(t2)}）', abs(t2 - top0) < 2)
        await pg.click('nav.tabs button[data-v="book"]'); await pg.wait_for_timeout(400)
        await pg.click('nav.tabs button[data-v="home"]'); await pg.wait_for_timeout(600)
        t3 = await pg.evaluate('$("homeSheet").getBoundingClientRect().top')
        check(f'図鑑へ行って戻っても最初の位置（{round(t3)}）', abs(t3 - top0) < 2)
        check('タブ帯の後ろに上の線がない', await pg.evaluate('getComputedStyle(document.querySelector("nav.tabs")).borderTopStyle') == 'none')
        check('範囲の中：エラーなし', not errs, errs); await c.close()

        # 2. 範囲の外（ログイン中・羽田から約10km）
        c, pg, errs = await page(b, OUT, login=True, shots=True)
        check('範囲の外：形', await state(pg) == 'out', await state(pg))
        d = await pg.inner_text('#nearDist')
        check('範囲の外：「判定範囲の外・ここから ○km」', '判定範囲の外' in d and 'ここから' in d and 'km' in d, d)
        check('範囲の外：半券は灰色で「範囲に入ると切れる」', '範囲に入る' in await pg.inner_text('#stubSub') and await pg.evaluate('$("checkin").classList.contains("off")'))
        v = await pg.evaluate(INVIEW)
        check('範囲の外：自分と空港が両方地図に入る縮尺', v['ap'] and v['me'] and not v['edge'], v)
        check('範囲の外：地図に「いまここ」', await pg.is_visible('#homeMap .hm-mel'))
        await measure(pg, '範囲の外')
        await pg.screenshot(path=os.path.join(SHOTS, '03-home-out.png'))
        await pg.evaluate('window.__ck = 0; window.checkin = async () => { window.__ck++; }; 0')
        await pg.click('#checkin')
        for _ in range(30):   # 調べ直しは長くても8秒で終わる
            await pg.wait_for_timeout(500)
            if '調べ直しています' not in await pg.inner_text('#msg'): break
        check('範囲の外：押しても確かめは出ず、位置を調べ直す（切らない）', not await pg.evaluate('$("dCkConfirm").open') and await pg.evaluate('window.__ck') == 0 and '判定範囲の外' in await pg.inner_text('#msg'), await pg.inner_text('#msg'))
        # 範囲に入ると切れる形に変わる
        await c.set_geolocation({'latitude':HND[0], 'longitude':HND[1], 'accuracy':20}); await pg.wait_for_timeout(1500)
        if await state(pg) != 'in': await pg.click('#checkin')   # 見張りの位置がまだ届かないときは、押して調べ直す
        try: await pg.wait_for_function('$("bpass").dataset.state === "in"', timeout=14000)
        except Exception: pass
        check('範囲の外 → 中：入ると琥珀の半券に変わる', await state(pg) == 'in', [await state(pg), await pg.inner_text('#msg')])
        check('範囲の外：エラーなし', not errs, errs); await c.close()

        # 3. 遠く（空港から80km より遠い）：地図の端に矢印と距離
        c, pg, errs = await page(b, FAR, login=True)
        v = await pg.evaluate(INVIEW)
        check('遠く：空港は地図に入り、自分は端の矢印と距離で出す', v['ap'] and v['edge'], v)
        e = (await pg.inner_text('#homeEdge')).replace('\n', ' ') if v['edge'] else ''
        check('遠く：矢印に「いまここ ○km」', 'いまここ' in e and 'km' in e, e)
        check('遠く：エラーなし', not errs, errs); await c.close()

        # 4. ログインしていない（範囲の外でも、ログインの案内が先）
        c, pg, errs = await page(b, OUT, shots=True)
        check('ログインしていない：形（範囲の外より先）', await state(pg) == 'guest', await state(pg))
        check('ログインしていない：半券は「ログインすると使える」', 'ログイン' in await pg.inner_text('#stubSub') and await pg.evaluate('$("checkin").classList.contains("off")'))
        check('ログインしていない：数字の帯の代わりに案内（ログイン・登録／デモで試す）', await pg.is_visible('#homeGate') and not await pg.is_visible('#homeStrip'))
        check('ログインしていない：上の段は「ログイン」', (await pg.inner_text('#openSettings')).strip() == 'ログイン')
        await measure(pg, 'ログインしていない')
        await pg.screenshot(path=os.path.join(SHOTS, '04-home-guest.png'))
        await pg.click('#checkin'); await pg.wait_for_timeout(300)
        check('ログインしていない：半券を押すとログインの画面', await pg.evaluate('$("dAuth").open && AU.flow === "login"'))
        await pg.evaluate('authClose()'); await pg.wait_for_timeout(200)
        await pg.click('#openSettings'); await pg.wait_for_timeout(300)
        check('ログインしていない：「ログイン」を押すとログインの画面（マイページではない）', await pg.evaluate('$("dAuth").open') and not await pg.evaluate('$("dSettings").open'))
        await pg.evaluate('authClose()'); await pg.wait_for_timeout(200)
        if await pg.is_visible('#modeSw'):
            await pg.click('#modeSw [data-mode=game]'); await pg.wait_for_timeout(300)
            check('ログインしていない：「エアライン経営」を押すとログインの画面（経営は開かない）', await pg.evaluate('$("dAuth").open') and await pg.evaluate('MODE') == 'rally')
            await pg.evaluate('authClose()'); await pg.wait_for_timeout(200)
        await pg.click('#gateDemo'); await pg.wait_for_timeout(900)
        check('ログインしていない：「デモで試す」でデモになる', await pg.evaluate('demo') and await state(pg) == 'in')
        check('ログインしていない：エラーなし', not errs, errs); await c.close()

        # 5. デモ：「デモ中」のピルだけ（帯は出さない）。終えるのはマイページから
        c, pg, errs = await page(b, HND, shots=True)
        await pg.evaluate('$("toggleDemo").click()'); await pg.wait_for_timeout(900)
        check('デモ：「デモ中」のピル', await pg.is_visible('#demoPill') and (await pg.inner_text('#demoPill')).strip() == 'デモ中')
        check('デモ：前のデモの帯は出さない', not await pg.is_visible('.demo-banner'))
        check('デモ：範囲の中の形', await state(pg) == 'in')
        check('デモ：見本の数字（16空港・30フライト）', await pg.inner_text('#hsAp') == '16' and await pg.inner_text('#hsFl') == '30')
        await measure(pg, 'デモ')
        await pg.screenshot(path=os.path.join(SHOTS, '05-home-demo.png'))
        await pg.click('#openSettings'); await pg.wait_for_timeout(300)
        check('デモ：マイページから終えられる', await pg.is_visible('#toggleDemo'))
        await pg.click('#toggleDemo'); await pg.wait_for_timeout(800)
        check('デモを終えると、ログインの案内に戻る', not await pg.evaluate('demo') and await state(pg) == 'guest' and not await pg.is_visible('#demoPill'))
        check('デモ：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
