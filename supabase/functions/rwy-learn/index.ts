// 日本中の空港の、着陸・離陸した滑走路を、1日の航跡から見つけて残す（毎晩。cron 'rwy-learn'）
//   GET /functions/v1/rwy-learn?part=0     → この24時間の、8つに分けたうちの0番目（呼び出し符号で分ける。cron は0〜7を同時に頼む）
//   GET /functions/v1/rwy-learn?part=0&hours=36 → この36時間（航跡は36時間で消えるので、36まで）
//   同じ航跡をもう一度読んでも、同じ記録は重ねない（rwy_samples_once）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { type Ap, type Pt, samplesOf } from "../_shared/rwy_track.ts";
import RW from "../_shared/jp_runways.json" with { type: "json" };

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const J = { "Content-Type": "application/json" };
const APS = Object.fromEntries(Object.entries(RW as unknown as Record<string, Ap>).filter(([, a]) => Object.keys(a.rw ?? {}).length));
const PARTS = 8;
// 羽田・成田は30秒ごとの見張り（airport-traffic）のほうがくわしいので、ここでは数えない
const SKIP = new Set(["HND", "NRT"]);

Deno.serve(async (req) => {
  const u = new URL(req.url), hours = Math.min(36, Math.max(1, Number(u.searchParams.get("hours")) || 24));
  const to = new Date(), from = new Date(to.getTime() - hours * 3600_000);
  const one = u.searchParams.get("part"), parts = one != null && /^[0-7]$/.test(one) ? [Number(one)] : [...Array(PARTS).keys()];
  let n = 0, planes = 0; const by: Record<string, number> = {};
  for (const part of parts) {
    const { data, error } = await admin.rpc("rwy_learn_points", { p_from: from.toISOString(), p_to: to.toISOString(), p_part: part, p_parts: PARTS });
    if (error) return new Response(JSON.stringify({ error: error.message, part }), { status: 500, headers: J });
    const rows: Record<string, unknown>[] = [];
    for (const x of (data ?? []) as { cs: string; p: Pt[] }[]) {
      planes++;
      for (const s of samplesOf(x.cs, x.p, APS, SKIP)) { rows.push({ ...s, src: "track" }); by[s.iata] = (by[s.iata] ?? 0) + 1; }
    }
    for (let i = 0; i < rows.length; i += 500) { const { error: e } = await admin.from("rwy_samples").upsert(rows.slice(i, i + 500), { onConflict: "src,iata,dir,callsign,at", ignoreDuplicates: true }); if (e) return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: J }); }
    n += rows.length;
  }
  return new Response(JSON.stringify({ from, to, planes, samples: n, airports: Object.keys(by).length, by }), { headers: J });
});
