import { assertEquals } from "jsr:@std/assert@1";
import { runVerification, type Row } from "../functions/_shared/verify_job.ts";
import type { OpenSkyFlight } from "../functions/_shared/verify.ts";

const t = (s: string) => Date.parse(s), sec = (s: string) => Math.floor(Date.parse(s) / 1000);
const rows: Row[] = [
  { id: 1, fromIcao: "RJTT", toIcao: "RJCC", dep: t("2026-10-03T08:10:00+09:00"), arr: t("2026-10-03T10:05:00+09:00"), flightNo: "JL501", attempts: 0 },
  { id: 2, fromIcao: "RJTT", toIcao: "RJCC", dep: t("2026-10-03T08:10:00+09:00"), arr: t("2026-10-03T10:05:00+09:00"), flightNo: "NH999", attempts: 0 }, // 便名違い
  { id: 3, fromIcao: "ROAH", toIcao: "ROIG", dep: t("2026-10-03T12:00:00+09:00"), arr: t("2026-10-03T13:30:00+09:00"), flightNo: null, attempts: 1 },     // 記録なし
  { id: 4, fromIcao: "RJTT", toIcao: null, dep: 0, arr: 1, flightNo: null, attempts: 0 },                                                            // ICAOなし
  { id: 5, fromIcao: "RJTT", toIcao: "RJFF", dep: t("2026-10-03T07:00:00+09:00"), arr: t("2026-10-03T09:10:00+09:00"), flightNo: "JL305", attempts: 2 }, // 通信エラー
];
const arrivals: Record<string, OpenSkyFlight[]> = {
  RJCC: [{ icao24: "a", callsign: "JAL501 ", estDepartureAirport: "RJTT", estArrivalAirport: "RJCC", firstSeen: sec("2026-10-03T08:32:00+09:00"), lastSeen: sec("2026-10-03T09:58:00+09:00") }],
  ROIG: [],
};

Deno.test("照合の実行：確認・便名違い・記録なし・ICAOなし・通信エラー", async () => {
  const saved: Record<number, [string | null, string, number]> = {};
  let calls = 0;
  const sum = await runVerification({
    loadFlights: async () => rows,
    fetchArrivals: async (icao) => { calls++; if (icao === "RJFF") throw new Error("503"); return arrivals[icao] ?? []; },
    save: async (id, status, note, attempts) => { saved[id] = [status, note, attempts]; },
  });
  assertEquals(sum, { checked: 5, verified: 1, no_data: 2, unmatched: 1, errors: 1 });
  assertEquals(saved[1][0], "verified"); assertEquals(saved[1][2], 1);
  assertEquals(saved[2], [null, "当てはまる便なし", 1]);
  assertEquals(saved[3], ["no_data", "到着記録なし", 2]);
  assertEquals(saved[4][0], "no_data");
  assertEquals(saved[5], undefined);          // 通信エラーは保存せず、次の晩にもう一度
  assertEquals(calls, 3);                     // 同じ空港・同じ時間帯（1と2）は1回の問い合わせで済む
});
