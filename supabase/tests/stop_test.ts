import { assertEquals } from "jsr:@std/assert@1";
import { tokenOk, cleanMessage, DEFAULT_MESSAGE } from "../functions/_shared/stop.ts";

Deno.test("合言葉が一致したときだけ通す", () => {
  assertEquals(tokenOk("abc123", "abc123"), true);
  assertEquals(tokenOk("abc124", "abc123"), false);
  assertEquals(tokenOk("abc12", "abc123"), false);      // 長さが違う
  assertEquals(tokenOk("abc1234", "abc123"), false);
});

Deno.test("合言葉が未設定、または渡されていないときは必ず拒否", () => {
  assertEquals(tokenOk(null, "abc123"), false);
  assertEquals(tokenOk("", "abc123"), false);
  assertEquals(tokenOk("", ""), false);
  assertEquals(tokenOk("x", ""), false);
});

Deno.test("利用者に見せる文は、空なら既定の文、長すぎれば200字で切る", () => {
  assertEquals(cleanMessage(undefined), DEFAULT_MESSAGE);
  assertEquals(cleanMessage("   "), DEFAULT_MESSAGE);
  assertEquals(cleanMessage(123), DEFAULT_MESSAGE);
  assertEquals(cleanMessage("  点検中です  "), "点検中です");
  assertEquals(cleanMessage("あ".repeat(300)).length, 200);
});
