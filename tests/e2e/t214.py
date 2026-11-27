import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# 不具合・意見を送る（11/27 本人の指示・design/gemini-1126 F1〜F4・データ data/feedback の表 feedback と関数 feedback-submit）
#   入口（マイページ・押せなかった札の下）・3択＋本文・自動で付ける情報を見せる・位置は送らない・受け付けました・電波がないと保留・断られたときの文
#   偽のサーバー（fake_sb.js と、feedback-submit は page.route）を使う。本物の Supabase には接続しない
import asyncio, json
from playwright.async_api import async_playwright
SHOTS = os.path.join(HERE, '..', '..', 'docs', 'pm', 'shots-feedback'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
INIT = "localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.tpTaught','1'); localStorage.setItem('soramemo.zk.notice','1');"
async def page(b, w=390, h=844, init='', geo=(35.5494, 139.7798), shots=True, posts=None, fnStatus=200, fnBody='{"ok":true}'):
    c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=2 if shots else 1, geolocation={'latitude':geo[0],'longitude':geo[1],'accuracy':20}, permissions=['geolocation'], timezone_id='Asia/Tokyo')
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    async def fn(r):
        if posts is not None: posts.append(json.loads(r.request.post_data or '{}'))
        await r.fulfill(status=fnStatus, body=fnBody, content_type='application/json')
    await c.route('https://fake.supabase.co/functions/v1/feedback-submit', fn)
    await c.add_init_script(INIT + init)
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://'+os.path.join(WORK,'index_server_test.html')); await pg.wait_for_load_state('load')
    await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && typeof sb !== "undefined" && !!sb'); await pg.wait_for_timeout(600)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return c, pg, errs
async def shot(pg, name): await pg.screenshot(path=os.path.join(SHOTS, name + '.png'))
LINT = """(() => { const d = document.querySelector('#dFb'), bad = [], small = [];
  for(const e of d.querySelectorAll('button, textarea, select')){ const r = e.getBoundingClientRect(); if(!r.width || e.tagName === 'SELECT') continue; if(r.height < 44) bad.push((e.textContent || e.id).trim().slice(0, 10) + ':' + Math.round(r.height)); if(r.right > innerWidth + 1) bad.push('over:' + (e.textContent || '').trim().slice(0, 10)); }
  for(const e of d.querySelectorAll('*')){ if(![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue; const f = parseFloat(getComputedStyle(e).fontSize); if(f < 12) small.push(e.textContent.trim().slice(0, 10) + ':' + f); }
  const cta = d.querySelector('.fbcta').getBoundingClientRect();
  return { bad, small, sw: document.documentElement.scrollWidth, iw: innerWidth, ctaIn: cta.bottom <= innerHeight + 1 }; })()"""
