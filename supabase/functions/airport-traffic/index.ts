// 空港の周りを今飛んでいる機体と、通ってきた線（いまは羽田だけ）。
//   GET /functions/v1/airport-traffic?iata=HND
// 位置は adsb.lol（有志の受信機による ADS-B のオープンデータ）。実際より数秒〜十数秒遅れる。ログインは不要。
// OpenSky は Supabase のサーバーから届かないため使わない。
// 配信元に負担をかけないよう、20秒ためて全員で使い回す。
// 通ってきた線は、位置をデータベース（traffic_trails）に足していって作る（関数の呼び出しをまたいで残すため）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { planesFromAdsb, type Trails, updateTrails } from "../_shared/traffic.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const JSON_HEADERS = { ...CORS, "Content-Type": "application/json" };
const TTL = 20_000;

// 空港の位置と、問い合わせる半径（海里。60海里＝約110km。房総半島の南や相模湾からの進入まで入る）
const AIRPORTS: Record<string, { at: [number, number]; nm: number }> = {
  HND: { at: [35.5533, 139.7811], nm: 60 },
};

// データベースの線を読み、今回の位置を足して書き戻す。いなくなった機体と古い位置は消える
async function syncTrails(iata: string, planes: { id: string; lat: number; lon: number }[]): Promise<Trails> {
  const tr: Trails = new Map();
  try {
    const { data } = await admin.from("traffic_trails").select("hex, pts").eq("iata", iata);
    for (const r of data ?? []) if (Array.isArray(r.pts)) tr.set(String(r.hex), r.pts.map((q: number[]) => ({ t: q[0], p: [q[1], q[2]] as [number, number] })));
  } catch { /* 読めなくても位置は出す */ }
  const before = new Set(tr.keys());
  // deno-lint-ignore no-explicit-any
  updateTrails(tr, planes as any, Date.now());
  const rows = [...tr.entries()].map(([hex, pts]) => ({ iata, hex, pts: pts.slice(-150).map((x) => [x.t, x.p[0], x.p[1]]), updated_at: new Date().toISOString() }));
  const gone = [...before].filter((h) => !tr.has(h));
  try {
    if (rows.length) await admin.from("traffic_trails").upsert(rows);
    if (gone.length) await admin.from("traffic_trails").delete().eq("iata", iata).in("hex", gone);
  } catch { /* 書けなくても位置は出す */ }
  return tr;
}

const cache = new Map<string, { at: number; body: string }>();

async function snapshot(iata: string): Promise<string> {
  const hit = cache.get(iata);
  if (hit && Date.now() - hit.at < TTL) return hit.body;
  const a = AIRPORTS[iata];
  const r = await fetch(`https://api.adsb.lol/v2/lat/${a.at[0]}/lon/${a.at[1]}/dist/${a.nm}`,
    { headers: { "User-Agent": "soramemo (airport-traffic)" }, signal: AbortSignal.timeout(10000) });
  if (!r.ok) throw new Error("adsb.lol " + r.status);
  const j = await r.json();
  const planes = planesFromAdsb(j?.ac, a.at);
  const tr = await syncTrails(iata, planes);
  const body = JSON.stringify({
    iata, at: new Date(typeof j?.now === "number" ? j.now : Date.now()).toISOString(), source: "adsb.lol",
    planes: planes.map((p) => ({ ...p, trail: (tr.get(p.id) ?? []).slice(-150).map((x) => x.p) })),
  });
  cache.set(iata, { at: Date.now(), body });
  return body;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "GET") return new Response(JSON.stringify({ error: "GET only" }), { status: 405, headers: JSON_HEADERS });
  const iata = (new URL(req.url).searchParams.get("iata") || "").toUpperCase();
  if (!AIRPORTS[iata]) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 404, headers: JSON_HEADERS });
  try {
    return new Response(await snapshot(iata), { headers: { ...JSON_HEADERS, "Cache-Control": "max-age=10" } });
  } catch (e) {
    console.error(e);
    const hit = cache.get(iata);
    if (hit) return new Response(hit.body, { headers: { ...JSON_HEADERS, "X-Stale": "1" } });
    const why = e instanceof Error ? (e.name === "TimeoutError" ? "timeout" : e.message.slice(0, 60)) : "error";
    return new Response(JSON.stringify({ error: "unavailable", why }), { status: 503, headers: JSON_HEADERS });
  }
});
