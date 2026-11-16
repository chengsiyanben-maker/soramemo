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
  assertEquals(m.has("HL7730"), false);   // 11/16 FR24 の出典しかなかったので外した
  assertEquals(m.get("VN-A897")?.name.startsWith("スカイチーム塗装"), true);
  assertEquals(m.get("N375HA")?.name.startsWith("ワンワールド塗装"), true);
  assertEquals(m.has("JA731A") || m.has("9V-SRI") || m.has("JA604J"), false);   // 退役・塗り替えで消したもの
});

Deno.test("2026-11 に足した塗装：GREEN×EXPO は就航日が出るまで出さない、J-AIR 30周年は 2027/3/31 まで", () => {
  const m = liveryMap(new Date("2026-11-03"));
  assertEquals(m.has("JA344J"), false);   // 11月就航予定（日は未発表）
  assertEquals(m.get("JA228J")?.name, "J-AIR 創立30周年記念機");
  assertEquals(liveryMap(new Date("2027-04-01")).has("JA228J"), false);
});

Deno.test("11/16 出典の差し替え：Flightradar24 の出典は1つもない。確かめた機体だけ残り、エバー・BA は報道の登録記号", () => {
  for (const l of LIVERIES) assertEquals(/(flightradar24|fr24)\./i.test(l.src), false, l.reg);
  const m = liveryMap(new Date("2026-11-16"));
  for (const r of ["B-17812", "B-16715", "B-16206", "VT-ALJ", "VT-ANU", "C-GHLM"]) assertEquals(m.get(r)?.name.startsWith("スターアライアンス塗装"), true, r);
  assertEquals(m.get("G-YMMR")?.name.startsWith("ワンワールド塗装"), true);
  for (const r of ["B-16701", "B-KPL", "A7-BAA", "N76021", "9V-SWI", "G-YMMU"]) assertEquals(m.has(r), false, r);
  assertEquals(m.get("N91007")?.src.includes("simpleflying.com"), true);
});
