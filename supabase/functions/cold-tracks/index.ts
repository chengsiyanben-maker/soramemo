// 空の道すじ（ファイル置き場に移した日）：その空港・その日の航跡の線だけを返す（便名・時刻は返さない）
//   GET /functions/v1/cold-tracks?iata=HND&day=2025-09-01 → [{d: 出発なら1, p: 線}, …]
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { COLD_BUCKET, coldPath, gunzip, tracksFrom } from "../_shared/cold.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  const u = new URL(req.url), iata = u.searchParams.get("iata") ?? "", day = u.searchParams.get("day") ?? "";
  if (!/^[A-Z]{3}$/.test(iata) || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return new Response("[]", { status: 400, headers: { ...CORS, "Content-Type": "application/json" } });
  for (const tbl of ["airport_tracks_all", "flight_tracks"] as const) {
    const dl = await admin.storage.from(COLD_BUCKET).download(coldPath(tbl, day));
    if (dl.error || !dl.data) continue;
    const rows = JSON.parse(await gunzip(await dl.data.arrayBuffer())).rows ?? [];
    const out = tracksFrom(tbl, rows, iata).slice(0, 3000);
    if (out.length) return new Response(JSON.stringify(out), { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "public, max-age=86400" } });
  }
  return new Response("[]", { headers: { ...CORS, "Content-Type": "application/json", "Cache-Control": "public, max-age=3600" } });
});
