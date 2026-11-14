// アメリカの空港の止まり具合（FAA NAS Status）を読み、日本から直行便のある空港の分を world_airport_status に残す（11/15 本人「OK」）。
//   GET /functions/v1/world-status   （pg_cron が2分ごとに呼ぶ。FAA に問い合わせるのは1回だけ。1日720回）
// FAA の Update_Time が10分より前（古い）・取れないときは何も書かない（表の行は10分で出なくなる：world_status_now）。
// 地上待機・閉鎖・出発の間引きが新しく始まった空港は、その空港を出る・着く便のうち「この便に乗る」で選ばれた便に、同じ便の通知を上書きして知らせる
// （新しい通知は増やさない。遅れのお知らせがある便は、その通知に1行足して送り直す：alert_push.ts の notifyFlights）。
// 出典：FAA NAS Status。運航の判断には使えません。遅れることがあります
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { FAA_URL, isStale, parseNas } from "../_shared/faa_nas.ts";
import { notifyFlights } from "../_shared/alert_push.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const JSON_HEADERS = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };
const H = 3600_000;
const NOTIFY_KINDS = ["closure", "ground_stop", "gdp"];

Deno.serve(async () => {
  const t0 = Date.now();
  try {
    let xml: string;
    try {
      const r = await fetch(FAA_URL, { headers: { "User-Agent": "soramemo (world-status; https://soramemo.jp/)", Accept: "application/xml" }, signal: AbortSignal.timeout(15000) });
      if (!r.ok) return new Response(JSON.stringify({ skipped: `faa ${r.status}` }), { headers: JSON_HEADERS });
      xml = await r.text();
    } catch (e) {
      return new Response(JSON.stringify({ skipped: "faa unreachable", error: String(e).slice(0, 120) }), { headers: JSON_HEADERS });
    }
    const { updatedAt, rows } = parseNas(xml);
    if (isStale(updatedAt, Date.now())) {
      return new Response(JSON.stringify({ skipped: "stale", update_time: updatedAt ? new Date(updatedAt).toISOString() : null }), { headers: JSON_HEADERS });
    }
    const { data: started, error } = await admin.rpc("world_status_put", { p_source: "faa", p_feed_at: new Date(updatedAt!).toISOString(), p: rows });
    if (error) throw error;
    // 新しく始まった地上待機・閉鎖・出発の間引き → その空港を出る・着く、まだ着いていない便
    const hit = [...new Set(((started ?? []) as { iata: string; kind: string }[]).filter((s) => NOTIFY_KINDS.includes(s.kind)).map((s) => s.iata))];
    let pushed = 0, flights = 0;
    if (hit.length) {
      const from = new Date(Date.now() - 14 * H).toISOString(), to = new Date(Date.now() + 12 * H).toISOString();
      const list = hit.join(",");
      const { data: fs } = await admin.from("flight_schedule").select("id")
        .or(`dep.in.(${list}),arr.in.(${list})`).gte("std", from).lte("std", to).is("ata", null).limit(300);
      const ids = (fs ?? []).map((r) => r.id as number);
      flights = ids.length;
      if (ids.length) pushed = await notifyFlights(admin, ids, true);
    }
    return new Response(JSON.stringify({ update_time: new Date(updatedAt!).toISOString(), rows: rows.length, started: (started ?? []).length, flights, pushed, ms: Date.now() - t0 }), { headers: JSON_HEADERS });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  }
});
