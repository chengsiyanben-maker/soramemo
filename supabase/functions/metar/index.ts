// 空港の気象通報（METAR）の中継。配信元（米国の航空気象センター）は、ほかのサイトのアプリから直接は読めないため、ここを通す。
// 同じ空港の通報は5分間使い回し、配信元に負担をかけない。ログインは不要（公開の気象情報だけを返す）。
//   GET /functions/v1/metar?ids=RJTT
import { fetchMetars } from "../_shared/metar.ts";

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
  try {
    const m = (await fetchMetars([id])).get(id);
    if (!m) throw new Error("no report");
    const { id: _, ...rest } = m;
    const body = JSON.stringify({ id, ...rest });
    cache.set(id, { at: Date.now(), body });
    return new Response(body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "max-age=120" } });
  } catch (e) {
    if (hit) return new Response(hit.body, { headers: { ...CORS, "Content-Type": "application/json", "X-Stale": "1" } });   // 取れないときは古い通報を返す
    return new Response(JSON.stringify({ error: "unavailable" }), { status: 503, headers: { ...CORS, "Content-Type": "application/json" } });
  }
});
