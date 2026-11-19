// 照合（運航確認）の読み書きと、到着の一覧の取り先（OpenSky か、私たちの全機の記録 reg_legs）。
// Supabase の関数（verify-flights）と、GitHub の定期実行（tools/verify_flights.ts）の両方から使う。
// OpenSky は Supabase のサーバーからは届かないため、毎晩の照合は GitHub の定期実行で動かす。
import type { SupabaseClient } from "npm:@supabase/supabase-js@2.117.2";
import { type Deps, JOB, type Row } from "./verify_job.ts";
import type { OpenSkyFlight } from "./verify.ts";

const API = "https://opensky-network.org/api";
const TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token";

// 照合で「その空港・時間帯に着いた機体」をどこから取るか。VERIFY_SOURCE=adsb なら私たちの全機の記録（reg_legs。adsb.lol・ODbL）、
// それ以外は今までどおり OpenSky（研究・非商用向けなので、ストアの前に adsb に切り替える案。11/16 data/redo-1116）
export type VerifySource = "opensky" | "adsb";
export const verifySource = (v: string | undefined | null): VerifySource => (v ?? "").trim().toLowerCase() === "adsb" ? "adsb" : "opensky";

// reg_legs から OpenSky と同じ形の到着の一覧を返す（関数 verify_arrivals。窓は2日まで）
export function adsbArrivals(admin: Pick<SupabaseClient, "rpc">) {
  return async (icao: string, begin: number, end: number): Promise<OpenSkyFlight[]> => {
    const { data, error } = await admin.rpc("verify_arrivals", { p_arr_icao: icao, p_begin: new Date(begin * 1000).toISOString(), p_end: new Date(end * 1000).toISOString() });
    if (error) throw new Error("verify_arrivals " + error.message);
    return Array.isArray(data) ? data as OpenSkyFlight[] : [];
  };
}

export function makeDeps(admin: SupabaseClient, opensky: { clientId: string; clientSecret: string; tokenUrl?: string }, source: VerifySource = "opensky"): Deps {
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

  async function loadFlights(): Promise<Row[]> {
    const today = new Date(); today.setUTCHours(0, 0, 0, 0);       // 到着記録は夜間にまとめて更新されるため、前日以前の分だけ
    const { data, error } = await admin.from("flights")
      .select("id, dep_at, arr_at, flight_no, verify_attempts, from:airports!flights_from_airport_fkey(icao, iata), to:airports!flights_to_airport_fkey(icao, iata)")
      .in("status", ["provisional", "with_flight_no"]).lt("verify_attempts", JOB.maxAttempts)
      .lt("arr_at", today.toISOString()).gte("arr_at", new Date(today.getTime() - 7 * 864e5).toISOString())
      .order("arr_at").limit(JOB.maxPerRun);
    if (error) throw error;
    // deno-lint-ignore no-explicit-any
    return (data ?? []).map((r: any) => ({ id: r.id, fromIcao: r.from?.icao || null, toIcao: r.to?.icao || null,
      dep: Date.parse(r.dep_at), arr: Date.parse(r.arr_at), flightNo: r.flight_no, attempts: r.verify_attempts,
      fromIata: r.from?.iata || null, toIata: r.to?.iata || null }));
  }

  async function save(id: number, status: "verified" | "no_data" | null, note: string, attempts: number, track?: [number, number][] | null) {
    const patch: Record<string, unknown> = { verify_attempts: attempts, verify_note: note };
    if (track) patch.track = track;
    if (status) patch.status = status;
    if (status === "verified") patch.verified_at = new Date().toISOString();
    const { error } = await admin.from("flights").update(patch).eq("id", id);
    if (error) throw error;
  }

  // 航空会社の運航情報：同じ区間・同じ便名（先頭の0は無視）で、記録の時間帯に実際に出発か到着した便があれば確認とする
  async function officialCheck(r: Row): Promise<string | null> {
    if (!r.flightNo || !r.fromIata || !r.toIata || !/^[A-Z]{3}$/.test(r.fromIata) || !/^[A-Z]{3}$/.test(r.toIata)) return null;
    const { data, error } = await admin.from("flight_schedule").select("flight, std, atd, ata")
      .eq("dep", r.fromIata).eq("arr", r.toIata).gte("std", new Date(r.dep - 3 * 3600_000).toISOString()).lte("std", new Date(r.arr).toISOString());
    if (error) throw error;
    const n = (f: string) => f.replace(/^([A-Z0-9]{2})0+(\d)/, "$1$2").toUpperCase();
    const hit = (data ?? []).find((x) => n(x.flight) === n(r.flightNo!) && (x.atd || x.ata));
    if (!hit) return null;
    const hm = (t: string | null) => t ? new Date(Date.parse(t) + 9 * 3600_000).toISOString().slice(11, 16) : "—";
    return `航空会社の運航情報で確認（${n(hit.flight)} ${hm(hit.atd)}発・${hm(hit.ata)}着）`;
  }

  // 実際の出発・到着の時刻（航空会社の運航情報 → 毎日の記録 → 時刻表）。照合した8日分を見直す
  async function fillActual(): Promise<unknown> {
    const { data, error } = await admin.rpc("flights_fill_actual", { p_days: 8, p_limit: 2000 });
    if (error) throw new Error("flights_fill_actual " + error.message);
    return data;
  }

  // 航跡は OpenSky から取らない（研究・非商用だけの条件のため。11/20）。毎晩の daily-archive が全機の記録（adsb.lol・ODbL）から付ける
  if (source === "adsb") return { loadFlights, fetchArrivals: adsbArrivals(admin), save, officialCheck, fillActual };
  return { loadFlights, fetchArrivals, save, officialCheck, fillActual };
}
