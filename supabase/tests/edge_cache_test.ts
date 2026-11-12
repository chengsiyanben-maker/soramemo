// 関数どうしで使い回す置き場（edge_cache）：記憶と置き場の新しいほうを選ぶ・古ければ配信元へ・置き場が使えなくても止まらない
import { assertEquals } from "jsr:@std/assert@1";
import { choose, readShared, writeShared } from "../functions/_shared/edge_cache.ts";

const NOW = 1_800_000_000_000, TTL = 5 * 60_000;
Deno.test("どちらもなければ配信元へ（fresh も stale もない）", () => {
  assertEquals(choose(undefined, undefined, TTL, NOW), { fresh: null, stale: null });
});
Deno.test("記憶が新しければ記憶、置き場が新しければ置き場", () => {
  const mem = { at: NOW - 60_000, v: "mem" }, sh = { at: NOW - 30_000, v: "shared" };
  assertEquals(choose(mem, sh, TTL, NOW).fresh?.v, "shared");
  assertEquals(choose({ ...mem, at: NOW - 10_000 }, sh, TTL, NOW).fresh?.v, "mem");
});
Deno.test("新しい入れ物（記憶が空）でも、置き場が ttl 以内ならそのまま使う", () => {
  assertEquals(choose(undefined, { at: NOW - TTL + 1, v: 1 }, TTL, NOW).fresh?.v, 1);
});
Deno.test("ttl を過ぎたら stale（配信元が取れないときの代わり）", () => {
  const r = choose(undefined, { at: NOW - TTL, v: 2 }, TTL, NOW);
  assertEquals(r.fresh, null); assertEquals(r.stale?.v, 2);
});
Deno.test("「通報がない」（null）も ttl の間は使い回す（配信元に何度も聞かない）", () => {
  const r = choose(undefined, { at: NOW - 1000, v: null }, TTL, NOW);
  assertEquals(r.fresh?.v, null); assertEquals(r.fresh !== null, true);
});
Deno.test("時刻の読めない行は使わない", () => {
  assertEquals(choose(undefined, { at: NaN, v: 3 }, TTL, NOW), { fresh: null, stale: null });
});

// 置き場の読み書き（Supabase の呼び出しの形だけをまねる）
function fakeAdmin(opts: { fail?: boolean; throws?: boolean } = {}) {
  const rows = new Map<string, { key: string; body: unknown; at: string }>(), calls: string[] = [];
  return { rows, calls, from(t: string) {
    calls.push(t);
    if (opts.throws) throw new Error("down");
    return {
      select: () => ({ in: (_c: string, keys: string[]) => Promise.resolve(opts.fail ? { data: null, error: { message: "x" } } : { data: keys.filter((k) => rows.has(k)).map((k) => rows.get(k)), error: null }) }),
      upsert: (r: { key: string; body: unknown; at: string }) => { rows.set(r.key, r); return Promise.resolve({ error: null }); },
    };
  } };
}
Deno.test("書いた値を1回の読み出しでまとめて読める（ない鍵は入らない）", async () => {
  const a = fakeAdmin();
  await writeShared(a, "now:fl:HND", { arr: [], dep: [] }, NOW);
  await writeShared(a, "now:wx:RJTT", null, NOW - 1000);
  const m = await readShared(a, ["now:fl:HND", "now:wx:RJTT", "now:taf:RJTT"]);
  assertEquals(m.size, 2);
  assertEquals(m.get("now:fl:HND"), { at: NOW, v: { arr: [], dep: [] } });
  assertEquals(m.get("now:wx:RJTT"), { at: NOW - 1000, v: null });
  assertEquals(a.calls.filter((c) => c === "edge_cache").length, 3);   // 書く2回＋読む1回
});
Deno.test("鍵がなければ置き場を読まない", async () => {
  const a = fakeAdmin();
  assertEquals((await readShared(a, [])).size, 0);
  assertEquals(a.calls.length, 0);
});
Deno.test("置き場がエラー・例外でも止まらない（空として配信元へ）", async () => {
  assertEquals((await readShared(fakeAdmin({ fail: true }), ["metar:RJTT"])).size, 0);
  assertEquals((await readShared(fakeAdmin({ throws: true }), ["metar:RJTT"])).size, 0);
  await writeShared(fakeAdmin({ throws: true }), "metar:RJTT", { id: "RJTT" });   // 例外を外に出さない
});
