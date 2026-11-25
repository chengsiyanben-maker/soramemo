# -*- coding: utf-8 -*-
# 撮影と測定：各画面を 390×844（2倍）と 375×667（1倍）で撮り、一覧の 13 個の動きは「前・途中・後」を止めて撮って横に並べる
# 測るもの：12px 未満の字・44px 未満の押す所・横のはみ出し・コンソールのエラー
import asyncio, os, json
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(HERE); PNG = D + '/png'; TMP = HERE + '/tmp'
os.makedirs(PNG, exist_ok=True); os.makedirs(TMP, exist_ok=True)
URL = 'file://' + D + '/'

MEASURE = r'''(() => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && !e.closest('[hidden]') && +s.opacity !== 0; };
  const small = [], tiny = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (tw.nextNode()) { const n = tw.currentNode; if (!n.textContent.trim()) continue; const e = n.parentElement; if (!vis(e) || e.closest('.toast,.sheet,.scrim')) continue;
    const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 12) small.push(fs + 'px ' + n.textContent.trim().slice(0, 12)); }
  document.querySelectorAll('button,a,[role=switch]').forEach(e => { if (!vis(e) || e.closest('.sheet') || e.closest('.sec')) return; const r = e.getBoundingClientRect();
    if (r.height < 44 - 0.5 || r.width < 44 - 0.5) tiny.push(Math.round(r.width) + 'x' + Math.round(r.height) + ' ' + (e.textContent.trim() || e.getAttribute('aria-label') || e.className).slice(0, 12)); });
  return {small, tiny, over: document.documentElement.scrollWidth - innerWidth};
})()'''

# 一覧の動き：手順（shot は止めた状態を撮る）
S = lambda t: ('shot', t)
STEPS = {
 '01': [S('前'), ('js', "document.querySelector('#m01 .pill').classList.add('is-down')"), ('wait', 30), ('freeze', 60), S('途中 0.06秒'), ('freeze', 120), S('押している間 0.12秒')],
 '02': [S('前'), ('js', "document.querySelectorAll('#m02 .tabs button')[2].click()"), ('wait', 30), ('freeze', 110), S('途中 0.11秒'), ('freeze', 250), S('後 0.25秒')],
 '03': [S('前'), ('js', "document.querySelector('#m03 .sw').click()"), ('wait', 30), ('freeze', 110), S('途中 0.11秒'), ('freeze', 250), S('後 0.25秒')],
 '04': [S('前'), ('js', "document.querySelector('#m04 .pinbtn').click()"), ('wait', 30), ('freeze', 70), S('途中 0.07秒'), ('freeze', 400), S('後 0.4秒')],
 '05': [S('前'), ('js', "document.querySelector('#m05 .pill').click()"), ('wait', 30), ('freeze', 110), S('途中 0.11秒'), ('freeze', 250), S('後 0.25秒')],
 '06': [S('読めた中身'), ('js', "document.querySelector('#m06 .again').click()"), ('wait', 450), ('freeze', 500), S('骨組み（光が流れる）'), ('js', "document.getAnimations().forEach(a=>a.play())"), ('wait', 1300), ('freeze', 120), S('読めた 0.12秒')],
 '07': [S('前'), ('js', "document.querySelector('#m07 .again').click()"), ('wait', 130), ('freeze', 170), S('途中 0.17秒'), ('freeze', 350), S('後 0.35秒')],
 '08': [('js', "n08.dataset.from=0;SM.countUp(n08,41744);SM.grow(b08,84)"), ('wait', 20), ('freeze', 0), ('wait', 80), S('開いた瞬間'), ('freeze', 160), ('wait', 80), S('途中 0.16秒'), ('freeze', 400), ('wait', 80), S('後 0.4秒')],
 '09': [S('前'), ('js', "SM.sortDemo(s09,1)"), ('wait', 30), ('freeze', 150), S('つかむ 0.15秒'), ('js', "SM.sortDemo(s09,2)"), ('wait', 30), ('freeze', 250), S('上へ動かす')],
 '10': [S('前'), ('js', "document.querySelector('#m10 .copy').click()"), ('wait', 30), ('freeze', 70), S('途中 0.07秒'), ('freeze', 250), S('後 0.15秒')],
 '11': [S('前'), ('js', "document.querySelector('#m11 .bell').click()"), ('wait', 30), ('freeze', 80), S('揺れ 0.08秒'), ('freeze', 180), S('揺れ 0.18秒')],
 '12': [S('前'), ('js', "document.querySelector('#m12 .retry').click()"), ('wait', 30), ('freeze', 250), S('回る 0.25秒'), ('js', "document.getAnimations().forEach(a=>a.play())"), ('wait', 900), S('読めた')],
 '13': [S('前'), ('js', "document.querySelector('#m13 [data-sheet-open]').click()"), ('wait', 30), ('freeze', 140), S('途中 0.14秒'), ('freeze', 300), S('後 0.3秒')],
}

def font(sz):
    for f in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    import glob
    g = glob.glob('/usr/share/fonts/**/*CJK*.tt*', recursive=True) + glob.glob('/usr/share/fonts/**/*Gothic*.tt*', recursive=True)
    return ImageFont.truetype(g[0], sz) if g else ImageFont.load_default()

