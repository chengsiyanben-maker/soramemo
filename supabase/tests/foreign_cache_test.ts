// airport-foreign の置き場の使い方：60秒以内はそのまま・作れないときは10分以内の古い答え・それより古ければ作った答え
import { assertEquals } from "jsr:@std/assert@1";
import { pickForeign, STALE_MAX } from "../functions/_shared/foreign_cache.ts";

const NOW = 1_800_000_000_000, TTL = 60_000, body = { iata: "HND", planes: [] };
Deno.test("置き場が60秒以内ならそのまま使う（位置も経路も読まない）", () => {
  assertEquals(pickForeign({ at: NOW - 59_000, v: body }, null, TTL, NOW).use, "fresh");
});
Deno.test("置き場がなければ作る", () => {
  assertEquals(pickForeign(undefined, null, TTL, NOW).use, "build");
  assertEquals(pickForeign(undefined, "routeset 503", TTL, NOW).use, "build");
});
Deno.test("60秒を過ぎていて今回ちゃんと作れたら、作った答え", () => {
  assertEquals(pickForeign({ at: NOW - TTL, v: body }, null, TTL, NOW).use, "build");
});
Deno.test("経路が取れなかった回は、10分以内の古い答えを代わりに出す", () => {
  assertEquals(pickForeign({ at: NOW - 5 * 60_000, v: body }, "routeset 503", TTL, NOW).use, "stale");
});
Deno.test("10分より古い答えは代わりにも出さない（作った答え。経路なしでも位置は新しい）", () => {
  assertEquals(pickForeign({ at: NOW - STALE_MAX, v: body }, "routeset 503", TTL, NOW).use, "build");
});
Deno.test("中身のない行・時刻の読めない行は使わない", () => {
  assertEquals(pickForeign({ at: NOW - 1000, v: null }, null, TTL, NOW).use, "build");
  assertEquals(pickForeign({ at: NaN, v: body }, "x", TTL, NOW).use, "build");
});
