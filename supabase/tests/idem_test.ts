import { assertEquals } from "jsr:@std/assert@1";
import { againBody, isUniqueViolation, parseCid } from "../functions/_shared/idem.ts";

Deno.test("parseCid：UUIDv7・v4 は小文字にして通す", () => {
  assertEquals(parseCid("0193A1B2-C3D4-7E5F-8A9B-0C1D2E3F4A5B"), "0193a1b2-c3d4-7e5f-8a9b-0c1d2e3f4a5b");
  assertEquals(parseCid("f47ac10b-58cc-4372-a567-0e02b2c3d479"), "f47ac10b-58cc-4372-a567-0e02b2c3d479");
});

Deno.test("parseCid：形の違うものは null（ID なしで前と同じ動き）", () => {
  for (const v of [undefined, null, 1, "", "abc", "f47ac10b58cc4372a5670e02b2c3d479", "00000000-0000-0000-0000-000000000000", "f47ac10b-58cc-4372-c567-0e02b2c3d479", "f47ac10b-58cc-4372-a567-0e02b2c3d479' or 1=1"]) {
    assertEquals(parseCid(v), null, String(v));
  }
});

Deno.test("isUniqueViolation：23505 と duplicate key だけ", () => {
  assertEquals(isUniqueViolation({ code: "23505" }), true);
  assertEquals(isUniqueViolation({ message: 'duplicate key value violates unique constraint "checkins_user_cid"' }), true);
  assertEquals(isUniqueViolation({ code: "23503" }), false);
  assertEquals(isUniqueViolation(null), false);
});

Deno.test("againBody：1回目の印をそのまま・初めての演出とボーナスは出さない", () => {
  const ci = { id: 5, airport_id: 3, terminal_id: "HND-T2", created_at: "2026-11-26T01:00:00Z", flags: ["low_accuracy"], weather: "rain", wind_kt: 12, ops: "北風" };
  const fl = { id: 9, from_airport: 1, to_airport: 3, dep_at: "2026-11-25T23:00:00Z", arr_at: "2026-11-26T01:00:00Z", distance_km: 500 };
  const b = againBody(ci, fl);
  assertEquals(b.ok, true); assertEquals(b.again, true); assertEquals(b.at, ci.created_at);
  assertEquals(b.first_airport, false); assertEquals(b.first_terminal, false); assertEquals(b.bonus, []);
  assertEquals(b.flight, fl); assertEquals(b.flags, ["low_accuracy"]); assertEquals(b.ops, "北風");
  assertEquals(againBody({ ...ci, terminal_id: null, flags: null }, null).flight, null);
  assertEquals(againBody({ ...ci, flags: null }, null).flags, []);
});
