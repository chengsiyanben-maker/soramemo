// 天気の記録（1時間ごと。cron 'wx-archive'）：日本の空港の METAR の原文（直近3時間ぶんを取り、同じものは重ねない）と、気象庁の台風情報
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { metarRow, tcKey, type TcRow, type WxRow } from "../_shared/wx_archive.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const J = { "Content-Type": "application/json" };
const UA = { "User-Agent": "soramemo (wx-archive)" };
const JMA = "https://www.jma.go.jp/bosai/typhoon/data";

Deno.serve(async (req) => {
  const out: Record<string, unknown> = {};
  // 取る時間の幅（ふだんは3時間。始めたときや抜けたときは ?hours=48 などで、さかのぼって取れる）
  const hours = Math.min(72, Math.max(1, Number(new URL(req.url).searchParams.get("hours")) || 3));
  // METAR
  try {
    const { data: aps } = await admin.from("airports").select("icao").not("icao", "is", null);
    const icaos = [...new Set(((aps ?? []) as { icao: string }[]).map((a) => a.icao).filter((c) => /^R[JO][A-Z]{2}$/.test(c)))];
    const rows: WxRow[] = [];
    for (let i = 0; i < icaos.length; i += 40) {
      const r = await fetch(`https://aviationweather.gov/api/data/metar?ids=${icaos.slice(i, i + 40).join(",")}&format=json&hours=${hours}`, { headers: UA, signal: AbortSignal.timeout(20000) });
      if (!r.ok) { out.metar_error = r.status; continue; }
      for (const m of (await r.json()) as unknown[]) { const x = metarRow(m); if (x) rows.push(x); }
    }
    const { error } = rows.length ? await admin.from("wx_obs").upsert(rows, { onConflict: "icao,at", ignoreDuplicates: true }) : { error: null };
    out.metar = rows.length; if (error) out.metar_error = error.message;
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
