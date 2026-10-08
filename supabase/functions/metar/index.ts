// 空港の気象通報（METAR）の中継。配信元（米国の航空気象センター）は、ほかのサイトのアプリから直接は読めないため、ここを通す。
// 同じ空港の通報は5分間使い回し、配信元に負担をかけない。ログインは不要（公開の気象情報だけを返す）。
//   GET /functions/v1/metar?ids=RJTT
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const cache = new Map<string, { at: number; body: string }>();
const TTL = 5 * 60_000;
const ALLOWED = new Set(["RJTT", "RJAA", "RJBB", "RJOO", "RJGG", "RJCC", "RJFF", "ROAH"]);   // 運用の表示に使う空港だけ

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  const id = (new URL(req.url).searchParams.get("ids") || "RJTT").toUpperCase();
  if (!ALLOWED.has(id)) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 400, headers: { ...CORS, "Content-Type": "application/json" } });
  const hit = cache.get(id);
  if (hit && Date.now() - hit.at < TTL) return new Response(hit.body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "max-age=120" } });
  try {
    const r = await fetch(`https://aviationweather.gov/api/data/metar?ids=${id}&format=json`, { headers: { "User-Agent": "soramemo (metar relay)" } });
    if (!r.ok) throw new Error("upstream " + r.status);
    const m = (await r.json())[0];
    if (!m) throw new Error("no report");
    // 視程：「6+」は6マイル以上（10km以上）。数字はマイル
    // 日本の空港の通報は、視程をメートルの4桁で書く（9999＝10km以上）。原文の数字を優先し、なければマイルの値を換算する
    const raw = String(m.rawOb ?? ""), mv = raw.match(/KT\s+(?:\d{3}V\d{3}\s+)?(\d{4})(?:\s|$)/) || raw.match(/\s(CAVOK)\s/);
    const visRaw = String(m.visib ?? ""), visMi = parseFloat(visRaw);
    const visM = mv ? (mv[1] === "CAVOK" || mv[1] === "9999" ? 10000 : parseInt(mv[1], 10)) : Number.isFinite(visMi) ? Math.round(visMi * 1609) : null;
    const body = JSON.stringify({
      id, time: m.reportTime, raw: m.rawOb,
      wdir: typeof m.wdir === "number" ? m.wdir : null,          // 風向（度）。風向が変わりやすいとき（VRB）は null
      wspd: m.wspd ?? null, wgst: m.wgst ?? null,                 // 風速・最大瞬間（ノット）
      vis_m: visM, vis_plus: mv ? mv[1] === "9999" || mv[1] === "CAVOK" : visRaw.endsWith("+"),
    });
    cache.set(id, { at: Date.now(), body });
    return new Response(body, { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "max-age=120" } });
  } catch (e) {
    if (hit) return new Response(hit.body, { headers: { ...CORS, "Content-Type": "application/json", "X-Stale": "1" } });   // 取れないときは古い通報を返す
    return new Response(JSON.stringify({ error: "unavailable" }), { status: 503, headers: { ...CORS, "Content-Type": "application/json" } });
  }
});
