// 空港の今：その空港の天気（気象通報）と、直近の到着・出発便（JAL・ANA の公式のリアルタイム情報）をまとめて返す。
//   GET /functions/v1/airport-now?iata=HND
// ログインは不要（公開の情報だけを返す）。配信元に負担をかけないよう、空港ごとに数分ためて使い回す。
// 便の情報は ODPT の合言葉（ODPT_CONSUMER_KEY）が設定されているときだけ取る。未設定なら flights は null（アプリは便の欄を出さない）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { amedasNearest, type AmedasStation, amedasWeather, type FlightRow, normalize, recent, tafPeriods, weather } from "../_shared/airport_now.ts";

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const JSON_HEADERS = { ...CORS, "Content-Type": "application/json" };
const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const ODPT_KEY = Deno.env.get("ODPT_CONSUMER_KEY") ?? "";
const ODPT = "https://api.odpt.org/api/v4";
const OPERATORS = ["JAL", "ANA"];
const WX_TTL = 5 * 60_000, FL_TTL = 3 * 60_000;

// 民間の空港（定期便のある空港）の IATA → ICAO と位置。番外編は対象外
type Apt = { icao: string; lat: number; lon: number };
let AIRPORTS: Map<string, Apt> | null = null;
async function airportOf(iata: string): Promise<Apt | null> {
  if (!AIRPORTS) {
    const { data, error } = await admin.from("airports").select("iata, icao, lat, lon").eq("game_target", true).is("extra_kind", null);
    if (error) throw error;
    AIRPORTS = new Map((data ?? []).filter((r) => r.iata && r.icao).map((r) => [String(r.iata), { icao: String(r.icao), lat: Number(r.lat), lon: Number(r.lon) }]));
  }
  return AIRPORTS.get(iata) ?? null;
}

// 予報（TAF）：30分ためて使う。ない空港も多い（その場合は null）
const TAF_TTL = 30 * 60_000;
const tafCache = new Map<string, { at: number; v: unknown }>();
async function getTaf(icao: string) {
  const hit = tafCache.get(icao);
  if (hit && Date.now() - hit.at < TAF_TTL) return hit.v;
  try {
    const r = await fetch(`https://aviationweather.gov/api/data/taf?ids=${icao}&format=json`, { headers: { "User-Agent": "soramemo (airport-now)" } });
    if (r.status === 204) { tafCache.set(icao, { at: Date.now(), v: null }); return null; }
    if (!r.ok) throw new Error("taf " + r.status);
    const t = (await r.json())[0];
    const periods = t && Array.isArray(t.fcsts) ? tafPeriods(t.fcsts, Math.floor(Date.now() / 1000)) : [];
    const v = periods.length ? { issued: t.issueTime ?? null, periods } : null;
    tafCache.set(icao, { at: Date.now(), v });
    return v;
  } catch { return hit ? hit.v : null; }
}

// 気象庁アメダス：METAR のない空港の代わり。観測所の一覧は1日、最新の値は10分ためて全空港で使い回す
const JMA = "https://www.jma.go.jp/bosai/amedas";
let amTable: { at: number; v: Record<string, AmedasStation> } | null = null;
let amMap: { at: number; time: string; v: Record<string, Record<string, [number | null, number | null]>> } | null = null;
async function getAmedas(apt: Apt) {
  try {
    if (!amTable || Date.now() - amTable.at > 864e5) {
      const r = await fetch(`${JMA}/const/amedastable.json`); if (!r.ok) throw new Error("amedas table " + r.status);
      amTable = { at: Date.now(), v: await r.json() };
    }
    const st = amedasNearest(amTable.v, apt.lat, apt.lon);
    if (!st) return null;
    if (!amMap || Date.now() - amMap.at > 10 * 60_000) {
      const t = (await (await fetch(`${JMA}/data/latest_time.txt`)).text()).trim();          // 例 2026-10-12T21:00:00+09:00
      const stamp = t.slice(0, 19).replace(/[-T:]/g, "");
      const r = await fetch(`${JMA}/data/map/${stamp}.json`); if (!r.ok) throw new Error("amedas map " + r.status);
      amMap = { at: Date.now(), time: t, v: await r.json() };
    }
    const v = amMap.v[st.id];
    return v ? amedasWeather(v, st.name, amMap.time) : null;
  } catch { return null; }
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
  let apt: Apt | null;
  try { apt = await airportOf(iata); } catch { return new Response(JSON.stringify({ error: "unavailable" }), { status: 503, headers: JSON_HEADERS }); }
  if (!apt) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 404, headers: JSON_HEADERS });
  const [metar, taf, flights] = await Promise.all([getWeather(apt.icao), getTaf(apt.icao), getFlights(iata)]);
  const wx = metar ?? await getAmedas(apt);     // 気象通報がない空港は、近くのアメダスで代わりにする
  return new Response(JSON.stringify({ iata, at: new Date().toISOString(), weather: wx, taf, flights }),
    { headers: { ...JSON_HEADERS, "Cache-Control": "max-age=60" } });
});
