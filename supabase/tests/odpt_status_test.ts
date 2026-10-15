// 航空会社の運航情報（ODPT の出発情報）から、欠航と出発の大きな遅れのお知らせを作る
import { assertEquals } from "jsr:@std/assert@1";
import { atNear, statusAlerts, type StatusSched } from "../functions/_shared/odpt_status.ts";

const T = (s: string) => Date.parse(s);
const S: StatusSched[] = [
  { id: 1, flight: "JL501", dep: "HND", arr: "CTS", std: T("2026-10-15T09:00:00+09:00") },
  { id: 2, flight: "NH55", dep: "HND", arr: "CTS", std: T("2026-10-15T08:00:00+09:00") },
  { id: 3, flight: "NH1852", dep: "AOJ", arr: "ITM", std: T("2026-10-15T23:30:00+09:00") },
  { id: 4, flight: "JL503", dep: "HND", arr: "CTS", std: T("2026-10-15T10:00:00+09:00") },
];
const names = (i: string) => ({ HND: "羽田", CTS: "新千歳", AOJ: "青森", ITM: "伊丹" } as Record<string, string>)[i] ?? i;
const item = (no: string, dep: string, std: string, extra: Record<string, string> = {}) =>
  ({ "odpt:flightNumber": [no], "odpt:departureAirport": `odpt.Airport:${dep}`, "odpt:scheduledDepartureTime": std, ...extra });

Deno.test("欠航・60分以上の遅れ（見込み・実際）を出し、短い遅れや結べない便は出さない", () => {
  const a = statusAlerts([
    item("JL0501", "HND", "09:00", { "odpt:flightStatus": "odpt.FlightStatus:Cancelled" }),
    item("NH55", "HND", "08:00", { "odpt:estimatedDepartureTime": "09:10" }),
    item("JL503", "HND", "10:00", { "odpt:actualDepartureTime": "10:40" }),
    item("NH999", "HND", "08:00", { "odpt:flightStatus": "odpt.FlightStatus:Cancelled" }),   // 予定の便にない
    item("NH55", "HND", "08:30", { "odpt:flightStatus": "odpt.FlightStatus:Cancelled" }),    // 定刻が違う（別の日の便）
  ], S, names);
  assertEquals(a.map((x) => [x.schedule_id, x.kind]), [[1, "cancel"], [2, "delay_dep"]]);
  assertEquals(a[0].message, "JL501（羽田→新千歳）は、欠航です（航空会社の運航情報）");
  assertEquals(a[1].message, "NH55（羽田→新千歳）は、出発が約70分遅れる見込みです（定刻 8:00 → 変更後 9:10・航空会社の運航情報）");
});

Deno.test("日付をまたぐ遅れ（23:30 → 0:45）も75分の遅れとして数える", () => {
  assertEquals(atNear(T("2026-10-15T23:30:00+09:00"), "00:45"), T("2026-10-16T00:45:00+09:00"));
  const a = statusAlerts([item("NH1852", "AOJ", "23:30", { "odpt:actualDepartureTime": "00:45" })], S, names);
  assertEquals(a.length, 1);
  assertEquals(a[0].message, "NH1852（青森→伊丹）は、出発が約75分遅れました（定刻 23:30 → 出発 0:45・航空会社の運航情報）");
});
