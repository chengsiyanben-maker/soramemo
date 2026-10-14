// ODPT のフライト時刻表を予定の便にするテスト（形は 2026年10月に ODPT から取った見本に合わせている）
import { assertEquals } from "jsr:@std/assert@1";
import { jstDates, scheduleRows } from "../functions/_shared/odpt_schedule.ts";

const item = (cal: string, objs: unknown[]) => ({ "odpt:calendar": `odpt.Calendar:${cal}`, "odpt:operator": "odpt.Operator:JAL",
  "odpt:originAirport": "odpt.Airport:AKJ", "odpt:destinationAirport": "odpt.Airport:HND", "odpt:flightScheduleObject": objs });
const obj = (from: string, to: string, t1: string, t2: string, no = "JL552") => ({ "odpt:isValidFrom": `${from}T00:00:00+09:00`, "odpt:isValidTo": `${to}T23:59:59+09:00`,
  "odpt:originTime": t1, "odpt:destinationTime": t2, "odpt:flightNumber": [no], "odpt:aircraftType": "738" });

Deno.test("曜日と期間が合う便だけを、日本時間の定刻で入れる", () => {
  // 2026-10-16 は金曜日
  const rows = scheduleRows([item("Friday", [obj("2026-09-01", "2026-10-24", "09:50", "11:35"), obj("2026-10-25", "2027-01-04", "10:00", "11:55")]),
    item("Monday", [obj("2026-09-01", "2026-10-24", "09:50", "11:35")])], ["2026-10-16"], "JAL");
  assertEquals(rows.length, 1);
  assertEquals(rows[0].flight, "JL552"); assertEquals(rows[0].dep, "AKJ"); assertEquals(rows[0].arr, "HND");
  assertEquals(rows[0].std, "2026-10-16T00:50:00.000Z"); assertEquals(rows[0].sta, "2026-10-16T02:35:00.000Z");
  assertEquals(rows[0].aircraft, "738");
});

Deno.test("日付をまたぐ便は、到着を翌日にする", () => {
  const rows = scheduleRows([item("Friday", [obj("2026-01-01", "2026-12-31", "23:30", "01:10", "JL999")])], ["2026-10-16"], "JAL");
  assertEquals(rows[0].sta, "2026-10-16T16:10:00.000Z");
});

Deno.test("便名や時刻が変なものは入れない", () => {
  assertEquals(scheduleRows([item("Friday", [obj("2026-01-01", "2026-12-31", "9時", "11:00"), obj("2026-01-01", "2026-12-31", "09:00", "11:00", "")])], ["2026-10-16"], "JAL").length, 0);
});

Deno.test("日本時間の今日から2日ぶん", () => {
  assertEquals(jstDates(new Date("2026-10-15T16:00:00Z"), 2), ["2026-10-16", "2026-10-17"]);
});
