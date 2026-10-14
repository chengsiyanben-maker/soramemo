// 遅れ・ダイバートのお知らせ用のダイヤを、ODPT の公式のフライト時刻表（JAL・ANA）から入れる。
//   GET /functions/v1/schedule-sync   （pg_cron が毎日2回呼ぶ。何度呼ばれても、1時間に1回しか取りに行かない）
// 運用タブの14空港を出発・到着する便を、今日と明日の2日ぶん。ODPT は1回に1,000件までしか返さないので、空港ごとに分けて問い合わせる。
// 鍵（ODPT_CONSUMER_KEY）がなければ何もしない。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { jstDates, scheduleRows, type ScheduleRow } from "../_shared/odpt_schedule.ts";
import { callsignsFor } from "../_shared/flight_watch.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const KEY = Deno.env.get("ODPT_CONSUMER_KEY") ?? "";
const J = { "Content-Type": "application/json" };
const AIRPORTS = ["HND", "NRT", "ITM", "KIX", "CTS", "FUK", "OKA", "NGO", "SDJ", "HIJ", "MYJ", "KMJ", "NGS", "KOJ"];
const OPERATORS = ["JAL", "ANA"];

async function fetchSchedules(op: string, side: "originAirport" | "destinationAirport", iata: string) {
  const u = new URL("https://api.odpt.org/api/v4/odpt:FlightSchedule");
  u.searchParams.set("odpt:operator", `odpt.Operator:${op}`);
  u.searchParams.set(`odpt:${side}`, `odpt.Airport:${iata}`);
  u.searchParams.set("acl:consumerKey", KEY);
  const r = await fetch(u, { headers: { "User-Agent": "soramemo (schedule-sync)" }, signal: AbortSignal.timeout(20000) });
  if (!r.ok) throw new Error(`ODPT ${r.status}`);
  const d = await r.json();
  return Array.isArray(d) ? d : [];
}

Deno.serve(async () => {
  if (!KEY) return new Response(JSON.stringify({ skipped: "no key" }), { headers: J });
  // 1時間に1回だけ
  const { data: run } = await admin.from("schedule_sync_runs").update({ ran_at: new Date().toISOString() })
    .eq("id", 1).lt("ran_at", new Date(Date.now() - 3600_000).toISOString()).select("id");
  if (!run?.length) return new Response(JSON.stringify({ skipped: "recent" }), { headers: J });
  const dates = jstDates(new Date(), 2), rows = new Map<string, ScheduleRow>(), errors: string[] = [];
  let full = 0;
  for (const op of OPERATORS) for (const iata of AIRPORTS) for (const side of ["originAirport", "destinationAirport"] as const) {
    try {
      const items = await fetchSchedules(op, side, iata);
      if (items.length >= 1000) full++;   // 1,000件ちょうどなら、取りこぼしがあるかもしれない
      // 呼び出し符号に直せない便名（見張れない便）は入れない
      for (const r of scheduleRows(items, dates, op)) if (callsignsFor(r.flight).length) rows.set(`${r.svc_date}|${r.flight}|${r.dep}`, r);
    } catch (e) { errors.push(`${op} ${side} ${iata}: ${e instanceof Error ? e.message : e}`); }
    await new Promise((r) => setTimeout(r, 300));   // ODPT に続けて問い合わせすぎない
  }
  const all = [...rows.values()];
  for (let i = 0; i < all.length; i += 500) {
    const { error } = await admin.from("flight_schedule").upsert(all.slice(i, i + 500), { onConflict: "svc_date,flight,dep" });
    if (error) { errors.push("upsert: " + error.message); break; }
  }
  const result = { dates, flights: all.length, truncated_queries: full, errors: errors.slice(0, 10) };
  await admin.from("schedule_sync_runs").update({ result }).eq("id", 1);
  return new Response(JSON.stringify(result), { headers: J });
});
