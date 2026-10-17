// 航空会社の運航情報（ODPT の出発情報）から、欠航と出発の大きな遅れのお知らせを作る
import { assertEquals } from "jsr:@std/assert@1";
import { atNear, liveryOf, liveryPlans, odptStatus, statusAlerts, type StatusSched } from "../functions/_shared/odpt_status.ts";

const T = (s: string) => Date.parse(s);
const S: StatusSched[] = [
  { id: 1, flight: "JL501", dep: "HND", arr: "CTS", std: T("2026-10-15T09:00:00+09:00") },
  { id: 2, flight: "NH55", dep: "HND", arr: "CTS", std: T("2026-10-15T08:00:00+09:00") },
  { id: 3, flight: "NH1852", dep: "AOJ", arr: "ITM", std: T("2026-10-15T23:30:00+09:00") },
  { id: 4, flight: "JL503", dep: "HND", arr: "CTS", std: T("2026-10-15T10:00:00+09:00") },
];
const names = (i: string) => ({ HND: "羽田", CTS: "新千歳", AOJ: "青森", ITM: "伊丹" } as Record<string, string>)[i] ?? i;
const item = (no: string, dep: string, std: string, extra: Record<string, unknown> = {}) =>
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

Deno.test("到着：遅れ・ダイバートを知らせ、実際の時刻・搭乗口を便に残す（予定の便名の先頭の0も無視して結ぶ）", () => {
  const sc: StatusSched[] = [{ id: 7, flight: "NH053", dep: "HND", arr: "CTS", std: T("2026-10-15T08:00:00+09:00"), sta: T("2026-10-15T09:35:00+09:00") },
    { id: 8, flight: "JL509", dep: "HND", arr: "CTS", std: T("2026-10-15T11:00:00+09:00"), sta: T("2026-10-15T12:35:00+09:00") }];
  const r = odptStatus(
    [item("NH53", "HND", "08:00", { "odpt:actualDepartureTime": "08:12", "odpt:departureGate": "59", "odpt:flightStatus": "odpt.FlightStatus:Departed" })],
    [{ "odpt:flightNumber": ["NH0053"], "odpt:departureAirport": "odpt.Airport:HND", "odpt:scheduledArrivalTime": "09:35", "odpt:actualArrivalTime": "10:50", "odpt:arrivalGate": "8" },
     { "odpt:flightNumber": ["JL509"], "odpt:departureAirport": "odpt.Airport:HND", "odpt:scheduledArrivalTime": "12:35", "odpt:flightStatus": "odpt.FlightStatus:Diverted" }],
    sc, names);
  assertEquals(r.alerts.map((a) => [a.schedule_id, a.kind]), [[7, "delay_arr"], [8, "divert"]]);
  assertEquals(r.alerts[0].message, "NH053（羽田→新千歳）は、到着が約75分遅れました（定刻 9:35 → 到着 10:50・航空会社の運航情報）");
  const u = r.updates.find((x) => x.id === 7)!;
  assertEquals([u.dep_status, u.atd, u.dep_gate, u.ata, u.arr_gate], ["Departed", "2026-10-14T23:12:00.000Z", "59", "2026-10-15T01:50:00.000Z", "8"]);
});

Deno.test("航空会社のお知らせの文（理由）を、お知らせの終わりに添える（言語ごとの形なら日本語）", () => {
  const r = statusAlerts([item("JL501", "HND", "09:00", { "odpt:flightStatus": "odpt.FlightStatus:Cancelled", "odpt:flightInformationText": { ja: "機材整備のため欠航", en: "Cancelled due to maintenance" } })], S, names);
  assertEquals(r[0].message, "JL501（羽田→新千歳）は、欠航です（航空会社の運航情報。機材整備のため欠航）");
  const d = statusAlerts([item("NH55", "HND", "08:00", { "odpt:estimatedDepartureTime": "09:10", "odpt:flightInformationSummary": "天候調査" })], S, names);
  assertEquals(d[0].message, "NH55（羽田→新千歳）は、出発が約70分遅れる見込みです（定刻 8:00 → 変更後 9:10・航空会社の運航情報。天候調査）");
});

