// 毎晩の照合（運航確認）と、実際に飛んだ航路の取り込み。GitHub の定期実行から動かす。
//   deno run --node-modules-dir=none --allow-net --allow-env --allow-read tools/verify_flights.ts
// 必要な環境変数：SUPABASE_URL、SUPABASE_SERVICE_ROLE_KEY、OPENSKY_CLIENT_ID、OPENSKY_CLIENT_SECRET
// （OpenSky は Supabase のサーバーから届かないため、Supabase の関数ではなくここで動かす）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { runVerification } from "../supabase/functions/_shared/verify_job.ts";
import { makeDeps } from "../supabase/functions/_shared/verify_io.ts";

const need = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "OPENSKY_CLIENT_ID", "OPENSKY_CLIENT_SECRET"];
const missing = need.filter((k) => !Deno.env.get(k));
if (missing.length) { console.error("設定が足りません：" + missing.join("・")); Deno.exit(1); }

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const sum = await runVerification(makeDeps(admin, { clientId: Deno.env.get("OPENSKY_CLIENT_ID")!, clientSecret: Deno.env.get("OPENSKY_CLIENT_SECRET")! }));
console.log("照合の結果", JSON.stringify(sum));
// 1件も問い合わせられなかった（全部が通信エラー）ときは、失敗として知らせる
if (sum.checked > 0 && sum.errors === sum.checked) { console.error("OpenSky に問い合わせられませんでした"); Deno.exit(1); }
