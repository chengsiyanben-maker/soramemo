# 下のタブ5つと「運用」→「いまの空港」の名前替え・印の振動（11/26 checkin/tabs-b・本人「B」・画面案 design/ia-ops 案B）
#   1 はじめの全部乗せのタブは今のまま5つ（ホーム・図鑑・フライト・いまの空港・修行）。「運用」の字は下のタブ帯に出ない
#   2 いまの空港の画面の名前（aria-label）・専用ページの戻る「いまの空港」・表示の編集の名前（いまの空港（空港）・（機体））
#   3 タブの長押しでは振動しない。印はハンコを出したときでなく、サーバーで確定したときだけ短く1回（11/26 13時50分 PM・本人「消音モードじゃないなら振動」）
#     マイページ「表示と色」の「印のときに振動」（はじめは ON）を OFF にすると振動しない
#   4 390／375 幅で下のタブ帯の字が1行に収まり、はみ出さない（写真 docs/pm/shots-tabs-b/）
import os, sys, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-tabs-b')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_tabsb_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
sys.path.insert(0, HERE); from stamp_perf import GEO
CTS = (42.7752, 141.6923); ITM = (34.7855, 135.4382)
VIB = "window.__vib = 0; window.__vibA = []; try{ Object.defineProperty(navigator, 'vibrate', {configurable:true, value:function(a){ window.__vib++; window.__vibA.push(a); return true; }}); }catch(e){}"
fails = []
def ok(cond, msg, extra=''):
    print(('ok   ' if cond else 'FAIL ') + msg + (f'  {extra}' if (extra and not cond) else ''))
    if not cond: fails.append(msg)
