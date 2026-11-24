// 通知の題と本文の書き方（_shared/push_text.ts）：題の「そらメモ：」を外し、推定は本文の最後に「（推定）」1つ
import { assertEquals } from "jsr:@std/assert@1";
import { pushBody, pushTitle, tidyPush } from "../functions/_shared/push_text.ts";
import { payloadOf } from "../functions/_shared/alert_merge.ts";
import { regFlyMessage } from "../functions/_shared/livery_push.ts";
import { spotMessage } from "../functions/_shared/spot_push.ts";

const count = (s: string) => s.split("推定").length - 1;

Deno.test("題の頭の「そらメモ：」を外す（ほかは変えない）", () => {
  assertEquals(pushTitle("そらメモ：JL123 があと約5分で着陸"), "JL123 があと約5分で着陸");
  assertEquals(pushTitle("そらメモ:★ミャクミャクジェット"), "★ミャクミャクジェット");
  assertEquals(pushTitle("羽田でゴーアラウンドが続いています"), "羽田でゴーアラウンドが続いています");
});

Deno.test("推定の書き方を本文の最後の「（推定）」1つにそろえる", () => {
  const cases: [string, string][] = [
    ["ワンワールド塗装（ブリティッシュ・エアウェイズ・BAW5）が羽田に着陸に向かっています（推定）。", "ワンワールド塗装（ブリティッシュ・エアウェイズ・BAW5）が羽田に着陸に向かっています（推定）。"],
    ["22 に降りる手前で上昇に移りました（機体の位置からの推定）（風 210° 15kt）。", "22 に降りる手前で上昇に移りました（風 210° 15kt）（推定）。"],
    ["北風 → 南風（実際の機体の動きからの推定）。", "北風 → 南風（推定）。"],
    ["横風が強い・低い雲（気象通報からの目安。着陸のやり直し）。", "横風が強い・低い雲（着陸のやり直し）（推定）。"],
    ["JL123 羽田→伊丹は、福岡へ向かっているようです（ダイバートの可能性・推定）", "JL123 羽田→伊丹は、福岡へ向かっているようです（ダイバートの可能性）（推定）"],
    ["JL123 羽田→伊丹は、出発が約30分遅れました（10時05分ごろ離陸・推定）", "JL123 羽田→伊丹は、出発が約30分遅れました（10時05分ごろ離陸）（推定）"],
    ["夏塗装の JL123（767）が、羽田にあと約5分で着陸しそうです（機体の位置からの推定）。", "夏塗装の JL123（767）が、羽田にあと約5分で着陸しそうです（推定）。"],
    ["JL123 が羽田からあと約8分で離陸しそうです（出発の見込みと地上走行の時間からの推定）。", "JL123 が羽田からあと約8分で離陸しそうです（推定）。"],
  ];
  for (const [a, b] of cases) { assertEquals(pushBody(a), b); assertEquals(count(pushBody(a)), 1); }
});

Deno.test("推定のない本文・航空会社の運航情報・FAA の行は変えない", () => {
  const s = "伊丹の門限（21時）に間に合わないおそれ：JL139 羽田→伊丹、到着の見込み 21時07分（約80分遅れ）（航空会社の運航情報から）";
  assertEquals(pushBody(s), s);
  assertEquals(pushBody("JL61 成田→ロサンゼルス：到着地ロサンゼルスで地上待機中（FAA・10時30分まで見込み）"), "JL61 成田→ロサンゼルス：到着地ロサンゼルスで地上待機中（FAA・10時30分まで見込み）");
});

Deno.test("2行の本文：推定のあった行の最後に付ける（FAA の行には付けない）", () => {
  assertEquals(pushBody("【更新】JL1 羽田→伊丹は、到着が約40分遅れました（10時ごろ着陸・推定）\n到着地で地上待機中（FAA）"),
    "【更新】JL1 羽田→伊丹は、到着が約40分遅れました（10時ごろ着陸）（推定）\n到着地で地上待機中（FAA）");
});

Deno.test("送る中身：遅れの通知・機体ごとの通知・撮影の知らせ", () => {
  const p = payloadOf({ gkey: "JL1@2026-11-24@HND", flight: "JL1", svc_date: "2026-11-24", dep: "HND", arr: "ITM", fkeys: [], iata: [], rank: 4, late: null, official: false, eta: null,
    body: "JL1 羽田→伊丹は、関西に着陸したようです（ダイバート・推定）" }, false);
  assertEquals(p.title, "JL1");
  assertEquals(p.body, "JL1 羽田→伊丹は、関西に着陸したようです（ダイバート）（推定）");
  assertEquals(p.tag, "fw-JL1@2026-11-24@HND");
  const r = regFlyMessage({ reg: "JA8089", name: "ミャクミャクジェット", airline: "JAL", callsign: "JAL123", alt_ft: 20000 });
  assertEquals(r.title, "★ミャクミャクジェット");
  assertEquals(count(r.body), 1);
  // 撮影の知らせ（撮る人用の持ち場）は送る直前の tidyPush でそろう
  const sp = tidyPush(spotMessage({ callsign: "JAL123", reg: "JA8089", type: "B763" } as never, { label: "特別塗装機" }, "羽田", Date.now() + 5 * 60_000));
  assertEquals(sp.title.startsWith("そらメモ"), false);
  assertEquals(count(sp.body), 1);
  assertEquals(sp.body.endsWith("（推定）。"), true);
});
