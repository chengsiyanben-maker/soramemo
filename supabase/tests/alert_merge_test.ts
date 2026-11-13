// 遅れの通知を1つの便につき1件にまとめる：推定→公式・出発→到着・共同運航2行・同じ遅れの繰り返し・15分と60分の分かれ目・30分ふえたときの上書き
import { assertEquals } from "jsr:@std/assert@1";
import { eligible, type MergeAlert, mergeAlerts, type MergeSched, payloadOf, shouldSend } from "../functions/_shared/alert_merge.ts";

const STD = "2026-11-13T01:00:00+00:00";
const S: MergeSched[] = [
  { id: 1, flight: "JL501", svc_date: "2026-11-13", dep: "HND", arr: "CTS", std: STD },
  { id: 2, flight: "NH4701", svc_date: "2026-11-13", dep: "HND", arr: "CTS", std: STD },        // 同じ便の別の便名（共同運航）
  { id: 3, flight: "JL503", svc_date: "2026-11-13", dep: "HND", arr: "CTS", std: "2026-11-13T02:00:00+00:00" },
];
const A = (schedule_id: number, kind: string, late: number | null, official: boolean, message = `${kind}${late}${official ? "公式" : "推定"}`): MergeAlert =>
  ({ schedule_id, kind, late, official, message, iata: kind === "delay_arr" ? ["CTS", "HND"] : ["HND", "CTS"] });
const sub = (flights: string[], airports: string[] = []) => ({ id: 9, flights, airports });

Deno.test("出発の遅れと到着の遅れは1件にまとめ、大きい方の遅れを見出しにする", () => {
  const g = mergeAlerts(S, [A(3, "delay_dep", 40, true), A(3, "delay_arr", 35, true)]);
  assertEquals(g.length, 1);
  assertEquals([g[0].gkey, g[0].rank, g[0].late, g[0].official, g[0].body], ["JL503@2026-11-13@HND", 1, 40, true, "delay_dep40公式"]);
  assertEquals(g[0].iata.sort(), ["CTS", "HND"]);
});

Deno.test("推定と航空会社の運航情報があれば、運航情報を使う（推定の方が大きくても）", () => {
  const g = mergeAlerts(S, [A(3, "delay_dep", 70, false), A(3, "delay_arr", 50, true)]);
  assertEquals([g.length, g[0].late, g[0].official, g[0].body], [1, 50, true, "delay_arr50公式"]);
});

Deno.test("共同運航の2行（同じ出発・到着・定刻）は1件にまとめ、どちらの便名を選んだ人にも届く", () => {
  const g = mergeAlerts(S, [A(2, "delay_dep", 20, true), A(1, "delay_dep", 20, false)]);
  assertEquals(g.length, 1);
  assertEquals(g[0].gkey, "NH4701@2026-11-13@HND");   // 運航情報が出ている便を代表にする
  assertEquals(g[0].fkeys.sort(), ["JL501@2026-11-13", "NH4701@2026-11-13"]);
  assertEquals([eligible(sub(["JL501@2026-11-13"]), g[0]), eligible(sub(["NH4701@2026-11-13"]), g[0])], [true, true]);
});

Deno.test("欠航は遅れより先に見出しにする", () => {
  const g = mergeAlerts(S, [A(3, "delay_dep", 90, true), A(3, "cancel", null, true, "欠航です")]);
  assertEquals([g[0].rank, g[0].late, g[0].body], [5, null, "欠航です"]);
  assertEquals(eligible(sub([], ["HND"]), g[0]), true);
});

Deno.test("15分と60分の分かれ目：乗る便は15分から、空港の人は60分から", () => {
  const g = (late: number) => mergeAlerts(S, [A(3, "delay_dep", late, true)])[0];
  const fl = sub(["JL503@2026-11-13"]), ap = sub([], ["HND"]);
  assertEquals([eligible(fl, g(14)), eligible(fl, g(15)), eligible(ap, g(59)), eligible(ap, g(60))], [false, true, false, true]);
  assertEquals(eligible(sub(["JL999@2026-11-13"], ["OKA"]), g(120)), false);   // 関係のない人には送らない
  assertEquals(eligible(sub(["JL0503@2026-11-13"]), g(15)), true);              // 先頭の0は無視して比べる
});

Deno.test("同じ遅れの繰り返しは送らず、重くなった・運航情報がはじめて届いた・30分以上ふえたときだけ送る", () => {
  const d = (late: number, official = false) => ({ rank: 1, late, official });
  assertEquals(shouldSend(null, d(20)), true);
  assertEquals(shouldSend(d(20), d(20)), false);           // 同じ遅れの繰り返し
  assertEquals(shouldSend(d(20), d(49)), false);           // 29分ふえた
  assertEquals(shouldSend(d(20), d(50)), true);            // 30分ふえた → 上書き
  assertEquals(shouldSend(d(50), d(40, true)), true);      // 推定 → 公式
  assertEquals(shouldSend(d(40, true), d(45, false)), false);
  assertEquals(shouldSend(d(40, true), { rank: 5, late: null, official: true }), true);   // 欠航になった
  assertEquals(shouldSend({ rank: 5, late: null, official: true }, d(90, true)), false);
});

Deno.test("通知は同じ便を同じ tag にし、上書きでも鳴らす。更新は【更新】を付ける", () => {
  const g = mergeAlerts(S, [A(3, "delay_dep", 40, true)])[0];
  assertEquals(payloadOf(g, false), { title: "そらメモ：JL503", body: "delay_dep40公式", tag: "fw-JL503@2026-11-13@HND", renotify: true, url: "./#ops-HND" });
  assertEquals(payloadOf(g, true).body, "【更新】delay_dep40公式");
});

Deno.test("遅れの分がない古いお知らせは60分として扱う", () => {
  const g = mergeAlerts(S, [A(3, "delay_arr", null, false)])[0];
  assertEquals([g.late, eligible(sub([], ["CTS"]), g)], [60, true]);
});
