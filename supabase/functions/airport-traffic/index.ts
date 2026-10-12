// 空港の周りを今飛んでいる機体と、通ってきた線（いまは羽田だけ）。
//   GET /functions/v1/airport-traffic?iata=HND
// 位置は OpenSky Network（ADS-B）。実際より10〜20秒ほど遅れる。ログインは不要。
// 問い合わせの回数に上限があるので、30秒ためて全員で使い回す。着陸に向かう機体は、はじめて見たときに一度だけ航跡も取る。
import { compactTrack } from "../_shared/track.ts";
import { planesFrom, type Trails, updateTrails } from "../_shared/traffic.ts";

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const JSON_HEADERS = { ...CORS, "Content-Type": "application/json" };
const TOKEN_URL = Deno.env.get("OPENSKY_TOKEN_URL") ?? "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token";
const API = "https://opensky-network.org/api";
const TTL = 30_000;

// 空港ごとの範囲（南北・東西におよそ90km。房総半島の南や相模湾からの進入まで入る）
const AIRPORTS: Record<string, { at: [number, number]; box: [number, number, number, number] }> = {
  HND: { at: [35.5533, 139.7811], box: [34.75, 139.05, 36.30, 140.60] },
};

let token: { value: string; until: number } | null = null;
async function bearer(): Promise<string> {
  if (token && Date.now() < token.until) return token.value;
  const res = await fetch(TOKEN_URL, { method: "POST", signal: AbortSignal.timeout(5000), headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ grant_type: "client_credentials", client_id: Deno.env.get("OPENSKY_CLIENT_ID") ?? "", client_secret: Deno.env.get("OPENSKY_CLIENT_SECRET") ?? "" }) });
  if (!res.ok) throw new Error(`token ${res.status}`);
  const j = await res.json();
  token = { value: j.access_token, until: Date.now() + Math.max(60, (j.expires_in ?? 1800) - 60) * 1000 };
  return token.value;
}

const trails = new Map<string, Trails>();
const seeded = new Map<string, number>();          // 航跡を取りに行った機体（10分は取り直さない）
const cache = new Map<string, { at: number; body: string }>();

async function seedTrack(iata: string, id: string, tr: Trails) {
  const last = seeded.get(id);
  if (last && Date.now() - last < 10 * 60_000) return;
  seeded.set(id, Date.now());
  try {
    const r = await osFetch(`${API}/tracks/all?icao24=${encodeURIComponent(id)}&time=0`, 6000);
    if (!r.ok) return;
    const path = compactTrack((await r.json())?.path);
    if (!path) return;
    const box = AIRPORTS[iata].box, now = Date.now();
    const inBox = path.filter(([la, lo]) => la >= box[0] - 0.5 && la <= box[2] + 0.5 && lo >= box[1] - 0.5 && lo <= box[3] + 0.5);
    const cur = tr.get(id) ?? [];
    tr.set(id, [...inBox.map((p) => ({ t: now - 60_000, p: p as [number, number] })), ...cur]);
  } catch { /* 航跡が取れなくても、位置だけは出す */ }
}

// 認証つきで取れなければ、認証なしで取る（認証サーバーに届かないことがあるため）
let STEP = "";
async function osFetch(url: string, ms: number): Promise<Response> {
  let auth: Record<string, string> = {};
  try { STEP = "token"; auth = { Authorization: `Bearer ${await bearer()}` }; } catch { auth = {}; }
  STEP = auth.Authorization ? "api(auth)" : "api(anon)";
  return await fetch(url, { headers: auth, signal: AbortSignal.timeout(ms) });
}

async function snapshot(iata: string): Promise<string> {
  const hit = cache.get(iata);
  if (hit && Date.now() - hit.at < TTL) return hit.body;
  const a = AIRPORTS[iata], [la1, lo1, la2, lo2] = a.box;
  const r = await osFetch(`${API}/states/all?lamin=${la1}&lomin=${lo1}&lamax=${la2}&lomax=${lo2}`, 12000);
  if (!r.ok) throw new Error(`states ${r.status} ${STEP}`);
  const j = await r.json();
  const planes = planesFrom(j?.states, a.at);
  if (!trails.has(iata)) trails.set(iata, new Map());
  const tr = trails.get(iata)!;
  updateTrails(tr, planes, Date.now());
  // 着陸に向かう機体で、まだ線の短いものは、航跡を一度だけ取る（1回の更新で3機まで）
  const need = planes.filter((p) => p.phase === "arr" && (tr.get(p.id)?.length ?? 0) < 3).slice(0, 3);
  await Promise.all(need.map((p) => seedTrack(iata, p.id, tr)));
  const body = JSON.stringify({
    iata, at: new Date((j?.time ?? Date.now() / 1000) * 1000).toISOString(),
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
    return new Response(await snapshot(iata), { headers: { ...JSON_HEADERS, "Cache-Control": "max-age=15" } });
  } catch (e) {
    console.error(e);
    const hit = cache.get(iata);
    if (hit) return new Response(hit.body, { headers: { ...JSON_HEADERS, "X-Stale": "1" } });
    // 理由（どの問い合わせで止まったか）だけを返す。合言葉などは含めない
    const why = e instanceof Error ? (e.name === "TimeoutError" ? "timeout " + STEP : e.message.slice(0, 60)) : "error";
    return new Response(JSON.stringify({ error: "unavailable", why }), { status: 503, headers: JSON_HEADERS });
  }
});
