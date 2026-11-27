import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# はじめての流れとログイン案B（11/26 本人「B」・design/onboarding の O1〜O5・b1・O6）
#   ログインなしで O1 → O2 使い方 → O3 行ったことがある空港（メモ）→ O4 次の予定 → O5 → ホーム（試せます・次のフライト）
#   範囲の中で半券を切ると b1（登録しないと印は押されない）→ やめると押されない → 登録すると、その印を押す
#   偽のサーバー（fake_sb.js）を使う。本物の Supabase には接続しない
import asyncio, json, datetime
from playwright.async_api import async_playwright
SHOTS = os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-onboarding-b'); os.makedirs(SHOTS, exist_ok=True)
NEW = "[{user_id:'u1', display_name:null, persona:'unanswered', terms_version:null, privacy_version:null, agreed_at:null}]"
HANEDA = (35.5494, 139.7798)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
async def page(b, w=390, h=844, init='', shots=True, geo=HANEDA):
    c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=2 if shots else 1, geolocation={'latitude':geo[0],'longitude':geo[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');" + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(600)
    return c, pg, errs
async def step(pg): return await pg.evaluate('$("dAuth").open ? AU.flow + ":" + AU.step : "closed"')
async def shot(pg, name): await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
# 横のはみ出し・12px 未満の字・押す所の高さ（見えているボタン）
LINT = """(() => { const d = document.querySelector('dialog[open]') || document.body, bad = [], small = [], over = [];
  for(const e of d.querySelectorAll('button, select, input, a')){ const r = e.getBoundingClientRect(); if(!r.width || getComputedStyle(e).visibility === 'hidden') continue; if(r.height < 44 && !e.closest('.steps')) bad.push((e.textContent || e.id || e.tagName).trim().slice(0, 12) + ':' + Math.round(r.height)); if(r.right > innerWidth + 1) over.push((e.textContent || '').trim().slice(0, 12)); }
  for(const e of d.querySelectorAll('*')){ if(!e.childNodes.length || ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue; const f = parseFloat(getComputedStyle(e).fontSize); if(f < 12) small.push(e.textContent.trim().slice(0, 10) + ':' + f); }
  return { bad, small, over, sw: document.documentElement.scrollWidth, iw: innerWidth }; })()"""
async def lint(pg, label):
    r = await pg.evaluate(LINT)
    check(f'{label}：はみ出しなし・12px 未満なし・押す所 44 以上', not r['bad'] and not r['small'] and not r['over'] and r['sw'] <= r['iw'], r)
async def main():
    day = (datetime.datetime.utcnow() + datetime.timedelta(hours=9) + datetime.timedelta(days=14)).strftime('%Y-%m-%d')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. はじめて開く：O1〜O5 → ホーム
        c, pg, errs = await page(b, init=f"window.__profiles = {NEW}; window.__viewPrefs = [];")
        check('はじめて開くと O1（ログインの画面ではない）', await step(pg) == 'onb:o1'); await shot(pg, 'o1-intro')
        t = await pg.inner_text('#dAuth')
        check('O1：「はじめる」と、ログイン・デモで試す', 'はじめる' in t and 'ログイン' in t and 'デモで試す' in t)
        check('今までの3枚の案内は出ない', not await pg.evaluate("$('dGuide').open")); await lint(pg, 'O1')
        await pg.click('[data-ob=start]'); await pg.wait_for_timeout(100)
        check('O1 → O2 使い方（1 / 4）', await step(pg) == 'onb:o2' and '1 / 4' in await pg.inner_text('#dAuth .top'))
        await pg.click('[data-ob-persona=spot]'); await shot(pg, 'o2-persona'); await lint(pg, 'O2')
        await pg.click('[data-ob=next]'); await pg.wait_for_timeout(100)
        check('O2 → O3 行ったことがある空港（2 / 4）', await step(pg) == 'onb:o3')
        check('O3：0件は「これから最初の1空港へ」「まだない・次へ」', 'これから最初の1空港へ' in await pg.inner_text('#dAuth') and 'まだない' in await pg.inner_text('#auFoot'))
        await shot(pg, 'o3b-zero')
        hnd, cts, fuk = [await pg.evaluate(f"IATA.{x}.id") for x in ('HND', 'CTS', 'FUK')]
        await pg.click(f'[data-ob-memo="{hnd}"]'); await pg.click(f'[data-ob-memo="{cts}"]')
        await pg.click('[data-ob-rg="九州"]'); await pg.wait_for_timeout(50)
        await pg.click(f'.obrg.open [data-ob-memo="{fuk}"]'); await pg.wait_for_timeout(50)
        check('O3：選んだ数がその場で増える（3 / 86）', await pg.inner_text('#obMemoN') == '3' and '3空港で次へ' in await pg.inner_text('#auFoot'))
        check('O3：選んだ空港は淡いピン（押した状態）', await pg.evaluate(f"document.querySelector('[data-ob-memo=\"{hnd}\"]').getAttribute('aria-pressed')") == 'true')
        await shot(pg, 'o3-visited'); await lint(pg, 'O3')
        await pg.click('[data-ob=next]'); await pg.wait_for_timeout(100)
        check('O3 → O4 次の予定（3 / 4）', await step(pg) == 'onb:o4' and '予定なしで次へ' in await pg.inner_text('#auFoot'))
        await pg.select_option('#obFrom', str(hnd)); await pg.wait_for_timeout(50); await pg.select_option('#obTo', str(cts)); await pg.wait_for_timeout(50)
        await pg.fill('#obDay', day); await pg.dispatch_event('#obDay', 'change'); await pg.wait_for_timeout(50)
        check('O4：予定がそろうと「あと14日」「この予定で次へ」', 'あと14日' in await pg.inner_text('#dAuth') and 'この予定で次へ' in await pg.inner_text('#auFoot'))
        await shot(pg, 'o4-plan'); await lint(pg, 'O4')
        await pg.click('[data-ob=next]'); await pg.wait_for_timeout(100)
        t = await pg.inner_text('#dAuth')
        check('O5：行ったことがある 3 空港・あと 14 日・最初の小目標・位置の説明', await step(pg) == 'onb:o5' and '3' in t and '14' in t and '最初の小目標' in t and '羽田でチェックインして' in t and '位置情報' in t, t[:200])
        await shot(pg, 'o5-ready'); await lint(pg, 'O5')
        await pg.click('[data-ob=allow]'); await pg.wait_for_timeout(900)
        check('O5 → ホーム（流れは閉じ、次からは出ない）', await step(pg) == 'closed' and await pg.evaluate("localStorage.getItem('soramemo.onboarded')") == '1' and await pg.evaluate('currentView()') == 'home')
        ob = await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.ob'))")
        check('答え・メモ・予定は端末に（サーバーには送らない）', ob['persona'] == 'spot' and sorted(ob['memo']) == sorted([hnd, cts, fuk]) and ob['plan']['day'] == day and ob['done'] == 'allow', ob)
        check('構成は変えない（全部乗せのまま）', await pg.evaluate('PERSONA') == 'all')
        await pg.wait_for_function('$("bpass").dataset.state === "in"', timeout=10000)
        check('ログインしていなくても半券は同じ形（範囲の中）', await pg.evaluate('$("bpass").dataset.state') == 'in' and '右へ引いて' in await pg.inner_text('#checkin'))
        check('ホーム：「いま空港にいなくても試せます」', await pg.is_visible('#obTry') and '羽田のいまを見てみる' in await pg.inner_text('#obTry') and not await pg.is_visible('#gateNorm'))
        await pg.evaluate('$("homeSheet").sheetGo("full")'); await pg.wait_for_timeout(400)
        check('ホーム：次のフライト（HND → CTS・あと14日）', await pg.is_visible('#obPlanCard') and 'HND → CTS' in await pg.inner_text('#obPlanCard') and '14' in await pg.inner_text('#obPlanCard'))
        await pg.evaluate('$("homeSheet").sheetGo("half")'); await pg.wait_for_timeout(400); await shot(pg, 'o6-home')
        await pg.evaluate("goTab('book')"); await pg.wait_for_timeout(700)
        check('図鑑：メモの空港は淡く（3つ）', await pg.locator('#zkBody .zk-ap.memo').count() >= 3, await pg.locator('#zkBody .zk-ap.memo').count())
        await pg.evaluate(f"zkJump && zkJump('関東')"); await pg.wait_for_timeout(300); await shot(pg, 'book-memo')
        await pg.evaluate("goTab('home')"); await pg.wait_for_timeout(500)
        # 2. 半券を切る → b1。やめると印は押されない
        n0 = await pg.evaluate('__fake.db.checkins.length')
        await pg.evaluate('checkin()'); await pg.wait_for_function('$("dObReg").open', timeout=10000)
        t = await pg.inner_text('#dObReg')
        check('範囲の中で切ると b1（印を残すために登録）', '記録をバックアップ' in t and '登録しないと' in t and '印は押されません' in t and '無料' in t, t[:120])
        check('b1：メモ（3空港）と予定はこの端末にだけ残る、と書く', '3空港' in t and 'この端末にだけ' in t)
        await shot(pg, 'b1-backup'); await lint(pg, 'b1')
        await pg.click('[data-obreg=later]'); await pg.wait_for_timeout(200)
        check('「いまはやめる」：印は押されず、そう伝える', await pg.evaluate('__fake.db.checkins.length') == n0 and '印は押されていません' in await pg.inner_text('#msg') and await pg.evaluate('S.checkins.length') == 0)
        # 3. もう一度切って登録 → 表示名 → 同意 → 位置 → その印を押す
        await pg.evaluate('checkin()'); await pg.wait_for_function('$("dObReg").open', timeout=10000)
        await pg.click('[data-obreg=send]'); await pg.wait_for_timeout(100)
        check('メールが空なら送らない', 'メールアドレス' in await pg.inner_text('#obRegMsg') and await pg.evaluate('!window.__otp'))
        await pg.fill('#obRegEmail', 'sora@example.jp'); await pg.click('[data-obreg=send]'); await pg.wait_for_timeout(400)
        o = await pg.evaluate('JSON.stringify(window.__otp)')
        check('確認コードを送る（アカウントを作る）→ コードの画面', await step(pg) == 'signup:code' and '"shouldCreateUser":true' in o and 'sora@example.jp' in o, o[:120])
        await pg.fill('#auCode', '12345678'); await pg.dispatch_event('#auCode', 'input'); await pg.click('#dAuth [data-au=verify]'); await pg.wait_for_timeout(700)
        check('コード → 表示名', await step(pg) == 'signup:name')
        bars = await pg.evaluate("document.querySelectorAll('#dAuth .steps i').length")
        check('段の帯は答えた所（使い方・位置）を数えない（4つ）', bars == 4, bars)
        await pg.fill('#auName', 'そらのたび人'); await pg.click('#dAuth [data-au=name-next]'); await pg.wait_for_timeout(400)
        prof = await pg.evaluate('JSON.stringify(__fake.db.user_profiles[0])')
        check('使い方のアンケートは飛ばし、O2 の答え（撮る）を保存', await step(pg) == 'signup:terms' and '"persona":"spot"' in prof, prof)
        await pg.click('#dAuth .agree'); await pg.click('#dAuth [data-au=agree]'); await pg.wait_for_timeout(1500)
        check('同意 → 位置の説明は飛ばしてホームへ（O5 で許可を聞いた）', await step(pg) == 'closed')
        await pg.wait_for_function(f'__fake.db.checkins.length > {n0}', timeout=10000)
        check('登録を終えると、その印を押す（サーバーで判定し直す）', await pg.evaluate('__fake.db.checkins.length') == n0 + 1 and await pg.evaluate(f'__fake.db.checkins[__fake.db.checkins.length - 1].airport_id === {hnd}'))
        await pg.wait_for_timeout(600); await shot(pg, 'b1-after-stamp')
        check('ログインしたら「試せます」は出ない', not await pg.is_visible('#homeGate'))
        check('はじめての流れ・登録：エラーなし', not errs, errs); await c.close()

        # 4. 範囲の外で切る → 登録の画面は出さない（距離の文）
        c, pg, errs = await page(b, init="localStorage.setItem('soramemo.onboarded','1');", shots=False, geo=(35.69, 139.70))
        await pg.evaluate('checkin()'); await pg.wait_for_timeout(1500)
        check('範囲の外：b1 は出さず、押せない理由を出す（ログインした人と同じ文）', not await pg.evaluate('$("dObReg").open') and len((await pg.inner_text('#msg')).strip()) > 0 and await pg.evaluate('__fake.db.checkins.length') == 1, await pg.inner_text('#msg'))
        check('範囲の外：エラーなし', not errs, errs); await c.close()

        # 5. O1 の「ログイン」は今のログインの画面・「あとで」を押した段は飛ばせる・Esc で閉じても次は出ない
        c, pg, errs = await page(b, shots=False)
        await pg.click('[data-ob=login]'); await pg.wait_for_timeout(200)
        check('O1 の「ログイン」→ 今のログインの画面（6けたのコード）', await step(pg) == 'login:login' and await pg.evaluate("localStorage.getItem('soramemo.onboarded')") == '1')
        await pg.evaluate("authClose(); obnOpen('o1')"); await pg.click('[data-ob=start]'); await pg.click('[data-ob=skip]'); await pg.wait_for_timeout(50)
        check('「あとで」でその段を飛ばす（O2 → O3・答えは「あとで決める」）', await step(pg) == 'onb:o3' and await pg.evaluate('OBS.persona') == 'unanswered')
        await pg.keyboard.press('Escape'); await pg.wait_for_timeout(200)
        check('Esc で閉じても次は出ない', await step(pg) == 'closed' and await pg.evaluate("localStorage.getItem('soramemo.onboarded')") == '1')
        await pg.evaluate("__fake.login()"); await pg.wait_for_timeout(1200)
        await pg.evaluate("openMyPage && openMyPage('acct')"); await pg.wait_for_timeout(300)
        await pg.evaluate("$('memoEdit').click()"); await pg.wait_for_timeout(200)
        check('マイページの「行ったことがある空港（メモ）」から O3 だけを開く', await step(pg) == 'onb:o3' and '保存する' in await pg.inner_text('#auFoot'))
        await pg.click(f'[data-ob-memo="{await pg.evaluate("IATA.ITM.id")}"]'); await pg.click('[data-ob=memo-save]'); await pg.wait_for_timeout(200)
        check('メモを直して保存', await step(pg) == 'closed' and await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.ob')).memo.includes(IATA.ITM.id)"))
        check('ログイン・メモの直し：エラーなし', not errs, errs); await c.close()

        # 6. 375×667：全部の段が送らずにボタンまで届く
        c, pg, errs = await page(b, 375, 667)
        for s in ('o1', 'o2', 'o3', 'o4', 'o5'):
            await pg.evaluate(f"OBS.step = '{s}'; AU.step = '{s}'; authRender()"); await pg.wait_for_timeout(80)
            await shot(pg, f'{s}-667'); await lint(pg, f'667 {s}')
            r = await pg.evaluate("(() => { const b = document.querySelector('#auFoot .cta').getBoundingClientRect(); return [Math.round(b.top), Math.round(b.bottom), innerHeight]; })()")
            check(f'667 {s}：「次へ」は送らずに押せる（画面の中）', r[1] <= r[2] and r[0] >= 0, r)
        await pg.evaluate("AU.flow = 'login'; authClose(); localStorage.setItem('soramemo.onboarded','1'); obHomeRender()"); await pg.wait_for_timeout(800)
        await shot(pg, 'o6-home-667')
        r = await pg.evaluate("(() => { const z = document.querySelector('.leaflet-control-zoom-in'); if(!z) return 'none'; const q = z.getBoundingClientRect(), t = document.elementFromPoint(q.left + q.width/2, q.top + q.height/2); return !!t && (t === z || z.contains(t)); })()")
        check('667 ホーム：「試せます」があっても地図の＋が押せる', r is True or r == 'none', r)
        await pg.evaluate('checkin()'); await pg.wait_for_function('$("dObReg").open', timeout=10000); await pg.wait_for_timeout(300)
        await shot(pg, 'b1-backup-667'); await lint(pg, '667 b1')
        check('667：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
