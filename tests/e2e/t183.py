import os, sys, re
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
import asyncio, json
from playwright.async_api import async_playwright
sys.path.insert(0, HERE); from keepls import goto_http
# 11/24 アプリ全体の見直し A の回（kaizen/sweep-all-a・report-sweep-all-a.md）の直し（checkin/sweep-all-1）
#   1 マイページの頭の札と成績のパスポートは車などと記録帳の便を入れない（ホームと同じ 30フライト・24,017km）
#   2 「記録を書き出す」の説明（バックアップは有料にしない。PM の決定①）と見出し「データとバックアップ」
#   5 デモの見本の最後の便は昨日。1回押すと「今日の印」は 1、印の日付は今日
#   6 375×667 の同意の画面で、チェックと「同意してはじめる」が送らずに見える
#   7 補足の字の色 4.5:1 以上　8 案内の3枚目は「はじめる」1つ　9 押せる所 44px　10 共有画像に「非公式アプリ」　B10 明朝体をゴシックに
SHOTS = os.path.join(WORK, 't183'); os.makedirs(SHOTS, exist_ok=True)
fails = []
def check(name, ok, detail=''):
    print(('OK  ' if ok else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not ok: fails.append(name)
CONTRAST = """(sel) => { const L = c => { const m = c.match(/[\\d.]+/g).slice(0,3).map(Number).map(v => v/255).map(v => v <= .03928 ? v/12.92 : ((v+.055)/1.055)**2.4); return .2126*m[0]+.7152*m[1]+.0722*m[2]; };
  const bgOf = el => { for(let e = el; e; e = e.parentElement){ const b = getComputedStyle(e).backgroundColor; if(b && !/rgba\\(.*,\\s*0\\)$/.test(b) && b !== 'transparent') return b; } return 'rgb(255,255,255)'; };
  return [...document.querySelectorAll(sel)].filter(e => e.offsetParent || getComputedStyle(e).position === 'fixed').map(e => { const a = L(getComputedStyle(e).color), b = L(bgOf(e)); return +(((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toFixed(2)); }); }"""
async def newpage(b, w, h, onboarded=True):
    c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=1, timezone_id='Asia/Tokyo')
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.add_init_script(("localStorage.setItem('soramemo.onboarded','1');" if onboarded else "") + "localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await goto_http(pg, os.path.join(WEB,'index.html')); await pg.wait_for_load_state('load'); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    return c, pg, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- デモ：数と日付 ----
        c, pg, errs = await newpage(b, 390, 844)
        await pg.evaluate('openMyPage()'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(600)
        r = await pg.evaluate("""(() => { const day = t => new Date(t + 9*36e5).toISOString().slice(0,10), now = Date.now();
          const last = S.flights[S.flights.length - 1];
          return { n:S.flights.length, fly:flyOnly(S.flights).length, lastDay:day(last.arr), yday:day(now - 864e5), today:day(now), hsToday:$('hsToday').textContent, hsFl:$('hsFl').textContent, km:fmtKm(focusKm()), clock:S.demoClock }; })()""")
        check('デモの見本の最後の便は日本時間の昨日に着く', r['lastDay'] == r['yday'], r)
        check('開いた直後の「今日の印」は 0（見本の便は今日に入らない）', r['hsToday'] == '0', r['hsToday'])
        check('ホームのフライトは 30・距離 24,017km（車などを入れない）', r['hsFl'] == '30' and r['km'] == '24,017', (r['hsFl'], r['km']))
        # マイページの頭の札
        await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(200)
        chips = await pg.inner_text('#mpChips')
        check('マイページの頭の札は「16空港・30フライト」', '16空港・30フライト' in chips, chips.replace('\n', ' '))
        check('データの欄の見出しは「データとバックアップ」', (await pg.inner_text('#mpData')).strip() == 'データとバックアップ')
        en = await pg.inner_text('#expNote')
        check('書き出しの説明に「まとめて取り込む」がない（デモの言い方）', 'まとめて取り込む' not in en and 'デモ' in en, en)
        await pg.screenshot(path=os.path.join(SHOTS, '01-mypage.png'), full_page=False)
        await pg.click('#dSettings .mp-back'); await pg.wait_for_timeout(150)
        # パスポート（これまで）
        pp = await pg.evaluate('(() => { renderPassport(); return $("passport").innerText; })()')
        check('パスポートのフライトは 30・距離 24,017km', re.search(r'フライト\s*30(?!\d)', pp) is not None and '24,017' in pp, pp[:160].replace('\n', ' '))
        check('パスポートに「車など 1（90 km）は…別に数えています」', re.search(r'車など 1（\d+ km）は、フライト・距離・飛行時間に入れず別に数えています', pp) is not None)
        st = await pg.evaluate('JSON.stringify(passStats("all"))')
        check('パスポートの飛行時間・空港も便だけ（空港16）', json.loads(st)['aps'] == 16 and json.loads(st)['car'] == 1, st[:200])
        # 成績の航空会社別も車などを入れない（前は車などが「航空会社が未記録のフライト 1便」と出ていた。11/24 定時の回で足した）
        o = await pg.evaluate("""(() => { const ys = [...new Set(S.flights.map(f => new Date(f.arr).getFullYear()))]; let yr = 0;
          for(const y of ys){ YEAR = y; renderYears(); const m = ($('yrBody') ? $('yrBody').innerText : '').match(/(\\d+)\\s*フライト/); yr += m ? +m[1] : 0; }
          renderAirlines(); const al = $('airlineStats') ? $('airlineStats').innerText : '';
          const n = [...al.matchAll(/(\\d+)\\s*便/g)].reduce((x, m) => x + +m[1], 0);
          return { yr, al:n, ys:ys.length, unset:/未記録/.test(al) }; })()""")
        check('航空会社別の便は合わせて 30・「未記録のフライト」が出ない（車などを入れない）', o['al'] == 30 and not o['unset'], o)
        # 記録帳の便を足しても、フライトの数は変わらず別の行に
        await pg.evaluate("S.manual.push({d:'2026-01-05', from:A.find(a=>a.iata==='HND').id, to:A.find(a=>a.iata==='CTS').id, airline:'JL'});")
        pp2 = await pg.evaluate('(() => { renderPassport(); return $("passport").innerText; })()')
        check('記録帳の便はフライトに入れず「記録帳の便 1・車など 1」の1行', re.search(r'フライト\s*30(?!\d)', pp2) is not None and '記録帳の便 1・車など 1' in pp2, pp2[:200].replace('\n', ' '))
        await pg.evaluate('S.manual.pop()')
        # 1回押す：今日の印は 1、印の日付は今日
        await pg.select_option('#demoAirport', 't:HND-T1'); await pg.press('#checkin', 'Enter'); await pg.wait_for_timeout(900)
        r2 = await pg.evaluate("""(() => { const c = S.checkins[S.checkins.length - 1], day = t => new Date(t + 9*36e5).toISOString().slice(0,10); return { stamp:day(c.t), today:day(Date.now()), hs:$('hsToday').textContent }; })()""")
        check('デモで1回押すと印の日付は今日・「今日の印」は 1', r2['stamp'] == r2['today'] and r2['hs'] == '1', r2)
        # 共有画像のロゴの横に「非公式アプリ」
        txt = await pg.evaluate("""(async () => { const out = []; const o = CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText = function(t, ...a){ out.push(String(t)); return o.call(this, t, ...a); };
          try{ await stampCard(A.find(a => a.iata === 'HND'), Date.now(), null); } finally { CanvasRenderingContext2D.prototype.fillText = o; } return out; })()""")
        check('印の共有画像に「非公式アプリ」', 'そらメモ' in txt and '非公式アプリ' in txt, txt[:6])
        check('JS のエラーがない（デモ）', not errs, errs[:3])
        await c.close()
        # ---- はじめの案内：3枚目は「はじめる」1つ・運用と修行の一文・明朝体なし ----
        c, pg, errs = await newpage(b, 390, 844, onboarded=False)
        check('はじめて開くと案内', await pg.is_visible('#dGuide'))
        hnd = await pg.evaluate("getComputedStyle(document.querySelector('#dGuide .ob-step text')).fontFamily")
        check('案内の印の「HND」はゴシック', 'Mincho' not in hnd and 'serif' not in hnd.replace('sans-serif', ''), hnd)
        check('1枚目には「とばす」がある', await pg.is_visible('#obSkip'))
        await pg.click('#obNext'); await pg.click('#obNext'); await pg.wait_for_timeout(100)
        check('3枚目は「とばす」がなく「はじめる」1つ', await pg.is_hidden('#obSkip') and (await pg.inner_text('#obNext')).strip() == 'はじめる')
        nb = await pg.evaluate("$('obNext').getBoundingClientRect().width / $('obNext').parentElement.getBoundingClientRect().width")
        check('「はじめる」は横いっぱい', nb > 0.95, nb)
        g3 = await pg.inner_text('#dGuide .ob-step.on')
        check('3枚目に「運用（空港の今）や修行も、ログインしなくても見られます」', '運用（空港の今）や修行も、ログインしなくても見られます' in g3)
        await pg.screenshot(path=os.path.join(SHOTS, '02-guide3.png'))
        await pg.click('#obNext'); await pg.wait_for_timeout(200)
        brand = await pg.evaluate("getComputedStyle(document.querySelector('.brand')).fontFamily")
        check('頭の「そらメモ」はゴシック', 'Mincho' not in brand, brand)
        await c.close()
        # ---- 375×667：同意の画面・補足の字・押せる所 ----
        c, pg, errs = await newpage(b, 375, 667)
        await pg.evaluate("authOpen('signup', 'terms')"); await pg.wait_for_timeout(300)
        vis = await pg.evaluate("""(() => { const H = innerHeight, r = s => document.querySelector(s).getBoundingClientRect(); const a = r('#dAuth .agree'), b = r('#dAuth [data-au=agree]');
          return { agreeBottom:a.bottom, ctaBottom:b.bottom, H, scrollable: $('dAuth').scrollHeight > $('dAuth').clientHeight }; })()""")
        check('375×667：同意のチェックが最初の画面に見える', vis['agreeBottom'] <= vis['H'], vis)
        check('375×667：「同意してはじめる」が最初の画面に見える', vis['ctaBottom'] <= vis['H'], vis)
        await pg.screenshot(path=os.path.join(SHOTS, '03-terms-667.png'))
        await pg.click('#dAuth .agree'); await pg.wait_for_timeout(50)
        check('チェックを入れるとボタンが押せる（下に固定したまま）', await pg.is_enabled('#dAuth [data-au=agree]'))
        await pg.evaluate("$('dAuth').scrollTop = 1e4"); await pg.wait_for_timeout(80)
        top = await pg.evaluate("document.querySelector('#dAuth .pts li:last-child').getBoundingClientRect().bottom <= document.querySelector('#auFoot').getBoundingClientRect().top + 1")
        check('下まで送ると3つ目の項目がボタンに隠れない', top)
        cr = await pg.evaluate(CONTRAST, '#dAuth .pts li small, #dAuth .agree small')
        check('同意の画面の補足の字は 4.5:1 以上', cr and min(cr) >= 4.5, cr)
        # ログインの画面・名前・コード
        for stp, sel in [('login', '#dAuth .note'), ('email', '#dAuth .note, #dAuth .lead'), ('name', '#dAuth .note, #dAuth .prev small'), ('location', '#dAuth .row small')]:
            await pg.evaluate(f"(() => {{ AU.flow = '{'login' if stp == 'login' else 'signup'}'; AU.step = '{stp}'; authRender(); }})()"); await pg.wait_for_timeout(80)
            cr = await pg.evaluate(CONTRAST, sel)
            check(f'{stp} の補足の字は 4.5:1 以上', cr and min(cr) >= 4.5, cr)
        await pg.evaluate("(() => { AU.flow = 'login'; AU.step = 'login'; authRender(); })()"); await pg.wait_for_timeout(80)
        h = await pg.evaluate("document.querySelector('#dAuth [data-au=close]').getBoundingClientRect().height")
        check('ログインの「あとで」は高さ 44px 以上', h >= 44, h)
        await pg.evaluate("(() => { AU.flow = 'login'; AU.step = 'code'; AU.email = 'a@example.jp'; LOGIN_GUARD.set('sentAt', 0); authRender(); })()"); await pg.wait_for_timeout(80)
        hs = await pg.evaluate("[...document.querySelectorAll('#dAuth .resend .linkish')].map(e => Math.round(e.getBoundingClientRect().height))")
        check('「アドレスを直す」「コードを送り直す」は高さ 44px 以上', len(hs) == 2 and min(hs) >= 44, hs)
        await pg.screenshot(path=os.path.join(SHOTS, '04-code-667.png'))
        await pg.evaluate("authClose()"); await pg.wait_for_timeout(100)
        # マイページ
        await pg.evaluate('openMyPage()'); await pg.wait_for_timeout(200)
        cr = await pg.evaluate(CONTRAST, '#dSettings .set-row small, #dSettings .legal, #dSettings .mp-sec h4')
        check('マイページの補足の字は 4.5:1 以上', cr and min(cr) >= 4.5, (min(cr) if cr else None, len(cr)))
        sw = await pg.evaluate("[...document.querySelectorAll('#dSettings .swatch')].map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })")
        check('マイページの色の丸は 44px 以上', sw and all(w >= 44 and h >= 44 for w, h in sw), sw)
        lg = await pg.evaluate("[...document.querySelectorAll('#dSettings .legal a')].map(e => Math.round(e.getBoundingClientRect().height))")
        check('規約のリンクは高さ 44px 以上', lg and min(lg) >= 44, lg)
        en = await pg.inner_text('#expNote')
        check('ログインしていない（端末だけ）の書き出しの説明', 'まとめて取り込む' not in en and '控え' in en, en)
        check('JS のエラーがない（登録・マイページ）', not errs, errs[:3])
        await c.close(); await b.close()
    print('errors', fails)
    sys.exit(1 if fails else 0)
asyncio.run(main())
