import { assertEquals } from "jsr:@std/assert@1";
import { isUniqueViolation, parseClientId, replayBody } from "../functions/_shared/checkin_idem.ts";

Deno.test("端末の ID：UUID の形だけ受け付け、小文字にそろえる", () => {
  assertEquals(parseClientId("0193A6F2-7B1C-7D2E-8F00-1234567890AB"), "0193a6f2-7b1c-7d2e-8f00-1234567890ab"); // v7
  assertEquals(parseClientId(" 3f2504e0-4f89-41d3-9a0c-0305e82c3301 "), "3f2504e0-4f89-41d3-9a0c-0305e82c3301"); // v4・前後の空白
  assertEquals(parseClientId(undefined), null);
  assertEquals(parseClientId(123), null);
  assertEquals(parseClientId("01ARZ3NDEKTSV4RRFFQ69G5FAV"), null); // ULID の字のままは受け付けない（UUID にして送ってもらう）
  assertEquals(parseClientId("00000000-0000-0000-0000-000000000000"), null);
  assertEquals(parseClientId("3f2504e0-4f89-41d3-9a0c-0305e82c3301; drop table"), null);
});

Deno.test("一意の索引にぶつかったかは 23505 だけで決める", () => {
  assertEquals(isUniqueViolation({ code: "23505", message: "duplicate key" }), true);
  assertEquals(isUniqueViolation({ code: "23503" }), false);
  assertEquals(isUniqueViolation(null), false);
});

const row = { id: 10, airport_id: 1, terminal_id: "HND-T1", created_at: "2026-11-26T00:00:00Z", flags: ["offline"], weather: "clear", wind_kt: 8, ops: "北風" };

Deno.test("送り直しの返事は1回目と同じ形（dup つき・ボーナスは空）", () => {
  const fl = { id: 5, from_airport: 2, to_airport: 1, dep_at: "2026-11-25T22:00:00Z", arr_at: "2026-11-26T00:00:00Z", distance_km: 500 };
  const r = replayBody(row, fl, 0, 0);
  assertEquals(r.ok, true);
  assertEquals(r.dup, true);
  assertEquals(r.at, row.created_at);
  assertEquals(r.flight, fl);
  assertEquals(r.first_airport, true);
  assertEquals(r.first_terminal, true);
  assertEquals(r.bonus, []);
  assertEquals(r.flags, ["offline"]);
  assertEquals(Object.keys(r).sort(), ["airport_id", "at", "bonus", "dup", "first_airport", "first_terminal", "flags", "flight", "ok", "ops", "terminal_id", "weather", "wind_kt"]);
});

Deno.test("前に同じ空港の印があれば初訪問ではない・ターミナルがなければ first_terminal は false", () => {
  const r = replayBody({ ...row, terminal_id: null, flags: null }, null, 3, 0);
  assertEquals(r.first_airport, false);
  assertEquals(r.first_terminal, false);
  assertEquals(r.flight, null);
  assertEquals(r.flags, []);
});