def strip(files, labels, out, night=False):
    ims = [Image.open(f) for f in files]
    w = max(i.width for i in ims); h = max(i.height for i in ims); pad = 24; lab = 56
    bg = (15, 20, 27) if night else (244, 245, 247); fg = (174, 185, 198) if night else (100, 107, 120)
    W = pad + len(ims) * (w + pad); H = lab + h + pad
    S2 = Image.new('RGB', (W, H), bg); dr = ImageDraw.Draw(S2); f = font(26)
    for k, (im, lb) in enumerate(zip(ims, labels)):
        x = pad + k * (w + pad); S2.paste(im, (x, lab)); dr.text((x + 4, 14), lb, fill=fg, font=f)
        if k < len(ims) - 1: dr.text((x + w + 2, lab + h // 2 - 16), '›', fill=fg, font=f)
    S2.save(out)

async def run_steps(pg, no, night):
    files, labels = [], []
    el = pg.locator('#m%s .stage' % no)
    await el.scroll_into_view_if_needed(); await pg.wait_for_timeout(100)
    for st in STEPS[no]:
        if st[0] == 'js': await pg.evaluate(st[1])
        elif st[0] == 'wait': await pg.wait_for_timeout(st[1])
        elif st[0] == 'freeze': await pg.evaluate('__freeze(%d)' % st[1]); await pg.wait_for_timeout(40)
        elif st[0] == 'shot':
            f = '%s/m%s-%d%s.png' % (TMP, no, len(files), '-n' if night else ''); await el.screenshot(path=f, animations='allow'); files.append(f); labels.append(st[1])
    strip(files, labels, '%s/m%s%s.png' % (PNG, no, '-n' if night else ''), night)

SCREENS = {
 's1-home': [('', None), ('-roll', "document.querySelectorAll('.demo button')[0].click()", 200), ('-sheet', "document.querySelectorAll('.demo button')[1].click()", 450), ('-toast', "document.querySelectorAll('.demo button')[2].click()", 400)],
 's2-airport': [('', None), ('-pin', "document.querySelector('.pinbtn').click()", 600), ('-bell', "document.querySelector('.bell').click();document.querySelector('.copy').click()", 600)],
 's3-ops': [('', None), ('-skel', "SM.loadInto(document.getElementById('bd'),5000)", 700), ('-sort', "document.getElementById('sortArea').hidden=false;SM.sortDemo(s3sort,2)", 500), ('-retry', "document.querySelector('.retry').click()", 900)],
 's4-edit': [('', None), ('-lift', "SM.sortDemo(s4sort,2)", 400), ('-toast', "document.querySelectorAll('.sw')[3].click();SM.toast(document.body,'表示を保存しました')", 450)],
 's5-shugyo': [('', None)],
}

async def main():
    report = {}; errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 画面ごと
        for name, states in SCREENS.items():
            for night in (False, True):
                if night and name not in ('s1-home', 's4-edit', 's3-ops'): continue
                for (w, h, dpr, sfx) in ((390, 844, 2, ''), (375, 667, 1, '-667')):
                    if sfx and night: continue
                    for st in states:
                        if sfx and st[0]: continue
                        pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
                        pg.on('pageerror', lambda e: errors.append(str(e)))
                        await pg.goto(URL + name + '.html' + ('?night=1' if night else '')); await pg.wait_for_timeout(900)
                        if st[1]: await pg.evaluate(st[1]); await pg.wait_for_timeout(st[2])
                        if not st[0]: report['%s%s%s' % (name, sfx, '-n' if night else '')] = await pg.evaluate(MEASURE)
                        await pg.screenshot(path='%s/%s%s%s%s.png' % (PNG, name, st[0], '-n' if night else '', sfx))
                        await pg.close()
        # 一覧（全体）と動きの連番
        for night in (False, True):
            for (w, h, dpr, sfx) in ((390, 844, 2, ''), (375, 667, 1, '-667')):
                if sfx and night: continue
                pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
                pg.on('pageerror', lambda e: errors.append(str(e)))
                await pg.goto(URL + 'index.html' + ('?night=1' if night else '')); await pg.wait_for_timeout(700)
                report['index%s%s' % (sfx, '-n' if night else '')] = await pg.evaluate(MEASURE)
                await pg.screenshot(path='%s/index%s%s-full.png' % (PNG, '-n' if night else '', sfx), full_page=True)
                await pg.close()
            for no in STEPS:
                pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
                pg.on('pageerror', lambda e: errors.append(str(e)))
                await pg.goto(URL + 'index.html' + ('?night=1' if night else '')); await pg.wait_for_timeout(600)
                await run_steps(pg, no, night); await pg.close()
        # 動きを減らす：骨組みの光と札が動かないこと
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
        await pg.goto(URL + 'index.html'); await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('#m06 .again').click()"); await pg.wait_for_timeout(500)
        report['reduce'] = await pg.evaluate("({anims: document.getAnimations().filter(a=>a.playState==='running').length})")
        await b.close()
    report['errors'] = errors
    json.dump(report, open(HERE + '/measure.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in report.items():
        if isinstance(v, dict) and 'small' in v: print(k, '12px未満', len(v['small']), '44未満', len(v['tiny']), 'はみ出し', v['over'], v['small'][:3], v['tiny'][:4])
        else: print(k, v)
asyncio.run(main())
