# 中部・仙台・広島・松山・熊本・長崎・鹿児島の進入経路・標準到着経路（RNAV STAR）・標準出発経路（RNAV SID）のデータを作る。
# AIP JAPAN（2026年10月1日版）の AD2 の PDF と、ENR の PDF（ENR 4.4 のフィックスの座標表。STAR・SID の途中の点の多くは AD2 に座標がない）から読む。
#   python3 tools/ap_routes2.py <ICAO> <ICAO__YYYYMMDD.pdf> <ENR_YYYYMMDD.pdf>
# 出力（標準出力の JSON：{"app":…, "star":…, "sid":…}）を src/index.html の <IATA>_RT に入れる。
# 進入は、進入チャート（AD2.24-IAC）の IAF・IF・FAF の名前を書き写し、座標は AD2 か ENR の表から取る（AIP が改訂されたら、チャートと見比べて直す）。
# SID は、チャートの説明文（RWY xx : Climb on HDG …, to A, to B.）の点を、座標がそろうものだけ全部入れる。
import json, math, re, subprocess, sys

icao, pdf, enr = sys.argv[1], sys.argv[2], sys.argv[3]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
lay = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
enl = subprocess.run(["pdftotext", "-layout", enr, "-"], capture_output=True, text=True).stdout.split("\n")

def deg(s):
    h = s[-1]; s = s[:-1]; k = 3 if h == "E" else 2
    return round(int(s[:k]) + int(s[k:k + 2]) / 60 + float(s[k + 2:]) / 3600, 5)
R = 3440.065
def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 2 * R * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
def brg(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    y = math.sin(lo2 - lo1) * math.cos(la2); x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# ENR のフィックスの表：名前・緯度・経度が、前後2行の中に別々に書かれている。近いものから1つずつ組にする
names, Ns, Es = [], [], []
for i, l in enumerate(enl):
    m = re.match(r"^\s*△?\s+([A-Z]{5})\s", l + " ")
    if m: names.append((i, m.group(1)))
    Ns += [(i, m.group(1)) for m in re.finditer(r"(?<![0-9])(\d{6}\.\d+N)\b", l)]
    Es += [(i, m.group(1)) for m in re.finditer(r"(?<![0-9])(\d{7}\.\d+E)\b", l)]
def pair(coords):
    ps = sorted((abs(ci - ni), k, j) for k, (ni, _) in enumerate(names) for j, (ci, _) in enumerate(coords) if abs(ci - ni) <= 2)
    un, uc, out = set(), set(), {}
    for _, k, j in ps:
        if k in un or j in uc: continue
        un.add(k); uc.add(j); out[k] = coords[j][1]
    return out
an, ae = pair(Ns), pair(Es)
C = {}
for k, (_, n) in enumerate(names):
    if k in an and k in ae: C.setdefault(n, [deg(an[k]), deg(ae[k])])
# AD2 のチャートの座標（同じ名前は AD2 を優先）
for txt in (lay, "\n".join(raw)):
    for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,4})\s*(?:\((?:IAF|IF|FAF|IAF/IF|IF/IAF|FAP)\))?\s*(?:\([A-Z/]+\)\s*)?[:：]?\s*(\d{6}(?:\.\d+)?N)\s*/?\s*(\d{7}(?:\.\d+)?E)", txt):
        C[m.group(1)] = [deg(m.group(2)), deg(m.group(3))]

