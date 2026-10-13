# 成田の進入経路と標準到着経路（RNAV STAR）のデータを作る。AIP JAPAN の RJAA AD2 の PDF（SWIM の AIP ファイルダウンロードサービス）から読む。
#   python3 tools/nrt_routes.py <RJAA__YYYYMMDD.pdf>
# 出力（標準出力の JSON：{"app":…, "star":…}）を src/index.html の NRT_APP・NRT_STAR に入れる。
# 進入は、進入チャート（RJAA AD2.24-IAC）のフィックスの並びを書き写したもの（AIP が改訂されたら、チャートと見比べて直す）。
# 実行すると、IF・FAF が滑走路の延長線上の正しい距離にあるかを表示する（チャートの NM to THR と比べる）。
import json, math, re, subprocess, sys

pdf = sys.argv[1]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")

def deg(s):
    h = s[-1]; s = s[:-1]; k = 3 if h == "E" else 2
    return round(int(s[:k]) + int(s[k:k + 2]) / 60 + float(s[k + 2:]) / 3600, 5)

# STAR のフィックスの座標（STAR のチャートの表から）
C = {}
for p in raw:
    if "STANDARD ARRIVAL CHART" not in p: continue
    for m in re.finditer(r"\b([A-Z][A-Z0-9]{4})\b[^\n0-9]{0,40}?(\d{6}(?:\.\d+)?N)\s*/?\s*(\d{7}(?:\.\d+)?E)", p):
        C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])

# 進入チャートのフィックス（各チャートの表の値）
F = {"ELGAR": "353129.2N 1404527.4E", "TYLER": "352650.5N 1403807.8E", "HARPS": "352757.7N 1404015.2E", "GIINA": "353120.7N 1403259.2E",
     "UGVIN": "353436.16N 1403038.77E", "FIONA": "352845.7N 1404126.0E", "TEMIS": "353201.7N 1403424.8E", "LAPIS": "353437.27N 1403233.16E",
     "NORMA": "355900.8N 1403254.0E", "GEMIN": "355738.6N 1402450.7E", "CURIO": "355949.2N 1402655.1E", "GLARE": "360047.8N 1401937.3E",
     "KONAN": "355758.8N 1401345.0E", "TENAG": "355323.17N 1401705.07E", "AMITY": "355818.3N 1401526.5E", "BIRDY": "355236.92N 1401934.27E"}
F = {k: [deg(v.split()[0]), deg(v.split()[1])] for k, v in F.items()}
for k, v in F.items(): C.setdefault(k, v)

# 滑走路の進入端（AD 2.12。src/index.html の OPS_AIRPORTS.NRT と同じ値）
THR = {"16R": (35.774389, 140.368292), "34L": (35.743322, 140.390739), "16L": (35.8052, 140.378108), "34R": (35.785783, 140.392144)}
# 進入：名前 → [[IAF から IF までの並び]…], IF, FAF, 滑走路, チャートの NM to THR（IF, FAF）
A = {
    "ILS 34L":   ([["ELGAR", "HARPS"], ["TYLER"]], "GIINA", "UGVIN", "34L", (15.4, 11.6)),
    "ILS Z 34R": ([["ELGAR", "FIONA"], ["TYLER"]], "TEMIS", "LAPIS", "34R", (17.5, 14.5)),
    "ILS Y 16R": ([["NORMA", "CURIO", "GLARE"], ["GEMIN", "CURIO", "GLARE"]], "KONAN", "TENAG", "16R", (13.4, 8.0)),
    "ILS Y 16L": ([["NORMA", "CURIO", "GLARE"], ["GEMIN", "CURIO", "GLARE"]], "AMITY", "BIRDY", "16L", (11.6, 5.0)),
}
R = 3440.065
def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 2 * R * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
app = {}
for name, (legs, iff, faf, rw, (dif, dfaf)) in A.items():
    t = THR[rw]
    print(f"{name}: IF {iff} {dist(C[iff], t):.1f}nm（チャート {dif}）, FAF {faf} {dist(C[faf], t):.1f}nm（チャート {dfaf}）", file=sys.stderr)
    # 地図では、いちばん長い並び（最初の並び）を1本の線にする。ほかの IAF は点で出す
    seq = legs[0] + [iff, faf]
    # 2本目以降の並び（別の IAF から）は、本線に合流するところまでを枝（b）として持つ
    br = []
    for l in legs[1:]:
        j = next((i for i, f in enumerate(l) if f in seq), None)
        br.append({"n": l[:j] if j is not None else l, "p": [C[f] for f in (l[:j + 1] if j is not None else l + [iff])]})
    app[name] = {"n": seq, "p": [C[f] for f in seq] + [list(t)], "b": br}

# STAR：「From X, to Y, … to Z.」を読む
S, seen, miss = [], set(), set()
for p in raw:
    if "STANDARD ARRIVAL CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"From ([A-Z]{5}), (to ?[A-Z][A-Z0-9]{4}.*?)\.", flat):
        fx = [m.group(1)] + re.findall(r"\bto ?([A-Z][A-Z0-9]{4})\b", m.group(2))
        k = tuple(fx)
        if k in seen: continue
        seen.add(k)
        if any(f not in C for f in fx): miss.update(f for f in fx if f not in C); continue
        S.append({"from": fx[0], "to": fx[-1], "p": [[*C[f], f] for f in fx]})
if miss: print("座標が見つからない：", sorted(miss), file=sys.stderr)
print(f"STAR {len(S)}本：" + ", ".join(f"{s['from']}→{s['to']}" for s in S), file=sys.stderr)
json.dump({"app": app, "star": S}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
