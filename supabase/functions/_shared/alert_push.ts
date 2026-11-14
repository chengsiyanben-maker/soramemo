// 遅れ・欠航・ダイバートのお知らせを、スマホへ通知する（flight-watch と odpt-status が使う。VAPID の鍵があるときだけ）。1つの便につき1件にまとめる
import webpush from "npm:web-push@3.6.7";
import type { SupabaseClient } from "npm:@supabase/supabase-js@2.117.2";
import { eligible, type MergeAlert, mergeAlerts, type MergeSched, payloadOf } from "./alert_merge.ts";

// お知らせが入った・書き直された便（schedule_id）について、同じ便のお知らせを1件の通知にまとめて送る（alert_merge.ts）。
// 送ってよいか（同じ中身を二度送らない）は alert_push_claim が1件ずつ決めて記録するので、flight-watch と odpt-status が同時に動いても二重にならない
export async function notifyFlights(admin: SupabaseClient, scheduleIds: number[]) {
  const pub = Deno.env.get("VAPID_PUBLIC_KEY"), priv = Deno.env.get("VAPID_PRIVATE_KEY");
  const ids = [...new Set(scheduleIds)];
  if (!pub || !priv || !ids.length) return 0;
  // 同じ便（同じ出発・到着・定刻）の行も集める（共同運航・時刻表の重なり）
  const { data: base } = await admin.from("flight_schedule").select("id, flight, svc_date, dep, arr, std, sta").in("id", ids);
  if (!base?.length) return 0;
  const { data: sib } = await admin.from("flight_schedule").select("id, flight, svc_date, dep, arr, std, sta")
    .in("dep", [...new Set(base.map((r) => r.dep))]).in("std", [...new Set(base.map((r) => r.std))]).limit(2000);
  const keyOf = (r: { dep: string; arr: string; std: string }) => `${r.dep}|${r.arr}|${Date.parse(r.std)}`;
  const want = new Set(base.map(keyOf));
  const scheds = [...new Map([...base, ...(sib ?? []).filter((r) => want.has(keyOf(r)))].map((r) => [r.id, r])).values()] as MergeSched[];
  const { data: rows } = await admin.from("flight_alerts").select("schedule_id, kind, message, iata, late, official").in("schedule_id", scheds.map((r) => r.id));
  // 空港の名前（門限・0時前後の文に使う）
  const iatas = [...new Set(scheds.flatMap((r) => [r.dep, r.arr]))];
  const { data: aps } = await admin.from("airports").select("iata, name").in("iata", iatas);
  const nm = new Map(((aps ?? []) as { iata: string; name: string }[]).map((a) => [a.iata, String(a.name).replace(/国際空港$|空港$/, "").replace(/^.*（(.+)）$/, "$1")]));
  const groups = mergeAlerts(scheds, (rows ?? []) as MergeAlert[], (i) => nm.get(i) ?? i);
  if (!groups.length) return 0;
  // 宛先：関係する空港を選んでいる人と、「この便に乗る」でその便（便名@運航日）を選んでいる人
  const cols = "id, endpoint, p256dh, auth, airports, flights";
  const [byAp, byFl] = await Promise.all([
    admin.from("push_subs").select(cols).overlaps("airports", [...new Set(groups.flatMap((g) => g.iata))]),
    admin.from("push_subs").select(cols).overlaps("flights", [...new Set(groups.flatMap((g) => g.fkeys))])]);
  const subs = [...new Map([...(byAp.data ?? []), ...(byFl.data ?? [])].map((s) => [s.id, s])).values()];
  // 同じ購読・同じ便は1件だけ（1回の記録で同じ行を二度書かない）
  const cand = [...new Map(subs.flatMap((s) => groups.filter((g) => eligible(s, g)).map((g) => [`${s.id}|${g.gkey}`, { s, g }] as const))).values()];
  if (!cand.length) return 0;
  const { data: ok, error } = await admin.rpc("alert_push_claim", { p: cand.map(({ s, g }) =>
    ({ sub_id: s.id, gkey: g.gkey, svc_date: g.svc_date, rank: g.rank, late: g.late, official: g.official, body: g.body })) });
  if (error) { console.error("alert_push_claim", error.message); return 0; }
  const go = new Map<string, boolean>(((ok ?? []) as { sub_id: number; gkey: string; again: boolean }[]).map((r) => [`${r.sub_id}|${r.gkey}`, r.again]));
  webpush.setVapidDetails(Deno.env.get("VAPID_SUBJECT") || "https://soramemo.jp", pub, priv);
  let sent = 0;
  const gone = new Set<number>();
  for (const { s, g } of cand) {
    const again = go.get(`${s.id}|${g.gkey}`);
    if (again == null || gone.has(s.id)) continue;
    try {
      await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(payloadOf(g, again)), { TTL: 3600, urgency: "high" });
      sent++; await admin.from("push_subs").update({ last_ok: new Date().toISOString() }).eq("id", s.id);
    } catch (e) {
      const code = (e as { statusCode?: number }).statusCode;
      if (code === 404 || code === 410) { gone.add(s.id); await admin.from("push_subs").delete().eq("id", s.id); }   // 購読が切れている
    }
  }
  return sent;
}

// 特別塗装機の通知（空港ごとに申し込んだ人：push_subs.sp_airports）。iata のどれかを選んでいる人に送る
export async function sendSpPush(admin: SupabaseClient, iata: string[], payload: { title: string; body: string; tag: string; url: string }) {
  const pub = Deno.env.get("VAPID_PUBLIC_KEY"), priv = Deno.env.get("VAPID_PRIVATE_KEY");
  if (!pub || !priv || !iata.length) return 0;
  const { data: subs } = await admin.from("push_subs").select("id, endpoint, p256dh, auth").overlaps("sp_airports", iata);
  if (!subs?.length) return 0;
  webpush.setVapidDetails(Deno.env.get("VAPID_SUBJECT") || "https://soramemo.jp", pub, priv);
  let sent = 0;
  for (const s of subs) {
    try { await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(payload), { TTL: 3600 }); sent++; }
    catch (e) { const code = (e as { statusCode?: number }).statusCode; if (code === 404 || code === 410) await admin.from("push_subs").delete().eq("id", s.id); }
  }
  return sent;
}
