// 乗る便を出発から到着まで追う（国際線・海外の航空会社も）
//   GET /functions/v1/flight-live?flight=NH106[&dep=HND]
// JAL・ANA の便は時刻表（ODPT）から出発・到着の空港と時刻を取り、機体は世界中の機体の位置（adsb.lol）から便名の呼び出し符号で探す。
// 時刻表にない便（海外の航空会社）は、機体が見つかったときだけ、adsb.lol の経路のデータから出発・到着の空港を推定する（日本発着の便だけ）。
// adsb.lol への問い合わせは、同じ呼び出し符号は45秒に1回まで（覚えておく）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { callsignsFor, type Airport } from "../_shared/flight_watch.ts";
import { liveState, type LiveSched, type Plane, toPlane } from "../_shared/flight_live.ts";
import { worldAirport } from "../_shared/world_airports.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const H = { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=30" };
const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: H });

let JP: Map<string, Airport> | null = null;
async function japan() {
  if (JP) return JP;
  const { data } = await admin.from("airports").select("iata, name, lat, lon").not("iata", "is", null);
  JP = new Map((data ?? []).filter((a) => /^[A-Z]{3}$/.test(a.iata)).map((a) => [a.iata, { iata: a.iata, lat: a.lat, lon: a.lon, name: a.name }]));
  return JP;
}
async function airport(iata: string): Promise<Airport | null> {
  const j = (await japan()).get(iata); if (j) return j;
  const w = worldAirport(iata); return w ? { iata, lat: w.lat, lon: w.lon, name: iata } : null;
}

const cache = new Map<string, { at: number; p: Plane | null }>();
let last = 0;
async function findPlane(cs: string): Promise<Plane | null> {
  const hit = cache.get(cs); if (hit && Date.now() - hit.at < 45_000) return hit.p;
  const wait = last + 1000 - Date.now(); if (wait > 0) await new Promise((r) => setTimeout(r, wait));   // 続けて問い合わせるときは1秒あける
  last = Date.now();
  const r = await fetch(`https://api.adsb.lol/v2/callsign/${encodeURIComponent(cs)}`, { headers: { "User-Agent": "soramemo (flight-live)" }, signal: AbortSignal.timeout(10000) });
  if (!r.ok) throw new Error("adsb.lol " + r.status);
  const j = await r.json(), now = typeof j?.now === "number" ? j.now : Date.now();
  const p = ((j?.ac ?? []) as unknown[]).map((a) => toPlane(a, now)).find((x) => x) ?? null;
  cache.set(cs, { at: Date.now(), p });
  return p;
}
// 時刻表にない便：機体の位置から経路を推定する（adsb.im の経路のデータ。tar1090 と同じ問い合わせ先。もっともらしいものだけ）
async function guessRoute(p: Plane): Promise<{ dep: string; arr: string } | null> {
  const r = await fetch("https://adsb.im/api/0/routeset", { method: "POST", headers: { "Content-Type": "application/json", "User-Agent": "soramemo (flight-live)" },
    body: JSON.stringify({ planes: [{ callsign: p.callsign, lat: p.lat, lng: p.lon }] }), signal: AbortSignal.timeout(10000) });
  if (!r.ok) return null;
  const x = ((await r.json()) as { _airport_codes_iata?: string; plausible?: boolean | number }[])?.[0];
  const m = /^([A-Z]{3})-(?:[A-Z]{3}-)*([A-Z]{3})$/.exec(x?._airport_codes_iata ?? "");
  if (!m || !x?.plausible) return null;
  const jp = await japan();
  return jp.has(m[1]) || jp.has(m[2]) ? { dep: m[1], arr: m[2] } : null;   // 日本発着の便だけ
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: { ...H, "Access-Control-Allow-Headers": "apikey, content-type" } });
  try {
    const u = new URL(req.url), flight = (u.searchParams.get("flight") ?? "").toUpperCase().replace(/\s/g, ""), dep = (u.searchParams.get("dep") ?? "").toUpperCase() || null;
    if (!/^[A-Z0-9]{2}\d{1,4}$/.test(flight) || (dep && !/^[A-Z]{3}$/.test(dep))) return json({ error: "bad_request" }, 400);
    const { data: sc } = await admin.rpc("live_flight_sched", { p_flight: flight, p_dep: dep });
    const css = callsignsFor(flight).slice(0, 4);
    let plane: Plane | null = null;
    for (const cs of css) { plane = await findPlane(cs).catch(() => null); if (plane) break; }
    const now = Date.now();
    let s: LiveSched | null = null, source = "odpt";
    if (sc) {
      const t = (v: string | null) => v ? Date.parse(v) : null;
      s = { flight: sc.flight, dep: sc.dep, arr: sc.arr, std: Date.parse(sc.std), sta: Date.parse(sc.sta), etd: t(sc.etd), eta: t(sc.eta), atd: t(sc.atd), ata: t(sc.ata), cancelled: sc.cancelled };
    } else if (plane) {
      const rt = await guessRoute(plane).catch(() => null);
      if (!rt) return json({ flight, found: false, plane: !!plane });
      s = { flight, dep: rt.dep, arr: rt.arr, std: now, sta: now }; source = "route_estimate";
    } else return json({ flight, found: false });
    const [a, b] = await Promise.all([airport(s.dep), airport(s.arr)]);
    const live = source === "odpt" ? liveState(s, plane, a, b, now) : liveState({ ...s, std: now - 36e5, sta: now + 36e5 }, plane, a, b, now);
    return json({ flight: s.flight, found: true, source, dep: s.dep, arr: s.arr,
      std: source === "odpt" ? new Date(s.std).toISOString() : null, sta: source === "odpt" ? new Date(s.sta).toISOString() : null,
      etd: sc?.etd ?? null, eta: sc?.eta ?? null, atd: sc?.atd ?? null, ata: sc?.ata ?? null, aircraft: sc?.aircraft ?? null,
      dep_pos: a ? [a.lat, a.lon] : null, arr_pos: b ? [b.lat, b.lon] : null,
      phase: live.phase, progress: live.progress, reg: live.reg, type: live.type, callsign: live.callsign,
      eta_pred: live.eta ? new Date(live.eta).toISOString() : null, land_pred: live.land ? new Date(live.land).toISOString() : null, pos: live.pos ? { ...live.pos, at: new Date(live.pos.at).toISOString() } : null });
  } catch (e) {
    console.error(e);
    return json({ error: "failed" }, 500);
  }
});
