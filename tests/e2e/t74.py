import os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.abspath(os.path.join(HERE,'..','..','web')); WORK=os.environ.get('SORAMEMO_TEST_WORK','/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
# ホームの搭乗券（3版）：半券は右へ 56px 引けば切れる（半券の真ん中をつかんでも画面の端までに届く）。短く引いたら戻る。
# 下へ引いても切れない。押すだけなら「印をもらいますか」を1回確かめてから切る。半券の上で始めた指ではシートは動かない。
# 最初の位置では、数字の帯の下端がタブ帯の上（小さい・ふつう・大きい画面のどれでも）。半券は琥珀の平らな面
import asyncio, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright
fails = []
def check(label, ok):
    print(label, ok)
    if not ok: fails.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=WEB)); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
async def drag(pg, dx, dy, steps=8):
    await pg.evaluate("$('checkin').disabled = false")   # ログイン前は押せないので、試すときだけ押せるようにする
    r = await pg.evaluate("(() => { const b = $('checkin').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; })()")
    await pg.mouse.move(r[0], r[1]); await pg.mouse.down()
    for k in range(1, steps + 1): await pg.mouse.move(r[0] + dx * k / steps, r[1] + dy * k / steps)
    await pg.mouse.up(); await pg.wait_for_timeout(250)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); errs = []
        for w, h in [(375, 667), (390, 844), (430, 932)]:
            c = await b.new_context(viewport={'width': w, 'height': h}, timezone_id='Asia/Tokyo')
            await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1');")
            pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(1500)
            if not await pg.evaluate("demo"): await pg.evaluate("$('toggleDemo').click(); 0"); await pg.wait_for_timeout(800)   # 範囲の中で試す（デモの空港）
            await pg.evaluate("goTab('home'); window.__ck = 0; window.checkin = async () => { window.__ck++; }; 0"); await pg.wait_for_timeout(700)
            check(f'{w}x{h} 範囲の中の形:', await pg.evaluate("$('bpass').dataset.state") == 'in')
            g = await pg.evaluate("(() => { const s = $('checkin').getBoundingClientRect(), st = $('homeStrip').getBoundingClientRect(), n = document.querySelector('nav.tabs .in').getBoundingClientRect(); return { strip: st.bottom, nav: n.top, right: innerWidth - (s.left + s.width / 2), top: $('homeSheet').getBoundingClientRect().top }; })()")
            check(f'{w}x{h} 数字の帯はタブ帯の上（{round(g["nav"] - g["strip"])}px）:', 0 <= g['nav'] - g['strip'] <= 16)
            if h >= 844: check(f'{w}x{h} 最初の位置で地図は450px以上（{round(g["top"])}px）:', g['top'] >= 450)
            check(f'{w}x{h} 半券の真ん中から画面の端まで56px以上（{round(g["right"])}px）:', g['right'] >= 56)
            await drag(pg, 40, 0)
            check(f'{w}x{h} 右へ40pxでは切れずに戻る:', await pg.evaluate("window.__ck") == 0 and await pg.evaluate("$('checkin').style.transform") == '')
            await drag(pg, 60, 0); await pg.wait_for_timeout(1400)
            check(f'{w}x{h} 真ん中をつかんで右へ60pxで切れる:', await pg.evaluate("window.__ck") == 1)
            top0 = await pg.evaluate("$('homeSheet').getBoundingClientRect().top")
            await drag(pg, 0, 80); await pg.wait_for_timeout(600)
            check(f'{w}x{h} 下へ引いても切れない:', await pg.evaluate("window.__ck") == 1)
            check(f'{w}x{h} 半券の上で引いてもシートは動かない:', abs(await pg.evaluate("$('homeSheet').getBoundingClientRect().top") - top0) < 1)
            r = await pg.evaluate("(() => { const b = document.querySelector('.bp-main').getBoundingClientRect(); return [b.left + 40, b.top + 30]; })()")
            await pg.mouse.move(r[0], r[1]); await pg.mouse.down(); await pg.mouse.move(r[0], r[1] - 60, steps=6); await pg.mouse.up(); await pg.wait_for_timeout(500)
            check(f'{w}x{h} 搭乗券の左の部分でもシートは動かない:', abs(await pg.evaluate("$('homeSheet').getBoundingClientRect().top") - top0) < 1)
            await drag(pg, 0, 0, 1)
            check(f'{w}x{h} 押すだけなら確かめが出る（まだ切らない）:', await pg.evaluate("$('dCkConfirm').open") and await pg.evaluate("window.__ck") == 1)
            await pg.click('#dCkConfirm button[value=no]'); await pg.wait_for_timeout(300)
            check(f'{w}x{h} 「やめる」なら切らない:', not await pg.evaluate("$('dCkConfirm').open") and await pg.evaluate("window.__ck") == 1)
            await drag(pg, 0, 0, 1); await pg.click('#dCkConfirm button[value=yes]'); await pg.wait_for_timeout(1400)
            check(f'{w}x{h} 「印をもらう」で切れる:', await pg.evaluate("window.__ck") == 2)
            if w == 390:
                check('半券は琥珀の平らな面:', await pg.evaluate("getComputedStyle($('checkin')).backgroundColor") == 'rgb(233, 196, 106)'
                      and await pg.evaluate("getComputedStyle($('checkin')).backgroundImage") == 'none')
                await pg.screenshot(path=os.path.join(WORK, 't73_home.png'))
            await c.close()
        check('エラーなし:', not errs)
        if errs: print(errs[:3])
        await b.close()
asyncio.run(main()); srv.shutdown()
if fails: print('FAIL', fails); sys.exit(1)
print('errors []')
