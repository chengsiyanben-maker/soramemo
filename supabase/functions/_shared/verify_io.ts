// 照合（運航確認）の読み書きと、OpenSky への問い合わせ。
// Supabase の関数（verify-flights）と、GitHub の定期実行（tools/verify_flights.ts）の両方から使う。
// OpenSky は Supabase のサーバーからは届かないため、毎晩の照合は GitHub の定期実行で動かす。
import type { SupabaseClient } from "npm:@supabase/supabase-js@2.117.2";
import { type Deps, JOB, type Row } from "./verify_job.ts";
import type { OpenSkyFlight } from "./verify.ts";

const API = "https://opensky-network.org/api";
const TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token";

export function makeDeps(admin: SupabaseClient, opensky: { clientId: string; clientSecret: string; tokenUrl?: string }): Deps {
  let token: { value: string; until: number } | null = null;
  async function bearer(): Promise<string> {
    if (token && Date.now() < token.until) return token.value;
    const res = await fetch(opensky.tokenUrl || TOKEN_URL, { method: "POST", signal: AbortSignal.timeout(15000), headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ grant_type: "client_credentials", client_id: opensky.clientId, client_secret: opensky.clientSecret }) });
    if (!res.ok) throw new Error(`token ${res.status}`);
    const j = await res.json();
    token = { value: j.access_token, until: Date.now() + Math.max(60, (j.expires_in ?? 1800) - 60) * 1000 };
    return token.value;
  }

  async function fetchArrivals(icao: string, begin: number, end: number): Promise<OpenSkyFlight[]> {
    const res = await fetch(`${API}/flights/arrival?airport=${icao}&begin=${begin}&end=${end}`, { headers: { Authorization: `Bearer ${await bearer()}` }, signal: AbortSignal.timeout(30000) });
    if (res.status === 404) return [];          // その時間帯の記録なし
    if (!res.ok) throw new Error(`arrival ${res.status}`);
    return await res.json();
  }

  // 実際に飛んだ航路（飛行中のどこかの時刻を渡すと、その飛行の全体が返る）。見つからなければ null
  async function fetchTrack(icao24: string, time: number): Promise<unknown> {
    const res = await fetch(`${API}/tracks/all?icao24=${encodeURIComponent(icao24)}&time=${time}`, { headers: { Authorization: `Bearer ${await bearer()}` }, signal: AbortSignal.timeout(30000) });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`track ${res.status}`);
    return (await res.json())?.path ?? null;
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

  async function save(id: number, status: "verified" | "no_data" | null, note: string, attempts: number, track?: [number, number][] | null) {
    const patch: Record<string, unknown> = { verify_attempts: attempts, verify_note: note };
    if (track) patch.track = track;
    if (status) patch.status = status;
    if (status === "verified") patch.verified_at = new Date().toISOString();
    const { error } = await admin.from("flights").update(patch).eq("id", id);
    if (error) throw error;
  }

  return { loadFlights, fetchArrivals, save, fetchTrack };
}
