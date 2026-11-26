# 空港にいるときのホームの半券（11/26 checkin/home-stub・本人「B」・画面案 design/home-airport 案B の B1・B1b・B2・B3）
#   1 判定範囲の中：黒いカードの下に横長の半券（つまみ＋「右へ引いて印をもらう」）。上の行は「いま空港にいます」。はじめての所は「はじめての空港」
#   2 前に来た空港は「○回目の訪問・前回 ○月○日」
#   3 つまみを右へ引くとつまみだけが動き、切れる所で印。押したあと30分は半券の代わりに「本日チェックイン済み ○時○分」
#   4 押すだけでも印にできる（確かめの画面→はい）。キーボード（Enter）でも押せる
#   5 電波がないとき：半券の色を落とし「電波が戻ったら、あとで送ります」
#   6 動きを減らす設定：引いてもつまみは動かず、切れる所で字が「離すとチェックイン」、離すと印
#   7 判定範囲の外は今までの縦の半券のまま
#   8 390／375 で横長の半券の字が1行・はみ出さない・つまみは 44px 以上（写真 docs/pm/shots-home-stub/）
import os, sys, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS=os.path.abspath(os.path.join(HERE,'..','..','docs','pm','shots-home-stub')); os.makedirs(SHOTS, exist_ok=True)
import asyncio
from playwright.async_api import async_playwright
shutil.copy(os.path.join(WEB, 'index.html'), os.path.join(WORK, 'index_homestub_test.html'))
open(os.path.join(WORK, 'config.js'), 'w', encoding='utf-8').write('window.SORAMEMO_CONFIG = { supabaseUrl: "https://fake.supabase.co", supabaseAnonKey: "anon" };')
sys.path.insert(0, HERE); from stamp_perf import GEO
CTS = (42.7752, 141.6923); ITM = (34.7855, 135.4382); FAR = (35.9, 138.6)
fails = []
def ok(cond, msg, extra=''):
    print(('ok   ' if cond else 'FAIL ') + msg + (f'  {extra}' if (extra and not cond) else ''))
    if not cond: fails.append(msg)
async def page(p, w=390, h=844, rm=False, scale=2):
    b = await p.chromium.launch(); c = await b.new_context(viewport={'width':w,'height':h}, device_scale_factor=scale, permissions=['geolocation'], reduced_motion='reduce' if rm else 'no-preference')
    await c.add_init_script("if(!localStorage.getItem('soramemo.onboarded')){ localStorage.setItem('soramemo.persona','all'); localStorage.setItem('soramemo.onboarded','1'); } localStorage.setItem('soramemo.tpTaught','1');" + GEO)
    await c.route('https://cdn.jsdelivr.net/npm/@supabase/**', lambda r: r.fulfill(path=os.path.join(HERE,'fake_sb.js'), content_type='application/javascript'))
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto('file://' + os.path.join(WORK, 'index_homestub_test.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function" && window.__fake'); await pg.wait_for_timeout(500)
    await pg.evaluate('__fake.login()'); await pg.wait_for_function('S.checkins.length >= 1'); await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); __fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); S.checkins.forEach(x => x.t -= 3*36e5)")
    return b, c, pg, errs
async def goto(pg, ll):
    await pg.evaluate(f"document.querySelectorAll('dialog[open]').forEach(d => d.close()); __geo.lat = {ll[0]}; __geo.lon = {ll[1]}; __geo.delay = 50; __geo.acc = 20; HOME_POS = null; POS_LAST = null; GEO_WARM = null; try{{ homeLocStop(); }}catch(e){{}} renderHome()")
    for _ in range(50):
        if await pg.evaluate(f"!!(HOME_NEAR && Math.abs(HOME_NEAR.a.lat - {ll[0]}) < 0.2) || ({ll[0]} === {FAR[0]} && HOME_NEAR && !HOME_NEAR.within)"): break
        await pg.wait_for_timeout(100)
    await pg.wait_for_timeout(300)
async def stamped(pg, n0):
    for _ in range(60):
        if await pg.evaluate("$('dStamp').open") and await pg.evaluate('S.checkins.length') > n0: return True
        await pg.wait_for_timeout(100)
    return False
