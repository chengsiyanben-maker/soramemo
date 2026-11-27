import { assertEquals } from "jsr:@std/assert@1";
import { parseFeedback } from "../functions/_shared/feedback.ts";

const base = { kind: "bug", body: "  印が押せません  ", session: "abc12345" };

Deno.test("parseFeedback：決まった形だけを通し、本文の前後の空白を除く", () => {
  const r = parseFeedback({ ...base, app_version: "2026.11.27", screen: "home", device: "ios", last_error: "checkin", airport: "hnd" });
  assertEquals(r, { ok: true, row: { kind: "bug", body: "印が押せません", session: "abc12345", app_version: "2026.11.27", screen: "home", device: "ios", last_error: "checkin", airport: "HND" } });
});

Deno.test("parseFeedback：位置・メール・IP などの余計なものは捨てる", () => {
  const r = parseFeedback({ ...base, lat: 35.5, lon: 139.7, email: "a@b.jp", ip: "1.2.3.4", user_id: "00000000-0000-0000-0000-000000000001" });
  assertEquals(r.ok, true);
  if (r.ok) assertEquals(Object.keys(r.row).sort(), ["airport", "app_version", "body", "device", "kind", "last_error", "screen", "session"]);
});

Deno.test("parseFeedback：自動の付けたしの形が違えば、その項目だけ捨てる", () => {
  const r = parseFeedback({ ...base, screen: "Home Screen!", device: "x".repeat(30), last_error: "TypeError: x", airport: "羽田" });
  assertEquals(r.ok && [r.row.screen, r.row.device, r.row.last_error, r.row.airport], [null, null, null, null]);
});

Deno.test("parseFeedback：種類・本文・起動の値が足りなければ断る", () => {
  assertEquals(parseFeedback({ ...base, kind: "other" }), { ok: false, error: "bad_kind" });
  assertEquals(parseFeedback({ ...base, body: "   " }), { ok: false, error: "empty" });
  assertEquals(parseFeedback({ ...base, body: "あ".repeat(2001) }), { ok: false, error: "too_long" });
  assertEquals(parseFeedback({ ...base, body: "あ".repeat(2000) }).ok, true);
  assertEquals(parseFeedback({ ...base, session: "ABC" }), { ok: false, error: "bad_session" });
  assertEquals(parseFeedback(null), { ok: false, error: "bad_kind" });
  assertEquals(parseFeedback([base]), { ok: false, error: "bad_kind" });
});
