// 計画の画面で使う時刻表（JAL・ANA の国内線）を、ODPT の公式のフライト時刻表から入れる。
//   GET /functions/v1/timetable-sync             （pg_cron が毎日 日本時間 3:00〜4:55 に5分ごとに呼ぶ）
//   GET /functions/v1/timetable-sync?iata=HND    （その空港だけ）
// 1回に6空港まで。20時間以内に取り込んだ空港は飛ばす。空港ごと・航空会社ごとに、出発する便を問い合わせ、
// 取れたら、その空港を出発する その航空会社の行をまるごと入れ替える（取れなかったときは前のまま残す）。入れ替えはデータベースの関数で1回に行う。
// 鍵（ODPT_CONSUMER_KEY）がなければ何もしない。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { isJpAirport, timetableRows, TT_AIRPORTS } from "../_shared/timetable.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const KEY = Deno.env.get("ODPT_CONSUMER_KEY") ?? "";
const J = { "Content-Type": "application/json" };
const OPERATORS = ["JAL", "ANA"];
const PER_CALL = 6;

async function fetchFrom(op: string, iata: string) {
  const u = new URL("https://api.odpt.org/api/v4/odpt:FlightSchedule");
  u.searchParams.set("odpt:operator", `odpt.Operator:${op}`);
  u.searchParams.set("odpt:originAirport", `odpt.Airport:${iata}`);
  u.searchParams.set("acl:consumerKey", KEY);
  const r = await fetch(u, { headers: { "User-Agent": "soramemo (timetable-sync)" }, signal: AbortSignal.timeout(20000) });
  if (!r.ok) throw new Error(`ODPT ${r.status}`);
  const d = await r.json();
  return Array.isArray(d) ? d : [];
}

Deno.serve(async (req) => {
  if (!KEY) return new Response(JSON.stringify({ skipped: "no key" }), { headers: J });
  const want = (new URL(req.url).searchParams.get("iata") || "").toUpperCase();
  if (want && !TT_AIRPORTS.includes(want)) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 400, headers: J });
  let list: string[];
  if (want) list = [want];
  else {
    const since = new Date(Date.now() - 20 * 3600_000).toISOString();
    const { data: runs } = await admin.from("timetable_sync_runs").select("iata, ran_at");
    const last = new Map((runs ?? []).map((r) => [r.iata, r.ran_at]));
    list = TT_AIRPORTS.filter((a) => !last.has(a) || last.get(a) < since).sort((a, b) => String(last.get(a) ?? "").localeCompare(String(last.get(b) ?? ""))).slice(0, PER_CALL);
  }
  const results: Record<string, unknown>[] = [];
  for (const iata of list) {
    const res: Record<string, unknown> = { iata };
    for (const op of OPERATORS) {
      try {
        const items = await fetchFrom(op, iata);
        const rows = timetableRows(items, op, isJpAirport).filter((r) => r.dep === iata);
        if (items.length >= 1000) res[`${op}_truncated`] = true;   // 1,000件ちょうどなら、取りこぼしがあるかもしれない
        // 入れ替えは1回の処理で（途中で止まっても、前の時刻表か新しい時刻表のどちらかが残る）
        const { error } = await admin.rpc("timetable_replace", { p_operator: op, p_dep: iata, p_rows: rows });
        if (error) throw new Error("replace: " + error.message);
        res[op] = rows.length;
      } catch (e) { res[`${op}_error`] = e instanceof Error ? e.message : String(e); }
      await new Promise((r) => setTimeout(r, 300));   // ODPT に続けて問い合わせすぎない
    }
    await admin.from("timetable_sync_runs").upsert({ iata, ran_at: new Date().toISOString(), result: res });
    results.push(res);
  }
  return new Response(JSON.stringify({ airports: results }), { headers: J });
});
