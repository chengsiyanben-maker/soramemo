import { assertEquals } from "jsr:@std/assert@1";
import { isSnow, metarRow, tcKey, wxTokens } from "../functions/_shared/wx_archive.ts";

Deno.test("METAR の天気の現象を取り出す", () => {
  assertEquals(wxTokens("ROAH 231700Z 36045G62KT 3000 +SHRA BR FEW005 BKN010 26/24 Q0985 RMK TS"), "+SHRA BR");
  assertEquals(wxTokens("RJCC 240000Z 32012KT 1200 -SN BLSN FEW010 M05/M07 Q1001"), "-SN BLSN");
  assertEquals(wxTokens("RJTT 240000Z 34008KT 9999 FEW030 15/08 Q1020 NOSIG"), null);
  assertEquals(wxTokens("RJAA 240000Z 05010KT 2000 FZRA BR OVC005 00/M01 Q1010"), "FZRA BR");
});
Deno.test("雪の日の判定", () => {
  assertEquals(isSnow("-SN BLSN"), true); assertEquals(isSnow("FZRA BR"), true); assertEquals(isSnow("+SHRA BR"), false); assertEquals(isSnow(null), false);
});
Deno.test("METAR の1件を記録の行に", () => {
  const r = metarRow({ icaoId: "ROAH", obsTime: 1792774800, rawOb: "ROAH 231700Z 36045G62KT 3000 +SHRA BR FEW005 26/24 Q0985", wdir: 360, wspd: 45, wgst: 62 });
  assertEquals(r?.icao, "ROAH"); assertEquals(r?.wx, "+SHRA BR"); assertEquals(r?.wgst, 62); assertEquals(r?.vis_m, 3000); assertEquals(r?.at, new Date(1792774800 * 1000).toISOString());
  assertEquals(metarRow({ icaoId: "x", rawOb: "" }), null);
});
Deno.test("台風の一覧の1件", () => {
  const k = tcKey({ tropicalCyclone: "TC2636", typhoonNumber: "2630", category: "TY", issue: "2026-10-23T22:45:00+09:00" });
  assertEquals(k, { tc_id: "TC2636", issue: "2026-10-23T13:45:00.000Z", number: "2630", category: "TY" });
  assertEquals(tcKey({ tropicalCyclone: "bad" }), null);
});
