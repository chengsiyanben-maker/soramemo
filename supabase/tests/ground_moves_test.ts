import { assert, assertEquals } from "jsr:@std/assert@1";
import { type GPlane, groundStep, type GRunway, type GWatch, onRunway, rwyName } from "../functions/_shared/ground_moves.ts";
import { OPS_AIRPORTS, runwaysOf } from "../functions/_shared/ops_core.js";

// deno-lint-ignore no-explicit-any
const def = (OPS_AIRPORTS as any).HND, rw = runwaysOf(def);
const rws = Object.values(rw) as GRunway[];
const T0 = Date.parse("2026-11-25T03:00:00Z");
// C滑走路（34R の端 → 16L の端）の上の点：割合 f
const onC = (f: number): [number, number] => [rw["34R"].end[0] + (rw["34R"].opp[0] - rw["34R"].end[0]) * f, rw["34R"].end[1] + (rw["34R"].opp[1] - rw["34R"].end[1]) * f];
const STAND: [number, number] = [35.5495, 139.7855];   // 第1ターミナルの前あたり（滑走路から離れた所）
const pl = (at: [number, number], kt: number, hdg: number | null = null, id = "84a1b2"): GPlane => ({ id, callsign: "JAL123", lat: at[0], lon: at[1], hdg, kt, type: "B738", reg: "JA301J", moving: kt >= 5 });

function run(steps: (GPlane[])[]) {
  const watch = new Map<string, GWatch>(), moves = [];
  for (const [i, planes] of steps.entries()) {
    const r = groundStep("HND", rws, rw, planes, watch, T0 + i * 30_000);
    for (const u of r.upserts) watch.set(u.hex, u);
    for (const d of r.deletes) watch.delete(d);
    moves.push(...r.moves);
  }
  return { watch, moves };
}

Deno.test("滑走路の上かどうか・走っている向きの名前", () => {
  const r = onRunway({ lat: onC(0.5)[0], lon: onC(0.5)[1], hdg: 330 }, rws);
  assert(r && (r.id === "34R" || r.id === "16L"));
  assertEquals(rwyName({ hdg: Math.round(rw["34R"].hdg) }, r!, rws), "34R");
  assertEquals(rwyName({ hdg: Math.round(rw["16L"].hdg) }, r!, rws), "16L");
  assertEquals(onRunway({ lat: STAND[0], lon: STAND[1], hdg: null }, rws), null);
});

Deno.test("到着：着陸 → 地上を走る → スポットで止まる", () => {
  const h = Math.round(rw["34R"].hdg);
  const { moves, watch } = run([[pl(onC(0.3), 60, h)], [pl(onC(0.8), 20, h)], [pl([35.552, 139.79], 15, 270)], [pl(STAND, 8, 270)], [pl(STAND, 0)], [pl(STAND, 0)]]);
  assertEquals(moves.length, 1);
  const m = moves[0];
  assertEquals([m.kind, m.rwy, m.lost], ["arr", "34R", false]);
  assertEquals(m.taxi_sec, 120);                  // 0秒に着陸を見て、120秒に止まり始めた
  assertEquals([m.stand_lat, m.stand_lon], STAND);
  assertEquals(watch.get("84a1b2")?.mode, "park");
});

Deno.test("出発：止まっている → 動き出す → 滑走路で速く → 見えなくなる＝離陸", () => {
  const h = Math.round(rw["16L"].hdg);
  const { moves, watch } = run([[pl(STAND, 0)], [pl(STAND, 0)], [pl(STAND, 0)], [pl([35.552, 139.79], 12, 90)], [pl(onC(0.95), 10, h)], [pl(onC(0.7), 80, h)], []]);
  assertEquals(moves.length, 1);
  const m = moves[0];
  assertEquals([m.kind, m.rwy], ["dep", "16L"]);
  assertEquals(m.taxi_sec, 60);                   // 90秒に動き出し、150秒に最後に見た（離陸）
  assertEquals([m.stand_lat, m.stand_lon], STAND);
  assertEquals(watch.size, 0);
});

Deno.test("止まる前に見えなくなった到着は lost・はじめから走っていた機体は動き出しの時刻なし", () => {
  const h = Math.round(rw["34R"].hdg);
  const steps: GPlane[][] = [[pl(onC(0.3), 50, h)], [pl([35.552, 139.79], 10, 270)]];
  for (let i = 0; i < 11; i++) steps.push([]);   // 5分半見えない
  const a = run(steps);
  assertEquals(a.moves.length, 1);
  assertEquals([a.moves[0].kind, a.moves[0].lost, a.moves[0].stand_lat], ["arr", true, 35.552]);
  const hd = Math.round(rw["16L"].hdg);
  const b = run([[pl([35.552, 139.79], 12, 90)], [pl(onC(0.7), 90, hd)], []]);
  assertEquals([b.moves[0].kind, b.moves[0].taxi_sec, b.moves[0].stand_lat], ["dep", null, null]);
});

Deno.test("止まっている機体は10分に1回だけ書き直す", () => {
  const watch = new Map<string, GWatch>(); let writes = 0;
  for (let i = 0; i < 40; i++) {
    const r = groundStep("HND", rws, rw, [pl(STAND, 0)], watch, T0 + i * 30_000);
    for (const u of r.upserts) watch.set(u.hex, u);
    writes += r.upserts.length;
  }
  assert(writes <= 4, `書いた回数 ${writes}`);
});
