import { assertEquals } from "jsr:@std/assert@1";
import { callsignFor, match, type OpenSkyFlight } from "../functions/_shared/verify.ts";

const t = (s: string) => Date.parse(s);
const sec = (s: string) => Math.floor(Date.parse(s) / 1000);
// 羽田 → 新千歳：羽田で 08:10 にチェックイン、新千歳で 10:05 にチェックイン
const f = { fromIcao: "RJTT", toIcao: "RJCC", dep: t("2026-10-03T08:10:00+09:00"), arr: t("2026-10-03T10:05:00+09:00"), flightNo: "JL501" };
const ok: OpenSkyFlight = { icao24: "86e1a0", callsign: "JAL501  ", estDepartureAirport: "RJTT", estArrivalAirport: "RJCC", firstSeen: sec("2026-10-03T08:32:00+09:00"), lastSeen: sec("2026-10-03T09:58:00+09:00") };
const other: OpenSkyFlight = { ...ok, icao24: "86e2b1", callsign: "ANA61   " };

Deno.test("便名→コールサイン", () => {
  assertEquals(callsignFor("JL501"), "JAL501"); assertEquals(callsignFor("NH0061"), "ANA61"); assertEquals(callsignFor("6J21"), "SNJ21");
  assertEquals(callsignFor("XX12"), null); assertEquals(callsignFor(null), null);
});
Deno.test("便名・空港・時間帯が合えば運航確認済み", () => {
  const v = match(f, [other, ok]); assertEquals(v.status, "verified"); if (v.status === "verified") assertEquals(v.byCallsign, true);
});
Deno.test("便名が違う機体しかなければ確認できない", () => assertEquals(match(f, [other]).status, "unmatched"));
Deno.test("出発空港が違えば確認できない", () => assertEquals(match(f, [{ ...ok, estDepartureAirport: "RJAA" }]).status, "unmatched"));
Deno.test("到着の推定が空でも、出発と時間帯と便名が合えば確認", () => assertEquals(match(f, [{ ...ok, estArrivalAirport: null }]).status, "verified"));
Deno.test("到着チェックインより2時間後の着陸は対象外", () =>
  assertEquals(match(f, [{ ...ok, lastSeen: sec("2026-10-03T12:05:00+09:00") }]).status, "unmatched"));
Deno.test("到着チェックインの15分後まで（駐機まで電波が続く）は認める", () =>
  assertEquals(match(f, [{ ...ok, lastSeen: sec("2026-10-03T10:20:00+09:00") }]).status, "verified"));
Deno.test("到着記録が1件もなければ運航データなし", () => assertEquals(match(f, []).status, "no_data"));
Deno.test("便名なし：空港と時間帯の一致だけで確認", () => {
  const v = match({ ...f, flightNo: null }, [other]); assertEquals(v.status, "verified"); if (v.status === "verified") assertEquals(v.byCallsign, false);
});
Deno.test("大昔に飛び立った機体（前日の便など）は除く", () =>
  assertEquals(match({ ...f, flightNo: null }, [{ ...ok, firstSeen: sec("2026-10-03T05:00:00+09:00") }]).status, "unmatched"));
