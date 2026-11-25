// POST /functions/v1/checkin
// 端末は「位置・誤差・取得時刻」だけを送る。判定・記録・フライト成立はすべてここで行う。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { type Airport, decide, type Terminal } from "../_shared/judge.ts";
import { weather, wxCode } from "../_shared/airport_now.ts";
import { OPS_AIRPORTS } from "../_shared/ops_core.js";
import { type CheckinWx, pickWx, WX_NONE } from "../_shared/checkin_wx.ts";
import { readShared } from "../_shared/edge_cache.ts";
import { type CheckinRow, type FlightRow, isUniqueViolation, parseClientId, replayBody } from "../_shared/checkin_idem.ts";

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

// チェックインしたときの空港の天気（気象通報）。同じ空港は10分使い回し、2.5秒で取れなければあきらめる。
// 配信元に取りに行くのは、データベースの中で決まらなかったときだけで、印を返したあとに回す（wxLater）
const wxCache = new Map<string, { at: number; v: { weather: string | null; wind_kt: number | null } }>();
async function wxAt(icao: string | null | undefined): Promise<{ weather: string | null; wind_kt: number | null }> {
  const none = { weather: null, wind_kt: null };
  if (!icao || !/^[A-Z]{4}$/.test(icao)) return none;
  const hit = wxCache.get(icao);
  if (hit && Date.now() - hit.at < 10 * 60_000) return hit.v;
  try {
    const r = await fetch(`https://aviationweather.gov/api/data/metar?ids=${icao}&format=json`, { headers: { "User-Agent": "soramemo (checkin)" }, signal: AbortSignal.timeout(2500) });
    if (!r.ok) return none;
    const m = (await r.json())[0];
    if (!m) return none;
    const w = weather(m);
    const v = { weather: wxCode(w.sky), wind_kt: w.wspd == null ? null : Math.min(200, Math.max(0, Math.round(w.wspd))) };
    wxCache.set(icao, { at: Date.now(), v });
    return v;
  } catch { return none; }
}

// 待たせない天気：記憶 → 置き場（edge_cache）→ 天気の記録（wx_obs）。データベースを1往復ずつ並べて読む（data/stamp-fast）
// 決まらなければ null（印を返したあとで wxLater が配信元から書き足す）
async function wxFast(icao: string | null | undefined): Promise<CheckinWx | null> {
  if (!icao || !/^[A-Z]{4}$/.test(icao)) return WX_NONE;
  const hit = wxCache.get(icao);
  if (hit && Date.now() - hit.at < 10 * 60_000) return hit.v;
  try {
    const [sh, ob] = await Promise.all([
      readShared(admin, [`now:wx:${icao}`]),
      admin.from("wx_obs").select("at, raw, wspd").eq("icao", icao)
        .gt("at", new Date(Date.now() - 2 * 3600_000).toISOString()).order("at", { ascending: false }).limit(1),
    ]);
    const v = pickWx(sh.get(`now:wx:${icao}`), ob.data?.[0]);
    if (v) wxCache.set(icao, { at: Date.now(), v });
    return v;
  } catch { return null; }
}
// 印を返したあとで、配信元から天気を取ってその印に書き足す（まだ空のときだけ）
function wxLater(icao: string, checkinId: number | string) {
  background((async () => {
    const v = await wxAt(icao);
    if (v.weather == null && v.wind_kt == null) return;
    await admin.from("checkins").update({ weather: v.weather, wind_kt: v.wind_kt }).eq("id", checkinId).is("weather", null).is("wind_kt", null);
  })());
}

// チェックインしたときの空港の運用（運用タブの14空港だけ）：運用の判定の記録（ops_log）の直近10分から。
// 実際の機体での判定を優先し、なければ風からの推定（決められたときだけ）。名前は画面と同じ（_shared/ops_core.js）
async function opsAt(iata: string | null | undefined): Promise<string | null> {
  // deno-lint-ignore no-explicit-any
  const def = iata ? (OPS_AIRPORTS as any)[iata] : null;
  if (!def) return null;
  try {
    const { data } = await admin.from("ops_log").select("est_mode, est_unsure, obs_mode").eq("iata", iata)
      .gt("at", new Date(Date.now() - 10 * 60_000).toISOString()).order("at", { ascending: false }).limit(1);
    const r = data?.[0]; if (!r) return null;
    const mode = r.obs_mode ?? (r.est_unsure ? null : r.est_mode);
    return mode && def.modes[mode] ? String(def.modes[mode].label).slice(0, 40) : null;
  } catch { return null; }
}

