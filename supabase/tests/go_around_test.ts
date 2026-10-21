import { assert, assertEquals } from "jsr:@std/assert@1";
import { ceilOf, gaStep, guessRwy, quietNow, type Watch, wxRisk } from "../functions/_shared/go_around.ts";

const P = (o: Record<string, unknown>) => ({ id: "86d123", callsign: "JAL123", lat: 35.5, lon: 139.8, alt_ft: 3000, fpm: -700, hdg: 337, phase: "arr", dist_km: 12, type: "B738", reg: "JA301J", ...o });
function run(seq: Record<string, unknown>[], start = Date.parse("2026-10-21T05:50:00Z")) {
  const watch = new Map<string, Watch>(); const all = [];
  for (const [i, o] of seq.entries()) {
    const r = gaStep("HND", [P(o) as never], watch, start + i * 30_000);
    for (const u of r.upserts) watch.set(u.hex, u); for (const d of r.deletes) watch.delete(d); all.push(...r.events);
  }
  return all;
}

Deno.test("降りてから上がった：ゴーアラウンド（推定）", () => {
  const ev = run([{ alt_ft: 2400, dist_km: 9 }, { alt_ft: 1400, dist_km: 6 }, { alt_ft: 600, dist_km: 3 }, { alt_ft: 450, dist_km: 2.1, fpm: -200 }, { alt_ft: 1200, dist_km: 1, fpm: 1800, phase: "dep" }]);
  assertEquals(ev.length, 1);
  assertEquals(ev[0].low_ft, 450); assertEquals(ev[0].flight, "JL123"); assertEquals(ev[0].callsign, "JAL123");
  assert(ev[0].pts.length >= 4);
});
Deno.test("ふつうに着陸（見えなくなる）：ゴーアラウンドにしない", () => {
  assertEquals(run([{ alt_ft: 1400, dist_km: 6 }, { alt_ft: 600, dist_km: 3 }, { alt_ft: 200, dist_km: 1 }]).length, 0);
});
Deno.test("1,000ft より低く降りていなければ、ゴーアラウンドにしない（高めで水平飛行に移っただけ）", () => {
  assertEquals(run([{ alt_ft: 1400, dist_km: 8 }, { alt_ft: 1300, dist_km: 6 }, { alt_ft: 2000, dist_km: 5, fpm: 900, phase: "dep" }]).length, 0);
});
Deno.test("6分より後に上がったもの（着陸してまた離陸した機体など）は数えない", () => {
  const seq = [{ alt_ft: 600, dist_km: 3 }, ...Array.from({ length: 13 }, () => ({ alt_ft: 99999, dist_km: 99, phase: "other" })), { alt_ft: 1500, dist_km: 2, fpm: 2000, phase: "dep" }];
  assertEquals(run(seq).length, 0);
});
Deno.test("自家用機など（呼び出し符号が JA…）は除く", () => {
  assertEquals(run([{ callsign: "JA4123", alt_ft: 600, dist_km: 3 }, { callsign: "JA4123", alt_ft: 1300, dist_km: 2, fpm: 1500, phase: "dep" }]).length, 0);
});
Deno.test("滑走路の推定：向きが合い、進入端がいちばん近いもの", () => {
  const rw = { "34L": { id: "34L", thr: [35.5366, 139.7857] as [number, number], hdg: 337 }, "16R": { id: "16R", thr: [35.5562, 139.7717] as [number, number], hdg: 157 }, "34R": { id: "34R", thr: [35.5425, 139.8031] as [number, number], hdg: 337 } };
  assertEquals(guessRwy(35.52, 139.794, 337, rw), "34L");
  assertEquals(guessRwy(35.53, 139.81, 337, rw), "34R");
});
Deno.test("天気の目安：横風・突風・雲・見通し・雷・ウインドシア", () => {
  const a = wxRisk({ wdir: 250, wspd: 25, wgst: 38, vis_m: 9999, raw: "RJTT 210530Z 25025G38KT 9999 FEW025 18/10 Q1002" }, [337]);
  assertEquals(a.level, 2); assertEquals(a.xwind, 25); assert(a.kinds.includes("wind"));
  const b = wxRisk({ wdir: 10, wspd: 6, wgst: null, vis_m: 1200, raw: "RJCC 210530Z 01006KT 1200 BR BKN003 10/09 Q1010" }, [6]);
  assertEquals(b.level, 2); assertEquals(b.ceil, 300); assert(b.kinds.includes("cloud"));
  const c = wxRisk({ wdir: 340, wspd: 8, wgst: null, vis_m: 9999, raw: "RJAA 210530Z 34008KT 9999 FEW030 SCT050 18/10 Q1012" }, [337]);
  assertEquals(c.level, 0);
  assertEquals(wxRisk({ wdir: 200, wspd: 10, wgst: null, vis_m: 8000, raw: "ROAH 210530Z 20010KT 8000 +TSRA BKN015CB 25/23 Q1006" }, [180]).kinds, ["ts"]);
  assertEquals(wxRisk({ wdir: 200, wspd: 10, wgst: null, vis_m: 9999, raw: "ROAH 210530Z 20010KT 9999 VCTS FEW020CB 25/23 Q1006" }, [180]).level, 1);
  assertEquals(wxRisk({ wdir: 200, wspd: 10, wgst: null, vis_m: 9999, raw: "RJFF 210530Z 20010KT 9999 FEW020 25/23 Q1006 WS R34" }, [160]).kinds, ["ts"]);
});
Deno.test("雲底と夜", () => {
  assertEquals(ceilOf("RJTT 21 FEW008 BKN012 OVC030"), 1200);
  assertEquals(ceilOf("RJTT 21 FEW008 SCT020"), null);
  assertEquals(ceilOf("RJTT 21 VV002"), 200);
  assert(quietNow(Date.parse("2026-10-21T15:00:00Z"))); assert(!quietNow(Date.parse("2026-10-21T03:00:00Z")));
});
