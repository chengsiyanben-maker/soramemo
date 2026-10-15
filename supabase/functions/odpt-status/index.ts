// 航空会社の運航情報（ODPT。JAL・ANA グループ）から、欠航と出発の大きな遅れを見つけて、お知らせ（flight_alerts）と通知にする。
//   GET /functions/v1/odpt-status   （pg_cron が5分ごとに呼ぶ。何度呼ばれても、ODPT に問い合わせるのは4分に1回）
// 機体の位置からの推定ではないので、お知らせに「推定」は付けず「航空会社の運航情報」と書く。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { statusAlerts } from "../_shared/odpt_status.ts";
import { sendAlertPush } from "../_shared/alert_push.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const ODPT_KEY = Deno.env.get("ODPT_CONSUMER_KEY") ?? "";
const ODPT = "https://api.odpt.org/api/v4";
const OPERATORS = ["JAL", "ANA"];
const JSON_HEADERS = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };
const MIN = 60_000;

async function odpt(op: string, airport?: string): Promise<unknown[]> {
  const u = new URL(`${ODPT}/odpt:FlightInformationDeparture`);
  u.searchParams.set("odpt:operator", `odpt.Operator:${op}`);
  if (airport) u.searchParams.set("odpt:departureAirport", `odpt.Airport:${airport}`);
  u.searchParams.set("acl:consumerKey", ODPT_KEY);
  const r = await fetch(u, { headers: { "User-Agent": "soramemo (odpt-status)" }, signal: AbortSignal.timeout(20000) });
  if (!r.ok) throw new Error(`odpt ${op} ${airport ?? "all"} ${r.status}`);
  const j = await r.json();
  return Array.isArray(j) ? j : [];
}

Deno.serve(async () => {
  try {
    if (!ODPT_KEY) return new Response(JSON.stringify({ skipped: "no key" }), { headers: JSON_HEADERS });
    // 4分に1回だけ
    const { data: run } = await admin.from("odpt_status_runs").update({ ran_at: new Date().toISOString() })
      .eq("id", 1).lt("ran_at", new Date(Date.now() - 4 * MIN).toISOString()).select("id");
    if (!run?.length) return new Response(JSON.stringify({ skipped: "recent" }), { headers: JSON_HEADERS });

    // 見る便：定刻が6時間前から3時間後まで
    const now = Date.now();
    const { data: rows } = await admin.from("flight_schedule").select("id, svc_date, flight, dep, arr, std")
      .gte("std", new Date(now - 6 * 60 * MIN).toISOString()).lte("std", new Date(now + 3 * 60 * MIN).toISOString()).limit(5000);
    const scheds = (rows ?? []).map((r) => ({ id: r.id, flight: r.flight, dep: r.dep, arr: r.arr, std: Date.parse(r.std), svc: r.svc_date }));
    if (!scheds.length) return new Response(JSON.stringify({ watching: 0 }), { headers: JSON_HEADERS });
    const { data: aps } = await admin.from("airports").select("iata, name").not("iata", "is", null);
    const names = new Map((aps ?? []).map((a) => [a.iata, String(a.name).replace(/国際空港$|空港$/, "").replace(/^.*（(.+)）$/, "$1")]));

    // 会社ごとに全空港の出発便をまとめて取る。まとめて取れないときは、予定の便の出発空港ごとに取る
    const items: unknown[] = [], errors: string[] = [];
    for (const op of OPERATORS) {
      try {
        let l = await odpt(op);
        if (!l.length) {
          l = [];
          for (const ap of [...new Set(scheds.map((s) => s.dep))]) { try { l.push(...await odpt(op, ap)); } catch (e) { errors.push(String(e)); } }
        }
        items.push(...l);
      } catch (e) { errors.push(String(e)); }
    }
    const alerts = statusAlerts(items, scheds, (i) => names.get(i) ?? i);
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
    return new Response(JSON.stringify({ watching: scheds.length, items: items.length, alerts: alerts.length, new: fresh.length, pushed, errors: errors.slice(0, 3) }), { headers: JSON_HEADERS });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  }
});