// 同じ ID の印がもう記録してあれば、1回目と同じ形の返事（dup: true）を作る。なければ null（data/idem・移行200）
async function replay(userId: string, cid: string) {
  const { data: rows, error } = await admin.from("checkins").select("id,airport_id,terminal_id,created_at,flags,weather,wind_kt,ops")
    .eq("user_id", userId).eq("client_id", cid).limit(1);
  if (error) throw error;
  const row = rows?.[0] as CheckinRow | undefined;
  if (!row) return null;
  const [fl, ea, et] = await Promise.all([
    admin.from("flights").select("id,from_airport,to_airport,dep_at,arr_at,distance_km").eq("arr_checkin", row.id).order("id").limit(1),
    admin.from("checkins").select("id", { count: "exact", head: true }).eq("user_id", userId).eq("airport_id", row.airport_id).lt("id", row.id),
    row.terminal_id
      ? admin.from("checkins").select("id", { count: "exact", head: true }).eq("user_id", userId).eq("terminal_id", row.terminal_id).lt("id", row.id)
      : Promise.resolve({ count: 0, error: null }),
  ]);
  if (fl.error) throw fl.error;
  return replayBody(row, (fl.data?.[0] ?? null) as FlightRow, ea.count ?? 1, et.count ?? 1);
}

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

  // 非常停止・回数制限（1人1分に20回まで）・空港の表・前の印・送られた中身は、互いに待たないので同時に読む（data/stamp-fast）。
  // 判断の順番（止まっている → 回数 → 中身）は前と同じ。読むだけなので、断る場合に先に読んでいても記録は変わらない
  const t0 = Date.now();
  const [allowed, rate, bodyR, masterR, lastR] = await Promise.all([
    checkinAllowed(),
    admin.rpc("rl_check", { p_key: "checkin:" + userId, p_limit: 20, p_window_sec: 60 }),
    req.json().then((v) => ({ ok: true as const, v }), () => ({ ok: false as const, v: null })),
    loadMaster().then((v) => ({ v, e: null }), (e) => ({ v: null, e })),
    admin.from("checkins").select("id,airport_id,terminal_id,created_at,client_id").eq("user_id", userId)
      .order("created_at", { ascending: false }).limit(1),
  ]);
  // 送り直し（data/idem）：前の印と同じ ID なら、判定も記録もせず1回目と同じ形の成功を返す（往復は増やさない。
  // 前の印より古い ID は、判定で断るときと記録で一意の索引にぶつかったときだけ探す）。止まっているときも、記録済みの印は成功で返す
  const cid = bodyR.ok ? parseClientId((bodyR.v as { cid?: unknown } | null)?.cid) : null;
  if (cid && !lastR.error && lastR.data?.[0]?.client_id === cid) {
    try {
      const r = await replay(userId, cid);
      if (r) { console.log(JSON.stringify({ ev: "checkin_dup", where: "last" })); return json(r); }
    } catch (e) { console.error(e); }
  }
  if (!allowed) {
    return json({ ok: false, reason: "paused", message: "ただいまチェックインを一時停止しています。しばらくしてからもう一度お試しください。" }, 503);
  }
  if (rate.data === false) return json({ ok: false, reason: "rate", message: "短い時間に何度も押されています。少し待ってからもう一度押してください。" }, 429);

  if (!bodyR.ok) return json({ ok: false, reason: "bad_request", message: "送信内容を読めませんでした。" }, 400);
  const body: { lat?: number; lon?: number; acc?: number; ts?: number; queued?: boolean } = bodyR.v ?? {};

  try {
    if (!masterR.v) throw masterR.e;
    const { airports, terminals } = masterR.v;
    const { data: lastRows, error: le } = lastR;
    if (le) throw le;
    const last = lastRows?.[0]
      ? { airport_id: lastRows[0].airport_id, terminal_id: lastRows[0].terminal_id, at: Date.parse(lastRows[0].created_at) }
      : null;

    const now = Date.now();
    const d = decide({ lat: Number(body.lat), lon: Number(body.lon), acc: Number(body.acc), ts: Number(body.ts) }, now, last, airports, terminals, body.queued === true);
    if (!d.ok) {
      // 断る前に、同じ ID の印がもう記録してあれば成功で返す（保留の送り直しで、そのあとに別の印がある場合など）
      if (cid) {
        const r = await replay(userId, cid);
        if (r) { console.log(JSON.stringify({ ev: "checkin_dup", where: "decide" })); return json(r); }
      }
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
    const [fa, ft, wx, ops] = await Promise.all([
      admin.from("checkins").select("id", { count: "exact", head: true }).eq("user_id", userId).eq("airport_id", d.place.airport.id),
      d.place.terminal
        ? admin.from("checkins").select("id", { count: "exact", head: true }).eq("user_id", userId).eq("terminal_id", d.place.terminal.id)
        : Promise.resolve({ count: 1 }),
      // deno-lint-ignore no-explicit-any
      wxFast((d.place.airport as any).icao),
      // deno-lint-ignore no-explicit-any
      opsAt((d.place.airport as any).iata),
    ]);

    const t1 = Date.now();
    const w = wx ?? WX_NONE;
    const { data: ci, error: ie } = await admin.from("checkins").insert({
      user_id: userId, airport_id: d.place.airport.id, terminal_id: d.place.terminal?.id ?? null,
      lat: body.lat, lon: body.lon, accuracy_m: body.acc, position_at: new Date(Number(body.ts)).toISOString(),
      created_at: new Date(d.at).toISOString(), flags: d.flags,
      weather: w.weather, wind_kt: w.wind_kt, ops, client_id: cid,
    }).select("id,created_at").single();
    if (ie && cid && isUniqueViolation(ie)) {
      // 同じ ID が同時に2回届いた：先に入った方の印を返す
      const r = await replay(userId, cid);
      if (r) { console.log(JSON.stringify({ ev: "checkin_dup", where: "insert" })); return json(r); }
    }
    if (ie) throw ie;
    // データベースの中で天気が決まらなかったときだけ、返したあとで配信元から書き足す
    // deno-lint-ignore no-explicit-any
    if (wx == null) wxLater((d.place.airport as any).icao, ci.id);

    // 行事のボーナス（期間中、空港ごとに1回。経営の資金）とフライトの記録は、どちらも印のあとで互いに待たないので同時に。
    // ボーナスが失敗してもチェックインは成功のまま（前と同じ）。フライトの記録が失敗したら前と同じく 500
    const [bonusR, flightR] = await Promise.all([
      admin.rpc("grant_event_bonus", { p_uid: userId, p_airport: d.place.airport.id, p_at: ci.created_at }),
      d.flight
        ? admin.from("flights").insert({
          user_id: userId, from_airport: d.flight.from, to_airport: d.flight.to,
          dep_checkin: lastRows![0].id, arr_checkin: ci.id,
          dep_at: new Date(d.flight.dep).toISOString(), arr_at: ci.created_at, distance_km: d.flight.km,
        }).select("id,from_airport,to_airport,dep_at,arr_at,distance_km").single()
        : Promise.resolve({ data: null, error: null }),
    ]);
    let bonus: unknown[] = [];
    if (bonusR.error) console.error("event bonus", bonusR.error.message); else if (Array.isArray(bonusR.data)) bonus = bonusR.data;
    if (flightR.error) throw flightR.error;
    const flight = flightR.data;
    // かかった時間（利用者IDと位置は書かない）。読む・判定まで／記録まで
    console.log(JSON.stringify({ ev: "checkin_ms", read: t1 - t0, total: Date.now() - t0, wx: wx == null ? "later" : "db", flight: !!d.flight }));

    return json({
      ok: true, at: ci.created_at,
      airport_id: d.place.airport.id, terminal_id: d.place.terminal?.id ?? null,
      first_airport: (fa.count ?? 0) === 0, first_terminal: (ft.count ?? 0) === 0,
      flight, flags: d.flags, weather: w.weather, wind_kt: w.wind_kt, ops, bonus,
    });
  } catch (e) {
    console.error(e);
    return json({ ok: false, reason: "server", message: "サーバーで問題が起きました。少し待ってからもう一度押してください。" }, 500);
  }
});
