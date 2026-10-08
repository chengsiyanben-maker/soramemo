// POST /functions/v1/verify-flights（毎晩の定期実行から呼ぶ。JWTの確認は切り、x-cron-secret で守る）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { JOB, type Row, runVerification } from "../_shared/verify_job.ts";
import type { OpenSkyFlight } from "../_shared/verify.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const CRON_SECRET = Deno.env.get("CRON_SECRET") ?? "";
const TOKEN_URL = Deno.env.get("OPENSKY_TOKEN_URL") ?? "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token";
const API = "https://opensky-network.org/api";

// 合言葉は、比べる時間から中身を推測されないよう、長さにかかわらず全部の文字を比べる
function sameSecret(a: string, b: string): boolean {
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}

let token: { value: string; until: number } | null = null;
async function bearer(): Promise<string> {
  if (token && Date.now() < token.until) return token.value;
  const res = await fetch(TOKEN_URL, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ grant_type: "client_credentials", client_id: Deno.env.get("OPENSKY_CLIENT_ID") ?? "", client_secret: Deno.env.get("OPENSKY_CLIENT_SECRET") ?? "" }) });
  if (!res.ok) throw new Error(`token ${res.status}`);
  const j = await res.json();
  token = { value: j.access_token, until: Date.now() + Math.max(60, (j.expires_in ?? 1800) - 60) * 1000 };
  return token.value;
}

async function fetchArrivals(icao: string, begin: number, end: number): Promise<OpenSkyFlight[]> {
  const res = await fetch(`${API}/flights/arrival?airport=${icao}&begin=${begin}&end=${end}`, { headers: { Authorization: `Bearer ${await bearer()}` } });
  if (res.status === 404) return [];          // その時間帯の記録なし
  if (!res.ok) throw new Error(`arrival ${res.status}`);
  return await res.json();
}

async function loadFlights(): Promise<Row[]> {
  const today = new Date(); today.setUTCHours(0, 0, 0, 0);       // 到着記録は夜間にまとめて更新されるため、前日以前の分だけ
  const { data, error } = await admin.from("flights")
    .select("id, dep_at, arr_at, flight_no, verify_attempts, from:airports!flights_from_airport_fkey(icao), to:airports!flights_to_airport_fkey(icao)")
    .in("status", ["provisional", "with_flight_no"]).lt("verify_attempts", JOB.maxAttempts)
    .lt("arr_at", today.toISOString()).gte("arr_at", new Date(today.getTime() - 7 * 864e5).toISOString())
    .order("arr_at").limit(JOB.maxPerRun);
  if (error) throw error;
  // deno-lint-ignore no-explicit-any
  return (data ?? []).map((r: any) => ({ id: r.id, fromIcao: r.from?.icao || null, toIcao: r.to?.icao || null,
    dep: Date.parse(r.dep_at), arr: Date.parse(r.arr_at), flightNo: r.flight_no, attempts: r.verify_attempts }));
}

async function save(id: number, status: "verified" | "no_data" | null, note: string, attempts: number) {
  const patch: Record<string, unknown> = { verify_attempts: attempts, verify_note: note };
  if (status) patch.status = status;
  if (status === "verified") patch.verified_at = new Date().toISOString();
  const { error } = await admin.from("flights").update(patch).eq("id", id);
  if (error) throw error;
}

Deno.serve(async (req) => {
  if (!CRON_SECRET || !sameSecret(req.headers.get("x-cron-secret") ?? "", CRON_SECRET)) return new Response("forbidden", { status: 403 });
  try {
    const sum = await runVerification({ loadFlights, fetchArrivals, save });
    console.log("verify-flights", sum);
    return new Response(JSON.stringify(sum), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    console.error(e);
    return new Response("error", { status: 500 });
  }
});
