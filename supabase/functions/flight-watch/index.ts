// 予定の便（flight_schedule）と、今飛んでいる機体（adsb.lol。機体の記録が live_positions に残したもの）を照らし合わせ、遅れ・ダイバートを見つけて知らせる。
//   GET /functions/v1/flight-watch   （pg_cron が1分ごとに呼ぶ。何度呼ばれても、機体を取りに行くのは1分に1回）
// ダイヤが空（または見張る便がない）なら、機体は取りに行かず、何もしない。
// 見つけたお知らせは flight_alerts に残し、その空港を選んでいる人のスマホへ通知する（VAPID の鍵があるときだけ）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { sendAlertPush } from "../_shared/alert_push.ts";
import { type Airport, blankWatch, callsignsFor, onRoute, type Sched, type Seen, step, type Watch, loadCalib } from "../_shared/flight_watch.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const JSON_HEADERS = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };
const MIN = 60_000;

let AIRPORTS: Map<string, Airport> | null = null;
async function airports() {
  if (AIRPORTS) return AIRPORTS;
  const { data } = await admin.from("airports").select("iata, name, lat, lon").not("iata", "is", null);
  AIRPORTS = new Map((data ?? []).filter((a) => /^[A-Z]{3}$/.test(a.iata)).map((a) => [a.iata, { iata: a.iata, lat: a.lat, lon: a.lon, name: String(a.name).replace(/国際空港$|空港$/, "").replace(/^.*（(.+)）$/, "$1") }]));
  return AIRPORTS;
}

Deno.serve(async () => {
  await loadCalib(() => admin.from("eta_calib").select("iata, taxi, extra"));
  try {
    // 1分に1回だけ
    const { data: run } = await admin.from("flight_watch_runs").update({ ran_at: new Date().toISOString() })
      .eq("id", 1).lt("ran_at", new Date(Date.now() - 50_000).toISOString()).select("id");
    if (!run?.length) return new Response(JSON.stringify({ skipped: "recent" }), { headers: JSON_HEADERS });

    const now = Date.now();
    const { data: rows } = await admin.from("flight_schedule").select("id, svc_date, flight, dep, arr, std, sta, aircraft, dep_status, arr_status, flight_watch(state)")
      .gte("std", new Date(now - 8 * 60 * MIN).toISOString()).lte("std", new Date(now + 30 * MIN).toISOString()).limit(3000);
    const list = (rows ?? []).map((r) => ({
      fkey: `${r.flight}@${r.svc_date}`,
      // 航空会社の運航情報（ODPT）が届いている便：遅れはそちら（odpt-status）に任せ、推定の遅れは出さない（欠航の便を別の機体と取り違えることがある）
      official: !!(r.dep_status || r.arr_status),
      s: { id: r.id, flight: r.flight, dep: r.dep, arr: r.arr, std: Date.parse(r.std), sta: Date.parse(r.sta), aircraft: r.aircraft } as Sched,
      w: ((Array.isArray(r.flight_watch) ? r.flight_watch[0]?.state : (r.flight_watch as { state?: Watch } | null)?.state) ?? blankWatch()) as Watch,
    })).filter((x) => x.w.phase !== "landed" && now - x.s.sta < 6 * 60 * MIN);
    const aps = await airports();
    // 国内の便だけ見張る（国際線は日本から離れると位置が届かず、着陸や遅れを見分けられない）
    for (let i = list.length - 1; i >= 0; i--) if (!aps.has(list[i].s.dep) || !aps.has(list[i].s.arr)) list.splice(i, 1);
    if (!list.length) return new Response(JSON.stringify({ watching: 0 }), { headers: JSON_HEADERS });

    // 機体の位置：機体の記録（airport-traffic）が30秒ごとに日本中の機体を取って live_positions に残している（adsb.lol に別に問い合わせない）
    const { data: pos } = await admin.from("live_positions").select("callsign, lat, lon, alt_ft, ground, fpm, kt, type, reg, seen_at")
      .gt("seen_at", new Date(now - 3 * MIN).toISOString()).limit(5000);
    // 位置がほとんど届いていない（記録が止まっている）ときは、離陸を確認できないと誤って知らせないよう、何もしない
    if ((pos?.length ?? 0) < 20) return new Response(JSON.stringify({ watching: list.length, skipped: "few positions", positions: pos?.length ?? 0 }), { headers: JSON_HEADERS });
    const seen = new Map<string, Seen>();
    for (const p of pos ?? []) seen.set(p.callsign, { callsign: p.callsign, lat: p.lat, lon: p.lon, alt_ft: p.alt_ft, ground: p.ground, fpm: p.fpm, kt: p.kt, type: p.type, reg: p.reg, at: Date.parse(p.seen_at) });
    const upd: { schedule_id: number; state: Watch; updated_at: string }[] = [];
    const out: { schedule_id: number; kind: string; flight: string; dep: string; arr: string; iata: string[]; message: string }[] = [];
    const fkeys = new Map<number, string>();
    for (const { s, w, fkey, official } of list) {
      fkeys.set(s.id, fkey);
      const hit = callsignsFor(s.flight).map((c) => seen.get(c)).find((x) => x && onRoute(s, x, aps)) ?? null;
      const r = step(s, w, hit, now, aps);
      if (JSON.stringify(r.watch) !== JSON.stringify(w)) upd.push({ schedule_id: s.id, state: r.watch, updated_at: new Date().toISOString() });
      for (const a of r.alerts) if (!(official && (a.kind === "delay_dep" || a.kind === "delay_arr"))) out.push({ schedule_id: s.id, kind: a.kind, flight: s.flight, dep: s.dep, arr: s.arr, iata: [...new Set(a.iata)], message: a.message });
    }
    if (upd.length) await admin.from("flight_watch").upsert(upd);
    // 同じ便・同じ種類のお知らせは1回だけ（航空会社の運航情報（odpt-status）が先に出していることがある）
    let fresh = out;
    // 安全装置：推定のお知らせが直近1時間に30件以上出ていたら、誤りが続いているおそれがあるので、新しく出さない（運営の見張りが気づく）
    if (out.length) {
      const { count } = await admin.from("flight_alerts").select("id", { count: "exact", head: true }).neq("kind", "cancel").gt("created_at", new Date(now - 60 * MIN).toISOString());
      if ((count ?? 0) >= 30) { out.length = 0; fresh = []; }
    }
    if (out.length) {
      const { data: ins } = await admin.from("flight_alerts").upsert(out, { onConflict: "schedule_id,kind", ignoreDuplicates: true }).select("schedule_id, kind");
      const ok = new Set((ins ?? []).map((r) => `${r.schedule_id}|${r.kind}`));
      fresh = out.filter((a) => ok.has(`${a.schedule_id}|${a.kind}`));
    }
    const pushed = await sendAlertPush(admin, fresh.map((a) => ({ ...a, fkey: fkeys.get(a.schedule_id)! })));
    return new Response(JSON.stringify({ watching: list.length, seen: seen.size, updated: upd.length, alerts: out.length, pushed }), { headers: JSON_HEADERS });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  }
});
