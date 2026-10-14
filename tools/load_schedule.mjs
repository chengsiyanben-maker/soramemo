// 予定の便（ダイヤ）の CSV を、サーバーの flight_schedule に読み込む（同じ日・便名・出発空港は上書き）。
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node tools/load_schedule.mjs schedule.csv
// CSV は tools/schedule_from_xlsx.py などで作る（列：svc_date,flight,dep,arr,std,sta,aircraft,source）。
// 本番に入れるのは公式の時刻表だけ。出典に NAVITIME・OAG など公式でないものが書いてあると断る
// （手元の確認用の環境にどうしても入れるときだけ --allow-unofficial を付ける）。
import fs from "node:fs";

const [file, ...flags] = process.argv.slice(2);
const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!file || !url || !key) { console.error("使い方：SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... node tools/load_schedule.mjs schedule.csv"); process.exit(1); }
const [head, ...lines] = fs.readFileSync(file, "utf8").trim().split(/\r?\n/);
const cols = head.split(",");
const rows = lines.map((l) => Object.fromEntries(l.split(",").map((v, i) => [cols[i], v]))).map((r) => ({
  svc_date: r.svc_date, flight: r.flight, dep: r.dep, arr: r.arr, std: r.std, sta: r.sta, aircraft: r.aircraft || null, source: r.source,
}));
const unofficial = rows.filter((r) => /NAVITIME|OAG|FlightAware|Flightradar/i.test(r.source));
if (unofficial.length && !flags.includes("--allow-unofficial")) {
  console.error(`公式でない出典のダイヤが ${unofficial.length} 件あります（例：${unofficial[0].source}）。本番には入れません。`);
  process.exit(1);
}
for (let i = 0; i < rows.length; i += 500) {
  const r = await fetch(`${url.replace(/\/$/, "")}/rest/v1/flight_schedule?on_conflict=svc_date,flight,dep`, {
    method: "POST", body: JSON.stringify(rows.slice(i, i + 500)),
    headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", Prefer: "resolution=merge-duplicates,return=minimal" },
  });
  if (!r.ok) { console.error("読み込みに失敗：", r.status, await r.text()); process.exit(1); }
  console.log(`${Math.min(i + 500, rows.length)} / ${rows.length}`);
}
