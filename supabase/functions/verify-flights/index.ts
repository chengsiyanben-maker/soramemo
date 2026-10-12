// POST /functions/v1/verify-flights（手で呼ぶとき用。JWTの確認は切り、x-cron-secret で守る）
// 注意：OpenSky は Supabase のサーバーから届かないため、毎晩の照合は GitHub の定期実行（.github/workflows/verify-flights.yml）で動かしている。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { runVerification } from "../_shared/verify_job.ts";
import { makeDeps } from "../_shared/verify_io.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CRON_SECRET = Deno.env.get("CRON_SECRET") ?? "";

// 合言葉は、比べる時間から中身を推測されないよう、長さにかかわらず全部の文字を比べる
function sameSecret(a: string, b: string): boolean {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

const deps = makeDeps(admin, { clientId: Deno.env.get("OPENSKY_CLIENT_ID") ?? "", clientSecret: Deno.env.get("OPENSKY_CLIENT_SECRET") ?? "", tokenUrl: Deno.env.get("OPENSKY_TOKEN_URL") ?? undefined });

Deno.serve(async (req) => {
  if (!CRON_SECRET || !sameSecret(req.headers.get("x-cron-secret") ?? "", CRON_SECRET)) return new Response("forbidden", { status: 403 });
  try {
    const sum = await runVerification(deps);
    console.log("verify-flights", sum);
    return new Response(JSON.stringify(sum), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    console.error(e);
    return new Response("error", { status: 500 });
  }
});
