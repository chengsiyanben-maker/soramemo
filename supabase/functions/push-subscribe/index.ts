// スマホへの通知（遅れ・ダイバートのお知らせ）の申し込み・取り消し。ログインは不要（ブラウザの購読と、選んだ空港だけを持つ）。
//   GET  /functions/v1/push-subscribe                         → { key: VAPID の公開鍵 }（鍵がまだなければ key は null）
//   POST /functions/v1/push-subscribe  { endpoint, keys:{p256dh, auth}, airports:["HND", ...] }  → 申し込み（同じ endpoint は上書き）
//   POST /functions/v1/push-subscribe  { endpoint, remove:true }                              → 取り消し
import { createClient } from "npm:@supabase/supabase-js@2.117.2";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
const J = { ...CORS, "Content-Type": "application/json" };
const res = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: J });

// 通知を送ってよい宛先（各ブラウザの配信サービス）だけ受け付ける
const PUSH_HOSTS = /^https:\/\/([a-z0-9-]+\.)*(fcm\.googleapis\.com|push\.services\.mozilla\.com|notify\.windows\.com|push\.apple\.com|web\.push\.apple\.com)\//;

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method === "GET") return res({ key: Deno.env.get("VAPID_PUBLIC_KEY") || null });
  if (req.method !== "POST") return res({ error: "GET/POST only" }, 405);
  let b: { endpoint?: unknown; keys?: { p256dh?: unknown; auth?: unknown }; airports?: unknown; remove?: unknown };
  try { b = await req.json(); } catch { return res({ error: "bad json" }, 400); }
  const endpoint = typeof b.endpoint === "string" ? b.endpoint : "";
  if (!PUSH_HOSTS.test(endpoint) || endpoint.length > 1000) return res({ error: "bad endpoint" }, 400);
  if (b.remove === true) {
    await admin.from("push_subs").delete().eq("endpoint", endpoint);
    return res({ ok: true, removed: true });
  }
  const p256dh = typeof b.keys?.p256dh === "string" ? b.keys.p256dh : "", auth = typeof b.keys?.auth === "string" ? b.keys.auth : "";
  if (!/^[A-Za-z0-9_-]{20,200}={0,2}$/.test(p256dh) || !/^[A-Za-z0-9_-]{8,100}={0,2}$/.test(auth)) return res({ error: "bad keys" }, 400);
  const airports = Array.isArray(b.airports) ? [...new Set(b.airports.filter((x) => typeof x === "string" && /^[A-Z]{3}$/.test(x)))].slice(0, 12) as string[] : [];
  if (!airports.length) return res({ error: "no airports" }, 400);
  const { error } = await admin.from("push_subs").upsert({ endpoint, p256dh, auth, airports }, { onConflict: "endpoint" });
  if (error) { console.error(error); return res({ error: "save failed" }, 500); }
  return res({ ok: true, airports });
});
