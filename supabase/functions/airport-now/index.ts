// 空港の今：その空港の天気（気象通報）と、直近の到着・出発便（JAL・ANA の公式のリアルタイム情報）をまとめて返す。
//   GET /functions/v1/airport-now?iata=HND
// ログインは不要（公開の情報だけを返す）。配信元に負担をかけないよう、空港ごとに数分ためて使い回す。
// 便の情報は ODPT の合言葉（ODPT_CONSUMER_KEY）が設定されているときだけ取る。未設定なら flights は null（アプリは便の欄を出さない）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { type FlightRow, normalize, recent, weather } from "../_shared/airport_now.ts";

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const JSON_HEADERS = { ...CORS, "Content-Type": "application/json" };
const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const ODPT_KEY = Deno.env.get("ODPT_CONSUMER_KEY") ?? "";
const ODPT = "https://api.odpt.org/api/v4";
const OPERATORS = ["JAL", "ANA"];
const WX_TTL = 5 * 60_000, FL_TTL = 3 * 60_000;

// 民間の空港（定期便のある空港）の IATA → ICAO。番外編は対象外
let AIRPORTS: Map<string, string> | null = null;
async function icaoOf(iata: string): Promise<string | null> {
  if (!AIRPORTS) {
    const { data, error } = await admin.from("airports").select("iata, icao").eq("game_target", true).is("extra_kind", null);
    if (error) throw error;
    AIRPORTS = new Map((data ?? []).filter((r) => r.iata && r.icao).map((r) => [String(r.iata), String(r.icao)]));
  }
  return AIRPORTS.get(iata) ?? null;
}

const wxCache = new Map<string, { at: number; v: unknown }>();
async function getWeather(icao: string) {
  const hit = wxCache.get(icao);
  if (hit && Date.now() - hit.at < WX_TTL) return hit.v;
  try {
    const r = await fetch(`https://aviationweather.gov/api/data/metar?ids=${icao}&format=json`, { headers: { "User-Agent": "soramemo (airport-now)" } });
    if (!r.ok) throw new Error("metar " + r.status);
    const m = (await r.json())[0];
    const v = m ? weather(m) : null;
    wxCache.set(icao, { at: Date.now(), v });
    return v;
  } catch { return hit ? hit.v : null; }   // 取れないときは古い通報（なければ null）
}

const flCache = new Map<string, { at: number; v: { arr: FlightRow[]; dep: FlightRow[] } }>();
async function odpt(type: string, op: string, key: string, iata: string): Promise<Record<string, unknown>[]> {
  const u = new URL(`${ODPT}/odpt:${type}`);
  u.searchParams.set("odpt:operator", `odpt.Operator:${op}`);
  u.searchParams.set(key, `odpt.Airport:${iata}`);
  u.searchParams.set("acl:consumerKey", ODPT_KEY);
  const r = await fetch(u, { headers: { "User-Agent": "soramemo (airport-now)" } });
  if (!r.ok) throw new Error(`odpt ${type} ${op} ${r.status}`);
  const j = await r.json();
  return Array.isArray(j) ? j : [];
}
async function getFlights(iata: string) {
  if (!ODPT_KEY) return null;
  const hit = flCache.get(iata);
  if (hit && Date.now() - hit.at < FL_TTL) return hit.v;
  try {
    const parts = await Promise.all(OPERATORS.flatMap((op) => [
      odpt("FlightInformationArrival", op, "odpt:arrivalAirport", iata).then((l) => l.map((x) => normalize(x, "arr"))),
      odpt("FlightInformationDeparture", op, "odpt:departureAirport", iata).then((l) => l.map((x) => normalize(x, "dep"))),
    ]));
    const now = new Date(Date.now() + 9 * 3600_000), nowMin = now.getUTCHours() * 60 + now.getUTCMinutes();   // 日本時間の今
    const pick = (i: number) => recent(parts.filter((_, k) => k % 2 === i).flat().filter((x): x is FlightRow => !!x), nowMin);
    const v = { arr: pick(0), dep: pick(1) };
    flCache.set(iata, { at: Date.now(), v });
    return v;
  } catch { return hit ? hit.v : null; }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "GET") return new Response(JSON.stringify({ error: "GET only" }), { status: 405, headers: JSON_HEADERS });
  const iata = (new URL(req.url).searchParams.get("iata") || "").toUpperCase();
  if (!/^[A-Z]{3}$/.test(iata)) return new Response(JSON.stringify({ error: "bad airport" }), { status: 400, headers: JSON_HEADERS });
  let icao: string | null;
  try { icao = await icaoOf(iata); } catch { return new Response(JSON.stringify({ error: "unavailable" }), { status: 503, headers: JSON_HEADERS }); }
  if (!icao) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 404, headers: JSON_HEADERS });
  const [wx, flights] = await Promise.all([getWeather(icao), getFlights(iata)]);
  return new Response(JSON.stringify({ iata, at: new Date().toISOString(), weather: wx, flights }),
    { headers: { ...JSON_HEADERS, "Cache-Control": "max-age=60" } });
});
