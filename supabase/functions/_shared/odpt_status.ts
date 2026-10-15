// 航空会社の運航情報（ODPT の FlightInformationDeparture。JAL・ANA グループ）から、欠航と出発の大きな遅れのお知らせを作る。
// 機体の位置からの推定（flight_watch.ts）と違い、航空会社が出している情報なので「推定」ではない。取得とは分けて、テストしやすくしている。
//   ・欠航：odpt:flightStatus が Cancelled
//   ・出発の遅れ：実際の出発時刻（odpt:actualDepartureTime）か、変更後の出発時刻（odpt:estimatedDepartureTime）が、定刻より60分以上あと
// 便は、予定の便（flight_schedule）の、同じ便名・同じ出発空港・同じ定刻の便に結ぶ（日付は予定の便から決まる）。結べない便は使わない。
import { flightNo } from "./airport_now.ts";

export type StatusSched = { id: number; flight: string; dep: string; arr: string; std: number };   // std：ミリ秒（UTC）
export type StatusAlert = { schedule_id: number; kind: "cancel" | "delay_dep"; flight: string; dep: string; arr: string; iata: string[]; message: string };

const MIN = 60_000;
const last = (v: unknown) => { const s = String(Array.isArray(v) ? v[0] ?? "" : v ?? ""); const i = s.lastIndexOf(":"); return i >= 0 ? s.slice(i + 1) : s; };
const hhmm = (v: unknown): string | null => { const m = String(v ?? "").match(/^(\d{1,2}):(\d{2})/); return m ? `${m[1].padStart(2, "0")}:${m[2]}` : null; };
const jstHM = (ms: number) => { const d = new Date(ms + 9 * 3600_000); return `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`; };
const hmText = (hm: string) => `${Number(hm.slice(0, 2))}:${hm.slice(3)}`;

// 定刻 std の日の "HH:MM"（日本時間）を、定刻にいちばん近い時刻（ミリ秒）にする（日付をまたぐ遅れにも対応）
export function atNear(std: number, hm: string): number {
  const d = new Date(std + 9 * 3600_000);
  const base = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), Number(hm.slice(0, 2)), Number(hm.slice(3, 5))) - 9 * 3600_000;
  return [base - 864e5, base, base + 864e5].sort((a, b) => Math.abs(a - std) - Math.abs(b - std))[0];
}

// deno-lint-ignore no-explicit-any
export function statusAlerts(items: any[], scheds: StatusSched[], names: (iata: string) => string): StatusAlert[] {
  const byKey = new Map<string, StatusSched[]>();
  for (const s of scheds) { const k = `${s.flight}|${s.dep}`; byKey.set(k, [...(byKey.get(k) ?? []), s]); }
  const out = new Map<string, StatusAlert>();
  for (const it of Array.isArray(items) ? items : []) {
    const fn = flightNo(it?.["odpt:flightNumber"]), dep = last(it?.["odpt:departureAirport"]).slice(0, 3).toUpperCase();
    const std = hhmm(it?.["odpt:scheduledDepartureTime"]);
    if (!fn || !std || !/^[A-Z]{3}$/.test(dep)) continue;
    const s = (byKey.get(`${fn.no}|${dep}`) ?? []).find((x) => jstHM(x.std) === std);
    if (!s) continue;
    const route = `${s.flight}（${names(s.dep)}→${names(s.arr)}）`, status = last(it["odpt:flightStatus"]).toLowerCase();
    if (/cancel/.test(status)) {
      out.set(`${s.id}|cancel`, { schedule_id: s.id, kind: "cancel", flight: s.flight, dep: s.dep, arr: s.arr, iata: [s.dep, s.arr],
        message: `${route}は、欠航です（航空会社の運航情報）` });
      continue;
    }
    const actual = hhmm(it["odpt:actualDepartureTime"]), est = hhmm(it["odpt:estimatedDepartureTime"]), t = actual ?? est;
    if (!t) continue;
    const late = Math.round((atNear(s.std, t) - s.std) / MIN);
    if (late >= 60) out.set(`${s.id}|delay_dep`, { schedule_id: s.id, kind: "delay_dep", flight: s.flight, dep: s.dep, arr: s.arr, iata: [s.dep, s.arr],
      message: `${route}は、出発が約${late}分遅れ${actual ? "ました" : "る見込みです"}（定刻 ${hmText(std)} → ${actual ? "出発" : "変更後"} ${hmText(t)}・航空会社の運航情報）` });
  }
  return [...out.values()];
}
