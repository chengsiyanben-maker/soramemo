// 毎日の記録を、運営者のパソコンに保存するために渡す（1日ぶんを gzip した JSON で）。
//   GET /functions/v1/archive-export?day=2026-10-17   見出し x-export-token に合言葉（ARCHIVE_EXPORT_TOKEN）
// 中身：便ごとの実績・航跡・空港ごとのまとめ・機体のつながり。ODPT のデータを含むので、運営者の手元に保存するだけにする（公開しない）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const TOKEN = Deno.env.get("ARCHIVE_EXPORT_TOKEN") ?? "";

function sameSecret(a: string, b: string): boolean {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}
async function all(table: string, col: string, day: string) {
  const out: unknown[] = [];
  for (let from = 0; ; from += 1000) {
    const { data, error } = await admin.from(table).select("*").eq(col, day).range(from, from + 999);
    if (error) throw error;
    out.push(...(data ?? []));
    if (!data || data.length < 1000) break;
  }
  return out;
}

Deno.serve(async (req) => {
  if (TOKEN.length < 24 || !sameSecret(req.headers.get("x-export-token") ?? "", TOKEN)) return new Response("forbidden", { status: 403 });
  const day = new URL(req.url).searchParams.get("day") ?? "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return new Response("bad day", { status: 400 });
  try {
    const [flights, tracks, airports, rotations, runs] = await Promise.all([
      all("flight_history", "svc_date", day), all("flight_tracks", "svc_date", day), all("airport_daily", "day", day),
      all("rotation_obs", "svc_date", day), all("archive_runs", "day", day)]);
    if (!runs.length) return new Response("not ready", { status: 404 });
    const body = JSON.stringify({ day, made_at: new Date().toISOString(), source: "そらメモ 毎日の記録（ODPT・adsb.lol をもとに作成。公開しないこと）", flights, tracks, airports, rotations });
    const gz = new Blob([body]).stream().pipeThrough(new CompressionStream("gzip"));
    return new Response(gz, { headers: { "Content-Type": "application/gzip", "Content-Disposition": `attachment; filename="${day}.json.gz"` } });
  } catch (e) {
    console.error(e);
    return new Response("error", { status: 500 });
  }
});
