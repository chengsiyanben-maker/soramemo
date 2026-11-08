// 空港の気象通報（METAR）の中継。配信元（米国の航空気象センター）は、ほかのサイトのアプリから直接は読めないため、ここを通す。
// 同じ空港の通報は5分間使い回し、配信元に負担をかけない。ログインは不要（公開の気象情報だけを返す）。
//   GET /functions/v1/metar?ids=RJTT
//   配信元が一時的に取れないとき（11/7 22:20 に RJTT で 503 があった）：1回だけ取り直し、それでもだめなら
//   この関数の中の古い通報 → 天気の記録（wx_obs。1時間ごと・3時間以内）の順に返す（"stale": true を付ける）。どれもなければ 503
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { fetchMetars, type Metar, metarFromObs } from "../_shared/metar.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
async function fromUpstream(id: string): Promise<Metar | null> {
  for (let i = 0; i < 2; i++) {
    try { const m = (await fetchMetars([id], 6000)).get(id); if (m) return m; } catch { /* もう1回 */ }
    if (!i) await new Promise((r) => setTimeout(r, 1500));
  }
  return null;
}
async function fromArchive(id: string): Promise<Metar | null> {
  try {
    const { data } = await admin.from("wx_obs").select("icao, at, raw, wdir, wspd, wgst, vis_m").eq("icao", id)
      .gt("at", new Date(Date.now() - 3 * 3600_000).toISOString()).order("at", { ascending: false }).limit(1);
    return metarFromObs(data?.[0]);
  } catch { return null; }
}

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const cache = new Map<string, { at: number; body: string }>();
const TTL = 5 * 60_000;
const ALLOWED = new Set(["RJTT", "RJAA", "RJBB", "RJOO", "RJGG", "RJCC", "RJFF", "ROAH", "RJSS", "RJOA", "RJOM", "RJFT", "RJFU", "RJFK"]);   // 運用の表示に使う空港だけ

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  const id = (new URL(req.url).searchParams.get("ids") || "RJTT").toUpperCase();
  if (!ALLOWED.has(id)) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 400, headers: { ...CORS, "Content-Type": "application/json" } });
  const hit = cache.get(id);
  if (hit && Date.now() - hit.at < TTL) return new Response(hit.body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "max-age=120" } });
  const m = await fromUpstream(id);
  if (m) {
    const { id: _, ...rest } = m;
    const body = JSON.stringify({ id, ...rest });
    cache.set(id, { at: Date.now(), body });
    return new Response(body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "max-age=120" } });
  }
  if (hit) return new Response(JSON.stringify({ ...JSON.parse(hit.body), stale: true }), { headers: { ...CORS, "Content-Type": "application/json", "X-Stale": "1", "Cache-Control": "max-age=30" } });   // 取れないときは古い通報を返す
  const a = await fromArchive(id);
  if (a) { const { id: _, ...rest } = a; return new Response(JSON.stringify({ id, ...rest, stale: true }), { headers: { ...CORS, "Content-Type": "application/json", "X-Stale": "1", "Cache-Control": "max-age=30" } }); }
  return new Response(JSON.stringify({ error: "unavailable" }), { status: 503, headers: { ...CORS, "Content-Type": "application/json" } });
});
