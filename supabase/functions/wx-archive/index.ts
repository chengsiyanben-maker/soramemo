// 天気の記録（1時間ごと。cron 'wx-archive'、羽田・成田は 'wx-hnd-nrt' も）：羽田・成田の TAF（移行198）と、日本の空港の METAR の原文（直近3時間ぶんを取り、同じものは重ねない）と、気象庁の台風情報
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { metarRow, tcKey, type TcRow, type WxRow } from "../_shared/wx_archive.ts";
import { awcDate, backDates, type TafHour, tafHours, tafRow, type TafRow } from "../_shared/taf.ts";
import { OPS_AIRPORTS } from "../_shared/ops_core.js";
import { readShared, writeShared } from "../_shared/edge_cache.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const J = { "Content-Type": "application/json" };
const UA = { "User-Agent": "soramemo (wx-archive)" };
const JMA = "https://www.jma.go.jp/bosai/typhoon/data";
const AWC = "https://aviationweather.gov/api/data";

// 羽田・成田（移行198）：TAF を残し、METAR は取りこぼさないよう直近6時間を取り直す。過去の TAF は ops_log の始まり（10/15）までさかのぼる
const HNT: Record<string, string> = { RJTT: "HND", RJAA: "NRT" };
const BACK_FROM = Date.parse("2026-10-14T15:00:00Z");   // 10/15 0時（日本時間）
// deno-lint-ignore no-explicit-any
const estimateOf = (icao: string) => (m: any, at: Date) => (OPS_AIRPORTS as any)[HNT[icao]]?.estimate(m, at)?.mode ?? null;
const sleep = (ms: number) => new Promise((ok) => setTimeout(ok, ms));

// TAF の JSON（配列）を2つの表に書く。同じ発表はもう一度書かない（原文は ignoreDuplicates、時間ごとも主キーで重ねない）
async function saveTafs(list: unknown[]): Promise<{ tafs: number; hours: number }> {
  const rows: TafRow[] = [], hours: TafHour[] = [];
  for (const t of list) {
    const r = tafRow(t); if (!r || !HNT[r.icao]) continue;
    rows.push(r); hours.push(...tafHours(t, estimateOf(r.icao)));
  }
  if (!rows.length) return { tafs: 0, hours: 0 };
  const a = await admin.from("wx_taf").upsert(rows, { onConflict: "icao,issued", ignoreDuplicates: true });
  if (a.error) throw new Error("wx_taf " + a.error.message);
  const b = hours.length ? await admin.from("wx_taf_hours").upsert(hours, { onConflict: "icao,at,issued", ignoreDuplicates: true }) : { error: null };
  if (b.error) throw new Error("wx_taf_hours " + b.error.message);
  return { tafs: rows.length, hours: hours.length };
}
async function getJson(url: string): Promise<unknown[]> {
  const r = await fetch(url, { headers: UA, signal: AbortSignal.timeout(15000) });
  if (!r.ok) { await r.body?.cancel(); throw new Error(`aviationweather ${r.status}`); }
  const text = await r.text();
  return text.trim() ? (JSON.parse(text) as unknown[]) : [];
}
// 羽田・成田の分（毎時7分の回も41分の回も）。back＝過去の TAF を1日ぶんさかのぼるか（41分の回だけ）
async function hndNrt(out: Record<string, unknown>, back: boolean) {
  const ids = Object.keys(HNT).join(",");
  try { out.taf = await saveTafs(await getJson(`${AWC}/taf?ids=${ids}&format=json`)); } catch (e) { out.taf_error = String(e).slice(0, 200); }
  if (!back) return;
  try {
    const rows: WxRow[] = [];
    for (const m of await getJson(`${AWC}/metar?ids=${ids}&format=json&hours=6`)) { const x = metarRow(m); if (x) rows.push(x); }
    const { error } = rows.length ? await admin.from("wx_obs").upsert(rows, { onConflict: "icao,at", ignoreDuplicates: true }) : { error: null };
    out.hnt_metar = rows.length; if (error) out.hnt_metar_error = error.message;
  } catch (e) { out.hnt_metar_error = String(e).slice(0, 200); }
  // さかのぼり：置き場の 'tafback:RJTT' に「次はこの時刻より前」を持つ。3時間ずつ8回（1日ぶん）。10/15 まで来たら止まる
  const sh = await readShared(admin, Object.keys(HNT).map((k) => `tafback:${k}`));
  const done: Record<string, unknown> = {};
  for (const icao of Object.keys(HNT)) {
    const cur = Date.parse(String(sh.get(`tafback:${icao}`)?.v ?? "")) || Date.now();
    const dates = backDates(cur, BACK_FROM);
    if (!dates.length) { done[icao] = "done"; continue; }
    let n = 0, failed = 0;
    for (const d of dates) {
      try { n += (await saveTafs(await getJson(`${AWC}/taf?ids=${icao}&format=json&date=${awcDate(d)}`))).tafs; } catch { failed++; }
      await sleep(300);   // 配信元に負担をかけないよう、1つずつあけて
    }
    // 半分より多く失敗したら、同じ所をもう一度（進めない）
    if (failed * 2 <= dates.length) await writeShared(admin, `tafback:${icao}`, new Date(dates[dates.length - 1]).toISOString());
    done[icao] = { from: new Date(dates[dates.length - 1]).toISOString(), tafs: n, failed };
  }
  out.taf_back = done;
}

Deno.serve(async (req) => {
  const out: Record<string, unknown> = {};
  // 羽田・成田だけの回（cron 'wx-hnd-nrt'、毎時41分。移行198）
  if (new URL(req.url).searchParams.get("part") === "hnt") {
    await hndNrt(out, true);
    return new Response(JSON.stringify(out), { headers: J });
  }
  // 取る時間の幅（ふだんは3時間。始めたときや抜けたときは ?hours=48 などで、さかのぼって取れる）
  const hours = Math.min(72, Math.max(1, Number(new URL(req.url).searchParams.get("hours")) || 3));
  // METAR
  try {
    const { data: aps } = await admin.from("airports").select("icao").not("icao", "is", null);
    const icaos = [...new Set(((aps ?? []) as { icao: string }[]).map((a) => a.icao).filter((c) => /^R[JO][A-Z]{2}$/.test(c)))];
    // 1回に返る件数に上限があるので、さかのぼるときは空港を少しずつに分ける。1つの組が失敗しても、ほかは残す
    const step = hours > 6 ? 4 : 40;
    let saved = 0, failed = 0;
    for (let i = 0; i < icaos.length; i += step) {
      try {
        const r = await fetch(`https://aviationweather.gov/api/data/metar?ids=${icaos.slice(i, i + step).join(",")}&format=json&hours=${hours}`, { headers: UA, signal: AbortSignal.timeout(20000) });
        const text = r.ok ? await r.text() : "";
        if (!r.ok) { failed++; continue; }
        if (!text.trim()) continue;   // 通報がない空港だけの組は空で返る
        const rows: WxRow[] = [];
        for (const m of JSON.parse(text) as unknown[]) { const x = metarRow(m); if (x) rows.push(x); }
        if (!rows.length) continue;
        const { error } = await admin.from("wx_obs").upsert(rows, { onConflict: "icao,at", ignoreDuplicates: true });
        if (error) { failed++; out.metar_error = error.message; } else saved += rows.length;
      } catch (e) { failed++; out.metar_error = String(e); }
    }
    out.metar = saved; out.metar_failed = failed;
  } catch (e) { out.metar_error = String(e); }
  // 羽田・成田の TAF（移行198 の前に動いても、表がなければ taf_error が出るだけ）
  await hndNrt(out, false);
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
