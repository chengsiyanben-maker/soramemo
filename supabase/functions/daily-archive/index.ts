// 毎日の飛行機の記録：前の日（日本時間）の便ごとの実績・航跡と、空港ごとのまとめ、機体のつながり（運用の予想に使う）を作る。
//   GET /functions/v1/daily-archive            … 前の日と2日前（遅れて届いた実際の時刻を取り直す）
//   GET /functions/v1/daily-archive?days=13    … 時刻表が残っている13日前までさかのぼって作る（初回用）
// 何度呼んでも同じ結果になる（上書き）。同じ日を30分以内に作り直すことはしない（呼び出しの悪用で重くならないように）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { buildHistory, encodePolyline, jstYesterday, normFlight, type SchedRow, thin, userTrack } from "../_shared/archive.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const JSON_HEADERS = { "Content-Type": "application/json" };

async function schedOf(day: string): Promise<SchedRow[]> {
  const out: SchedRow[] = [];
  for (let from = 0; ; from += 1000) {
    const { data, error } = await admin.from("flight_schedule")
      .select("svc_date, flight, dep, arr, std, sta, atd, ata, dep_status, arr_status, aircraft, source, flight_watch(state)")
      .eq("svc_date", day).order("id").range(from, from + 999);
    if (error) throw error;
    for (const r of data ?? []) {
      const fw = (r as Record<string, unknown>).flight_watch as { state?: Record<string, unknown> } | { state?: Record<string, unknown> }[] | null;
      out.push({ ...(r as unknown as SchedRow), state: (Array.isArray(fw) ? fw[0]?.state : fw?.state) ?? null });
    }
    if (!data || data.length < 1000) break;
  }
  return out;
}

async function archiveDay(day: string) {
  const { data: run } = await admin.from("archive_runs").select("ran_at").eq("day", day).maybeSingle();
  if (run && Date.now() - Date.parse(run.ran_at) < 30 * 60_000) return { day, skipped: "recent" };
  const rows = await schedOf(day);
  if (!rows.length) return { day, flights: 0 };
  const hist = buildHistory(rows);
  for (let i = 0; i < hist.length; i += 500) {
    const { error } = await admin.from("flight_history").upsert(hist.slice(i, i + 500), { onConflict: "svc_date,flight,dep" });
    if (error) throw error;
  }
  // 航跡（点が届いている日だけ。36時間で消えるので、前の日のぶんだけ作れる）
  let tracks = 0;
  const { data: tp, error: tpe } = await admin.rpc("archive_track_points", { p_day: day });
  if (tpe) console.error("tracks", tpe.message);
  const keep = new Set(hist.map((h) => `${h.flight}|${h.dep}`));
  const thinned = new Map<string, { lat: number; lon: number }[]>();   // 便名（0を取ったもの・共同運航の便名も）|出発空港 → 航跡
  const alsoOf = new Map(hist.map((h) => [`${h.flight}|${h.dep}`, h.also]));
  const tr = ((tp ?? []) as { flight: string; dep: string; pts: [number, number, number | null][] }[])
    .filter((t) => keep.has(`${t.flight}|${t.dep}`) && t.pts.length >= 2)
    .map((t) => { const p = thin(t.pts.map(([lat, lon, alt]) => ({ lat, lon, alt })));
      for (const f of [t.flight, ...(alsoOf.get(`${t.flight}|${t.dep}`) ?? [])]) thinned.set(`${normFlight(f)}|${t.dep}`, p);
      return { svc_date: day, flight: t.flight, dep: t.dep, pts: encodePolyline(p).slice(0, 20000), alts: p.map((x) => x.alt ?? 0) }; });
  for (let i = 0; i < tr.length; i += 300) {
    const { error } = await admin.from("flight_tracks").upsert(tr.slice(i, i + 300), { onConflict: "svc_date,flight,dep" });
    if (error) { console.error("tracks", error.message); break; }
    tracks += Math.min(300, tr.length - i);
  }
  // 利用者のフライトに航跡を付ける（照合で OpenSky の航跡が取れなかった便。地図に実際の上昇・降下の道筋を描く）
  let users = 0;
  const { data: uf, error: ufe } = await admin.rpc("archive_user_flights", { p_day: day });
  if (ufe) console.error("user tracks", ufe.message);
  for (const u of (uf ?? []) as { id: number; flight: string; dep: string }[]) {
    const p = thinned.get(`${u.flight}|${u.dep}`), track = p ? userTrack(p) : null;
    if (!track) continue;
    const { error } = await admin.from("flights").update({ track }).eq("id", u.id).is("track", null);
    if (error) { console.error("user tracks", error.message); break; }
    users++;
  }
  const { data: aps } = await admin.rpc("archive_airport_daily", { p_day: day });
  const { data: links } = await admin.rpc("archive_rotations", { p_day: day });
  const result = { day, schedule: rows.length, flights: hist.length, with_reg: hist.filter((h) => h.reg).length, tracks, user_tracks: users, airports: aps, links };
  await admin.from("archive_runs").upsert({ day, ran_at: new Date().toISOString(), result });
  return result;
}

Deno.serve(async (req) => {
  try {
    const u = new URL(req.url), days = Math.min(13, Math.max(2, Number(u.searchParams.get("days")) || 2));
    const y = jstYesterday(), out = [];
    for (let i = 0; i < days; i++) {
      const d = new Date(Date.parse(y + "T00:00:00Z") - i * 86_400_000).toISOString().slice(0, 10);
      out.push(await archiveDay(d));
    }
    console.log("daily-archive", JSON.stringify(out));
    return new Response(JSON.stringify(out), { headers: JSON_HEADERS });
  } catch (e) {
    console.error(e);
    return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  }
});
