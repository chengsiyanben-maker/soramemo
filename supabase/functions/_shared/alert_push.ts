// 遅れ・欠航・ダイバートのお知らせを、スマホへ通知する（flight-watch と odpt-status が使う。VAPID の鍵があるときだけ）
import webpush from "npm:web-push@3.6.7";
import type { SupabaseClient } from "npm:@supabase/supabase-js@2.117.2";

export async function sendAlertPush(admin: SupabaseClient, alerts: { iata: string[]; message: string; flight: string; fkey: string }[]) {
  const pub = Deno.env.get("VAPID_PUBLIC_KEY"), priv = Deno.env.get("VAPID_PRIVATE_KEY");
  if (!pub || !priv || !alerts.length) return 0;
  webpush.setVapidDetails(Deno.env.get("VAPID_SUBJECT") || "https://soramemo.jp", pub, priv);
  // 宛先：関係する空港を選んでいる人と、「この便に乗る」でその便（便名@運航日）を選んでいる人
  const all = [...new Set(alerts.flatMap((a) => a.iata))], keys = [...new Set(alerts.map((a) => a.fkey))];
  const cols = "id, endpoint, p256dh, auth, airports, flights";
  const [byAp, byFl] = await Promise.all([admin.from("push_subs").select(cols).overlaps("airports", all), admin.from("push_subs").select(cols).overlaps("flights", keys)]);
  const subs = [...new Map([...(byAp.data ?? []), ...(byFl.data ?? [])].map((s) => [s.id, s])).values()];
  let sent = 0;
  for (const s of subs) {
    for (const a of alerts.filter((x) => x.iata.some((i) => s.airports.includes(i)) || (s.flights ?? []).includes(x.fkey))) {
      try {
        await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } },
          JSON.stringify({ title: `そらメモ：${a.flight}`, body: a.message, tag: `fw-${a.flight}` }), { TTL: 3600 });
        sent++; await admin.from("push_subs").update({ last_ok: new Date().toISOString() }).eq("id", s.id);
      } catch (e) {
        const code = (e as { statusCode?: number }).statusCode;
        if (code === 404 || code === 410) { await admin.from("push_subs").delete().eq("id", s.id); break; }   // 購読が切れている
      }
    }
  }
  return sent;
}
