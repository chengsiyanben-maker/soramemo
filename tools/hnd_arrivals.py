# 羽田の標準到着経路（RNAV STAR）のデータを作る。AIP JAPAN の RJTT AD2 の PDF（SWIM の AIP ファイルダウンロードサービス）から読む。
#   python3 tools/hnd_arrivals.py <RJTT__YYYYMMDD.pdf>
# 出力（標準出力の JSON）を src/index.html の HND_STAR に入れる。
# 各 STAR の終わりのフィックスが、どの進入につながるかで分ける（例：KAIHO → ILS X 34L、BACON → LDA W 22、SANDY → 16L）。
import json, math, re, subprocess, sys

pdf = sys.argv[1]
raw = subprocess.run(["pdftotext", "-raw", pdf, "-"], capture_output=True, text=True).stdout.split("\f")
lay = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f")

def deg(s):
    h = s[-1]; s = s[:-1]; k = 3 if h == "E" else 2
    return round(int(s[:k]) + int(s[k:k + 2]) / 60 + float(s[k + 2:]) / 3600, 5)
def is_star(p): return "STANDARD ARRIVAL CHART" in p

C = {}
for p in lay:
    if not is_star(p): continue
    for m in re.finditer(r"\b([A-Z][A-Z0-9]{2,4})\s+(\d{6}(?:\.\d+)?N)\s*/\s*(\d{7}(?:\.\d+)?E)", p):
        C.setdefault(m.group(1), [deg(m.group(2)), deg(m.group(3))])
# 進入チャートにしか座標がないフィックス（tools/hnd_approaches.py と同じ値）と、大島 VOR/DME
EXTRA = {"ARLON": "351525.3N 1395859.8E", "KAIHO": "351857.8N 1394642.4E", "CREAM": "351743.4N 1400612.4E", "CLOAK": "351548.0N 1400208.2E",
         "CAMEL": "351718.2N 1395857.8E", "CACAO": "352212.81N 1395530.14E", "NYLON": "354018.5N 1400919.9E", "BACON": "353155.0N 1401215.1E",
         "STEAM": "355553.3N 1395708.4E", "DATUM": "354259.6N 1400824.3E", "SANDY": "354917.53N 1394402.84E", "NATTY": "355350.86N 1394531.32E"}
for k, v in EXTRA.items():
    a, b = v.split(); C.setdefault(k, [deg(a), deg(b)])

S = []
for p in raw:
    if not is_star(p): continue
    flat = re.sub(r"\s+", " ", p)
    rw = re.findall(r"RNAV STAR RWY ?([0-9LR/]+)", flat)
    for m in re.finditer(r"From ([A-Z]{3,5}) ?(?:at [^,]*)?,(.*?\bto [A-Z][A-Z0-9]{2,4})\.", flat):
        fx = [m.group(1)] + re.findall(r"\bto ([A-Z][A-Z0-9]{2,4})\b", m.group(2))
        S.append({"rw": rw[0] if rw else "", "fix": fx})
# 同じ経路をまとめる
seen, out = set(), []
miss = set()
for s in S:
    k = tuple(s["fix"])
    if k in seen or "UTIBO" in k: continue   # 深夜早朝の経路（UTIBO 経由）は出さない
    seen.add(k)
    m = [f for f in s["fix"] if f not in C]
    if m: miss.update(m); continue
    out.append({"from": s["fix"][0], "to": s["fix"][-1], "p": [[*C[f], f] for f in s["fix"]]})
if miss: print("座標が見つからない：", sorted(miss), file=sys.stderr)
json.dump(out, sys.stdout, ensure_ascii=False, separators=(",", ":"))
