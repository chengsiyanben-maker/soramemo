# 新千歳・福岡・那覇の進入経路・標準到着経路（RNAV STAR）・標準出発経路（RNAV SID）のデータを作る。
# AIP JAPAN の AD2 の PDF（SWIM の AIP ファイルダウンロードサービス）から読む。
#   python3 tools/ap_routes.py <ICAO> <ICAO__YYYYMMDD.pdf>
# 出力（標準出力の JSON：{"app":…, "star":…, "sid":…}）を src/index.html の <IATA>_APP・_STAR・_SID に入れる。
# 進入は、進入チャート（AD2.24-IAC）のフィックスの並びと座標を書き写したもの（AIP が改訂されたら、チャートと見比べて直す）。
# 座標がチャートにない IF は、FAF から最終進入の向きと逆へ、チャートの DME の差の距離で置く（{"ext": [FAF, 海里]}）。
import json, math, re, subprocess, sys

icao, pdf = sys.argv[1], sys.argv[2]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
lay = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout

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
def dest(a, b, nm):
    la1, lo1 = map(math.radians, a); t = math.radians(b); d = nm / R
    la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(t))
    lo2 = lo1 + math.atan2(math.sin(t) * math.sin(d) * math.cos(la1), math.cos(d) - math.sin(la1) * math.sin(la2))
    return [round(math.degrees(la2), 5), round(math.degrees(lo2), 5)]

# 空港ごとの設定。THR：滑走路の進入端（AD 2.12。src/index.html の OPS_AIRPORTS と同じ値）、OPP：反対側の端
# A：進入名 → (IAF からの並び（最初が本線）, IF, FAF, 滑走路)。F：チャートの表の座標。SID：使う RNAV SID（最後のフィックス）
CFG = {
  "RJCC": dict(
    THR={"01L": (42.761639, 141.692825), "19R": (42.788433, 141.688106), "01R": (42.761986, 141.696458), "19L": (42.788767, 141.691744)},
    OPP={"01L": "19R", "19R": "01L", "01R": "19L", "19L": "01R"},
    F={"EKELU": "423955.37N 1414235.09E", "IGIKU": "423955.67N 1414248.30E", "NESIC": "425303.52N 1414029.62E", "PUNCH": "425801.7N 1413936.6E",
       "ASIRI": "425714.7N 1413130.5E", "BANSU": "430358.8N 1413632.7E", "KAORY": "430302.3N 1414406.7E", "PUPIG": "425846.3N 1414742.6E",
       "OPORO": "425301.43N 1414016.64E"},
    EXT={"GUVOX": ("EKELU", 9.0, "01L"), "YOTEI": ("IGIKU", 9.0, "01R"), "NACKS": ("OPORO", 7.0, "19R")},
    A={"ILS Z 01L": ([[]], "GUVOX", "EKELU", "01L"), "ILS Z 01R": ([[]], "YOTEI", "IGIKU", "01R"),
       "ILS Z 19L": ([["KAORY"], ["BANSU"], ["PUPIG"], ["ASIRI"]], "PUNCH", "NESIC", "19L"), "ILS Z 19R": ([[]], "NACKS", "OPORO", "19R")},
    SID=["TOBBY", "KURIS", "DALBI"], TR={"TOBBY": ["NOHEY", "APIOS", "PANSY"]}),
  "RJFF": dict(
    THR={"16L": (33.596919, 130.443186), "34R": (33.574967, 130.458186), "16R": (33.595969, 130.441219), "34L": (33.576403, 130.454589)},
    OPP={"16L": "34R", "34R": "16L", "16R": "34L", "34L": "16R"},
    F={"DAZAI": "332200.9N 1304208.1E", "KIGUS": "331715.7N 1303211.9E", "ADPAR": "331948.0N 1303730.0E", "ANGAG": "332408.73N 1303432.82E",
       "ENTIX": "334757.5N 1301818.9E", "AKTIB": "334520.8N 1302005.9E", "ADMUB": "334059.54N 1302302.92E"},
    EXT={},
    A={"ILS 34R": ([["KIGUS"], ["DAZAI"]], "ADPAR", "ANGAG", "34R"), "ILS 16L": ([["ENTIX"]], "AKTIB", "ADMUB", "16L")},
    SID=["YOKAT", "YAMEK", "YAMGA", "KIKYU"], TR={"YOKAT": ["KOHZA", "BRAID", "ENGID"], "YAMEK": ["SGE"], "YAMGA": ["KUE"], "KIKYU": ["NOGAB", "CARSE"]}),
  "ROAH": dict(
    THR={"18L": (26.209342, 127.645233), "36R": (26.182289, 127.646503), "18R": (26.203056, 127.6324), "36L": (26.178706, 127.633547)},
    OPP={"18L": "36R", "36R": "18L", "18R": "36L", "36L": "18R"},
    F={"VIGER": "255743.9N 1273526.9E", "UTAKI": "260233.2N 1273250.4E", "SEIFA": "260303.9N 1274448.5E", "DEIJI": "260251.8N 1273915.6E",
       "NATON": "260705.80N 1273900.65E", "BLISS": "260249.3N 1273823.0E", "BOOST": "260653.15N 1273811.59E",
       "KUKUL": "262952.0N 1273641.6E", "THETA": "262020.0N 1273159.3E", "SALSA": "262032.6N 1273725.1E", "PARTY": "261542.55N 1273743.62E",
       "RYCOM": "262034.70N 1273820.22E", "KAMJI": "261608.84N 1273832.73E"},
    EXT={},
    A={"ILS Z 36R": ([["VIGER"], ["UTAKI"], ["SEIFA"]], "DEIJI", "NATON", "36R"), "ILS Z 36L": ([["VIGER"], ["UTAKI"], ["SEIFA"]], "BLISS", "BOOST", "36L"),
       "ILS 18R": ([["KUKUL"], ["THETA"]], "SALSA", "PARTY", "18R"), "RNP 18L": ([["KUKUL"], ["THETA"]], "RYCOM", "KAMJI", "18L")},
    SID=["ESKOB", "DORIS", "GANJU"], TR={"ESKOB": ["ADDAN"]}),
}[icao]
THR, OPP = CFG["THR"], CFG["OPP"]

