# -*- coding: utf-8 -*-
# 画面案を PNG に撮る（393×852 と 393×667 の2倍。一覧と index は -full も）。13px 未満の字・44px 未満の押す所・はみ出し・字の切れを測る。
# 動き：M1 を R(k, p, d) で1コマずつ止めて撮り、ffmpeg で動画（30コマ／秒）にする。8コマを並べた1枚（連番）も作る。
import os, sys, asyncio, subprocess, shutil
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); PNG = os.path.join(OUT, "png")
os.makedirs(PNG, exist_ok=True)
NAMES = ["H1", "H1n", "H1b", "H1bn", "H2", "H2n", "H2m", "H2mn", "H2d", "H3", "H3n", "H4", "H4n", "H5", "H6", "index"]
FULL = {"H1", "H1n", "H1b", "H1bn", "index"}
CHECK = """() => {
  const small = [], tap = [], cut = [];
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || el.closest('#fly .from')) continue;
    if (!el.childNodes.length || ['STYLE','SCRIPT','svg','path','circle','rect','g'].includes(el.tagName)) continue;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own && parseFloat(cs.fontSize) < 13) small.push(el.tagName + ':' + el.textContent.trim().slice(0, 12) + ':' + cs.fontSize);
    if (cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 1) cut.push(el.textContent.trim().slice(0, 16));
  }
  for (const el of document.querySelectorAll('.ap, .ic, .back, .search, .pillbtn, .fl span, .aprow .pn, .shh button, .tabbar span, .c, .idx li a, .brand span')) {
    const r = el.getBoundingClientRect(); if (r.height && getComputedStyle(el).visibility !== 'hidden' && r.height < 44 && !el.closest('#fly') && !(document.querySelector('#stage.on') && el.closest('#list'))) tap.push(el.className + ':' + el.textContent.trim().slice(0, 10) + ':' + Math.round(r.height));
  }
  return { small, tap, cut, over: document.documentElement.scrollWidth > 393 };
}"""

async def stills(b):
    for h in (852, 667):
        pg = await b.new_page(viewport={"width": 393, "height": h}, device_scale_factor=2)
        for n in NAMES:
            if h == 667 and n == "index": continue
            await pg.goto("file://" + os.path.join(OUT, n + ".html")); await pg.wait_for_timeout(200)
            await pg.screenshot(path=os.path.join(PNG, n + ("" if h == 852 else "-667") + ".png"))
            if h == 852 and n in FULL: await pg.screenshot(path=os.path.join(PNG, n + "-full.png"), full_page=True)
            print(h, n, await pg.evaluate(CHECK))
        await pg.close()

def ease(t): return 1 - (1 - t) ** 3

def timeline():
    # (k, p, d) を1コマずつ。開く 14 コマ（約0.47秒）・止める・左端から引く・離す・地図を開く・戻るで戻る
    fr = []
    hold = lambda k, p, d, n: fr.extend([(k, p, d)] * n)
    hold("rw", 0, 0, 18)
    fr.extend(("rw", ease(i / 14), 0) for i in range(1, 15))
    hold("rw", 1, 0, 24)
    fr.extend(("rw", 1, 0.45 * (i / 12)) for i in range(1, 13))          # 指で引く
    for i in range(1, 13):                                                  # 離す→カードへ縮む
        t = ease(i / 12); fr.append(("rw", 1 - t, 0.45 * (1 - ease(min(1, i / 6)))))
    hold("map", 0, 0, 16)
    fr.extend(("map", ease(i / 14), 0) for i in range(1, 15))
    hold("map", 1, 0, 24)
    fr.extend(("map", 1 - ease(i / 12), 0) for i in range(1, 13))          # 戻るのボタン
    hold("map", 0, 0, 14)
    return fr

async def motion(b, name, suffix):
    tmp = os.path.join(HERE, "_frames" + suffix); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    pg = await b.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=2)
    await pg.goto("file://" + os.path.join(OUT, name + ".html")); await pg.wait_for_timeout(200)
    fr = timeline()
    for i, (k, p, d) in enumerate(fr):
        await pg.evaluate("([k,p,d]) => R(k,p,d)", [k, p, d])
        await pg.screenshot(path=os.path.join(tmp, f"f{i:04d}.png"))
    await pg.close()
    mp4 = os.path.join(PNG, "motion" + suffix + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", os.path.join(tmp, "f%04d.png"), "-vf", "scale=786:-2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", mp4], check=True)
    # 連番：開く途中4コマ＋引いて戻る途中4コマ
    pick = [18, 22, 26, 31, 62, 70, 76, 80]
    files = [os.path.join(tmp, f"f{i:04d}.png") for i in pick]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + sum([["-i", f] for f in files], []) +
                   ["-filter_complex", "".join(f"[{i}]scale=393:-1,pad=405:ih+12:6:6:color=#EEF1F5[a{i}];" for i in range(8)) + "".join(f"[a{i}]" for i in range(8)) + "hstack=inputs=8",
                    os.path.join(PNG, "motion-strip" + suffix + ".png")], check=True)
    shutil.rmtree(tmp)
    print("motion", name, len(fr), "コマ")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        if "--no-still" not in sys.argv: await stills(b)
        if "--no-motion" not in sys.argv:
            await motion(b, "M1", ""); await motion(b, "M1n", "-n")
        await b.close()
asyncio.run(main())
