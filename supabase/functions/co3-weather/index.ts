// エアライン経営 co-v3：空港の気象通報（METAR）から、その時間の天気（雪・強風・霧・雷）を co3_wx に残す
//   GET /functions/v1/co3-weather   （pg_cron が毎時2分に呼ぶ。何度呼ばれても、同じ時間の行は上書きするだけ）
//   出どころは metar 関数と同じ米国の航空気象センター（公開の気象情報）。40空港ずつまとめて取り、負担をかけない
//   便の欠航・遅れのうち、天気に当たるものを「天気の備え」で減らすのに使う（co3_wx_cxl_mult・co3_wx_delay_mult）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { fetchMetars } from "../_shared/metar.ts";
import { wxFlags } from "../_shared/co3_wx.js";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const JSON_HEADERS = { "Content-Type": "application/json" };

Deno.serve(async () => {
  try {
    const { data: aps, error } = await admin.from("airports").select("iata, icao").not("icao", "is", null).not("iata", "is", null);
    if (error) throw error;
    const byIcao = new Map((aps ?? []).filter((a) => /^[A-Z]{4}$/.test(a.icao) && /^[A-Z]{3}$/.test(a.iata)).map((a) => [a.icao, a.iata]));
    const ids = [...byIcao.keys()];
    const at = new Date(); at.setUTCMinutes(0, 0, 0);
    const rows: Record<string, unknown>[] = [];
    for (let i = 0; i < ids.length; i += 40) {
      try {
        const got = await fetchMetars(ids.slice(i, i + 40));
        for (const [icao, m] of got) {
          // 2時間より古い通報は使わない（出していない空港の古い通報）
          if (Date.now() - Date.parse(m.time) > 2 * 3600_000) continue;
          rows.push({ iata: byIcao.get(icao), at: at.toISOString(), ...wxFlags(m), raw: String(m.raw || "").slice(0, 300) });
        }
      } catch (_) { /* 1まとまり取れなくても、ほかは続ける */ }
    }
    if (rows.length) {
      const { error: e2 } = await admin.from("co3_wx").upsert(rows, { onConflict: "iata,at" });
      if (e2) throw e2;
    }
    return new Response(JSON.stringify({ saved: rows.length }), { headers: JSON_HEADERS });
  } catch (e) {
    return new Response(JSON.stringify({ error: String((e as Error).message || e) }), { status: 500, headers: JSON_HEADERS });
  }
});