C = {}
for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,4})\s+(?:\([A-Z/]+\)\s+)?(\d{6}(?:\.\d+)?N)\s*/?\s*(\d{7}(?:\.\d+)?E)", lay):
    C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])
# 表が「名前・緯度・経度」と行ごとに分かれているチャート（那覇など）
for m in re.finditer(r"(?:^|\n)([A-Z][A-Z0-9]{4})\s*\n(?:\([A-Z/]+\)\s*\n)?[^\n0-9A-Z]*(\d{6}(?:\.\d+)?N)\s*\n[^\n0-9A-Z]*(\d{7}(?:\.\d+)?E)", "\n".join(raw)):
    C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])
for k, v in CFG["F"].items(): C[k] = [deg(v.split()[0]), deg(v.split()[1])]
for k, (faf, nm, rw) in CFG["EXT"].items():
    C[k] = dest(C[faf], brg(THR[rw], THR[OPP[rw]]) + 180, nm)

app = {}
for name, (legs, iff, faf, rw) in CFG["A"].items():
    t = THR[rw]; h = brg(t, THR[OPP[rw]])
    print(f"{name}: IF {iff} {dist(C[iff], t):.1f}nm, FAF {faf} {dist(C[faf], t):.1f}nm, 延長線からのずれ {abs((brg(C[faf], t) - h + 540) % 360 - 180):.1f}°", file=sys.stderr)
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

# SID：TR の空港は、行き先がわかるように主な移行経路（トランジション）の先までつなぐ。方向は空港の中心から最後の点への向き（8方位）
ctr = [sum(v[0] for v in THR.values()) / 4, sum(v[1] for v in THR.values()) / 4]
d8 = lambda b: ["北", "北東", "東", "南東", "南", "南西", "西", "北西"][round(b / 45) % 8] + "へ"
SID = {}
for p in raw:
    if "STANDARD DEPARTURE CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"RWY ?(\d\d[LR]?(?:/\d\d[LR]?)?) ?: Climb on HDG ?\d+[˚°][^,]*, (.*?)\.(?= |$)", flat):
        fx = re.findall(r"\bto ?([A-Z][A-Z0-9]{2,4})\b", m.group(2))
        if not fx or fx[-1] not in CFG["SID"]: continue
        fx = fx + CFG.get("TR", {}).get(fx[-1], [])
        if any(f not in C for f in fx): print("SID の座標が見つからない：", [f for f in fx if f not in C], file=sys.stderr); continue
        name = [f for f in fx if f in CFG["SID"]][-1]
        for rw in re.sub(r"^(\d\d)([LR])/(\d\d)([LR])$", r"\1\2/\3\4", m.group(1)).split("/"):
            if name in SID.get(rw, {}): continue
            SID.setdefault(rw, {})[name] = {"dir": d8(brg(ctr, C[fx[-1]])), "v": {"A": [[*C[f], f] for f in fx]}}
print("SID：" + ", ".join(f"{r} {[(k, v['dir']) for k, v in sorted(o.items())]}" for r, o in sorted(SID.items())), file=sys.stderr)
json.dump({"app": app, "star": S, "sid": SID}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
