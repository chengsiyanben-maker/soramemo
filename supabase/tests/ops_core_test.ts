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

// 2026-10-15 10:32 の鹿児島（実際の機体）：34 へ着陸に向かう1機（JL3740）と 34 から離陸した1機（SKY381）。JA04KM は訓練の小型機
const KOJ_1015 = [{"id":"841087","callsign":"JA04KM","lat":31.7997,"lon":130.7236,"alt_ft":2525,"phase":"dep","trail":[[31.6638,130.8161],[31.667,130.8106],[31.6789,130.8023],[31.6932,130.794],[31.7061,130.7851],[31.7195,130.7759],[31.733,130.767],[31.7369,130.7643],[31.7454,130.7585],[31.7576,130.7502],[31.7698,130.7423],[31.7823,130.7342],[31.7967,130.7253],[31.7997,130.7236]]},{"id":"84178e","callsign":"JL3740","lat":31.7154,"lon":130.7759,"alt_ft":2400,"phase":"arr","trail":[[31.664,130.5881],[31.6693,130.6081],[31.6709,130.6496],[31.6696,130.6854],[31.6694,130.6931],[31.6691,130.7157],[31.6687,130.7448],[31.6735,130.7723],[31.6853,130.78],[31.7116,130.7778],[31.7154,130.7759]]},{"id":"86808a","callsign":"SKY381","lat":31.7716,"lon":130.6033,"alt_ft":6950,"phase":"dep","trail":[[31.8073,130.7168],[31.8276,130.7033],[31.8336,130.6996],[31.8489,130.6902],[31.8607,130.6674],[31.8478,130.6379],[31.8145,130.6248],[31.7785,130.6099],[31.7716,130.6033]]}];
Deno.test("便の少ない空港：着陸1機と離陸1機が同じ運用なら判定する。登録記号で飛ぶ小型機は数えない", () => {
  // deno-lint-ignore no-explicit-any
  const A = OPS_AIRPORTS as any, rw34 = A.KOJ.modes.a.arr.includes("34") ? "a" : "b";
  // deno-lint-ignore no-explicit-any
  const r = observeOps(KOJ_1015, A.KOJ) as any;
  assertEquals(r?.mode, rw34);
  assertEquals(r?.n, { "34": 1 });
  assertEquals(r?.dep, 1);
  // 着陸機だけ（1機）では判定しない
  assertEquals(observeOps(KOJ_1015.filter((p) => p.callsign === "JL3740"), A.KOJ), null);
  // 小型機（登録記号）だけでは判定しない
  assertEquals(observeOps(KOJ_1015.filter((p) => p.callsign === "JA04KM"), A.KOJ), null);
});
