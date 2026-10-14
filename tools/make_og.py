# 公開ページ「空港のいま」を共有したときに出る画像（OGP、1200×630）を空港ごとに作る。
#   python3 tools/make_og.py   → web/og/<IATA>.png
# 滑走路の形は AIP の滑走路の端（src/index.html の OPS_AIRPORTS と同じ値）から描く。文字は Noto Serif/Sans CJK JP（手元にある書体）
import json, math, re, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = __file__.rsplit("/tools/", 1)[0]
# 運用の判定の中心から、空港の名前・中心・滑走路を取り出す（node で ops_core を読む）
js = r'''
import { OPS_AIRPORTS } from "%s/supabase/functions/_shared/ops_core.js";
console.log(JSON.stringify(Object.values(OPS_AIRPORTS).map(d => ({ iata:d.iata, name:d.name, center:d.center, rwy:d.rwy }))));
''' % ROOT
aps = json.loads(subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, check=True).stdout)

SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def font(path, size):
    # .ttc の中の日本語（JP）の書体を選ぶ
    for i in range(10):
        try:
            f = ImageFont.truetype(path, size, index=i)
            if "JP" in f.getname()[0]: return f
        except OSError: break
    return ImageFont.truetype(path, size)

INK, PAPER, SUMI, LINE = (17, 17, 17), (244, 244, 244), (92, 92, 92), (214, 214, 214)
FULL = {"KIX": "関西空港", "NGO": "中部空港"}
for a in aps:
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H - 40], fill=(255, 255, 255))
    name = FULL.get(a["iata"], a["name"] + "空港")
    d.text((90, 92), "そらメモ（非公式）", font=font(SANS, 30), fill=SUMI)
    d.text((90, 150), f"{name}のいま", font=font(SERIF, 84 if len(name) <= 4 else 70), fill=INK)
    d.text((90, 290), "いまの滑走路の使い方（運用）を、", font=font(SANS, 34), fill=INK)
    d.text((90, 340), "風と実際に飛んでいる機体から推定します。", font=font(SANS, 34), fill=INK)
    d.text((90, 500), "soramemo.jp", font=font(SANS, 30), fill=SUMI)
    d.text((90, 540), "推定です。航法には使えません", font=font(SANS, 24), fill=SUMI)
    # 滑走路の形（右側の枠に、北を上にして収める）
    lat0, lon0 = a["center"]; kx = math.cos(math.radians(lat0)) * 111; ky = 111
    pts = [((lo - lon0) * kx, -(la - lat0) * ky) for r in a["rwy"] for (la, lo) in ((r[1], r[2]), (r[5], r[6]))]
    span = max(max(abs(x) for x, _ in pts), max(abs(y) for _, y in pts), 1.6)
    cx, cy, R = 960, 330, 170; s = R / span
    d.ellipse([cx - R - 30, cy - R - 30, cx + R + 30, cy + R + 30], outline=LINE, width=3)
    boxes, ends = [], []
    for r in a["rwy"]:
        x1, y1 = (r[2] - lon0) * kx * s + cx, -(r[1] - lat0) * ky * s + cy
        x2, y2 = (r[6] - lon0) * kx * s + cx, -(r[5] - lat0) * ky * s + cy
        d.line([x1, y1, x2, y2], fill=(28, 43, 74), width=18)
        ends += [(x1, y1, r[0]), (x2, y2, r[4])]
    # 札は線を全部描いてから（線の下に隠れないように）。重なるときは出さない（羽田のように滑走路の端が近い空港）
    for (x, y, t) in ends:
        ux, uy = (x - cx), (y - cy); n = math.hypot(ux, uy) or 1
        bx, by = x + ux / n * 36 - 16, y + uy / n * 36 - 14
        if any(abs(bx - ox) < 46 and abs(by - oy) < 30 for ox, oy in boxes): continue
        boxes.append((bx, by)); d.text((bx, by), t, font=font(SANS, 24), fill=SUMI)
    d.text((cx - R - 20, cy - R - 26), "↑北", font=font(SANS, 22), fill=SUMI)
    im.save(f"{ROOT}/web/og/{a['iata']}.png", optimize=True)
    print(a["iata"], name)
