// 特別塗装機の一覧：登録記号がデータベースに入る形・出典が https・重複なし
import { assertEquals } from "jsr:@std/assert@1";
import { LIVERIES, liveryMap } from "../functions/_shared/liveries.ts";

Deno.test("特別塗装機の一覧は、登録記号の形・出典・重複がそろっている（海外の機体も）", () => {
  const re = /^[A-Z0-9]{1,3}-?[A-Z0-9]{2,6}$/;   // supabase/migrations の livery_sightings_reg_check と同じ
  for (const l of LIVERIES) {
    assertEquals(re.test(l.reg) && l.reg.length <= 10, true, l.reg);
    assertEquals(l.src.startsWith("https://"), true, l.reg);
    assertEquals(l.name.length > 0 && l.name.length <= 80 && l.airline.length <= 40, true, l.reg);
  }
  assertEquals(new Set(LIVERIES.map((l) => l.reg)).size, LIVERIES.length);
  assertEquals(liveryMap(new Date("2026-10-15")).has("9V-OJJ"), true);
  assertEquals(liveryMap(new Date("2027-05-01")).has("JA339J"), false);   // 期間が過ぎたものは外れる
});
