// POST /functions/v1/checkin
// 端末は「位置・誤差・取得時刻」だけを送る。判定・記録・フライト成立はすべてここで行う。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { type Airport, decide, type Terminal } from "../_shared/judge.ts";

const URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const admin = createClient(URL, SERVICE_KEY, { auth: { persistSession: false } });

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });

// 非常停止（運営画面で切り替え）。30秒ごとに読み直す
let allowedCache: { v: boolean; until: number } | null = null;
async function checkinAllowed(): Promise<boolean> {
  if (allowedCache && Date.now() < allowedCache.until) return allowedCache.v;
  const { data, error } = await admin.rpc("checkin_allowed");
  const v = error ? true : data !== false;            // 読めないときは止めない（判定そのものは別に守られている）
  allowedCache = { v, until: Date.now() + 30_000 };
  return v;
}
// 記録は本処理を待たせない（失敗してもチェックインには影響させない）
// deno-lint-ignore no-explicit-any
const background = (p: PromiseLike<unknown>) => { const q = Promise.resolve(p).catch(() => {}); const rt = (globalThis as any).EdgeRuntime; if (rt?.waitUntil) rt.waitUntil(q); };

// 空港とターミナルはほぼ変わらないので、関数のインスタンスごとに一度だけ読む
let master: { airports: Airport[]; terminals: Terminal[] } | null = null;
async function loadMaster() {
  if (master) return master;
  const [a, t] = await Promise.all([
    admin.from("airports").select("id,name,iata,icao,lat,lon,radius_m,rare,game_target,extra_kind").or("game_target.eq.true,extra_kind.not.is.null"),
    admin.from("terminals").select("id,airport_id,name,tag,lat,lon,stamp_m"),
  ]);
  if (a.error || t.error) throw a.error ?? t.error;
  // 番外編（自衛隊・米軍の飛行場、滑空場、飛行場）は extra_kind で見分け、extra の印を付ける（民間空港より優先度が低く、フライトにしない）
  // deno-lint-ignore no-explicit-any
  const airports = (a.data as any[]).map((r) => ({ ...r, iata: r.iata ?? r.icao ?? "", extra: !r.game_target && !!r.extra_kind })) as Airport[];
  master = { airports, terminals: t.data as Terminal[] };
  return master;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ ok: false, reason: "method", message: "POSTのみ" }, 405);

  // 利用者の確認（ログイン中のトークンが必要）
  const jwt = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  const { data: u, error: ue } = await admin.auth.getUser(jwt);
  if (ue || !u?.user) return json({ ok: false, reason: "auth", message: "ログインしてください。" }, 401);
  const userId = u.user.id;

  // 非常停止と回数制限（1人1分に20回まで）
  if (!(await checkinAllowed())) {
    return json({ ok: false, reason: "paused", message: "ただいまチェックインを一時停止しています。しばらくしてからもう一度お試しください。" }, 503);
  }
  const { data: rateOk } = await admin.rpc("rl_check", { p_key: "checkin:" + userId, p_limit: 20, p_window_sec: 60 });
  if (rateOk === false) return json({ ok: false, reason: "rate", message: "短い時間に何度も押されています。少し待ってからもう一度押してください。" }, 429);

  let body: { lat?: number; lon?: number; acc?: number; ts?: number; queued?: boolean };
  try { body = await req.json(); } catch { return json({ ok: false, reason: "bad_request", message: "送信内容を読めませんでした。" }, 400); }

  try {
    const { airports, terminals } = await loadMaster();
    const { data: lastRows, error: le } = await admin.from("checkins")
      .select("id,airport_id,terminal_id,created_at").eq("user_id", userId)
      .order("created_at", { ascending: false }).limit(1);
    if (le) throw le;
    const last = lastRows?.[0]
      ? { airport_id: lastRows[0].airport_id, terminal_id: lastRows[0].terminal_id, at: Date.parse(lastRows[0].created_at) }
      : null;

    const now = Date.now();
    const d = decide({ lat: Number(body.lat), lon: Number(body.lon), acc: Number(body.acc), ts: Number(body.ts) }, now, last, airports, terminals, body.queued === true);
    if (!d.ok) {
      // 判定ルールの見直し用に、断った理由を記録する（利用者IDと座標は残さず、最寄り空港・距離・誤差の目安だけ）
      if (["out_of_range", "low_accuracy", "stale_position", "too_soon", "already"].includes(d.reason)) {
        const acc = Number(body.acc);
        background(admin.rpc("log_rejection", {
          p_reason: d.reason, p_airport: d.place?.airport.id ?? null,
          p_dist_km: d.place ? Math.round(d.place.distKm * 10) / 10 : null,
          p_accuracy: Number.isFinite(acc) ? Math.min(99990, Math.round(acc / 10) * 10) : null, p_queued: body.queued === true,
        }));
      }
      return json({ ok: false, reason: d.reason, message: d.message,
        nearest: d.place ? { airport_id: d.place.airport.id, dist_km: d.place.distKm } : null });
    }

    // 初訪問かどうか（印の演出用）
    const [fa, ft] = await Promise.all([
      admin.from("checkins").select("id", { count: "exact", head: true }).eq("user_id", userId).eq("airport_id", d.place.airport.id),
      d.place.terminal
        ? admin.from("checkins").select("id", { count: "exact", head: true }).eq("user_id", userId).eq("terminal_id", d.place.terminal.id)
        : Promise.resolve({ count: 1 }),
    ]);

    const { data: ci, error: ie } = await admin.from("checkins").insert({
      user_id: userId, airport_id: d.place.airport.id, terminal_id: d.place.terminal?.id ?? null,
      lat: body.lat, lon: body.lon, accuracy_m: body.acc, position_at: new Date(Number(body.ts)).toISOString(),
      created_at: new Date(d.at).toISOString(), flags: d.flags,
    }).select("id,created_at").single();
    if (ie) throw ie;

    let flight = null;
    if (d.flight) {
      const { data: f, error: fe } = await admin.from("flights").insert({
        user_id: userId, from_airport: d.flight.from, to_airport: d.flight.to,
        dep_checkin: lastRows![0].id, arr_checkin: ci.id,
        dep_at: new Date(d.flight.dep).toISOString(), arr_at: ci.created_at, distance_km: d.flight.km,
      }).select("id,from_airport,to_airport,dep_at,arr_at,distance_km").single();
      if (fe) throw fe;
      flight = f;
    }

    return json({
      ok: true, at: ci.created_at,
      airport_id: d.place.airport.id, terminal_id: d.place.terminal?.id ?? null,
      first_airport: (fa.count ?? 0) === 0, first_terminal: (ft.count ?? 0) === 0,
      flight, flags: d.flags,
    });
  } catch (e) {
    console.error(e);
    return json({ ok: false, reason: "server", message: "サーバーで問題が起きました。少し待ってからもう一度押してください。" }, 500);
  }
});
