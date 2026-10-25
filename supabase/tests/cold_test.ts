import { assertEquals } from "jsr:@std/assert@1";
import { coldBefore, coldPath, gunzip, gzip, tracksFrom } from "../functions/_shared/cold.ts";

Deno.test("置き場所と、移す日の境目（日本時間で400日前）", () => {
  assertEquals(coldPath("reg_legs", "2025-09-01"), "reg_legs/2025/2025-09-01.json.gz");
  assertEquals(coldBefore(Date.parse("2026-10-22T03:00:00Z")), "2025-09-17");
});
Deno.test("圧縮して戻せる", async () => {
  const s = JSON.stringify({ rows: Array.from({ length: 500 }, (_, i) => ({ i, p: "abc" })) });
  const z = await gzip(s); assertEquals(z.length < s.length / 5, true); assertEquals(await gunzip(z), s);
});
Deno.test("空の道すじの取り出し：全機の航跡と、便の航跡（出発・到着の空港から）", () => {
  assertEquals(tracksFrom("airport_tracks_all", [{ iata: "HND", dep_here: 1, pts: "a" }, { iata: "KIX", dep_here: 0, pts: "b" }], "HND"), [{ d: 1, p: "a" }]);
  assertEquals(tracksFrom("airport_tracks_all", [{ iata: "HND", dep_here: 0, pts: "c", at: "2026-10-24T03:20:00Z" }], "HND"), [{ d: 0, p: "c", h: 12 }]);   // 日本時間の「時」も
  assertEquals(tracksFrom("flight_tracks", [{ dep: "HND", arr: "ITM", pts: "a" }, { dep: "CTS", arr: "HND", pts: "b" }, { dep: "FUK", arr: "OKA", pts: "c" }], "HND"), [{ d: 1, p: "a" }, { d: 0, p: "b" }]);
});