async def page(p, w, h):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=2, permissions=['geolocation'], has_touch=False)
    await c.add_init_script("if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); }" + GEO + VIB)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_tabsb_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await pg.wait_for_function('S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
    return b, pg, errs
TABS = "[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden && b.offsetParent).map(b => b.querySelector('span').textContent).join()"
async def main():
    allerrs = []
    async with async_playwright() as p:
        b, pg, errs = await page(p, 390, 844)
        t = await pg.evaluate(TABS)
        ok(t == 'ホーム,図鑑,フライト,いまの空港,修行', '1 はじめのタブは5つ（ホーム・図鑑・フライト・いまの空港・修行）', t)
        ok('運用' not in await pg.inner_text('nav.tabs'), '1 下のタブ帯に「運用」の字がない')
        ok(await pg.evaluate("TAB_NAME.ops") == 'いまの空港' and await pg.evaluate("vsName('ops') === 'いまの空港' && vsName('opsp') === 'いまの空港'"), '1 TAB_NAME・vsName も「いまの空港」')
        await pg.screenshot(path=os.path.join(SHOTS, '01-home-390.png'))
        # 2 画面の名前と専用ページの戻る
        await pg.click('nav.tabs button[data-v="ops"]'); await pg.wait_for_timeout(800)
        ok(await pg.get_attribute('#v-ops', 'aria-label') == 'いまの空港', '2 画面の aria-label が「いまの空港」')
        ok(await pg.evaluate("document.querySelector('nav.tabs button[data-v=ops]').getAttribute('aria-current')") == 'page', '2 いまの空港のタブが選ばれている')
        await pg.screenshot(path=os.path.join(SHOTS, '02-now-list-390.png'))
        card = pg.locator('#opsHubList [data-ohub]').first
        if await card.count():
            await card.click(); await pg.wait_for_timeout(900)
            bk = await pg.inner_text('#opsHubBack'); lab = await pg.get_attribute('#opsHubBack', 'aria-label')
            ok(bk.strip() == 'いまの空港' and lab == 'いまの空港の一覧に戻る', '2 専用ページの戻るは「いまの空港」', f'{bk!r} {lab!r}')
            r = await pg.evaluate("(() => { const e = $('opsHubBack'); return { w:e.scrollWidth, cw:e.clientWidth, h:e.getBoundingClientRect().height }; })()")
            ok(r['w'] <= r['cw'] + 1 and r['h'] <= 48, '2 戻るの字が切れない・1行', r)
            await pg.screenshot(path=os.path.join(SHOTS, '03-now-page-390.png'))
        else:
            ok(False, '2 一覧のカードがある')
        await pg.evaluate("openLayout && openLayout()"); await pg.wait_for_timeout(600)
        lt = await pg.inner_text('#dLayout')
        ok('いまの空港（空港）' in lt and 'いまの空港（機体）' in lt and '運用（空港）' not in lt, '2 表示の編集の名前は「いまの空港（空港）・（機体）」')
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 3 振動を呼ばない：タブの長押し
        await pg.click('nav.tabs button[data-v="home"]'); await pg.wait_for_timeout(400)
        bx = await pg.locator('nav.tabs button[data-v="book"]').bounding_box()
        await pg.mouse.move(bx['x'] + bx['width']/2, bx['y'] + bx['height']/2); await pg.mouse.down(); await pg.wait_for_timeout(900); await pg.mouse.up(); await pg.wait_for_timeout(400)
        ok(await pg.evaluate("$('dTabs').open"), '3 長押しでタブを選ぶシートが開く')
        ok(await pg.evaluate("window.__vib") == 0, '3 長押しで振動しない', await pg.evaluate("window.__vib"))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        # 3 印：ハンコでは振動せず、サーバーで確定したら1回
        SHIFT = "__fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); S.checkins.forEach(x => x.t -= 3*36e5)"
        async def press(ll):
            await pg.evaluate(SHIFT)
            await pg.evaluate(f'__geo.lat = {ll[0]}; __geo.lon = {ll[1]}; __geo.delay = 100; __geo.acc = 20; HOME_POS = null; POS_LAST = null; GEO_WARM = null')
            n0 = await pg.evaluate('S.checkins.length')
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); document.getElementById('checkin').dispatchEvent(new MouseEvent('click', {detail:0, bubbles:true}))")
            for _ in range(60):
                if await pg.evaluate("$('dStamp').open"): break
                await pg.wait_for_timeout(100)
            return await pg.evaluate("$('dStamp').open") and await pg.evaluate('S.checkins.length') > n0
        await pg.evaluate('window.__netDelay = 1500')
        ok(await press(CTS), '3 印が押せた（ハンコの画面）')
        ok(await pg.evaluate("window.__vib") == 0, '3 ハンコを出したとき（返事の前）は振動しない', await pg.evaluate("window.__vib"))
        for _ in range(60):
            if await pg.evaluate("window.__vib") > 0: break
            await pg.wait_for_timeout(100)
        await pg.wait_for_timeout(600)
        ok(await pg.evaluate("window.__vib") == 1 and await pg.evaluate("window.__vibA[0]") == 20, '3 サーバーで確定したら短く1回（20ms）', await pg.evaluate("window.__vibA"))
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); openMyPage('show')"); await pg.wait_for_timeout(400)
        ok(await pg.locator('#vibRow').is_visible() and await pg.get_attribute('#vibRow [data-vib]', 'aria-checked') == 'true', '3 マイページ「表示と色」に「印のときに振動」（はじめは ON）')
        await pg.screenshot(path=os.path.join(SHOTS, '08-mypage-vib-390.png'))
        await pg.click('#vibRow [data-vib]'); await pg.wait_for_timeout(200)
        ok(await pg.get_attribute('#vibRow [data-vib]', 'aria-checked') == 'false' and await pg.evaluate("localStorage.getItem('soramemo.stamp.vibrate')") == '0', '3 OFF にできる（この端末に覚える）')
        await pg.evaluate('window.__netDelay = 0')
        ok(await press(ITM), '3 OFF のあとも印は押せる')
        await pg.wait_for_timeout(2500)
        ok(await pg.evaluate("window.__vib") == 1, '3 OFF なら確定しても振動しない', await pg.evaluate("window.__vibA"))
        ok(await pg.evaluate("window.__vib") == 1, '3 タブの長押し・並べ替えは振動しない（長押しのあとも数は増えていない）')
        allerrs += errs; await b.close()
        # 4 幅ごとのタブ帯
        for w, h in [(390, 844), (375, 667)]:
            b, pg, errs = await page(p, w, h)
            r = await pg.evaluate("""[...document.querySelectorAll('nav.tabs button')].filter(b => !b.hidden && b.offsetParent).map(b => { const s = b.querySelector('span'), r = s.getBoundingClientRect(), br = b.getBoundingClientRect();
              return { t:s.textContent, sw:s.scrollWidth, cw:s.clientWidth, h:r.height, lh:parseFloat(getComputedStyle(s).lineHeight) || parseFloat(getComputedStyle(s).fontSize) * 1.5, fs:parseFloat(getComputedStyle(s).fontSize), out:r.left < br.left - 1 || r.right > br.right + 1 }; })""")
            now = [x for x in r if x['t'] == 'いまの空港']
            ok(len(now) == 1 and all(x['h'] <= x['lh'] * 1.2 for x in r), f'4 {w}：タブの字が1行', r)
            ok(all(not x['out'] for x in r) and all(x['sw'] <= x['cw'] + 1 for x in r), f'4 {w}：タブの字がボタンからはみ出さない', r)
            ok(all(x['fs'] >= 10 for x in r), f'4 {w}：タブの字は 10px 以上（今のタブ帯の大きさのまま）', [x['fs'] for x in r])
            await pg.locator('nav.tabs').screenshot(path=os.path.join(SHOTS, f'04-tabs-{w}.png'))
            await pg.click('nav.tabs button[data-v="ops"]'); await pg.wait_for_timeout(800)
            await pg.screenshot(path=os.path.join(SHOTS, f'05-now-{w}.png'))
            allerrs += errs; await b.close()
    print('errors', fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
