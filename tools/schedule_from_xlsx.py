# ダイヤの表（Excel の「全便（日別）」シート）を、flight_schedule に読み込む CSV にする。国内線だけ。
#   python3 tools/schedule_from_xlsx.py <ダイヤ.xlsx> <出典の説明> > schedule.csv
# 列：svc_date,flight,dep,arr,std,sta,aircraft,source（std・sta は日本時間の ISO 形式）
# 注意：本番に入れるダイヤは、航空会社などの公式の時刻表にする（公式でないダイヤは手元の確認だけに使う）。
import csv, datetime as dt, re, sys
import openpyxl

xlsx, source = sys.argv[1], sys.argv[2]
YEAR = 2026
ws = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)["全便（日別）"]
w = csv.writer(sys.stdout)
w.writerow(["svc_date", "flight", "dep", "arr", "std", "sta", "aircraft", "source"])
for r in ws.iter_rows(min_row=5, values_only=True):
    if not r or not r[0] or r[8] != "国内線": continue
    m = re.match(r"(\d+)/(\d+)", str(r[0])); arr = re.search(r"（([A-Z]{3})）\s*$", str(r[2]))
    if not m or not arr or not isinstance(r[1], dt.time) or not isinstance(r[3], dt.time): continue
    d = dt.date(YEAR, int(m[1]), int(m[2]))
    std = dt.datetime.combine(d, r[1]); sta = dt.datetime.combine(d, r[3])
    if sta <= std: sta += dt.timedelta(days=1)          # 日付をまたぐ便
    jst = lambda x: x.strftime("%Y-%m-%dT%H:%M:00+09:00")
    w.writerow([d.isoformat(), str(r[6]).strip().upper(), "HND", arr[1], jst(std), jst(sta), r[11] or "", source])