async def drag(pg, dist, hold=0):
    bx = await pg.locator('#checkin .kn').bounding_box(); x, y = bx['x'] + bx['width']/2, bx['y'] + bx['height']/2
    await pg.mouse.move(x, y); await pg.mouse.down()
    for i in range(1, 11): await pg.mouse.move(x + dist * i / 10, y + 1); await pg.wait_for_timeout(20)
    if hold: await pg.wait_for_timeout(hold)
    return x
ROW = "({ lay: $('bpass').dataset.lay || '', done: $('bpass').dataset.done || '', label: $('nearLabel').textContent, dist: $('nearDist').textContent, rt: $('stubRt').innerText, ckvis: !!$('checkin').offsetHeight, dn: $('bpDone').hidden ? '' : $('bpDone').innerText })"
async def main():
    allerrs = []
    async with async_playwright() as p:
        b, c, pg, errs = await page(p)
        # 7 範囲の外は縦のまま
        await goto(pg, FAR)
        r = await pg.evaluate(ROW)
        ok(r['lay'] == '' and r['ckvis'], '7 判定範囲の外は今までの縦の半券のまま', r)
        # 1 はじめての空港（新千歳）
        await goto(pg, CTS)
        r = await pg.evaluate(ROW)
        ok(r['lay'] == 'row' and r['done'] == '' and r['label'] == 'いま空港にいます', '1 範囲の中は横長の半券・「いま空港にいます」', r)
        ok('はじめての空港' in r['dist'], '1 はじめての所は「はじめての空港」', r['dist'])
        ok('右へ引いて印をもらう' in r['rt'] and '半券を切るとチェックイン' in r['rt'], '1 半券の字「右へ引いて印をもらう／半券を切るとチェックイン」', r['rt'])
        await pg.screenshot(path=os.path.join(SHOTS, '01-first-390.png'))
        # 3 引く：つまみだけ動き、切れる所で印
        n0 = await pg.evaluate('S.checkins.length')
        await drag(pg, 70)
        mid = await pg.evaluate("({ k: getComputedStyle(document.querySelector('#checkin .kn')).transform, b: $('checkin').style.transform })")
        ok(mid['k'] not in ('none', '') and mid['b'] == '', '3 引いている間はつまみだけが右へ動く（半券は傾けない）', mid)
        await pg.screenshot(path=os.path.join(SHOTS, '02-drag-390.png'))
        await pg.mouse.up()
        ok(await stamped(pg, n0), '3 切れる所まで引くと印（ハンコの画面）')
        await pg.wait_for_timeout(800)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); await pg.wait_for_timeout(300)
        r = await pg.evaluate(ROW)
        ok(r['done'] == '1' and not r['ckvis'] and '本日チェックイン済み' in r['dn'] and __import__('re').search(r'\d\d:\d\d', r['dn']), '3 押したあとは「本日チェックイン済み ○時○分」（半券は隠す）', r)
        await pg.screenshot(path=os.path.join(SHOTS, '03-done-390.png'))
        ok(await pg.evaluate("$('bpDone').getAttribute('role')") == 'status', '3 済みの行は role=status')
        # 30分たつと半券に戻る
        await pg.evaluate("S.checkins.forEach(x => x.t -= 31*60e3); __fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 31*60e3).toISOString()); homeState()")
        r = await pg.evaluate(ROW)
        ok(r['done'] == '' and r['ckvis'], '3 30分たつと半券に戻る', r)
        # 2 前に来た空港（伊丹：5日前に来た）
        await pg.evaluate("(() => { const a = A.find(x => x.iata === 'ITM'); const t = Date.now() - 5*864e5; __fake.db.checkins.unshift({airport_id:a.id, terminal_id:null, created_at:new Date(t).toISOString(), accuracy_m:20}); S.checkins.unshift({a:a.id, t, acc:20, term:null}); })()")
        await goto(pg, ITM)
        r = await pg.evaluate(ROW)
        exp = await pg.evaluate("(() => { const d = new Date(Date.now() - 5*864e5 + 9*36e5); return `${d.getUTCMonth()+1}月${d.getUTCDate()}日`; })()")
        ok(r['lay'] == 'row' and '2回目の訪問' in r['dist'] and f'前回 {exp}' in r['dist'], '2 前に来た空港は「2回目の訪問・前回 ○月○日」', r['dist'])
        await pg.screenshot(path=os.path.join(SHOTS, '04-visit-390.png'))
        # 4 押すだけ（確かめの画面→はい）
        await pg.evaluate("S.checkins.forEach(x => x.t -= 3*36e5); __fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); homeState()")
        n0 = await pg.evaluate('S.checkins.length')
        await pg.click('#checkin .rt'); await pg.wait_for_timeout(300)
        ok(await pg.evaluate("$('dCkConfirm').open"), '4 押すだけで確かめの画面が開く')
        yes = pg.locator('#dCkConfirm [value="yes"], #dCkConfirm button:has-text("チェックイン")').first
        await yes.click()
        ok(await stamped(pg, n0), '4 確かめの画面で「はい」→ 印')
        # 4 キーボード
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); S.checkins.forEach(x => x.t -= 3*36e5); __fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); homeState()")
        n0 = await pg.evaluate('S.checkins.length')
        await pg.focus('#checkin'); await pg.keyboard.press('Enter')
        ok(await stamped(pg, n0), '4 キーボード（Enter）でも印')
        # 5 電波がないとき
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close()); S.checkins.forEach(x => x.t -= 3*36e5); __fake.db.checkins.forEach(x => x.created_at = new Date(Date.parse(x.created_at) - 3*36e5).toISOString()); homeState()")
        await pg.evaluate("document.querySelector('#homeSheet .sbody').scrollTop = 0")
        await c.set_offline(True); await pg.wait_for_timeout(400)
        r = await pg.evaluate(ROW); net = await pg.evaluate("$('checkin').classList.contains('net')")
        ok(net and '電波が戻ったら、あとで送ります' in r['rt'], '5 電波がないときは色を落とし「電波が戻ったら、あとで送ります」', r['rt'])
        await pg.screenshot(path=os.path.join(SHOTS, '05-offline-390.png'))
        await c.set_offline(False); await pg.wait_for_timeout(400)
        ok(not await pg.evaluate("$('checkin').classList.contains('net')") and '半券を切るとチェックイン' in (await pg.evaluate(ROW))['rt'], '5 電波が戻ると元の字')
        allerrs += errs; await b.close()
        # 6 動きを減らす設定
        b, c, pg, errs = await page(p, rm=True)
        await goto(pg, CTS)
        n0 = await pg.evaluate('S.checkins.length')
        await drag(pg, 70)
        r = await pg.evaluate("({ k: getComputedStyle(document.querySelector('#checkin .kn')).transform, b: $('checkin').style.transform, t: $('stubRt').firstElementChild.textContent })")
        ok(r['k'] in ('none', '') and r['b'] == '' and r['t'] == '離すとチェックイン', '6 動きを減らす設定：つまみは動かず、字が「離すとチェックイン」', r)
        await pg.mouse.up()
        ok(await stamped(pg, n0), '6 離すと印')
        allerrs += errs; await b.close()
        # 8 幅ごと
        for w, h in [(390, 844), (375, 667)]:
            b, c, pg, errs = await page(p, w, h)
            await goto(pg, CTS)
            r = await pg.evaluate("""(() => { const ck = $('checkin'), k = ck.querySelector('.kn').getBoundingClientRect(), t = ck.querySelector('.rt b'), s = ck.querySelector('.rt small'), cr = ck.getBoundingClientRect(), bp = $('bpass').getBoundingClientRect();
              return { kh: k.height, kw: k.width, tw: t.scrollWidth, tc: t.clientWidth, sh: s.getBoundingClientRect().height, sfs: parseFloat(getComputedStyle(s).fontSize), right: cr.right, bpr: bp.right, vw: document.documentElement.clientWidth, sw: document.documentElement.scrollWidth,
                vis: cr.bottom <= document.querySelector('nav.tabs').getBoundingClientRect().top + 1 }; })()""")
            ok(r['kh'] >= 44 and r['kw'] >= 44, f'8 {w}：つまみは 44px 以上', r)
            ok(r['tw'] <= r['tc'] + 1 and r['sh'] <= r['sfs'] * 1.6 and r['sfs'] >= 12, f'8 {w}：半券の字が1行・12px 以上', r)
            ok(r['sw'] <= r['vw'] and r['right'] <= r['bpr'] + 1, f'8 {w}：横にはみ出さない', r)
            ok(r['vis'], f'8 {w}：最初の位置で半券がタブ帯にかからず見える', r)
            await pg.screenshot(path=os.path.join(SHOTS, f'06-first-{w}.png'))
            allerrs += errs; await b.close()
    print('errors', fails + allerrs)
if __name__ == "__main__": asyncio.run(main())
