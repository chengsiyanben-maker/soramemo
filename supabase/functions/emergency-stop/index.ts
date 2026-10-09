// 非常停止：メンテナンスを「オン」にする（チェックインを止め、利用者に文を見せる）。
// 「オフ」にする機能は置かない。戻すのは運営画面から、運営者が行う。
//   POST /functions/v1/emergency-stop
//   ヘッダー x-stop-token: <EMERGENCY_STOP_TOKEN>　本文（任意）: {"message": "利用者に見せる文"}
// JWT の確認は切り、合言葉（EMERGENCY_STOP_TOKEN）で守る。合言葉が未設定なら、すべて拒否する。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { tokenOk, cleanMessage } from "../_shared/stop.ts";

const JSON_HEADERS = { "Content-Type": "application/json" };
const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const TOKEN = Deno.env.get("EMERGENCY_STOP_TOKEN") ?? "";

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers: JSON_HEADERS });
  if (!tokenOk(req.headers.get("x-stop-token"), TOKEN)) return new Response(JSON.stringify({ error: "forbidden" }), { status: 403, headers: JSON_HEADERS });
  let message: unknown = undefined;
  try { message = (await req.json())?.message; } catch { /* 本文がなくてもよい */ }
  const { error } = await admin.rpc("emergency_stop", { p_message: cleanMessage(message) });
  if (error) return new Response(JSON.stringify({ error: "failed" }), { status: 500, headers: JSON_HEADERS });
  return new Response(JSON.stringify({ ok: true, stopped: true }), { headers: JSON_HEADERS });
});
