// 空港の近くにいる海外の航空会社の便（推定）：この空港に着く便・この空港を出た便。
//   GET /functions/v1/airport-foreign?iata=HND
// 時刻表は JAL・ANA の分しかないので、海外の航空会社は、機体の位置（live_positions。adsb.lol の ADS-B）と、
// adsb.lol の経路のデータ（routeset）から推定する。便名は呼び出し符号から（KAL703 → KE703）。航空会社の発表ではない。
// 配信元に負担をかけないよう、空港ごとに60秒ためて全員で使い回す。ログインは不要。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { classifyForeign, foreignNear, type LivePos, parseRoutes } from "../_shared/foreign_now.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const H = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, OPTIONS", "Content-Type": "application/json" };
const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: H });
const TTL = 60_000;

let JP: Map<string, { lat: number; lon: number }> | null = null;
async function japan() {
  if (JP) return JP;
  const { data } = await admin.from("airports").select("iata, lat, lon").not("iata", "is", null);
  JP = new Map((data ?? []).filter((a) => /^[A-Z]{3}$/.test(a.iata)).map((a) => [a.iata, { lat: a.lat, lon: a.lon }]));
  return JP;
}

const cache = new Map<string, { at: number; body: unknown }>();
let lastRoute = 0;
async function routes(planes: { callsign: string; lat: number; lon: number }[]) {
  if (!planes.length) return new Map();
  const wait = 1000 - (Date.now() - lastRoute); if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastRoute = Date.now();
  const r = await fetch("https://api.adsb.lol/api/0/routeset", { method: "POST", headers: { "Content-Type": "application/json", "User-Agent": "soramemo (airport-foreign)" },
    body: JSON.stringify({ planes: planes.map((p) => ({ callsign: p.callsign, lat: p.lat, lng: p.lon })) }), signal: AbortSignal.timeout(10000) });
  return r.ok ? parseRoutes(await r.json()) : new Map();
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: { ...H, "Access-Control-Allow-Headers": "apikey, content-type" } });
  try {
    const iata = (new URL(req.url).searchParams.get("iata") ?? "").toUpperCase();
    if (!/^[A-Z]{3}$/.test(iata)) return json({ error: "bad_request" }, 400);
    const c = cache.get(iata); if (c && Date.now() - c.at < TTL) return json(c.body);
    const at = (await japan()).get(iata); if (!at) return json({ error: "unknown_airport" }, 404);
    const d = 0.6;   // 約65km四方を先に絞る
    const { data, error } = await admin.from("live_positions").select("callsign, lat, lon, alt_ft, ground, fpm, type, reg, seen_at")
      .gt("seen_at", new Date(Date.now() - 5 * 60_000).toISOString())
      .gte("lat", at.lat - d).lte("lat", at.lat + d).gte("lon", at.lon - d * 1.25).lte("lon", at.lon + d * 1.25).limit(500);
    if (error) throw error;
    const near = foreignNear((data ?? []) as LivePos[], at, 60).slice(0, 40);
    const rt = await routes(near).catch(() => new Map());
    const planes = classifyForeign(near, rt, iata);
    const body = { iata, at: new Date().toISOString(), planes, source: "adsb.lol（機体の位置と経路のデータ。推定）" };
    cache.set(iata, { at: Date.now(), body });
    return json(body);
  } catch (e) {
    return json({ error: "failed", detail: e instanceof Error ? e.message : String(e) }, 500);
  }
});
