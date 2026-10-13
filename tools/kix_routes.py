# 関西の進入経路・標準到着経路（RNAV STAR）・標準出発経路（RNAV SID）のデータを作る。
# AIP JAPAN の RJBB AD2 の PDF（SWIM の AIP ファイルダウンロードサービス）から読む。
#   python3 tools/kix_routes.py <RJBB__YYYYMMDD.pdf>
# 出力（標準出力の JSON：{"app":…, "star":…, "sid":…}）を src/index.html の KIX_APP・KIX_STAR・KIX_SID に入れる。
# 進入は、進入チャート（RJBB AD2.24-IAC の ILS Z）のフィックスの並びを書き写したもの（AIP が改訂されたら、チャートと見比べて直す）。
import json, math, re, subprocess, sys

pdf = sys.argv[1]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
lay = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout

def deg(s):
    h = s[-1]; s = s[:-1]; k = 3 if h == "E" else 2
    return round(int(s[:k]) + int(s[k:k + 2]) / 60 + float(s[k + 2:]) / 3600, 5)

# フィックスの座標：SID・STAR のチャートの表（「名前 緯度 / 経度」）と、進入チャートの表
C = {}
for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,4})\s+(\d{6}(?:\.\d+)?N)\s*/\s*(\d{7}(?:\.\d+)?E)", lay):
    C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])
for p in raw:
    if "STANDARD ARRIVAL CHART" not in p: continue
    for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,4})\b[^\n0-9]{0,40}?(\d{6}(?:\.\d+)?N)\s*/?\s*(\d{7}(?:\.\d+)?E)", p):
        C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])
F = {"BERRY": "341502.0N 1345631.6E", "ATVID": "341811.4N 1345605.1E", "AVDOX": "341624.1N 1350055.5E", "MIBIB": "341952.4N 1350341.5E",
     "OGABA": "342317.34N 1350845.81E", "OTBON": "342039.2N 1350713.7E", "NOLOP": "342236.58N 1351008.14E",
     "MAYAH": "343623.7N 1351211.0E", "ONEGU": "343614.2N 1352014.2E", "OSNIT": "343611.2N 1352239.8E", "BB452": "343344.3N 1352235.3E",
     "OPARU": "343201.5N 1352147.5E", "AMBER": "342942.2N 1352042.7E", "AMEZY": "342827.29N 1351850.73E", "BEBIL": "343003.98N 1351851.77E"}
for k, v in F.items(): C[k] = [deg(v.split()[0]), deg(v.split()[1])]

# 滑走路の進入端（AD 2.12。src/index.html の OPS_AIRPORTS.KIX と同じ値）
THR = {"06R": (34.417378, 135.229278), "24L": (34.437233, 135.258867), "06L": (34.428572, 135.206203), "24R": (34.451272, 135.240022)}
# 進入（ILS Z）：名前 → [[IAF からの並び]…], IF, FAF, 滑走路
A = {
    "ILS Z 06L": ([["BERRY"], ["ATVID"], ["AVDOX"]], "MIBIB", "OGABA", "06L"),
    "ILS Z 06R": ([["BERRY", "MIBIB"], ["ATVID", "MIBIB"]], "OTBON", "NOLOP", "06R"),
    "ILS Z 24L": ([["MAYAH", "ONEGU", "OSNIT", "BB452", "OPARU"]], "AMBER", "AMEZY", "24L"),
    "ILS Z 24R": ([["MAYAH", "ONEGU", "OSNIT", "BB452"]], "OPARU", "BEBIL", "24R"),
}
R = 3440.065
def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 2 * R * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
def brg(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    y = math.sin(lo2 - lo1) * math.cos(la2); x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360
app = {}
for name, (legs, iff, faf, rw) in A.items():
    t = THR[rw]; opp = {"06R": "24L", "24L": "06R", "06L": "24R", "24R": "06L"}[rw]; h = brg(t, THR[opp])
    # FAF が滑走路の延長線の上にあるか（向きのずれ）を表示する
    print(f"{name}: IF {iff} {dist(C[iff], t):.1f}nm, FAF {faf} {dist(C[faf], t):.1f}nm, 延長線からのずれ {abs((brg(C[faf], t) - h + 540) % 360 - 180):.1f}°", file=sys.stderr)
    seq = legs[0] + [iff, faf]
    br = []
    for l in legs[1:]:
        j = next((i for i, f in enumerate(l) if f in seq), None)
        br.append({"n": l[:j] if j is not None else l, "p": [C[f] for f in (l[:j + 1] if j is not None else l + [iff])]})
    app[name] = {"n": seq, "p": [C[f] for f in seq] + [list(t)], "b": br}

# STAR：「From X, to Y, … to Z.」
S, seen, miss = [], set(), set()
for p in raw:
    if "STANDARD ARRIVAL CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"From ([A-Z]{5}), (to ?[A-Z][A-Z0-9]{4}.*?)\.", flat):
        fx = [m.group(1)] + re.findall(r"(?:\bto ?|, )([A-Z][A-Z0-9]{4})\b", m.group(2))
        if tuple(fx) in seen: continue
        seen.add(tuple(fx))
        if any(f not in C for f in fx): miss.update(f for f in fx if f not in C); continue
        S.append({"from": fx[0], "to": fx[-1], "p": [[*C[f], f] for f in fx]})
if miss: print("STAR の座標が見つからない：", sorted(miss), file=sys.stderr)
print(f"STAR {len(S)}本：" + ", ".join(f"{s['from']}→{s['to']}" for s in S), file=sys.stderr)

# SID（RNAV）：方向ごとに代表の経路を選ぶ（名前は最後のフィックス）。MAIKO は PUNIB 経由のもの
DIR = {"NANKO": "北へ", "SOVRI": "東へ", "MAIKO": "西へ", "OBLUR": "南西へ", "TOMOH": "南へ"}
SID = {}
for p in raw:
    if "STANDARD DEPARTURE CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"RWY ?(\d\d[LR]) : Climb on HDG ?\d+[˚°][^,]*, (.*?)\.(?= |$)", flat):
        fx = re.findall(r"\bto ?([A-Z][A-Z0-9]{4})\b", m.group(2))
        if not fx or fx[-1] not in DIR or fx[-1] in SID.get(m.group(1), {}): continue
        if fx[-1] == "MAIKO" and "PUNIB" not in fx: continue
        if any(f not in C for f in fx): print("SID の座標が見つからない：", [f for f in fx if f not in C], file=sys.stderr); continue
        SID.setdefault(m.group(1), {})[fx[-1]] = {"dir": DIR[fx[-1]], "v": {"A": [[*C[f], f] for f in fx]}}
print("SID：" + ", ".join(f"{r} {sorted(v)}" for r, v in sorted(SID.items())), file=sys.stderr)
json.dump({"app": app, "star": S, "sid": SID}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
