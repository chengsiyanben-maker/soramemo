// エアライン経営 co-v3：気象庁の台風の予報から、明日台風が近づきそうな空港を co3_typhoon_fcst に入れる
//   GET /functions/v1/co3-typhoon   （pg_cron が毎時17分に呼ぶ。何度呼ばれても、同じ日の行を入れ直すだけ）
//   出どころ：気象庁ホームページの防災情報XML（随時の情報の一覧 extra.xml → 台風解析・予報情報（５日予報））
//     気象庁のコンテンツの利用規約で、出典を書けば使える。加工したことは画面に書く（ゲームの判断に使う）
//   予報の進路（中心の位置）が、明日（日本時間）その空港から300km以内を通る空港だけ。予報円の大きさは見ない
//   取る電文は1回に12件まで。一覧が読めないときは何も変えない（それまでの予報を残す）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { approachDays, jstDay, latestPerEvent, parseTyphoon, typhoonFeedUrls } from "../_shared/co3_typhoon.js";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const J = { "Content-Type": "application/json" };
const UA = { "User-Agent": "soramemo (co3-typhoon)" };
const FEED = "https://www.data.jma.go.jp/developer/xml/feed/extra.xml";

Deno.serve(async () => {
  try {
    const r = await fetch(FEED, { headers: UA, signal: AbortSignal.timeout(20000) });
    if (!r.ok) throw new Error(`feed ${r.status}`);
    const urls = typhoonFeedUrls(await r.text()).slice(0, 12);
    const storms = [];
    for (const u of urls) {
      try {
        const x = await fetch(u, { headers: UA, signal: AbortSignal.timeout(15000) });
        if (x.ok) storms.push(parseTyphoon(await x.text()));
      } catch (_) { /* 1つ読めなくても、ほかは続ける */ }
    }
    const { data: aps, error } = await admin.from("airports").select("iata, lat, lon").not("iata", "is", null);
    if (error) throw error;
    const tomorrow = jstDay(Date.now() + 86400_000);
    const rows = new Map<string, { iata: string; event: string; note: string }>();
    for (const s of latestPerEvent(storms)) {
      const hit = approachDays(s, aps ?? [], 300);
      for (const [iata, days] of Object.entries(hit)) {
        if (!days.includes(tomorrow) || rows.has(iata)) continue;
        const no = s.number && /^\d{4}$/.test(s.number) ? `台風第${Number(s.number.slice(2))}号` : "台風";
        rows.set(iata, { iata, event: s.event, note: no });
      }
    }
    // 電文が1つも読めなかったとき（一覧には台風の電文があるのに）は、予報を消さない
    if (urls.length && !storms.some(Boolean)) throw new Error("no typhoon message could be read");
    const { data, error: e2 } = await admin.rpc("co3_typhoon_auto", { p_day: tomorrow, p_rows: [...rows.values()] });
    if (e2) throw e2;
    return new Response(JSON.stringify({ messages: urls.length, ...(data as object) }), { headers: J });
  } catch (e) {
    return new Response(JSON.stringify({ error: String((e as Error).message || e) }), { status: 500, headers: J });
  }
});