async def lint(pg, label, cta=True):
    r = await pg.evaluate(LINT)
    check(f'{label}：はみ出しなし・12px 未満なし・押す所 44 以上' + ('・「送る」が画面の中' if cta else ''), not r['bad'] and not r['small'] and r['sw'] <= r['iw'] and (r['ctaIn'] or not cta), r)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1. ログインした人：マイページの入口 → 不具合 → 送る（表 feedback に直接）
        c, pg, errs = await page(b)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1200)
        await pg.click('#openSettings'); await pg.wait_for_timeout(300)
        check('マイページの目次に「意見を送る」', await pg.is_visible('#mpIdx [data-fb-open=mypage]') and '不具合・ほしい機能・空港データの直し' in await pg.inner_text('#mpIdx'))
        await shot(pg, 'f1-entry')
        await pg.click('#mpIdx [data-fb-open=mypage]'); await pg.wait_for_timeout(300)
        check('押すと「意見を送る」のシート（はじめは不具合）', await pg.evaluate("$('dFb').open") and await pg.get_attribute('[data-fb-kind=bug]', 'aria-checked') == 'true')
        t = await pg.inner_text('#dFb')
        check('自動で付ける情報を送る前に見せる（版・端末・画面・直前のエラー）', all(x in t for x in ('アプリの版', '端末の種類', '開いていた画面 マイページ', '直前のエラー なし')), t)
        check('位置は送らないと書く', '送らないもの' in t and '位置' in t)
        check('本文が空なら送れない', await pg.is_disabled('#dFb [data-fb=send]'))
        await pg.fill('#fbText', 'いまの空港で羽田を開くと、特別塗装機のカードが2回出ます'); await pg.wait_for_timeout(50)
        check('数がその場で増える', await pg.inner_text('#fbN') == str(len('いまの空港で羽田を開くと、特別塗装機のカードが2回出ます')))
        await shot(pg, 'f2-form'); await lint(pg, '390 不具合')
        await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(400)
        rows = await pg.evaluate('JSON.stringify(__fake.db.feedback || [])')
        r = json.loads(rows)
        check('ログインしている人は表 feedback に入れる（決まった列だけ）', len(r) == 1 and r[0]['kind'] == 'bug' and r[0]['screen'] == 'mypage' and r[0]['app_version'] and r[0]['device'] and r[0]['session'] and set(r[0].keys()) <= {'id', 'kind', 'body', 'app_version', 'screen', 'device', 'last_error', 'airport', 'session'}, r)
        check('位置・メールは送らない', not any(k in rows for k in ('lat', 'lon', 'email', 'test@example.com')))
        check('送ったら「受け付けました」', '受け付けました' in await pg.inner_text('#dFb')); await shot(pg, 'f4-sent')
        await pg.click('#dFb [data-fb=close]'); await pg.wait_for_timeout(200)
        # 空港データの直し：空港・どこが違うか
        await pg.evaluate("fbOpen('mypage')"); await pg.click('[data-fb-kind=airport_data]'); await pg.wait_for_timeout(100)
        check('空港データの直し：空港（はじめはいる空港）とどこが違うか', await pg.is_visible('#fbAp') or await pg.locator('#fbAp').count() == 1)
        await pg.select_option('#fbAp', 'ITM'); await pg.click('[data-fb-part="滑走路"]'); await pg.fill('#fbText', '滑走路の長さが違います'); await pg.wait_for_timeout(50)
        check('自動の情報に空港も出る', '空港 ITM' in await pg.inner_text('#dFb'))
        await shot(pg, 'f3-airport'); await lint(pg, '390 空港データ', cta=False)
        await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(400)
        r = json.loads(await pg.evaluate('JSON.stringify(__fake.db.feedback)'))
        check('空港データ：種類・空港・本文の頭に【滑走路】', len(r) == 2 and r[1]['kind'] == 'airport_data' and r[1]['airport'] == 'ITM' and r[1]['body'].startswith('【滑走路】'), r[-1])
        # 断られたとき
        await pg.evaluate("window.__fbErr = {code:'54000', message:'feedback_too_many'}"); await pg.evaluate("fbOpen('mypage')"); await pg.fill('#fbText', 'もう1件'); await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(300)
        check('送りすぎ：10分に3件まで、と出して閉じない', '10分に3件' in await pg.inner_text('#fbMsg') and await pg.evaluate("$('dFb').open"))
        await pg.evaluate("window.__fbErr = {code:'55000', message:'closed'}"); await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(300)
        check('止めている：受け付けを止めています', '止めています' in await pg.inner_text('#fbMsg'))
        await pg.evaluate("window.__fbErr = null")
        # 2001字
        await pg.fill('#fbText', 'あ' * 2001); await pg.wait_for_timeout(50)
        check('2000字を超えると送れない', await pg.is_disabled('#dFb [data-fb=send]') and '2000字まで' in await pg.inner_text('#fbMsg'))
        await pg.evaluate("document.documentElement.dataset.night = 'on'"); await pg.fill('#fbText', 'よるの表示'); await pg.wait_for_timeout(100); await shot(pg, 'f2-form-night')
        await pg.evaluate("delete document.documentElement.dataset.night")
        check('ログインした人：エラーなし', not errs, errs); await c.close()

        # 2. ログインしていない人：押せなかった札の下の「不具合を知らせる」→ feedback-submit
        posts = []
        c, pg, errs = await page(b, geo=(35.69, 139.70), posts=posts)
        await pg.evaluate("say('判定範囲の外です。', true); ckNote()"); await pg.wait_for_timeout(200)
        check('押せなかった札の下に「不具合を知らせる」', await pg.is_visible('#fbErrStub') and await pg.is_visible('#fbErrMsg'))
        await shot(pg, 'f0-error-link')
        await pg.evaluate("say('チェックインしました。')"); await pg.wait_for_timeout(100)
        check('できたときは出さない（ホームの文）', not await pg.is_visible('#fbErrMsg'))
        await pg.evaluate("say('判定範囲の外です。', true); ckNote()"); await pg.click('#fbErrStub'); await pg.wait_for_timeout(300)
        t = await pg.inner_text('#dFb')
        check('札から開くと、開いていた画面と直前のエラーが付く', '開いていた画面 ホーム' in t and '直前のエラー 押せなかった' in t, t)
        await pg.fill('#fbText', '空港の中なのに押せません'); await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(500)
        check('ログインしていない人は feedback-submit へ（起動の値つき・利用者は送らない）', len(posts) == 1 and posts[0]['kind'] == 'bug' and posts[0]['last_error'] == 'app_msg' and posts[0]['screen'] == 'home' and len(posts[0]['session']) >= 8 and 'user_id' not in posts[0], posts)
        check('位置は送らない（関数へも）', not any(k in json.dumps(posts) for k in ('"lat', '"lon', '35.69', '139.7')))
        check('受け付けました', '受け付けました' in await pg.inner_text('#dFb'))
        check('ログインしていない人：エラーなし', not errs, errs); await c.close()

        # 3. 関数が断った（429）
        c, pg, errs = await page(b, shots=False, fnStatus=429, fnBody='{"error":"too_many"}')
        await pg.evaluate("fbOpen('error')"); await pg.fill('#fbText', 'テスト'); await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(400)
        check('関数の 429：10分に3件まで', '10分に3件' in await pg.inner_text('#fbMsg'))
        check('429：エラーなし', not errs, errs); await c.close()

        # 4. 電波がない：保留して、つながったら送る
        posts = []
        c, pg, errs = await page(b, posts=posts)
        await pg.evaluate("fbOpen('mypage')"); await pg.fill('#fbText', '電波がないときの報告')
        await pg.context.set_offline(True); await pg.wait_for_timeout(100)
        await pg.click('#dFb [data-fb=send]'); await pg.wait_for_timeout(300)
        check('電波がないと保存して「つながったら送ります」', '保存しました' in await pg.inner_text('#dFb') and 'つながったら送ります' in await pg.inner_text('#dFb') and len(await pg.evaluate("JSON.parse(localStorage.getItem('soramemo.fbq') || '[]')")) == 1)
        await shot(pg, 'f4-queued')
        await pg.context.set_offline(False); await pg.wait_for_timeout(2500)
        check('つながったら送り、保留は空になる', len(posts) == 1 and posts[0]['body'] == '電波がないときの報告' and not await pg.evaluate("localStorage.getItem('soramemo.fbq')"), posts)
        check('電波：エラーなし', not errs, errs); await c.close()

        # 5. 375×667
        c, pg, errs = await page(b, 375, 667)
        await pg.evaluate('__fake.login()'); await pg.wait_for_timeout(1000)
        await pg.click('#openSettings'); await pg.wait_for_timeout(300); await shot(pg, 'f1-entry-667')
        await pg.click('#mpIdx [data-fb-open=mypage]'); await pg.wait_for_timeout(300); await pg.fill('#fbText', '375 の幅で確かめる'); await shot(pg, 'f2-form-667'); await lint(pg, '375 不具合')
        await pg.click('[data-fb-kind=airport_data]'); await pg.wait_for_timeout(100); await shot(pg, 'f3-airport-667'); await lint(pg, '375 空港データ', cta=False)
        check('375：エラーなし', not errs, errs); await c.close()
        await b.close()
    print('errors', fails)
asyncio.run(main())
