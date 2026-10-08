// ダッシュボードのエディタに貼り付ける用の1ファイル版（checkin/index.ts と _shared/judge.ts を結合したもの）
// POST /functions/v1/checkin
// 端末は「位置・誤差・取得時刻」だけを送る。判定・記録・フライト成立はすべてここで行う。

// チェックイン判定（サーバー側）。DBやネットワークに触れない純粋な関数だけを置く。
// 数値は 2026年10月の羽田実地検証を反映している。

// extra：番外編（自衛隊・米軍の飛行場、滑空場）。民間空港より優先度が低く、これらとの間はフライトにしない
type Airport = { id: number; name: string; iata: string; lat: number; lon: number; radius_m: number; rare: boolean; extra?: boolean };
type Terminal = { id: string; airport_id: number; name: string; tag: string; lat: number; lon: number; stamp_m?: number };
type LastCheckin = { airport_id: number; terminal_id: string | null; at: number } | null;
type Position = { lat: number; lon: number; acc: number; ts: number };

const RULE = {
  maxAccuracyM: 1000,      // これより誤差が大きい位置は受け付けない
  maxPositionAgeMs: 5 * 60e3, // 端末で取得してから5分以上たった位置は古いとみなす
  maxQueuedAgeMs: 24 * 36e5,  // 電波がなく端末に保留したチェックインは、24時間以内なら受け付ける
  maxFutureSkewMs: 2 * 60e3,  // 端末時計の進みすぎの許容
  minIntervalMs: 20e3,     // 同じ利用者の連続チェックインの最短間隔
  sameSpotMin: 30,         // 同じ空港・同じターミナルへの再チェックインを無視する分数
  flightMaxGapH: 24,       // 出発から到着までの最大時間
  flightMaxKmh: 1000,      // これより速い移動はフライトとして認めない
  termRadiusM: 800,        // ターミナルから800m以内も空港の範囲とする
  termStampM: 400,         // ターミナルの印はそのターミナルから400m以内のときだけ
};

function km(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const R = 6371, r = Math.PI / 180;
  const dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const h = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

type Place = { airport: Airport; terminal: Terminal | null; within: boolean; distKm: number };

// 民間空港の範囲内なら民間空港。そうでなければ、範囲内の番外編の飛行場。どちらでもなければ、いちばん近い民間空港（範囲外の案内用）
function locate(p: { lat: number; lon: number }, airports: Airport[], terminals: Terminal[]): Place {
  const civil = airports.filter((a) => !a.extra), extra = airports.filter((a) => a.extra);
  const c = locateIn(p, civil.length ? civil : airports, terminals);
  if (c.within || !extra.length) return c;
  let eb = extra[0], ed = Infinity;
  for (const a of extra) { const k = km(p, a); if (k < ed) { ed = k; eb = a; } }
  if (ed * 1000 <= eb.radius_m) return { airport: eb, terminal: null, within: true, distKm: ed };
  return c;
}
function locateIn(p: { lat: number; lon: number }, airports: Airport[], terminals: Terminal[]): Place {
  let best = airports[0], d = Infinity;
  for (const a of airports) { const k = km(p, a); if (k < d) { d = k; best = a; } }
  const byId = new Map(airports.map((a) => [a.id, a]));
  for (const t of terminals) { const k = km(p, t); if (k < d) { d = k; best = byId.get(t.airport_id)!; } }
  let term: Terminal | null = null, tk = Infinity;
  for (const t of terminals) { if (t.airport_id !== best.id) continue; const k = km(p, t); if (k < tk) { tk = k; term = t; } }
  const airportKm = km(p, best);
  const within = airportKm * 1000 <= best.radius_m || (term !== null && tk * 1000 <= RULE.termRadiusM);
  return { airport: best, terminal: term && tk * 1000 <= (term.stamp_m ?? RULE.termStampM) ? term : null, within, distKm: Math.min(d, airportKm) };
}

type Decision =
  | { ok: false; reason: string; message: string; place?: Place }
  | {
    ok: true; at: number; place: Place; flags: string[];
    flight: { from: number; to: number; dep: number; arr: number; km: number } | null;
  };

// queued = 電波がなく端末に保留していたチェックイン。判定の時刻は端末が位置を取った時刻（p.ts）を使い、offline の印を付ける
function decide(p: Position, now: number, last: LastCheckin, airports: Airport[], terminals: Terminal[], queued = false): Decision {
  if (!(Number.isFinite(p.lat) && Number.isFinite(p.lon) && Math.abs(p.lat) <= 90 && Math.abs(p.lon) <= 180)) {
    return { ok: false, reason: "bad_position", message: "位置の形式が正しくありません。" };
  }
  if (!Number.isFinite(p.acc) || p.acc <= 0) return { ok: false, reason: "bad_accuracy", message: "位置の誤差が不明です。" };
  const maxAge = queued ? RULE.maxQueuedAgeMs : RULE.maxPositionAgeMs;
  if (!Number.isFinite(p.ts) || now - p.ts > maxAge || p.ts - now > RULE.maxFutureSkewMs) {
    return { ok: false, reason: "stale_position", message: queued ? "24時間以上前のチェックインは送れません。" : "古い位置は使えません。もう一度チェックインしてください。" };
  }
  const at = queued ? Math.min(p.ts, now) : now;
  if (queued && last && at <= last.at) {
    return { ok: false, reason: "out_of_order", message: "このチェックインより後の記録がすでにあるため、送れませんでした。" };
  }
  if (p.acc > RULE.maxAccuracyM) {
    return { ok: false, reason: "low_accuracy", message: `位置の精度が低すぎます（誤差 約${Math.round(p.acc)}m）。窓の近くか屋外でもう一度押してください。` };
  }
  if (last && at - last.at < RULE.minIntervalMs) {
    return { ok: false, reason: "too_soon", message: "少し時間をおいてからもう一度押してください。" };
  }
  const place = locate(p, airports, terminals);
  if (!place.within) {
    const rest = Math.max(0, place.distKm - place.airport.radius_m / 1000);
    return { ok: false, reason: "out_of_range", message: `${place.airport.name}の判定範囲の外です。あと約${rest.toFixed(1)}km近づいてください。`, place };
  }
  const tid = place.terminal ? place.terminal.id : null;
  if (last && last.airport_id === place.airport.id && last.terminal_id === tid && at - last.at < RULE.sameSpotMin * 60e3) {
    return { ok: false, reason: "already", message: "ここにはチェックイン済みです。", place };
  }

  const flags: string[] = [];
  if (p.acc > 300) flags.push("low_accuracy");
  if (queued) flags.push("offline");
  let flight = null;
  if (last && last.airport_id !== place.airport.id) {
    const h = (at - last.at) / 36e5;
    const a = airports.find((x) => x.id === last.airport_id);
    if (a && h <= RULE.flightMaxGapH && !a.extra && !place.airport.extra) {
      const d = km(a, place.airport);
      if (h > 0 && d / h <= RULE.flightMaxKmh) flight = { from: a.id, to: place.airport.id, dep: last.at, arr: at, km: d };
      else flags.push("impossible_speed"); // 旅客機でも不可能な速さ。フライトにせず、目視確認の対象にする
    }
  }
  return { ok: true, at, place, flags, flight };
}

import { createClient } from "npm:@supabase/supabase-js@2.117.2";

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
