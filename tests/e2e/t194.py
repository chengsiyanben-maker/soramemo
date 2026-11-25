# 小さな動き（11/25 本人 OK「全部」・見本 design/micro・checkin/micro）
#   02 タブの点がすべる・05 下から出る札（「できた」だけ・2 秒で消える・エラーは字のまま）・06 骨組み（0.3 秒より早ければ出ない）
#   07 数字の繰り上がり＋1・09 並べ替え（持ち上がる・保存・札）・10 コピーが ✓・12 もう一度の矢印・13 シートが上がる
#   動きを減らす設定では、状態は変わるが動いているものが 0
import os, sys, asyncio
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.abspath(os.path.join(HERE, '..', '..', 'web'))
WORK = os.environ.get('SORAMEMO_TEST_WORK', '/tmp/soramemo-e2e'); os.makedirs(WORK, exist_ok=True)
SHOTS = os.path.join(WORK, 't194'); os.makedirs(SHOTS, exist_ok=True)
sys.path.insert(0, HERE); from keepls import goto_http
from playwright.async_api import async_playwright

fails = []
def check(name, cond, detail=''):
    print(('OK  ' if cond else 'NG  ') + name + (('  ' + str(detail)) if detail != '' else ''))
    if not cond: fails.append(name)

# 動いているもの（CSS の animation・transition と Web Animations）。無限の光（骨組み）も数える
RUNNING = "() => document.getAnimations().filter(a => a.playState === 'running').map(a => a.animationName || a.transitionProperty || (a.effect && a.effect.target && a.effect.target.className) || 'js')"

