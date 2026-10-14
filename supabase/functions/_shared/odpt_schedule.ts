// ODPT のフライト時刻表（odpt:FlightSchedule）を、予定の便（flight_schedule）の行にする。取得とは分けて、テストしやすくしている。
//   1件：出発空港・到着空港・曜日（odpt:calendar = odpt.Calendar:Monday など）と、期間ごとの便（odpt:flightScheduleObject）
//   便：odpt:flightNumber（コードシェアがあれば複数。最初の便名を使う）・odpt:originTime / odpt:destinationTime（日本時間 "09:50"）・
//       odpt:isValidFrom / odpt:isValidTo（その期間だけ）・odpt:aircraftType
export type ScheduleRow = { svc_date: string; flight: string; dep: string; arr: string; std: string; sta: string; aircraft: string | null; source: string };

const DAY = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
export const ODPT_SOURCE = "ODPT（公共交通オープンデータセンター）フライト時刻表";

// 日本時間の日付（"2026-10-15"）の曜日
function weekday(date: string) { return DAY[new Date(date + "T12:00:00+09:00").getUTCDay()]; }
const apt = (s: unknown) => typeof s === "string" ? (/^odpt\.Airport:([A-Z]{3})$/.exec(s) ?? [])[1] ?? null : null;
const hm = (s: unknown) => typeof s === "string" && /^\d{1,2}:\d{2}$/.test(s) ? s.padStart(5, "0") : null;

// deno-lint-ignore no-explicit-any
export function scheduleRows(items: any[], dates: string[], operator: string): ScheduleRow[] {
  const out = new Map<string, ScheduleRow>();
  for (const it of Array.isArray(items) ? items : []) {
    const dep = apt(it?.["odpt:originAirport"]), arr = apt(it?.["odpt:destinationAirport"]);
    const cal = String(it?.["odpt:calendar"] ?? "").replace("odpt.Calendar:", "");
    if (!dep || !arr) continue;
    for (const date of dates) {
      // 曜日の時刻表だけ使う（毎日・平日などの書き方が来たときも、曜日に合えば使う）
      const wd = weekday(date), ok = cal === wd || cal === "Everyday" || (cal === "Weekday" && wd !== "Saturday" && wd !== "Sunday");
      if (!ok) continue;
      for (const f of Array.isArray(it["odpt:flightScheduleObject"]) ? it["odpt:flightScheduleObject"] : []) {
        const from = String(f?.["odpt:isValidFrom"] ?? "").slice(0, 10), to = String(f?.["odpt:isValidTo"] ?? "").slice(0, 10);
        if ((from && date < from) || (to && date > to)) continue;
        const no = Array.isArray(f?.["odpt:flightNumber"]) ? String(f["odpt:flightNumber"][0] ?? "") : "";
        const t1 = hm(f?.["odpt:originTime"]), t2 = hm(f?.["odpt:destinationTime"]);
        if (!/^[A-Z0-9]{2}\d{1,4}[A-Z]?$/.test(no) || !t1 || !t2) continue;
        const std = new Date(`${date}T${t1}:00+09:00`);
        let sta = new Date(`${date}T${t2}:00+09:00`);
        if (sta <= std) sta = new Date(sta.getTime() + 864e5);   // 日付をまたぐ便
        const row = { svc_date: date, flight: no, dep, arr, std: std.toISOString(), sta: sta.toISOString(),
          aircraft: typeof f["odpt:aircraftType"] === "string" ? f["odpt:aircraftType"].slice(0, 20) : null, source: `${ODPT_SOURCE}（${operator}）` };
        out.set(`${date}|${no}|${dep}`, row);
      }
    }
  }
  return [...out.values()];
}

// 日本時間の今日から n 日ぶんの日付
export function jstDates(now: Date, n: number): string[] {
  return Array.from({ length: n }, (_, i) => new Date(now.getTime() + 9 * 36e5 + i * 864e5).toISOString().slice(0, 10));
}
