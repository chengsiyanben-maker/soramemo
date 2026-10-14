// 予定の便（flight_schedule）と、今飛んでいる機体（adsb.lol）を照らし合わせ、遅れ・ダイバートを見つけて知らせる。
//   GET /functions/v1/flight-watch   （pg_cron が1分ごとに呼ぶ。何度呼ばれても、機体を取りに行くのは1分に1回）
// ダイヤが空（または見張る便がない）なら、機体は取りに行かず、何もしない。
// 見つけたお知らせは flight_alerts に残し、その空港を選んでいる人のスマホへ通知する（VAPID の鍵があるときだけ）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import webpush from "npm:web-push@3.6.7";
import { type Airport, blankWatch, callsignsFor, normCallsign, type Sched, type Seen, step, type Watch } from "../_shared/flight_watch.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const JSON_HEADERS = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" };
const MIN = 60_000;

// 日本の上空をおおう円（中心と半径250海里。adsb.lol の上限）。見張る便の近くの円だけ取りに行く
const CIRCLES: [number, number][] = [[35.6, 139.8], [34.6, 135.4], [33.4, 130.6], [43.0, 142.0], [38.6, 140.6], [26.3, 127.8], [29.5, 129.8], [24.4, 124.2]];
function km(a: [number, number], b: [number, number]) {
  const r = Math.PI / 180, dl = (b[0] - a[0]) * r, dn = (b[1] - a[1]) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

let AIRPORTS: Map<string, Airport> | null = null;
async function airports() {
  if (AIRPORTS) return AIRPORTS;
  const { data } = await admin.from("airports").select("iata, name, lat, lon").not("iata", "is", null);
  AIRPORTS = new Map((data ?? []).filter((a) => /^[A-Z]{3}$/.test(a.iata)).map((a) => [a.iata, { iata: a.iata, lat: a.lat, lon: a.lon, name: String(a.name).replace(/国際空港$|空港$/, "").replace(/^.*（(.+)）$/, "$1") }]));
  return AIRPORTS;
}

async function fetchCircle([lat, lon]: [number, number]) {
  const r = await fetch(`https://api.adsb.lol/v2/lat/${lat}/lon/${lon}/dist/250`, { headers: { "User-Agent": "soramemo (flight-watch)" }, signal: AbortSignal.timeout(15000) });
  if (!r.ok) throw new Error("adsb.lol " + r.status);
  const j = await r.json();
  return { now: typeof j?.now === "number" ? j.now : Date.now(), ac: Array.isArray(j?.ac) ? j.ac : [] };
}

async function sendPush(alerts: { iata: string[]; message: string; flight: string }[]) {
  const pub = Deno.env.get("VAPID_PUBLIC_KEY"), priv = Deno.env.get("VAPID_PRIVATE_KEY");
  if (!pub || !priv || !alerts.length) return 0;
  webpush.setVapidDetails(Deno.env.get("VAPID_SUBJECT") || "https://soramemo.jp", pub, priv);
  const all = [...new Set(alerts.flatMap((a) => a.iata))];
  const { data: subs } = await admin.from("push_subs").select("id, endpoint, p256dh, auth, airports").overlaps("airports", all);
  let sent = 0;
  for (const s of subs ?? []) {
    for (const a of alerts.filter((x) => x.iata.some((i) => s.airports.includes(i)))) {
      try {
        await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
          JSON.stringify({ title: `そらメモ：${a.flight}`, body: a.message, tag: `fw-${a.flight}` }), { TTL: 3600 });
        sent++; await admin.from("push_subs").update({ last_ok: new Date().toISOString() }).eq("id", s.id);
      } catch (e) {
        const code = (e as { statusCode?: number }).statusCode;
        if (code === 404 || code === 410) { await admin.from("push_subs").delete().eq("id", s.id); break; }   // 購読が切れている
      }
    }
  }
  return sent;
}

Deno.serve(async () => {
  try {
    // 1分に1回だけ
    const { data: run } = await admin.from("flight_watch_runs").update({ ran_at: new Date().toISOString() })
      .eq("id", 1).lt("ran_at", new Date(Date.now() - 50_000).toISOString()).select("id");
    if (!run?.length) return new Response(JSON.stringify({ skipped: "recent" }), { headers: JSON_HEADERS });

    const now = Date.now();
    const { data: rows } = await admin.from("flight_schedule").select("id, flight, dep, arr, std, sta, flight_watch(state)")
      .gte("std", new Date(now - 8 * 60 * MIN).toISOString()).lte("std", new Date(now + 30 * MIN).toISOString()).limit(3000);
    const list = (rows ?? []).map((r) => ({
      s: { id: r.id, flight: r.flight, dep: r.dep, arr: r.arr, std: Date.parse(r.std), sta: Date.parse(r.sta) } as Sched,
      w: ((Array.isArray(r.flight_watch) ? r.flight_watch[0]?.state : (r.flight_watch as { state?: Watch } | null)?.state) ?? blankWatch()) as Watch,
    })).filter((x) => x.w.phase !== "landed" && now - x.s.sta < 6 * 60 * MIN);
    if (!list.length) return new Response(JSON.stringify({ watching: 0 }), { headers: JSON_HEADERS });

    const aps = await airports();
    // 見張る便の出発・到着・最後の位置の近くの円だけ取りに行く
    const pts: [number, number][] = list.flatMap(({ s, w }) => [aps.get(s.dep), aps.get(s.arr)].filter(Boolean).map((a) => [a!.lat, a!.lon] as [number, number])
      .concat(w.last ? [[w.last.lat, w.last.lon]] : []));
    const need = CIRCLES.filter((c) => pts.some((p) => km(c, p) < 500));
    const seen = new Map<string, Seen>();
    for (const c of need) {
      try {
        const { now: t, ac } = await fetchCircle(c);
        for (const a of ac) {
          if (typeof a?.flight !== "string" || typeof a.lat !== "number") continue;
          const cs = normCallsign(a.flight);
          seen.set(cs, { callsign: cs, lat: a.lat, lon: a.lon, alt_ft: typeof a.alt_baro === "number" ? a.alt_baro : null, ground: a.alt_baro === "ground",
            fpm: typeof a.baro_rate === "number" ? a.baro_rate : typeof a.geom_rate === "number" ? a.geom_rate : null, at: t - (typeof a.seen_pos === "number" ? a.seen_pos * 1000 : 0) });
        }
      } catch (e) { console.error(e); }
    }

    const upd: { schedule_id: number; state: Watch; updated_at: string }[] = [];
    const out: { schedule_id: number; kind: string; flight: string; dep: string; arr: string; iata: string[]; message: string }[] = [];
    for (const { s, w } of list) {
      const hit = callsignsFor(s.flight).map((c) => seen.get(c)).find(Boolean) ?? null;
      const r = step(s, w, hit, now, aps);
      if (JSON.stringify(r.watch) !== JSON.stringify(w)) upd.push({ schedule_id: s.id, state: r.watch, updated_at: new Date().toISOString() });
      for (const a of r.alerts) out.push({ schedule_id: s.id, kind: a.kind, flight: s.flight, dep: s.dep, arr: s.arr, iata: [...new Set(a.iata)], message: a.message });
    }
    if (upd.length) await admin.from("flight_watch").upsert(upd);
    if (out.length) await admin.from("flight_alerts").insert(out);
    const pushed = await sendPush(out);
    return new Response(JSON.stringify({ watching: list.length, circles: need.length, seen: seen.size, updated: upd.length, alerts: out.length, pushed }), { headers: JSON_HEADERS });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  }
});
