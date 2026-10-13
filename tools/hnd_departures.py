# 羽田の標準出発経路（RNAV SID）のデータを作る。AIP JAPAN の RJTT AD2 の PDF（SWIM の AIP ファイルダウンロードサービス）から読む。
#   python3 tools/hnd_departures.py <RJTT__YYYYMMDD.pdf>
# 出力（標準出力の JSON）を src/index.html の HND_SID に入れる。
# どの滑走路からどの SID を使うかは、RJTT AD 2.20「1.3 Departure」の表による（北風：ROVER は 34R、BEKLA・GUSRO は 34R か 05、NINOX・LAXAS は 05 など）。
# ROVER・BEKLA の A・B・C は離陸の時刻で決まる（B：日本時間 7:00〜11:30、C：15〜19時のうち約3時間、それ以外は A）。
import json, math, re, subprocess, sys

pdf = sys.argv[1]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
lay = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f")

def deg(s):
    h = s[-1]; s = s[:-1]; k = 3 if h == "E" else 2
    return round(int(s[:k]) + int(s[k:k + 2]) / 60 + float(s[k + 2:]) / 3600, 5)

def is_sid(p): return "STANDARD DEPARTURE CHART" in p and "RNAV SID" in p

# 1) 座標（Waypoint Coordinates の表。列がそろう -layout の文字から読む）
C = {}
for p in lay:
    if not is_sid(p): continue
    for m in re.finditer(r"\b([A-Z][A-Z0-9]{4})\s+(\d{6}\.\dN)\s*/\s*(\d{7}\.\dE)", p):
        C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])

# 2) 経路の文（RWY05 : Climb on HDG 050˚ ..., direct to TT501, ... to VAMOS）
S = {}
for p in raw:
    if not is_sid(p) or "Climb on HDG" not in p: continue
    name = re.findall(r"([A-Z]{4,8}(?: [A-Z]+){1,3}) DEPARTURE", p)[0]
    flat = re.sub(r"\s+", " ", p)
    rwpat = r"RWY ?\d\d[LR]?(?:/(?:RWY)?\d\d[LR]?)*"
    for m in re.finditer(rf"({rwpat}) ?: ?(Climb on HDG.*?)(?={rwpat} ?: ?Climb|Note|CHANGE|$)", flat):
        fixes = [f for f in re.findall(r"\b[A-Z][A-Z0-9]{4}\b", m.group(2)) if f in C]
        end = name.split()[0]
        if fixes and fixes[-1] != end and end in C: fixes.append(end)
        for r in re.findall(r"\d\d[LR]?", m.group(1)): S.setdefault(r, {})[name] = fixes

# GUSRO は文の説明がないため、コーディング表（RJTT AD2.24-SID-78・79）の順を書き写す
G = {"16R": ["T6R13", "HATBA", "KAMAT", "LAYER", "GUSRO"], "16L": ["T6L43", "HATBA", "KAMAT", "LAYER", "GUSRO"],
     "34R": ["TT502", "LOCUP", "TT503", "KAMAT", "LAYER", "GUSRO"], "05": ["TT501", "TT502", "LOCUP", "TT503", "KAMAT", "LAYER", "GUSRO"]}

# 3) 運用ごとに使う SID（AD 2.20 1.3 の表）
USE = {"north": {"34R": ["ROVER", "BEKLA", "GUSRO"], "05": ["BEKLA", "GUSRO", "NINOX", "LAXAS"]},
       "south": {"16L": ["ROVER", "BEKLA", "GUSRO"], "16R": ["BEKLA", "GUSRO", "NINOX", "LAXAS"]},
       "city":  {"16R": ["ROVER", "BEKLA", "GUSRO"], "22": ["NINOX", "LAXAS"]}}
H = (35.5533, 139.7811)
def brg(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    y = math.sin(lo2 - lo1) * math.cos(la2); x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return (math.degrees(math.atan2(y, x)) + 360) % 360
def way(b): return ["北", "北東", "東", "南東", "南", "南西", "西", "北西"][int((b + 22.5) // 45) % 8] + "へ"

out = {}
for mode, rws in USE.items():
    for rw, sids in rws.items():
        for sid in sids:
            if sid == "GUSRO": v = {"A": G.get(rw)}
            else:
                v = {}
                for name, fx in S.get(rw, {}).items():
                    if name.split()[0] != sid: continue
                    k = name.split()[-1] if name.split()[-1] in ("A", "B", "C") else "A"
                    v[k] = fx
            v = {k: [[*C[f], f] for f in fx] for k, fx in v.items() if fx}
            if not v: print("見つからない", mode, rw, sid, file=sys.stderr); continue
            out.setdefault(rw, {})[sid] = {"dir": way(brg(H, C[sid])), "v": v}
json.dump(out, sys.stdout, ensure_ascii=False, separators=(",", ":"))
