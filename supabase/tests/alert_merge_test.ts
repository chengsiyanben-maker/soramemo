// 遅れの通知を1つの便につき1件にまとめる：推定→公式・出発→到着・共同運航2行・同じ遅れの繰り返し・乗る便の15分・空港は主要空港の門限と0時前後だけ（欠航・ダイバート・引き返しはどの空港にも）・30分ふえたときの上書き
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

Deno.test("乗る便は15分から。空港の人には、ふつうの遅れは何分でも知らせない", () => {
  const g = (late: number) => mergeAlerts(S, [A(3, "delay_dep", late, true)])[0];
  const fl = sub(["JL503@2026-11-13"]), ap = sub([], ["HND"]);
  assertEquals([eligible(fl, g(14)), eligible(fl, g(15)), eligible(ap, g(60)), eligible(ap, g(180))], [false, true, false, false]);
  assertEquals(eligible(sub(["JL999@2026-11-13"], ["OKA"]), g(120)), false);   // 関係のない人には送らない
  assertEquals(eligible(sub(["JL0503@2026-11-13"]), g(15)), true);              // 先頭の0は無視して比べる
});

// 夜の便：到着の定刻を日本時間で決める
const J = (hhmm: string, day = "2026-11-13") => `${day}T${hhmm}:00+09:00`;
const N = (id: number, flight: string, dep: string, arr: string, std: string, sta: string): MergeSched => ({ id, flight, svc_date: "2026-11-13", dep, arr, std: J(std), sta: J(sta) });
const names = (i: string) => ({ HND: "羽田", ITM: "伊丹", FUK: "福岡", NRT: "成田", CTS: "新千歳", KMJ: "熊本", OKA: "那覇" } as Record<string, string>)[i] ?? i;
const night = (s: MergeSched, late: number, kind = "delay_arr", official = true) =>
  mergeAlerts([s], [{ schedule_id: s.id, kind, late, official, message: `ふつうの文${late}`, iata: [s.arr, s.dep] }], names)[0];

Deno.test("門限：伊丹の21時の30分前より後に着く見込みは「間に合わないおそれ」、21時より後は引き返し・ほかの空港も書く。主要空港を選んだ人に届く", () => {
  const g = night(N(11, "JL139", "HND", "ITM", "18:30", "19:47"), 65);
  assertEquals(g.rank, 2);
  assertEquals(g.body, "伊丹の門限（21時）に間に合わないおそれ：JL139 羽田→伊丹、到着の見込み 20時52分（約65分遅れ）（航空会社の運航情報から）");
  assertEquals(night(N(11, "JL139", "HND", "ITM", "18:30", "19:47"), 80, "delay_arr", false).body,
    "伊丹の門限（21時）に間に合わない見込み：JL139 羽田→伊丹、到着の見込み 21時07分（約80分遅れ）。出発した空港へ引き返すか、ほかの空港へ向かうことがあります（推定）");
  assertEquals([eligible(sub([], ["ITM"]), g), eligible(sub([], ["HND"]), g), eligible(sub([], ["KMJ"]), g)], [true, true, false]);
});

Deno.test("門限：福岡の22時の30分前より後に着く見込み。30分より前なら知らせない", () => {
  assertEquals(night(N(12, "NH265", "HND", "FUK", "19:30", "21:20"), 15).body.startsWith("福岡の門限（22時）に間に合わないおそれ：NH265 羽田→福岡、到着の見込み 21時35分（約15分遅れ）"), true);
  assertEquals(night(N(12, "NH265", "HND", "FUK", "19:30", "21:00"), 20).rank, 1);   // 21時20分：30分より前
  assertEquals(night(N(13, "JL3083", "HND", "NRT", "21:00", "23:00"), 40).body.startsWith("成田の門限（24時）"), true);
});

Deno.test("0時前後：24時間の空港に、遅れで23時30分〜翌1時に着く見込みの便。定刻がもともと遅い便や1時より後は知らせない", () => {
  const g = night(N(14, "JL529", "HND", "CTS", "21:30", "23:05"), 45, "delay_dep", false);
  assertEquals([g.rank, g.body], [2, "0時前後に着く見込み：JL529 羽田→新千歳、到着の見込み 23時50分（約45分遅れ）"]);
  assertEquals(night(N(15, "NH1", "HND", "OKA", "21:00", "23:40"), 20).rank, 1);   // 定刻が23時30分より後
  assertEquals(night(N(16, "NH2", "HND", "CTS", "21:00", "22:40"), 150).rank, 1);  // 1時10分：1時より後
  assertEquals(night(N(17, "NH3", "HND", "CTS", "21:00", "23:20"), 10).rank, 1);   // 15分より短い遅れ
  assertEquals(eligible(sub([], ["CTS"]), g), true);
});

Deno.test("門限・0時前後になったら、前にふつうの遅れを送った人にも送り直す（重くなった）", () => {
  assertEquals(shouldSend({ rank: 1, late: 30, official: true }, { rank: 2, late: 40, official: true }), true);
  assertEquals(shouldSend({ rank: 2, late: 40, official: true }, { rank: 2, late: 55, official: true }), false);
  assertEquals(shouldSend({ rank: 2, late: 40, official: true }, { rank: 2, late: 70, official: true }), true);
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
  assertEquals([g.late, eligible(sub(["JL503@2026-11-13"]), g), eligible(sub([], ["CTS"]), g)], [60, true, false]);
});

Deno.test("欠航・ダイバート・引き返しは、主要でない空港を選んだ人にも届く。ふつうの遅れ・門限の遅れは届かない", () => {
  const T: MergeSched[] = [{ id: 21, flight: "JL631", svc_date: "2026-11-14", dep: "HND", arr: "KMJ", std: STD }];
  const a = (kind: string, late: number | null) => ({ schedule_id: 21, kind, late, official: true, message: kind, iata: ["HND", "KMJ"] });
  const km = sub([], ["KMJ"]), ok = sub([], ["OKA"]);
  for (const k of ["cancel", "divert", "divert_landed", "return"]) {
    const g = mergeAlerts(T, [a(k, null)])[0];
    assertEquals([k, g.rank >= 3, eligible(km, g), eligible(ok, g)], [k, true, true, false]);   // 関係のない空港の人には送らない
  }
  assertEquals(eligible(km, mergeAlerts(T, [a("delay_dep", 180)])[0]), false);
  assertEquals(eligible(sub([], ["HND"]), mergeAlerts(T, [a("cancel", null)])[0]), true);   // 主要空港の人にもこれまでどおり
});
