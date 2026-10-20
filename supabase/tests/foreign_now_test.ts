// 空港の近くにいる海外の航空会社の便（推定）
import { assertEquals } from "jsr:@std/assert@1";
import { foreignFlightOf } from "../functions/_shared/flight_watch.ts";
import { classifyForeign, foreignNear, type LivePos, parseRoutes } from "../functions/_shared/foreign_now.ts";

const HND = { lat: 35.5533, lon: 139.7811 };
const P = (o: Partial<LivePos>): LivePos => ({ callsign: "KAL2707", lat: 35.7, lon: 139.9, alt_ft: 4000, ground: false, fpm: -800, type: "A333", reg: "HL7789", seen_at: "2026-10-20T03:00:00Z", ...o });

Deno.test("呼び出し符号 → 海外の航空会社の便名", () => {
  assertEquals(foreignFlightOf("KAL703"), { flight: "KE703", airline: "KE" });
  assertEquals(foreignFlightOf("TZP0021"), { flight: "ZG21", airline: "ZG" });
  assertEquals(foreignFlightOf("UAL837"), { flight: "UA837", airline: "UA" });
  assertEquals(foreignFlightOf("ANA106"), null);   // 日本の航空会社
  assertEquals(foreignFlightOf("JTA41"), null);
  assertEquals(foreignFlightOf("JA12AB"), null);   // 呼び出し符号の形でない
  assertEquals(foreignFlightOf("XYZ123"), null);   // 表にない会社
});

Deno.test("空港から60km以内の海外の航空会社だけ、近い順", () => {
  const n = foreignNear([P({ callsign: "UAL837", lat: 35.9 }), P({}), P({ callsign: "ANA5", lat: 35.6 }), P({ callsign: "CPA500", lat: 37.5 })], HND, 60);
  assertEquals(n.map((x) => x.flight), ["KE2707", "UA837"]);
});

Deno.test("経路のデータを読む（もっともらしいものだけ・途中の空港は最初と最後）", () => {
  const r = parseRoutes([{ callsign: "KAL2707", _airport_codes_iata: "GMP-HND", plausible: 1 }, { callsign: "UAL837", _airport_codes_iata: "SFO-HND", plausible: false },
    { callsign: "CPA500", _airport_codes_iata: "HKG-TPE-HND", plausible: true }, { callsign: "X", _airport_codes_iata: "unknown", plausible: true }]);
  assertEquals([...r.values()].map((x) => `${x.callsign}:${x.dep}-${x.arr}`), ["KAL2707:GMP-HND", "CPA500:HKG-HND"]);
});

Deno.test("答えに呼び出し符号がなければ、問い合わせた順で対応させる", () => {
  const r = parseRoutes([{ _airport_codes_iata: "GMP-HND", plausible: 1 }, { _airport_codes_iata: "HND-SFO", plausible: 1 }], ["KAL2707", "UAL838"]);
  assertEquals([...r.values()].map((x) => `${x.callsign}:${x.dep}-${x.arr}`), ["KAL2707:GMP-HND", "UAL838:HND-SFO"]);
});

Deno.test("この空港に着く便・出た便に分ける", () => {
  const near = foreignNear([P({}), P({ callsign: "UAL838", lat: 35.56, lon: 139.79, ground: true, alt_ft: null }), P({ callsign: "CPA501", lat: 35.4, alt_ft: 9000, fpm: 2000 }),
    P({ callsign: "THA661", lat: 35.9, lon: 140.3, ground: true, alt_ft: null }), P({ callsign: "EVA197", lat: 35.8 })], HND, 60);
  const rt = parseRoutes([{ callsign: "KAL2707", _airport_codes_iata: "GMP-HND", plausible: 1 }, { callsign: "UAL838", _airport_codes_iata: "HND-SFO", plausible: 1 },
    { callsign: "CPA501", _airport_codes_iata: "HND-HKG", plausible: 1 }, { callsign: "THA661", _airport_codes_iata: "BKK-HND", plausible: 1 },
    { callsign: "EVA197", _airport_codes_iata: "TPE-NRT", plausible: 1 }]);
  const c = classifyForeign(near, rt, "HND");
  assertEquals(c.map((x) => `${x.flight}:${x.kind}:${x.other}:${x.status}`).sort(), ["CX501:dep:HKG:departed", "KE2707:arr:GMP:approach", "UA838:dep:SFO:ground"]);
  // 地上で空港から遠い機体（成田にいる THA661）と、ほかの空港の便（EVA197 は成田行き）は入れない
});
