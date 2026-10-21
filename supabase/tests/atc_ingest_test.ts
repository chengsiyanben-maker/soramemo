import { assertEquals } from "jsr:@std/assert@1";
import { checkIn, parseAtc, sameMsg, verified } from "../functions/_shared/atc_ingest.ts";

const NOW = Date.parse("2026-10-21T10:00:00Z");
Deno.test("送られてきた形を確かめる", () => {
  assertEquals(typeof checkIn({ iata: "HND", ch: "gnd", text: "All Nippon 106 taxi", at: NOW }, NOW), "object");
  assertEquals(checkIn({ iata: "KIX", ch: "gnd", text: "abc def", at: NOW }, NOW), "unsupported airport");
  assertEquals(checkIn({ iata: "HND", ch: "xx", text: "abc def", at: NOW }, NOW), "bad channel");
  assertEquals(checkIn({ iata: "HND", ch: "twr", text: "abc def", at: NOW - 3600_000 }, NOW), "bad time");
  const m = checkIn({ iata: "HND", ch: "twr", text: "x".repeat(900), at: NOW, freq: "118.10", conf: 2 }, NOW) as { text: string; freq: string; conf: number | null };
  assertEquals(m.text.length, 400); assertEquals(m.freq, "118.10"); assertEquals(m.conf, null);
});
Deno.test("近くを飛んでいる機体と合うものだけ出す", () => {
  const p = parseAtc("Japan Air 123, runway 22, cleared to land");
  const near = { lat: 35.60, lon: 139.85, seen_at: new Date(NOW - 60_000).toISOString() };
  assertEquals(verified(p, "HND", "twr", near, NOW), true);
  assertEquals(verified(p, "HND", "twr", { ...near, lat: 34.7, lon: 135.4 }, NOW), false);       // 伊丹のあたり
  assertEquals(verified(p, "HND", "twr", { ...near, seen_at: new Date(NOW - 30 * 60_000).toISOString() }, NOW), false);
  assertEquals(verified(p, "HND", "twr", null, NOW), false);
  assertEquals(verified(parseAtc("roger"), "HND", "twr", near, NOW), false);
});
Deno.test("同じ交信の重なり", () => {
  assertEquals(sameMsg({ callsign: "JAL123", ja: "a", at: NOW }, { callsign: "JAL123", ja: "a", at: NOW + 6000 }), true);
  assertEquals(sameMsg({ callsign: "JAL123", ja: "a", at: NOW }, { callsign: "JAL123", ja: "a", at: NOW + 20000 }), false);
  assertEquals(sameMsg({ callsign: null, ja: "a", at: NOW }, { callsign: null, ja: "a", at: NOW }), false);
});
