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

Deno.test("まだ始まっていない塗装（from）は出さず、終わる日のあるアライアンス塗装は外れる。スカイチームの名前", () => {
  const m = liveryMap(new Date("2026-10-26"));
  assertEquals(m.has("JA56AN"), false);   // ポケモンジェット 青：就航日が未発表
  assertEquals(m.has("JA609A"), true);
  assertEquals(m.has("HL7730"), true);
  assertEquals(liveryMap(new Date("2026-12-17")).has("HL7730"), false);   // アシアナはスカイチームへ
  assertEquals(m.get("VN-A897")?.name.startsWith("スカイチーム塗装"), true);
  assertEquals(m.get("N375HA")?.name.startsWith("ワンワールド塗装"), true);
  assertEquals(m.has("JA731A") || m.has("9V-SRI") || m.has("JA604J"), false);   // 退役・塗り替えで消したもの
});
