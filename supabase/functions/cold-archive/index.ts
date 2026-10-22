// 古い記録をファイル置き場に移す（毎晩。cron 'cold-archive'）。400日より前の日を、表ごと・日ごとに gzip の JSON にして Storage（非公開）へ。
//   置けたことを読み直して確かめてから、データベースから消す（cold_done は、行数が変わっていたら消さない）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { COLD_BUCKET, coldBefore, coldPath, gunzip, gzip } from "../_shared/cold.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const J = { "Content-Type": "application/json" };

Deno.serve(async (req) => {
  const lim = Math.min(40, Math.max(1, Number(new URL(req.url).searchParams.get("limit")) || 12));
  const { data: cands, error } = await admin.rpc("cold_candidates", { p_before: coldBefore(), p_limit: lim });
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: J });
  const done: unknown[] = [];
  for (const c of (cands ?? []) as { tbl: string; day: string }[]) {
    const { data: rows, error: e1 } = await admin.rpc("cold_rows", { p_tbl: c.tbl, p_day: c.day });
    if (e1 || !Array.isArray(rows)) { done.push({ ...c, error: e1?.message ?? "rows" }); continue; }
    const body = JSON.stringify({ tbl: c.tbl, day: c.day, made_at: new Date().toISOString(), note: "そらメモの記録（ODPT・adsb.lol をもとに作成。公開しないこと）", rows });
    const gz = await gzip(body), path = coldPath(c.tbl, c.day);
    const up = await admin.storage.from(COLD_BUCKET).upload(path, gz, { contentType: "application/gzip", upsert: true });
    if (up.error) { done.push({ ...c, error: up.error.message }); continue; }
    // 置けたものを読み直して、行数を確かめる
    const dl = await admin.storage.from(COLD_BUCKET).download(path);
    if (dl.error || !dl.data) { done.push({ ...c, error: "verify" }); continue; }
    const back = JSON.parse(await gunzip(await dl.data.arrayBuffer()));
    if (!Array.isArray(back.rows) || back.rows.length !== rows.length) { done.push({ ...c, error: "verify count" }); continue; }
    const { data: n, error: e2 } = await admin.rpc("cold_done", { p_tbl: c.tbl, p_day: c.day, p_path: path, p_rows: rows.length, p_bytes: gz.length });
    done.push({ ...c, rows: rows.length, bytes: gz.length, deleted: n, error: e2?.message });
  }
  return new Response(JSON.stringify({ before: coldBefore(), done }), { headers: J });
});
