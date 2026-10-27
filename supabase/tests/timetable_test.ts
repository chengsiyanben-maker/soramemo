// 計画の画面の時刻表：ODPT のフライト時刻表を、曜日をまとめた行にするテスト
import { assertEquals } from "jsr:@std/assert@1";
import { calendarDays, isJpAirport, timetableRows } from "../functions/_shared/timetable.ts";

const item = (cal: string, dep: string, arr: string, objs: unknown[]) => ({ "odpt:calendar": `odpt.Calendar:${cal}`, "odpt:operator": "odpt.Operator:ANA",
  "odpt:originAirport": `odpt.Airport:${dep}`, "odpt:destinationAirport": `odpt.Airport:${arr}`, "odpt:flightScheduleObject": objs });
const obj = (t1: string, t2: string, no = "NH461", from = "2026-10-25", to = "2027-03-27") => ({ "odpt:isValidFrom": `${from}T00:00:00+09:00`, "odpt:isValidTo": `${to}T23:59:59+09:00`,
  "odpt:originTime": t1, "odpt:destinationTime": t2, "odpt:flightNumber": [no, "XX1234"], "odpt:aircraftType": "789" });

Deno.test("同じ便・期間・時刻は、曜日を1つの数にまとめる", () => {
  const rows = timetableRows([item("Monday", "HND", "OKA", [obj("07:30", "10:15")]), item("Friday", "HND", "OKA", [obj("07:30", "10:15")]),
    item("Saturday", "HND", "OKA", [obj("07:40", "10:25")])], "ANA", isJpAirport);
  assertEquals(rows.length, 2);
  const a = rows.find((r) => r.dep_time === "07:30")!;
  assertEquals(a.days, 2 | 32); assertEquals(a.flight, "NH461"); assertEquals(a.arr, "OKA");
  assertEquals(a.valid_from, "2026-10-25"); assertEquals(a.valid_to, "2027-03-27"); assertEquals(a.aircraft, "789"); assertEquals(a.arr_day, 0);
  assertEquals(rows.find((r) => r.dep_time === "07:40")!.days, 64);
});

Deno.test("曜日の書き方", () => {
  assertEquals(calendarDays("odpt.Calendar:Sunday"), 1);
  assertEquals(calendarDays("odpt.Calendar:Everyday"), 127);
  assertEquals(calendarDays("odpt.Calendar:Weekday"), 62);
  assertEquals(calendarDays("odpt.Calendar:Specific.2026-12-31"), 0);
});

Deno.test("国際線・変な便名や時刻・期間の逆転は入れない。日付をまたいで着く便は翌日着", () => {
  const rows = timetableRows([item("Monday", "HND", "ICN", [obj("08:00", "10:30", "NH861")]),
    item("Monday", "HND", "CTS", [obj("9時", "10:30"), obj("08:00", "09:30", "ANA"), obj("08:00", "09:30", "NH51", "2027-01-01", "2026-12-01"), obj("23:50", "01:20", "NH99")])], "ANA", isJpAirport);
  assertEquals(rows.length, 1);
  assertEquals(rows[0].flight, "NH99"); assertEquals(rows[0].arr_day, 1);
});
