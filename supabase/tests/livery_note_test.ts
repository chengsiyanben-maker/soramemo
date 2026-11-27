// 特別塗装機の知らせを1便で1つに・夜の静かな時間（livery_note.ts。11/25 見直し2回目の4番）
import { assertEquals } from "jsr:@std/assert@1";
import { awake, liveryTag, normFlight, quietWindow } from "../functions/_shared/livery_note.ts";
import { regFlyMessage } from "../functions/_shared/livery_push.ts";

Deno.test("予定（便名）・飛んでいる（呼び出し符号）・着陸に向かっている は同じ tag", () => {
  const plan = liveryTag({ flight: "JL0113" });
  assertEquals(plan, "sp-JL113");
  assertEquals(liveryTag({ callsign: "JAL113", reg: "JA339J" }), plan);
  assertEquals(liveryTag({ callsign: "JAL0113", reg: "JA339J" }), plan);
  assertEquals(regFlyMessage({ reg: "JA339J", name: "JAL Jubilee Express", airline: "JAL", callsign: "JAL113", alt_ft: 24300 }).tag, plan);
  assertEquals(liveryTag({ callsign: "ANA21", reg: "JA136A" }), liveryTag({ flight: "NH21" }));
  // 折り返しの便は別の通知
  assertEquals(liveryTag({ callsign: "JAL114" }) === plan, false);
});

Deno.test("便名が分からないときは登録記号、表にない会社の呼び出し符号はそのまま", () => {
  assertEquals(liveryTag({ callsign: null, reg: "JA339J" }), "sp-JA339J");
  assertEquals(liveryTag({ callsign: "", reg: "JA339J" }), "sp-JA339J");
  assertEquals(liveryTag({ callsign: "ZZZ0042", reg: "N1" }), "sp-ZZZ42");
  assertEquals(normFlight("nh0021"), "NH21");
});

Deno.test("書き換えでも鳴らす（renotify）", () => {
  assertEquals(regFlyMessage({ reg: "JA339J", name: "x", airline: "JAL", callsign: "JAL113", alt_ft: 24300 }).renotify, true);
});

Deno.test("夜の静かな時間（23〜7時）は quiet_night が false の人だけ。null・列なしは止める側", () => {
  const subs = [{ id: 1, quiet_night: true }, { id: 2, quiet_night: false }, { id: 3, quiet_night: null }, { id: 4 }];
  const at = (h: number, m = 0) => Date.parse(`2026-11-25T00:00:00Z`) + ((h - 9 + 24) % 24) * 3600_000 + m * 60_000;   // 日本時間 h時
  assertEquals(awake(subs, at(12)).map((s) => s.id), [1, 2, 3, 4]);
  assertEquals(awake(subs, at(22, 59)).map((s) => s.id), [1, 2, 3, 4]);
  assertEquals(awake(subs, at(23)).map((s) => s.id), [2]);
  assertEquals(awake(subs, at(3)).map((s) => s.id), [2]);
  assertEquals(awake(subs, at(6, 59)).map((s) => s.id), [2]);
  assertEquals(awake(subs, at(7)).map((s) => s.id), [1, 2, 3, 4]);
});

Deno.test("朝の送り直しの幅は日本時間の前の日23時〜今日7時", () => {
  const now = Date.parse("2026-11-25T00:30:00Z");   // 日本時間 9:30
  assertEquals(quietWindow(now), { from: "2026-11-24T14:00:00.000Z", to: "2026-11-24T22:00:00.000Z" });
  const late = Date.parse("2026-11-25T14:30:00Z");   // 日本時間 23:30（静かな時間なので呼ばれないが、幅はその日の朝）
  assertEquals(quietWindow(late).to, "2026-11-24T22:00:00.000Z");
});
