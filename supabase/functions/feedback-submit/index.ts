// 不具合・意見の報告を受け取る（ログインしていない人の入口。ログイン案B）
//   POST /functions/v1/feedback-submit
//        { kind: "bug"|"request"|"airport_data", body: "本文（2000字まで）", session: "起動ごとの使い捨ての値",
//          app_version?, screen?, device?, last_error?, airport? }
//        → { ok: true } / 400 { error: "bad_kind"|"empty"|"too_long"|"bad_session"|"bad_json" } / 429 { error: "too_many" } / 503 { error: "closed" }
//   ログインしている人は、この入口を使わず表 feedback に直接入れる（RLS で自分の分だけ）
//   ここから入れた行は user_id が必ず空（サービスの鍵には利用者がいない。表の trigger が決める）
//   位置・メール・IP は受け取らない・保存しない・ログに出さない。送りすぎの制限は表の trigger（同じ起動の値で10分に3件・全体で10分に30件）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { parseFeedback } from "../_shared/feedback.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const res = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...CORS, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "POST") return res({ error: "POST only" }, 405);
  const raw = await req.text();
  if (raw.length > 16000) return res({ error: "too_long" }, 400);
  let b: unknown;
  try { b = JSON.parse(raw); } catch { return res({ error: "bad_json" }, 400); }
  const p = parseFeedback(b);
  if (!p.ok) return res({ error: p.error }, 400);
  const { error } = await admin.from("feedback").insert(p.row);   // 返す行は読まない（return=minimal）
  if (error) {
    if (error.code === "54000") return res({ error: "too_many" }, 429);
    if (error.code === "55000") return res({ error: "closed" }, 503);   // 運営が受け付けを止めている（ops.flags の feedback_enabled）
    console.error("feedback-submit", error.code ?? "error");      // 本文は出さない
    return res({ error: "failed" }, 500);
  }
  console.log(JSON.stringify({ ev: "feedback", kind: p.row.kind }));
  return res({ ok: true });
});
