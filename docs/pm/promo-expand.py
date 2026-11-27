#!/usr/bin/env python3
# 広報の動画の材料：docs/pm/promo-day.sql の ③（古い日の航跡の線）の CSV を、② と同じ形の「点の CSV」にする
#   使い方：python3 promo-expand.py ③の結果.csv > 点.csv
#   線の点には時刻がないので、出発〜到着の時刻（実績。なければ定刻）を、道のりの割合で点に割り振る（時刻は推定）。
#   出す列：flight, reg, dep, arr, t_jst, lat, lon, alt_ft, time_estimated（いつも true）
#   ほかの道具は使わない（Python の標準だけ）。記録には触らない（手元のファイルを読むだけ）
import csv, math, sys
from datetime import datetime, timedelta

def decode(s, precision=4):
    # Google の polyline（そらメモの記録は小数4桁）
    pts, i, lat, lon, f = [], 0, 0, 0, 10 ** precision
    while i < len(s):
        vals = []
        for _ in range(2):
            shift = res = 0
            while True:
                b = ord(s[i]) - 63; i += 1
                res |= (b & 0x1F) << shift; shift += 5
                if b < 0x20: break
            vals.append(~(res >> 1) if res & 1 else res >> 1)
        lat += vals[0]; lon += vals[1]
        pts.append((lat / f, lon / f))
    return pts

def dist(a, b):
    # 2点の間の道のり（km、球として）
    r = math.radians
    h = math.sin(r(b[0] - a[0]) / 2) ** 2 + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin(r(b[1] - a[1]) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))

def main(path):
    out = csv.writer(sys.stdout)
    out.writerow(["flight", "reg", "dep", "arr", "t_jst", "lat", "lon", "alt_ft", "time_estimated"])
    with open(path, newline="", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            pts = decode(row["pts"] or "")
            if len(pts) < 2: continue
            alts = [int(x) for x in (row.get("alts") or "").split()] if row.get("alts") else []
            t0 = datetime.strptime(row["dep_jst"], "%Y-%m-%d %H:%M:%S")
            t1 = datetime.strptime(row["arr_jst"], "%Y-%m-%d %H:%M:%S")
            seg = [0.0] + [dist(pts[k - 1], pts[k]) for k in range(1, len(pts))]
            total = sum(seg) or 1.0
            acc = 0.0
            for k, p in enumerate(pts):
                acc += seg[k]
                t = t0 + timedelta(seconds=(t1 - t0).total_seconds() * acc / total)
                alt = alts[k] * 100 if k < len(alts) else ""
                out.writerow([row["flight"], row.get("reg") or "", row["dep"], row["arr"], t.strftime("%Y-%m-%d %H:%M:%S"),
                              f"{p[0]:.4f}", f"{p[1]:.4f}", alt, "true"])

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit("使い方：python3 promo-expand.py ③の結果.csv > 点.csv")
    main(sys.argv[1])