Deno.test("要約（出発遅延）と本文の両方があれば、本文（理由）を使う", () => {
  const d = statusAlerts([item("NH55", "HND", "08:00", { "odpt:estimatedDepartureTime": "09:10",
    "odpt:flightInformationSummary": { en: "Delayed", ja: "出発遅延" }, "odpt:flightInformationText": { en: "due to aircraft maintenance.", ja: "飛行機の整備のため出発に遅延が生じています。" } })], S, names);
  assertEquals(d[0].message.endsWith("・航空会社の運航情報。飛行機の整備のため出発に遅延が生じています。）"), true);
});

Deno.test("特別塗装機で飛ぶ予定の便：お知らせの文から見つける（一覧の名前、なければ「〇〇ジェットで運航」）", () => {
  const names = ["JAL Jubilee Express", "ポケモンジェット 緑", "ピカチュウジェットNH"];
  assertEquals(liveryOf("JAL Jubilee Expressで運航いたします。", names), "JAL Jubilee Express");
  assertEquals(liveryOf("本日は「ピカチュウジェットNH」で運航します。", names), "ピカチュウジェットNH");
  assertEquals(liveryOf("ドラえもんジェットで運航いたします。", names), "ドラえもんジェット");
  assertEquals(liveryOf("飛行機の整備のため出発に遅延が生じています。", names), null);
  assertEquals(liveryOf("小型機で運航いたします。", names), null);   // 特別塗装ではない「〇〇で運航」は使わない
  const p = liveryPlans([
    item("JL0501", "HND", "09:00", { "odpt:flightInformationText": { ja: "JAL Jubilee Expressで運航いたします。", en: "JAL Jubilee Express Flight." } }),
    item("NH55", "HND", "08:00", { "odpt:flightInformationText": { ja: "ポケモンジェット 緑で運航します。" }, "odpt:flightStatus": "odpt.FlightStatus:Cancelled" }),
    item("JL503", "HND", "10:00", { "odpt:flightInformationText": { ja: "使用する飛行機の到着遅れのため出発に遅延が生じています。" } }),
  ], S, names);
  assertEquals(p.map((x) => [x.schedule_id, x.livery]), [[1, "JAL Jubilee Express"]]);   // 欠航の便・特別塗装でない便は入れない
});

Deno.test("時刻表と運航情報で定刻が数分ずれていても結ぶ（JL333 の到着：時刻表 21:05・運航情報 21:10 → 実際 21:16）。遅れは運航情報の定刻から数える", () => {
  const sc: StatusSched[] = [{ id: 9, flight: "JL333", dep: "HND", arr: "FUK", std: T("2026-10-17T19:15:00+09:00"), sta: T("2026-10-17T21:05:00+09:00") },
    { id: 10, flight: "JL333", dep: "HND", arr: "FUK", std: T("2026-10-16T19:15:00+09:00"), sta: T("2026-10-16T21:05:00+09:00") }];
  const r = odptStatus([], [{ "odpt:flightNumber": ["JL333"], "odpt:departureAirport": "odpt.Airport:HND", "odpt:scheduledArrivalTime": "21:10", "odpt:actualArrivalTime": "21:16", "odpt:flightStatus": "odpt.FlightStatus:Arrived" }], sc, names);
  const u = r.updates.find((x) => x.id === 9)!;
  assertEquals([u.ata, u.arr_status], ["2026-10-17T12:16:00.000Z", "Arrived"]);
  assertEquals(r.updates.some((x) => x.id === 10), false);   // 前の日の便には結ばない
  assertEquals(r.alerts.length, 0);   // 6分の遅れはお知らせにしない
  // 20分を超えてずれた便は、別の便として結ばない
  const far = odptStatus([], [{ "odpt:flightNumber": ["JL333"], "odpt:departureAirport": "odpt.Airport:HND", "odpt:scheduledArrivalTime": "22:30", "odpt:actualArrivalTime": "22:40" }], sc, names);
  assertEquals(far.updates.length, 0);
});