# 空港ごとの設定。THR：滑走路の進入端（AD 2.12。src/index.html の OPS_AIRPORTS と同じ値）
# A：進入名 → (IAF からの並び（最初が本線、ほかは IF に合流する枝）, IF, FAF, 滑走路)。RF（円弧）の進入は、点だけでは形が分からないので入れない
CFG = {
  "RJGG": dict(THR={"18": (34.873892, 136.801675), "36": (34.842942, 136.809114)},
    A={"ILS Z 36": ([[]], "PROBE", "WILBA", "36"), "ILS Z 18": ([[]], "QUEST", "ORVIL", "18")}),
  "RJSS": dict(THR={"09": (38.138772, 140.898722), "27": (38.142272, 140.932656)},
    A={"ILS 27": ([["SNOOK"]], "OVRID", "SEKMO", "27"), "RNP 09": ([["ALDOG"]], "TILES", "SUGOH", "09")}),
  "RJOA": dict(THR={"10": (34.436025, 132.903125), "28": (34.436025, 132.935764)},
    A={"ILS Z 10": ([[]], "MISEN", "MACKY", "10"), "RNP 28": ([[]], "VISTA", "BUENA", "28")}),
  "RJOM": dict(THR={"14": (33.834583, 132.689369), "32": (33.819931, 132.709892)},
    A={"ILS Z 14": ([[]], "ROBIN", "MIKAS", "14")}),   # RNP 32 は RF（円弧）で回り込むため、線は入れない（最終進入の直線で出す）
  "RJFT": dict(THR={"07": (32.831514, 130.840581), "25": (32.843122, 130.869522)},
    A={"ILS 07": ([[]], "MISMI", "HINOK", "07")}),   # RNP 25 は RF（円弧）で回り込むため、線は入れない
  "RJFU": dict(THR={"14": (32.927022, 129.902714), "32": (32.906919, 129.924178)},
    A={"ILS Z 32": ([[]], "FUBKI", "CHARA", "32"), "RNP 14": ([["SARUK"], ["IORIE"]], "TENBO", "NODEP", "14")}),
  "RJFK": dict(THR={"16": (31.815114, 130.711483), "34": (31.791686, 130.727328)},
    A={"ILS Z 34": ([["ZAIHO"]], "SIMAZ", "RYUMO", "34"), "RNP 16": ([["OGOJO"], ["OIDON"], ["YUKSA"]], "WAZZE", "YUSUI", "16")}),
}[icao]
THR = CFG["THR"]; OPP = dict(zip(THR, reversed(list(THR))))

app = {}
for name, (legs, iff, faf, rw) in CFG["A"].items():
    t = THR[rw]; h = brg(t, THR[OPP[rw]])
    print(f"{name}: IF {iff} {dist(C[iff], t):.1f}nm, FAF {faf} {dist(C[faf], t):.1f}nm, 延長線からのずれ FAF {abs((brg(C[faf], t) - h + 540) % 360 - 180):.1f}° IF {abs((brg(C[iff], t) - h + 540) % 360 - 180):.1f}°", file=sys.stderr)
    seq = legs[0] + [iff, faf]
    br = [{"n": l, "p": [C[f] for f in l + [iff]]} for l in legs[1:]]
    app[name] = {"n": seq, "p": [C[f] for f in seq] + [list(t)], "b": br}

S, seen, miss = [], set(), set()
for p in raw:
    if "STANDARD ARRIVAL CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"From ([A-Z]{5})[^,]*, (to ?[A-Z][A-Z0-9]{4}.*?)\.", flat):
        fx = [m.group(1)] + re.findall(r"(?:\bto ?|, )([A-Z][A-Z0-9]{4})\b", m.group(2))
        if tuple(fx) in seen: continue
        seen.add(tuple(fx))
        if any(f not in C for f in fx): miss.update(f for f in fx if f not in C); continue
        S.append({"from": fx[0], "to": fx[-1], "p": [[*C[f], f] for f in fx]})
if miss: print("STAR の座標が見つからない：", sorted(miss), file=sys.stderr)
print(f"STAR {len(S)}本：" + ", ".join(f"{s['from']}→{s['to']}" for s in S), file=sys.stderr)

ctr = [sum(v[0] for v in THR.values()) / len(THR), sum(v[1] for v in THR.values()) / len(THR)]
d8 = lambda b: ["北", "北東", "東", "南東", "南", "南西", "西", "北西"][round(b / 45) % 8] + "へ"
SID, smiss = {}, set()
for p in raw:
    if "STANDARD DEPARTURE CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"RWY ?(\d\d[LR]?(?:/\d\d[LR]?)?) ?: Climb on HDG ?\d+[˚°][^,]*, (.*?)\.(?= |$)", flat):
        fx = re.findall(r"\bto ?([A-Z][A-Z0-9]{2,4})\b", m.group(2))
        if not fx: continue
        if any(f not in C for f in fx): smiss.update(f for f in fx if f not in C); continue
        name = fx[-1]
        for rw in m.group(1).split("/"):
            if name in SID.get(rw, {}): continue
            SID.setdefault(rw, {})[name] = {"dir": d8(brg(ctr, C[name])), "v": {"A": [[*C[f], f] for f in fx]}}
if smiss: print("SID の座標が見つからない：", sorted(smiss), file=sys.stderr)
print("SID：" + ", ".join(f"{r} {[(k, v['dir']) for k, v in sorted(o.items())]}" for r, o in sorted(SID.items())), file=sys.stderr)
json.dump({"app": app, "star": S, "sid": SID}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
