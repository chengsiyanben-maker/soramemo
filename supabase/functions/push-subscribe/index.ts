// スマホへの通知（遅れ・ダイバートのお知らせ）の申し込み・取り消し。ログインは不要（ブラウザの購読と、選んだ空港だけを持つ）。
//   GET  /functions/v1/push-subscribe                         → { key: VAPID の公開鍵 }（鍵がまだなければ key は null）
//   POST /functions/v1/push-subscribe  { endpoint, keys:{p256dh, auth}, airports:["HND", ...], flights:["JL509@2026-10-26", ...] }
//        → 申し込み（同じ endpoint は上書き）。flights は「この便に乗る」で選んだ便（5便まで）
//        sp_airports:["HND", ...] を付けると、その空港に特別塗装機が着陸に向かってきたときも知らせる
//        spot:{ iata:"HND", kinds:["special","big","foreign","reg","ops"], lead:5, regs:["JA01XJ"], flights:["JL123@2026-10-21"] } を付けると、
//        撮影の知らせ（その空港に、選んだ種類の機体が着陸の lead 分前になったら。運用が変わったときも）。spot:null で撮影の知らせをやめる
//   POST /functions/v1/push-subscribe  { endpoint, remove:true }                              → 取り消し
import { createClient } from "npm:@supabase/supabase-js@2.117.2";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
const J = { ...CORS, "Content-Type": "application/json" };
const res = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: J });

// 通知を送ってよい宛先（各ブラウザの配信サービス）だけ受け付ける
const PUSH_HOSTS = /^https:\/\/([a-z0-9-]+\.)*(fcm\.googleapis\.com|push\.services\.mozilla\.com|notify\.windows\.com|push\.apple\.com|web\.push\.apple\.com)\//;

// 撮影の知らせの設定を、決まった形だけに絞る
const KINDS = new Set(["special", "big", "foreign", "reg", "ops"]);
function spotOf(v: unknown) {
  const o = (v && typeof v === "object" ? v : {}) as Record<string, unknown>;
  const arr = (x: unknown, re: RegExp, max: number) => Array.isArray(x) ? [...new Set(x.filter((y) => typeof y === "string" && re.test(y)))].slice(0, max) as string[] : [];
  return {
    spot_iata: typeof o.iata === "string" && /^[A-Z]{3}$/.test(o.iata) ? o.iata : null,
    spot_kinds: Array.isArray(o.kinds) ? [...new Set(o.kinds.filter((k) => typeof k === "string" && KINDS.has(k)))] as string[] : [],
    spot_lead: o.lead === 3 || o.lead === 10 ? o.lead : 5,
    spot_regs: arr(o.regs, /^JA[0-9A-Z]{3,5}$/, 10),
    spot_flights: arr(o.flights, /^[A-Z0-9]{2}\d{1,4}[A-Z]?@\d{4}-\d{2}-\d{2}$/, 10),
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method === "GET") return res({ key: Deno.env.get("VAPID_PUBLIC_KEY") || null });
  if (req.method !== "POST") return res({ error: "GET/POST only" }, 405);
  let b: { endpoint?: unknown; keys?: { p256dh?: unknown; auth?: unknown }; airports?: unknown; flights?: unknown; sp_airports?: unknown; spot?: unknown; remove?: unknown };
  try { b = await req.json(); } catch { return res({ error: "bad json" }, 400); }
  const endpoint = typeof b.endpoint === "string" ? b.endpoint : "";
  if (!PUSH_HOSTS.test(endpoint) || endpoint.length > 1000) return res({ error: "bad endpoint" }, 400);
  if (b.remove === true) {
    await admin.from("push_subs").delete().eq("endpoint", endpoint);
    return res({ ok: true, removed: true });
  }
  const p256dh = typeof b.keys?.p256dh === "string" ? b.keys.p256dh : "", auth = typeof b.keys?.auth === "string" ? b.keys.auth : "";
  if (!/^[A-Za-z0-9_-]{20,200}={0,2}$/.test(p256dh) || !/^[A-Za-z0-9_-]{8,100}={0,2}$/.test(auth)) return res({ error: "bad keys" }, 400);
  const airports = Array.isArray(b.airports) ? [...new Set(b.airports.filter((x) => typeof x === "string" && /^[A-Z]{3}$/.test(x)))].slice(0, 12) as string[] : [];
  const flights = Array.isArray(b.flights) ? [...new Set(b.flights.filter((x) => typeof x === "string" && /^[A-Z0-9]{2}\d{1,4}[A-Z]?@\d{4}-\d{2}-\d{2}$/.test(x)))].slice(0, 5) as string[] : [];
  const sp_airports = Array.isArray(b.sp_airports) ? [...new Set(b.sp_airports.filter((x) => typeof x === "string" && /^[A-Z]{3}$/.test(x)))].slice(0, 14) as string[] : [];
  const spot = spotOf(b.spot), hasSpot = !!spot.spot_iata && (spot.spot_kinds.length > 0 || spot.spot_flights.length > 0);
  if (!airports.length && !flights.length && !sp_airports.length && !hasSpot) {   // 何も選ばれていなければ取り消し
    await admin.from("push_subs").delete().eq("endpoint", endpoint);
    return res({ ok: true, removed: true });
  }
  const row = { endpoint, p256dh, auth, airports, flights, sp_airports, ...(hasSpot ? spot : { spot_iata: null, spot_kinds: [] as string[], spot_lead: 5, spot_regs: [] as string[], spot_flights: [] as string[] }) };
  const { error } = await admin.from("push_subs").upsert(row, { onConflict: "endpoint" });
  if (error) { console.error(error); return res({ error: "save failed" }, 500); }
  return res({ ok: true, airports, flights, sp_airports, spot: hasSpot ? spot : null });
});
