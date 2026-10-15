// 航空会社の運航情報（ODPT。JAL・ANA グループの出発・到着）から、欠航・遅れ・ダイバート・引き返しを見つけてお知らせ（flight_alerts）と通知にし、
// 便ごとの実際の時刻・状態・搭乗口を予定の便（flight_schedule）に残す（フライトの記録の照合・便の候補に使う）。
//   GET /functions/v1/odpt-status         （pg_cron が5分ごとに呼ぶ。何度呼ばれても、ODPT に問い合わせるのは4分に1回）
//   GET /functions/v1/odpt-status?diag=1  （運営の確認用：ODPT が返してくる項目の名前と状態の値の一覧だけを返す。便のデータは返さない）
// 機体の位置からの推定ではないので、お知らせに「推定」は付けず「航空会社の運航情報」と書く。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { odptStatus } from "../_shared/odpt_status.ts";
import { sendAlertPush } from "../_shared/alert_push.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const ODPT_KEY = Deno.env.get("ODPT_CONSUMER_KEY") ?? "";
const ODPT = "https://api.odpt.org/api/v4";
const OPERATORS = ["JAL", "ANA"];
const JSON_HEADERS = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };
const MIN = 60_000;

async function odpt(type: "Departure" | "Arrival", op: string, airport?: string): Promise<unknown[]> {
  const u = new URL(`${ODPT}/odpt:FlightInformation${type}`);
  u.searchParams.set("odpt:operator", `odpt.Operator:${op}`);
  if (airport) u.searchParams.set(type === "Departure" ? "odpt:departureAirport" : "odpt:arrivalAirport", `odpt.Airport:${airport}`);
  u.searchParams.set("acl:consumerKey", ODPT_KEY);
  const r = await fetch(u, { headers: { "User-Agent": "soramemo (odpt-status)" }, signal: AbortSignal.timeout(20000) });
  if (!r.ok) throw new Error(`odpt ${op} ${airport ?? "all"} ${r.status}`);
  const j = await r.json();
  return Array.isArray(j) ? j : [];
}

// 会社ごとに全空港の便をまとめて取る。まとめて取れないときは、空港ごとに取る
async function fetchAll(type: "Departure" | "Arrival", airports: string[], errors: string[]) {
  const items: unknown[] = [];
  for (const op of OPERATORS) {
    try {
      let l = await odpt(type, op);
      if (!l.length) { l = []; for (const ap of airports) { try { l.push(...await odpt(type, op, ap)); } catch (e) { errors.push(String(e)); } } }
      items.push(...l);
    } catch (e) { errors.push(String(e)); }
  }
  return items;
}

Deno.serve(async (req) => {
  try {
    if (!ODPT_KEY) return new Response(JSON.stringify({ skipped: "no key" }), { headers: JSON_HEADERS });
    if (new URL(req.url).searchParams.get("diag") === "1") {
      // 運営の確認用：項目の名前と、状態の値（何種類あるか）だけ。羽田の分だけ見る
      const errors: string[] = [], keys = new Map<string, number>(), status = new Map<string, number>();
      for (const type of ["Departure", "Arrival"] as const) for (const op of OPERATORS) {
        try { for (const x of await odpt(type, op, "HND") as Record<string, unknown>[]) {
          for (const k of Object.keys(x)) keys.set(`${type}:${k}`, (keys.get(`${type}:${k}`) ?? 0) + 1);
          const v = String(x["odpt:flightStatus"] ?? "（なし）"); status.set(`${type}:${v}`, (status.get(`${type}:${v}`) ?? 0) + 1);
        } } catch (e) { errors.push(String(e)); }
      }
      return new Response(JSON.stringify({ keys: Object.fromEntries(keys), status: Object.fromEntries(status), errors }), { headers: JSON_HEADERS });
    }
    // 4分に1回だけ
    const { data: run } = await admin.from("odpt_status_runs").update({ ran_at: new Date().toISOString() })
      .eq("id", 1).lt("ran_at", new Date(Date.now() - 4 * MIN).toISOString()).select("id");
    if (!run?.length) return new Response(JSON.stringify({ skipped: "recent" }), { headers: JSON_HEADERS });

    // 見る便：定刻が6時間前から3時間後まで
    const now = Date.now();
    const { data: rows } = await admin.from("flight_schedule").select("id, svc_date, flight, dep, arr, std, sta")
      .gte("std", new Date(now - 6 * 60 * MIN).toISOString()).lte("std", new Date(now + 3 * 60 * MIN).toISOString()).limit(5000);
    const scheds = (rows ?? []).map((r) => ({ id: r.id, flight: r.flight, dep: r.dep, arr: r.arr, std: Date.parse(r.std), sta: Date.parse(r.sta), svc: r.svc_date }));
    if (!scheds.length) return new Response(JSON.stringify({ watching: 0 }), { headers: JSON_HEADERS });
    const { data: aps } = await admin.from("airports").select("iata, name").not("iata", "is", null);
    const names = new Map((aps ?? []).map((a) => [a.iata, String(a.name).replace(/国際空港$|空港$/, "").replace(/^.*（(.+)）$/, "$1")]));

    const errors: string[] = [];
    const depItems = await fetchAll("Departure", [...new Set(scheds.map((x) => x.dep))], errors);
    const arrItems = await fetchAll("Arrival", [...new Set(scheds.map((x) => x.arr))], errors);
    const { alerts, updates } = odptStatus(depItems, arrItems, scheds, (i) => names.get(i) ?? i);
    // 欠航の便に出ていた推定の遅れ・飛行中のお知らせは消す（別の機体と取り違えたもの）
    const cancelled = alerts.filter((a) => a.kind === "cancel").map((a) => a.schedule_id);
    if (cancelled.length) await admin.from("flight_alerts").delete().in("schedule_id", cancelled).in("kind", ["delay_dep", "delay_arr", "no_takeoff"]);
    // 便ごとの実際の時刻・状態・搭乗口を残す（一度入った実際の時刻は消さない）
    if (updates.length) { const { error } = await admin.rpc("apply_flight_status", { p: updates }); if (error) errors.push("apply " + error.message); }
    // 同じ便・同じ種類のお知らせは1回だけ（機体の位置からの推定が先に出していることもある）
    let fresh = alerts;
    if (alerts.length) {
      const { data: ins, error } = await admin.from("flight_alerts").upsert(alerts, { onConflict: "schedule_id,kind", ignoreDuplicates: true }).select("schedule_id, kind");
      if (error) throw error;
      const ok = new Set((ins ?? []).map((r) => `${r.schedule_id}|${r.kind}`));
      fresh = alerts.filter((a) => ok.has(`${a.schedule_id}|${a.kind}`));
    }
    const svc = new Map(scheds.map((s) => [s.id, s.svc]));
    const pushed = await sendAlertPush(admin, fresh.map((a) => ({ ...a, fkey: `${a.flight}@${svc.get(a.schedule_id)}` })));
    return new Response(JSON.stringify({ watching: scheds.length, dep: depItems.length, arr: arrItems.length, updated: updates.length, alerts: alerts.length, new: fresh.length, pushed, errors: errors.slice(0, 3) }), { headers: JSON_HEADERS });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  }
});
