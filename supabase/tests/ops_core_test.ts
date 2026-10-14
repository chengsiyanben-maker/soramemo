// 運用の判定の中心（_shared/ops_core.js）が、画面（src/index.html の <ops-core> の部分）と同じであること、と判定の決まりのテスト
import { assertEquals } from "jsr:@std/assert@1";
import { OPS_AIRPORTS, observeOps } from "../functions/_shared/ops_core.js";

Deno.test("ops_core.js は src/index.html の <ops-core> の部分を写した最新のもの（違えば node tools/sync_ops_core.mjs）", async () => {
  const src = await Deno.readTextFile(new URL("../../src/index.html", import.meta.url));
  const cur = await Deno.readTextFile(new URL("../functions/_shared/ops_core.js", import.meta.url));
  const parts = [...src.matchAll(/\/\/ <ops-core>[^\n]*\n([\s\S]*?)\/\/ <\/ops-core>\n/g)].map((m) => m[1]);
  assertEquals(parts.length, 2);
  for (const p of parts) assertEquals(cur.includes(p), true);
});

Deno.test("14空港すべてに、風からの推定が出る", () => {
  // deno-lint-ignore no-explicit-any
  const defs = Object.values(OPS_AIRPORTS) as any[];
  assertEquals(defs.length, 14);
  for (const d of defs) { const e = d.estimate({ wdir: 200, wspd: 12, vis_m: 9999, time: new Date().toISOString() }); assertEquals(typeof d.modes[e.mode]?.label, "string"); }
});

Deno.test("福岡：追い風10kt以下なら16運用、仙台：風が弱ければ27着陸・09離陸", () => {
  // deno-lint-ignore no-explicit-any
  const A = OPS_AIRPORTS as any;
  assertEquals(A.FUK.estimate({ wdir: 330, wspd: 6 }).mode, "a");
  assertEquals(A.FUK.estimate({ wdir: 330, wspd: 14 }).mode, "b");
  assertEquals(A.SDJ.estimate({ wdir: null, wspd: 2 }).mode, "p");
  assertEquals(A.SDJ.estimate({ wdir: 90, wspd: 12 }).mode, "a");
});

Deno.test("機体がいなければ判定しない", () => {
  // deno-lint-ignore no-explicit-any
  for (const d of Object.values(OPS_AIRPORTS) as any[]) assertEquals(observeOps([], d), null);
});
