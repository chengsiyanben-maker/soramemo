// 管制の交信を受け取る（受信の協力者の端末から）。音は受け取らず、端末で聞き取った英語の文字だけ。
//   POST /functions/v1/atc-ingest  ヘッダー x-feeder-token: 協力用の合言葉（atc_new_feeder で作る）
//        { iata:"HND", ch:"gnd", freq:"121.70", at: ミリ秒, text:"All Nippon 106, taxi to ...", conf:0.82 }
//        → { ok:true, shown:true|false, ja }   shown は、近くを飛んでいる機体と合って画面に出したか
//   POST { iata, ch, freq, ping:true } → 受信中の印だけ（交信がない間も、いま受信していることを数える）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { checkIn, parseAtc, sameMsg, verified } from "../_shared/atc_ingest.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-feeder-token", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const res = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...CORS, "Content-Type": "application/json" } });
const sha = async (s: string) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)))].map((b) => b.toString(16).padStart(2, "0")).join("");
const RATE = new Map<string, number[]>();

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "POST") return res({ error: "method" }, 405);
  const tok = req.headers.get("x-feeder-token") ?? "";
  if (!/^[0-9a-f]{64}$/.test(tok)) return res({ error: "token" }, 401);
  const { data: f } = await admin.from("atc_feeders").select("id, sent").eq("token_hash", await sha(tok)).maybeSingle();
  if (!f) return res({ error: "token" }, 401);
  // 1台あたり1分に40件まで
  const now = Date.now(), r = (RATE.get(f.id) ?? []).filter((t) => now - t < 60_000); r.push(now); RATE.set(f.id, r);
  if (r.length > 40) return res({ error: "rate" }, 429);
  let b: Record<string, unknown>; try { b = await req.json(); } catch { return res({ error: "json" }, 400); }
  if (b.ping === true) {
    const iata = typeof b.iata === "string" && /^(HND|NRT)$/.test(b.iata) ? b.iata : null, ch = typeof b.ch === "string" ? b.ch : null;
    await admin.from("atc_feeders").update({ last_seen: new Date(now).toISOString(), iata, ch: ch && /^(atis|del|ramp|gnd|twr|app|dep)$/.test(ch) ? ch : null,
      freq: typeof b.freq === "string" && /^1[1-3]\d\.\d{1,3}$/.test(b.freq) ? b.freq : null }).eq("id", f.id);
    return res({ ok: true });
  }
  const m = checkIn(b, now); if (typeof m === "string") return res({ error: m }, 400);
  const p = parseAtc(m.text);
  await admin.from("atc_feeders").update({ last_seen: new Date(now).toISOString(), iata: m.iata, ch: m.ch, freq: m.freq, sent: (f.sent ?? 0) + 1 }).eq("id", f.id);
  if (!p.items.length) return res({ ok: true, shown: false, ja: "" });
  const { data: pos } = p.callsign ? await admin.from("live_positions").select("lat, lon, seen_at").eq("callsign", p.callsign).maybeSingle() : { data: null };
  const ok = verified(p, m.iata, m.ch, pos, now);
  // 同じ交信をほかの協力者がもう送っていれば、受けた人数を足すだけ（はっきり聞こえたほうの文字を残す）
  const { data: near } = await admin.from("atc_msgs").select("id, callsign, ja, at, conf, heard").eq("iata", m.iata).eq("ch", m.ch)
    .gte("at", new Date(m.at - 10_000).toISOString()).lte("at", new Date(m.at + 10_000).toISOString()).limit(20);
  const dup = (near ?? []).find((x) => sameMsg({ ...x, at: Date.parse(x.at) }, { callsign: p.callsign, ja: p.ja, at: m.at }));
  if (dup) {
    await admin.from("atc_msgs").update({ heard: Math.min(99, (dup.heard ?? 1) + 1), ...(m.conf != null && m.conf > (dup.conf ?? 0) ? { conf: m.conf, text_en: m.text } : {}) }).eq("id", dup.id);
    return res({ ok: true, shown: ok, ja: p.ja, dup: true });
  }
  const { error } = await admin.from("atc_msgs").insert({ iata: m.iata, ch: m.ch, freq: m.freq, at: new Date(m.at).toISOString(), feeder: f.id, text_en: m.text, conf: m.conf,
    callsign: p.callsign, flight: p.flight, items: p.items, ja: p.ja, tags: p.tags, verified: ok });
  if (error) return res({ error: "save" }, 500);
  return res({ ok: true, shown: ok, ja: p.ja });
});
