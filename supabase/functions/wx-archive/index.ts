// 天気の記録（1時間ごと。cron 'wx-archive'）：日本の空港の METAR の原文（直近3時間ぶんを取り、同じものは重ねない）と、気象庁の台風情報、
//   羽田・成田の飛行場予報（TAF。11/25 本人「羽田、成田は優先的に取って」。原文と1時間ごとの風。_shared/taf.ts）
//   ?taf_back=7（&taf_skip=7）で、過去の TAF を3時間おきにさかのぼって取れる（API で取れるのは約2週間前まで）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { metarRow, tcKey, type TcRow, type WxRow } from "../_shared/wx_archive.ts";
import { tafBackDates, type TafHourRow, type TafObsRow, tafRows } from "../_shared/taf.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const J = { "Content-Type": "application/json" };
const UA = { "User-Agent": "soramemo (wx-archive)" };
const JMA = "https://www.jma.go.jp/bosai/typhoon/data";
const AWC = "https://aviationweather.gov/api/data";
// 優先して取りこぼさない空港（羽田・成田）
const PRIORITY = ["RJTT", "RJAA"];

async function saveMetars(list: unknown[]): Promise<number> {
  const rows: WxRow[] = [];
  for (const m of list) { const x = metarRow(m); if (x) rows.push(x); }
  if (!rows.length) return 0;
  const { error } = await admin.from("wx_obs").upsert(rows, { onConflict: "icao,at", ignoreDuplicates: true });
  if (error) throw new Error(error.message);
  return rows.length;
}

// TAF を取って残す（date があれば、その時刻に出ていた予報）。同じ発表は重ねない
async function saveTafs(date?: string): Promise<number> {
  const r = await fetch(`${AWC}/taf?ids=${PRIORITY.join(",")}&format=json${date ? `&date=${date}` : ""}`, { headers: UA, signal: AbortSignal.timeout(20000) });
  if (r.status === 204) { await r.body?.cancel(); return 0; }
  if (!r.ok) { await r.body?.cancel(); throw new Error("taf " + r.status); }
  const text = await r.text(); if (!text.trim()) return 0;
  const obs: TafObsRow[] = [], hours: TafHourRow[] = [];
  for (const t of JSON.parse(text) as unknown[]) { const x = tafRows(t); if (x) { obs.push(x.obs); hours.push(...x.hours); } }
  if (!obs.length) return 0;
  const a = await admin.from("taf_obs").upsert(obs, { onConflict: "icao,issued_at", ignoreDuplicates: true });
  if (a.error) throw new Error(a.error.message);
  const b = await admin.from("taf_hours").upsert(hours, { onConflict: "icao,hr,issued_at", ignoreDuplicates: true });
  if (b.error) throw new Error(b.error.message);
  return obs.length;
}

Deno.serve(async (req) => {
  const out: Record<string, unknown> = {};
  // 取る時間の幅（ふだんは3時間。始めたときや抜けたときは ?hours=48 などで、さかのぼって取れる）
  const url = new URL(req.url), hours = Math.min(72, Math.max(1, Number(url.searchParams.get("hours")) || 3));
  const tafBack = Math.min(7, Math.max(0, Math.floor(Number(url.searchParams.get("taf_back")) || 0)));
  const tafSkip = Math.min(14, Math.max(0, Math.floor(Number(url.searchParams.get("taf_skip")) || 0)));
  // 羽田・成田の METAR は別に1回（6時間ぶん）取り、全空港の組の上限で抜けないようにする（30分ごとの通報と臨時の通報 SPECI）
  try {
    const r = await fetch(`${AWC}/metar?ids=${PRIORITY.join(",")}&format=json&hours=${Math.max(6, hours)}`, { headers: UA, signal: AbortSignal.timeout(20000) });
    const text = r.ok ? await r.text() : "";
    out.metar_priority = r.ok ? (text.trim() ? await saveMetars(JSON.parse(text) as unknown[]) : 0) : "http " + r.status;
  } catch (e) { out.metar_priority_error = String(e); }
  // 羽田・成田の TAF（今出ている予報。さかのぼるときは3時間おき。1分100回の目安より十分少なく、0.5秒ずつあける）
  try {
    let saved = await saveTafs(), failed = 0;
    for (const d of tafBack ? tafBackDates(Date.now(), tafBack, tafSkip) : []) {
      await new Promise((ok) => setTimeout(ok, 500));
      try { saved += await saveTafs(d); } catch { failed++; }
    }
    out.taf = saved; if (failed) out.taf_failed = failed;
  } catch (e) { out.taf_error = String(e); }
  // METAR
  try {
    const { data: aps } = await admin.from("airports").select("icao").not("icao", "is", null);
    const icaos = [...new Set(((aps ?? []) as { icao: string }[]).map((a) => a.icao).filter((c) => /^R[JO][A-Z]{2}$/.test(c)))];
    // 1回に返る件数に上限があるので、さかのぼるときは空港を少しずつに分ける。1つの組が失敗しても、ほかは残す
    const step = hours > 6 ? 4 : 40;
    let saved = 0, failed = 0;
    for (let i = 0; i < icaos.length; i += step) {
      try {
        const r = await fetch(`${AWC}/metar?ids=${icaos.slice(i, i + step).join(",")}&format=json&hours=${hours}`, { headers: UA, signal: AbortSignal.timeout(20000) });
        const text = r.ok ? await r.text() : "";
        if (!r.ok) { failed++; continue; }
        if (!text.trim()) continue;   // 通報がない空港だけの組は空で返る
        saved += await saveMetars(JSON.parse(text) as unknown[]);
      } catch (e) { failed++; out.metar_error = String(e); }
    }
    out.metar = saved; out.metar_failed = failed;
  } catch (e) { out.metar_error = String(e); }
  // 台風
  try {
    const r = await fetch(`${JMA}/targetTc.json`, { headers: UA, signal: AbortSignal.timeout(15000) });
    const list = r.ok ? ((await r.json()) as unknown[]) : [];
    const rows: TcRow[] = [];
    for (const t of list) {
      const k = tcKey(t); if (!k) continue;
      const get = async (f: string) => { try { const x = await fetch(`${JMA}/${k.tc_id}/${f}`, { headers: UA, signal: AbortSignal.timeout(15000) }); return x.ok ? await x.json() : null; } catch { return null; } };
      rows.push({ ...k, spec: await get("specifications.json"), forecast: await get("forecast.json") });
    }
    const { error } = rows.length ? await admin.from("typhoon_snap").upsert(rows, { onConflict: "tc_id,issue", ignoreDuplicates: true }) : { error: null };
    out.typhoon = rows.length; if (error) out.typhoon_error = error.message;
  } catch (e) { out.typhoon_error = String(e); }
  return new Response(JSON.stringify(out), { headers: J });
});