async def newpage(b, w, h, rm=False):
    c = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, timezone_id='Asia/Tokyo', reduced_motion='reduce' if rm else 'no-preference')
    await c.grant_permissions(['clipboard-read', 'clipboard-write'])
    await c.route('**/web/config.js', lambda r: r.fulfill(body='window.SORAMEMO_CONFIG = {};', content_type='application/javascript'))
    await c.add_init_script("localStorage.setItem('soramemo.onboarded','1'); localStorage.setItem('soramemo.install.later','1'); localStorage.setItem('soramemo.zk.swipe','1');")
    pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    await goto_http(pg, os.path.join(WEB, 'index.html')); await pg.wait_for_function('document.readyState === "complete" && typeof render === "function"'); await pg.wait_for_timeout(600)
    return c, pg, errs

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w, h in ((390, 844), (375, 667)):
            c, pg, errs = await newpage(b, w, h)
            await pg.evaluate('openMyPage("adv")'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(700); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); await pg.wait_for_timeout(300)
            # ---- 02 タブの点 ----
            await pg.click('nav.tabs button[data-v="book"]'); await pg.wait_for_timeout(400)
            d = await pg.evaluate("""() => { const n = document.querySelector('nav.tabs'), d = n.querySelector('.mxdot'), b = n.querySelector('button[aria-current="page"]');
              const dr = d.getBoundingClientRect(), br = b.getBoundingClientRect();
              return { on: n.classList.contains('mxdot-on'), dx: Math.abs((dr.left + dr.width / 2) - (br.left + br.width / 2)), v: b.dataset.v,
                before: getComputedStyle(b, '::before').opacity }; }""")
            check(f'{w} 02 点は押したタブ（図鑑）の真下・元の点は隠す', d['on'] and d['dx'] < 1.5 and d['v'] == 'book' and d['before'] == '0', d)
            moving = await pg.evaluate("""async () => { document.querySelector('nav.tabs button[data-v="log"]').click(); await new Promise(r => setTimeout(r, 60));
              return document.getAnimations().some(a => a.transitionProperty === 'transform' && a.effect.target.classList.contains('mxdot')); }""")
            check(f'{w} 02 点はすべって動く', moving)
            await pg.click('nav.tabs button[data-v="home"]'); await pg.wait_for_timeout(500)
            # ---- 07 数字の繰り上がり：1回押す ----
            await pg.select_option('#demoAirport', 't:HND-T1'); await pg.press('#checkin', 'Enter'); await pg.wait_for_timeout(150)
            r = await pg.evaluate("() => ({ hs: $('hsToday').textContent, up: $('hsToday').classList.contains('mxup'), plus: [...document.querySelectorAll('#homeStrip .mxplus')].map(x => x.textContent) })")
            check(f'{w} 07 今日の印は 1 に繰り上がり、「+1」が出る', r['hs'] == '1' and r['up'] and '+1' in r['plus'], r)
            await pg.wait_for_timeout(1400)
            check(f'{w} 07 「+1」は消える', await pg.evaluate("document.querySelectorAll('#homeStrip .mxplus').length") == 0)
            await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); await pg.wait_for_timeout(300)
            # ---- 05 下から出る札 ----
            await pg.evaluate("say('記録を消しました。')"); await pg.wait_for_timeout(350)
            t = await pg.evaluate("""() => { const t = document.querySelector('.mxtoast'), r = t && t.getBoundingClientRect(), nav = document.querySelector('nav.tabs .in').getBoundingClientRect();
              return { show: !!t && t.classList.contains('show'), text: t && t.innerText, msg: $('msg').textContent, hidden: $('msg').classList.contains('mxsr'),
                above: !!r && r.bottom <= nav.top, inside: !!r && r.left >= 0 && r.right <= innerWidth }; }""")
            check(f'{w} 05 「できた」は札で出す（字は読み上げ用に残す・タブ帯の上・はみ出さない）', t['show'] and t['text'] == '記録を消しました。' and t['msg'] == '記録を消しました。' and t['hidden'] and t['above'] and t['inside'], t)
            await pg.screenshot(path=os.path.join(SHOTS, f'toast-{w}.png'))
            await pg.wait_for_timeout(2000)
            check(f'{w} 05 札は2秒で下がる', not await pg.evaluate("document.querySelector('.mxtoast').classList.contains('show')"))
            await pg.evaluate("say('位置を取得できませんでした。電波のよい場所でもう一度押してください。', true)"); await pg.wait_for_timeout(300)
            e = await pg.evaluate("() => ({ show: document.querySelector('.mxtoast').classList.contains('show'), vis: !$('msg').classList.contains('mxsr') && $('msg').getBoundingClientRect().height > 10 })")
            check(f'{w} 05 エラーは札にせず画面の字のまま', not e['show'] and e['vis'], e)
            await pg.evaluate("say('サーバーで判定しています…')"); await pg.wait_for_timeout(100)
            check(f'{w} 05 途中の知らせ（…）は札にしない', not await pg.evaluate("document.querySelector('.mxtoast').classList.contains('show')"))
            # ---- 06 骨組み ----
            sk = await pg.evaluate("""async () => { const box = document.createElement('div'); document.body.appendChild(box);
              const seen = []; box.innerHTML = mxSkel(3); for(let i = 0; i < 4; i++){ await new Promise(r => setTimeout(r, 50)); seen.push(+getComputedStyle(box.firstChild).opacity); }
              box.innerHTML = '<p>中身</p>'; const fast = seen.every(o => o === 0);
              box.innerHTML = mxSkel(3); await new Promise(r => setTimeout(r, 450)); const slow = +getComputedStyle(box.firstChild).opacity;
              const shine = document.getAnimations().some(a => a.animationName === 'mxShine'); box.remove(); return { fast, seen, slow, shine }; }""")
            check(f'{w} 06 0.3 秒より早く読めたら骨組みは出ない', sk['fast'], sk['seen'])
            check(f'{w} 06 遅いときは骨組みが出て光る', sk['slow'] == 1 and sk['shine'], sk)
            # ---- 10 コピー ----
            cp = await pg.evaluate("""async () => { const box = document.createElement('p'); box.innerHTML = 'JA8089' + mxCopyHTML('JA8089'); document.body.appendChild(box);
              const b = box.querySelector('.mxcopy'); b.click(); await new Promise(r => setTimeout(r, 300));
              const clip = await navigator.clipboard.readText().catch(() => ''), done = b.classList.contains('done'), lab = b.getAttribute('aria-label');
              const toast = document.querySelector('.mxtoast.show'), tt = toast && toast.innerText; const size = b.getBoundingClientRect();
              await new Promise(r => setTimeout(r, 1400)); const back = !b.classList.contains('done') && b.getAttribute('aria-label') === 'JA8089をコピー'; box.remove();
              return { clip, done, lab, tt, back, w: size.width, h: size.height }; }""")
            check(f'{w} 10 コピーで ✓・札・1.5 秒で戻る・押せる所 44px', cp['clip'] == 'JA8089' and cp['done'] and cp['lab'] == 'コピーしました' and cp['tt'] == 'コピーしました' and cp['back'] and cp['w'] >= 44 and cp['h'] >= 44, cp)
            # ---- 12 もう一度 ----
            rt = await pg.evaluate("""async () => { const box = document.createElement('div'); box.id = 'opsStrip_t'; box.innerHTML = opsFailHTML('', false); document.body.appendChild(box);
              const b = box.querySelector('.opsretry'); mxRetryBox(box); await new Promise(r => setTimeout(r, 100));
              const spin = document.getAnimations().some(a => a.animationName === 'mxSpin'), txt = box.innerText; box.remove(); return { spin, txt, svg: !!b.querySelector('svg') }; }""")
            check(f'{w} 12 「もう一度」は矢印が回り、その場で「読み込んでいます…」', rt['spin'] and rt['svg'] and '読み込んでいます' in rt['txt'], rt)
            # ---- 09 並べ替え（持ち上がる・ほかが動く・保存・札） ----
            await pg.evaluate("""() => { const box = document.createElement('div'); box.id = 'roT'; box.style.cssText = 'position:fixed;left:16px;right:16px;top:120px;z-index:99;background:#fff';
              box.innerHTML = ['a','b','c','d'].map(x => `<div data-ro="${x}" style="display:flex;align-items:center;height:60px;margin:0 0 10px;background:#eee;border-radius:16px"><b style="flex:1">${x}</b><button type="button" class="roh" data-ro-h="${x}" style="width:44px;height:44px">≡</button></div>`).join('');
              document.body.appendChild(box); window.__ro = null; roBind(box, { done: o => { window.__ro = o.join(''); }, name: x => x }); }""")
            hb = await pg.locator('#roT [data-ro-h="a"]').bounding_box()
            await pg.mouse.move(hb['x'] + 22, hb['y'] + 22); await pg.mouse.down(); await pg.wait_for_timeout(50)
            await pg.mouse.move(hb['x'] + 22, hb['y'] + 22 + 75, steps=6); await pg.wait_for_timeout(40)
            lift = await pg.evaluate("""() => { const el = document.querySelector('#roT [data-ro="a"]');
              return { lift: el.classList.contains('rodrag'), scale: getComputedStyle(el).scale, flip: document.getAnimations().some(a => !a.animationName && !a.transitionProperty && a.effect && a.effect.target && a.effect.target.dataset && a.effect.target.dataset.ro) }; }""")
            await pg.mouse.move(hb['x'] + 22, hb['y'] + 22 + 150, steps=6); await pg.mouse.up(); await pg.wait_for_timeout(300)
            so = await pg.evaluate("() => ({ order: [...document.querySelectorAll('#roT [data-ro]')].map(x => x.dataset.ro).join(''), saved: window.__ro, toast: (document.querySelector('.mxtoast.show') || {}).innerText })")
            check(f'{w} 09 持った行は持ち上がり（1.02 倍）、ほかの行はすっと場所をあける', lift['lift'] and lift['scale'] == '1.02' and lift['flip'], lift)
            check(f'{w} 09 離すと並びを保存し「並びを保存しました」', so['order'] != 'abcd' and so['saved'] == so['order'] and so['toast'] == '並びを保存しました', so)
            await pg.evaluate("document.getElementById('roT').remove()")
            # ---- 13 シートが上がる ----
            sh = await pg.evaluate("""async () => { openTabPicker('test'); await new Promise(r => setTimeout(r, 60));
              const a = document.getAnimations().find(x => x.animationName === 'mxSheet'), y = $('dTabs').getBoundingClientRect().top;
              await new Promise(r => setTimeout(r, 400)); const y2 = $('dTabs').getBoundingClientRect().top; $('dTabs').close(); return { anim: !!a, mid: y, end: y2, dur: a ? a.effect.getTiming().duration : 0 }; }""")
            check(f'{w} 13 シートは下から 0.3 秒で上がり、行き過ぎない', sh['anim'] and sh['dur'] == 300 and sh['mid'] > sh['end'], sh)
            await pg.wait_for_timeout(300)
            if w == 390:
                await pg.evaluate("say('並びを保存しました。')"); await pg.wait_for_timeout(350)
                await pg.screenshot(path=os.path.join(SHOTS, 'home-toast-390.png'))
            check(f'{w} エラーなし', not errs, errs)
            await c.close()
        # ---- 動きを減らす設定：状態は変わるが、動いているものが 0 ----
        c, pg, errs = await newpage(b, 390, 844, rm=True)
        await pg.evaluate('openMyPage("adv")'); await pg.click('#toggleDemo'); await pg.wait_for_timeout(700); await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())"); await pg.wait_for_timeout(300)
        await pg.click('nav.tabs button[data-v="book"]'); await pg.wait_for_timeout(30)
        r1 = await pg.evaluate(RUNNING)
        dot = await pg.evaluate("""() => { const d = document.querySelector('nav.tabs .mxdot'), b = document.querySelector('nav.tabs button[aria-current="page"]'), dr = d.getBoundingClientRect(), br = b.getBoundingClientRect(); return Math.abs((dr.left + dr.width / 2) - (br.left + br.width / 2)); }""")
        await pg.click('nav.tabs button[data-v="home"]'); await pg.wait_for_timeout(300)
        await pg.select_option('#demoAirport', 't:HND-T1'); await pg.press('#checkin', 'Enter'); await pg.wait_for_timeout(120)
        await pg.evaluate("document.querySelectorAll('dialog[open]').forEach(d => d.close())")
        r2 = await pg.evaluate("""async () => { say('記録を消しました。'); const box = document.createElement('div'); box.innerHTML = mxSkel(3) + opsFailHTML('', false); document.body.appendChild(box);
          mxRetryBox(box); openTabPicker('test'); await new Promise(r => setTimeout(r, 450));
          const run = (""" + RUNNING + """)(), toast = document.querySelector('.mxtoast').classList.contains('show'), skel = +getComputedStyle(box.querySelector('.mxskel')).opacity;
          const sheet = $('dTabs').open; $('dTabs').close(); box.remove(); return { run, toast, skel, sheet }; }""")
        check('動きを減らす：タブの点は動かずに押したタブの下', not r1 and dot < 1.5, (r1, dot))
        check('動きを減らす：札・骨組み・シートは状態だけ変わる（出る・開く）', r2['toast'] and r2['skel'] == 1 and r2['sheet'], r2)
        check('動きを減らす：骨組みの読み込み中・札・シート・もう一度で動いているものが 0', not r2['run'], r2['run'])
        check('動きを減らす：エラーなし', not errs, errs)
        await c.close(); await b.close()
    print('errors:', fails)

asyncio.run(main())
