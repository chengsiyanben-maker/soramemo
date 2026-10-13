# 伊丹の進入経路と標準到着経路（RNAV STAR）のデータを作る。AIP JAPAN の RJOO AD2 の PDF（SWIM の AIP ファイルダウンロードサービス）から読む。
#   python3 tools/itm_routes.py <RJOO__YYYYMMDD.pdf>
# 出力（標準出力の JSON：{"app":…, "star":…}）を src/index.html の ITM_APP・ITM_STAR に入れる。
# 伊丹には14向きのまっすぐな進入がない。南東から32Lの進入（ILS 32L・VOR A）で近づき、空港の西側を回って14Rに降りる（周回進入。ジェット機は西回りだけ）。
# 周回の線はチャートにないため、滑走路の位置から そらメモ が作ったおおよその線（西へ1.2海里ずれて北西へ進み、14Rの延長線に戻る）。
import json, math, re, subprocess, sys

pdf = sys.argv[1]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
lay = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout

def deg(s):
    h = s[-1]; s = s[:-1]; k = 3 if h == "E" else 2
    return round(int(s[:k]) + int(s[k:k + 2]) / 60 + float(s[k + 2:]) / 3600, 5)
C = {}
for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,4})\s+(\d{6}(?:\.\d+)?N)\s*/\s*(\d{7}(?:\.\d+)?E)", lay):
    C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])
C["MIDOH"] = [deg("343857.74N"), deg("1353600.86E")]   # ILS RWY32L の FAF（チャートの表）

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

# 滑走路の進入端（AD 2.12。src/index.html の OPS_AIRPORTS.ITM と同じ値）
T32L, T14R = (34.7722, 135.451878), (34.791325, 135.428706)
h32 = brg(T32L, T14R)
print(f"ILS 32L: IF IKOMA {dist(C['IKOMA'], T32L):.1f}nm（チャート D14.4 ISK）, FAF MIDOH {dist(C['MIDOH'], T32L):.1f}nm, "
      f"延長線からのずれ {abs((brg(C['MIDOH'], T32L) - h32 + 540) % 360 - 180):.1f}°", file=sys.stderr)
app = {"ILS 32L": {"n": ["IKOMA", "MIDOH"], "p": [C["IKOMA"], C["MIDOH"], list(T32L)]}}
# 周回進入（14R）：32Lの進入で近づき（滑走路の手前1海里まで）、西（左）へ1.2海里ずれて北西へ進み、14Rの延長線（2海里）に戻って降りる
west = (h32 - 90) % 360
c = [C["IKOMA"], C["MIDOH"], dest(T32L, (h32 + 180) % 360, 1.0),
     dest(dest(T32L, west, 1.2), h32, 0.3), dest(dest(T14R, west, 1.2), h32, 1.3), dest(T14R, h32, 2.0), list(T14R)]
app["CIRCLE 14R"] = {"n": ["IKOMA", "MIDOH"], "p": c}

S, seen = [], set()
for p in raw:
    if "STANDARD ARRIVAL CHART" not in p: continue
    flat = re.sub(r"\s+", " ", p)
    for m in re.finditer(r"From ([A-Z]{5})[^,]*, (to ?[A-Z][A-Z0-9]{4}.*?)\.", flat):
        fx = [m.group(1)] + re.findall(r"\bto ?([A-Z][A-Z0-9]{4})\b", m.group(2))
        if tuple(fx) in seen: continue
        seen.add(tuple(fx))
        if any(f not in C for f in fx): print("座標が見つからない：", [f for f in fx if f not in C], file=sys.stderr); continue
        S.append({"from": fx[0], "to": fx[-1], "p": [[*C[f], f] for f in fx]})
print(f"STAR {len(S)}本：" + ", ".join(f"{s['from']}→{s['to']}" for s in S), file=sys.stderr)
json.dump({"app": app, "star": S}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
