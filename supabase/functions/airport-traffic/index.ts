// 空港の周りを今飛んでいる機体と、通ってきた線（羽田・成田・伊丹・関西・新千歳・福岡・那覇・中部・仙台・広島・松山・熊本・長崎・鹿児島）。
//   GET /functions/v1/airport-traffic?iata=HND
//   GET /functions/v1/airport-traffic?iata=RECORD   （記録用。14空港の線を足すだけ）
// 位置は adsb.lol（有志の受信機による ADS-B のオープンデータ）。実際より数秒〜十数秒遅れる。ログインは不要。
// OpenSky は Supabase のサーバーから届かないため使わない。
// 配信元に負担をかけないよう、20秒ためて全員で使い回す。
// 通ってきた線は、位置をデータベース（traffic_trails）に足していって作る（関数の呼び出しをまたいで残すため）。
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import { planesFromAdsb, type Trails, updateTrails } from "../_shared/traffic.ts";
import { fetchMetars } from "../_shared/metar.ts";
import { OPS_AIRPORTS, observeOps } from "../_shared/ops_core.js";
import { liveryMap } from "../_shared/liveries.ts";
import { normCallsign } from "../_shared/flight_watch.ts";
import webpush from "npm:web-push@3.6.7";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type", "Access-Control-Allow-Methods": "GET, OPTIONS" };
const JSON_HEADERS = { ...CORS, "Content-Type": "application/json" };
const TTL = 20_000;

// 空港の位置と、問い合わせる半径（海里。60海里＝約110km。房総半島の南や相模湾からの進入まで入る）
const AIRPORTS: Record<string, { at: [number, number]; nm: number }> = {
  HND: { at: [35.5533, 139.7811], nm: 60 },
  // ほかの空港：滑走路の向きの判定と、近づいてくる機体の表示（線は、地図を開いている人がいるあいだに伸びる）
  NRT: { at: [35.7772, 140.3823], nm: 40 },
  ITM: { at: [34.7856, 135.4380], nm: 40 },
  KIX: { at: [34.4336, 135.2336], nm: 40 },
  CTS: { at: [42.7752, 141.6923], nm: 40 },
  FUK: { at: [33.5861, 130.4493], nm: 40 },
  OKA: { at: [26.1933, 127.6394], nm: 40 },
  NGO: { at: [34.8584, 136.8054], nm: 40 },
  SDJ: { at: [38.1405, 140.9157], nm: 40 },
  HIJ: { at: [34.4360, 132.9194], nm: 40 },
  MYJ: { at: [33.8273, 132.6996], nm: 40 },
  KMJ: { at: [32.8373, 130.8551], nm: 40 },
  NGS: { at: [32.9170, 129.9134], nm: 40 },
  KOJ: { at: [31.8034, 130.7194], nm: 40 },
};

// 着陸・離陸の見分けで「ほかの空港のほうが近い機体」を除くための、近くの空港（神戸・札幌丘珠・横田・名古屋（小牧）・佐賀・北九州・岩国も含む）
const NEARBY: [number, number][] = [...Object.values(AIRPORTS).map((a) => a.at),
  [34.6328, 135.2239], [43.1161, 141.3800], [35.7485, 139.3485], [35.2550, 136.9244], [33.1497, 130.3022], [33.8459, 131.0349], [34.1440, 132.2356]];

// データベースの線を読み、今回の位置を足して書き戻す。いなくなった機体と古い位置は消える
async function syncTrails(iata: string, planes: { id: string; lat: number; lon: number }[]): Promise<Trails> {
  const tr: Trails = new Map();
  try {
    const { data } = await admin.from("traffic_trails").select("hex, pts").eq("iata", iata);
    for (const r of data ?? []) if (Array.isArray(r.pts)) tr.set(String(r.hex), r.pts.map((q: number[]) => ({ t: q[0], p: [q[1], q[2]] as [number, number] })));
  } catch { /* 読めなくても位置は出す */ }
  const before = new Set(tr.keys());
  // deno-lint-ignore no-explicit-any
  updateTrails(tr, planes as any, Date.now());
  const rows = [...tr.entries()].map(([hex, pts]) => ({ iata, hex, pts: pts.slice(-150).map((x) => [x.t, x.p[0], x.p[1]]), updated_at: new Date().toISOString() }));
  const gone = [...before].filter((h) => !tr.has(h));
  try {
    if (rows.length) await admin.from("traffic_trails").upsert(rows);
    if (gone.length) await admin.from("traffic_trails").delete().eq("iata", iata).in("hex", gone);
  } catch { /* 書けなくても位置は出す */ }
  return tr;
}

const cache = new Map<string, { at: number; body: string }>();

// 空港は、広い円（adsb.lol の上限の250海里）でまとめて問い合わせる（adsb.lol への問い合わせを減らす。1回の記録で3つまでしか答えてもらえない）
//   東：羽田・成田・中部・伊丹・関西・仙台（中心からいちばん遠い仙台が約205海里、仙台の40海里まで入る）
//   西：福岡・熊本・長崎・鹿児島・広島・松山（いちばん遠い広島が約120海里）。
//   北：新千歳を中心に250海里（北海道と東北の北）。南：那覇を中心に250海里（奄美・宮古・石垣まで）。
//   日本中の機体の位置は live_positions にも残し、便の見張り（flight-watch）が使う
const REGIONS: Record<string, { at: [number, number]; nm: number }> = {
  EAST: { at: [35.6, 138.0], nm: 250 }, WEST: { at: [33.2, 131.0], nm: 250 },
  NORTH: { at: [42.7752, 141.6923], nm: 250 }, SOUTH: { at: [26.1933, 127.6394], nm: 250 },
};
const REGION_OF: Record<string, string> = { HND: "EAST", NRT: "EAST", NGO: "EAST", ITM: "EAST", KIX: "EAST", SDJ: "EAST",
  FUK: "WEST", KMJ: "WEST", NGS: "WEST", KOJ: "WEST", HIJ: "WEST", MYJ: "WEST", CTS: "NORTH", OKA: "SOUTH" };
const regionCache = new Map<string, { at: number; j: { now?: number; ac?: unknown[] } }>();
async function fetchArea(iata: string) {
  const key = REGION_OF[iata] ?? iata, area = REGIONS[key] ?? AIRPORTS[iata];
  const hit = regionCache.get(key);
  if (hit && Date.now() - hit.at < TTL) return hit.j;
  const r = await fetch(`https://api.adsb.lol/v2/lat/${area.at[0]}/lon/${area.at[1]}/dist/${area.nm}`,
    { headers: { "User-Agent": "soramemo (airport-traffic)" }, signal: AbortSignal.timeout(area.nm > 100 ? 20000 : 10000) });   // 広い円は返事が大きいので長めに待つ
  if (!r.ok) throw new Error("adsb.lol " + r.status);
  const j = await r.json();
  regionCache.set(key, { at: Date.now(), j });
  return j;
}

async function snapshot(iata: string): Promise<string> {
  const hit = cache.get(iata);
  if (hit && Date.now() - hit.at < TTL) return hit.body;
  const a = AIRPORTS[iata];
  const j = await fetchArea(iata);
  // まとめて取った円から、この空港の半径の中だけを使う
  const planes = planesFromAdsb(j?.ac, a.at, 14000, NEARBY.filter((o) => o !== a.at)).filter((p) => p.dist_km <= a.nm * 1.852);
  const tr = await syncTrails(iata, planes);
  const body = JSON.stringify({
    iata, at: new Date(typeof j?.now === "number" ? j.now : Date.now()).toISOString(), source: "adsb.lol",
    planes: planes.map((p) => ({ ...p, trail: (tr.get(p.id) ?? []).slice(-150).map((x) => x.p) })),
  });
  cache.set(iata, { at: Date.now(), body });
  return body;
}

// 今回取った円の機体（便名のあるもの）の位置を live_positions に残す
async function recordPositions(bodies: Map<string, string>) {
  const keys = new Set([...bodies.keys()].map((k) => REGION_OF[k] ?? k)), rows = new Map<string, Record<string, unknown>>(), track = new Map<string, Record<string, unknown>>();
  for (const k of keys) {
    const c = regionCache.get(k); if (!c || Date.now() - c.at > TTL) continue;
    const t = typeof c.j.now === "number" ? c.j.now : Date.now();
    for (const a of (c.j.ac ?? []) as Record<string, unknown>[]) {
      if (typeof a.flight !== "string" || !a.flight.trim() || typeof a.lat !== "number" || typeof a.lon !== "number") continue;
      const cs = normCallsign(a.flight).slice(0, 10), at = t - (typeof a.seen_pos === "number" ? a.seen_pos * 1000 : 0);
      rows.set(cs, { callsign: cs, hex: typeof a.hex === "string" ? a.hex : null, lat: a.lat, lon: a.lon,
        alt_ft: typeof a.alt_baro === "number" ? Math.round(a.alt_baro) : null, ground: a.alt_baro === "ground",
        fpm: typeof a.baro_rate === "number" ? Math.round(a.baro_rate) : typeof a.geom_rate === "number" ? Math.round(a.geom_rate) : null,
        kt: typeof a.gs === "number" ? Math.round(a.gs) : null, type: typeof a.t === "string" ? a.t.slice(0, 8) : null,
        reg: typeof a.r === "string" && /^[A-Z0-9-]{2,10}$/.test(a.r) ? a.r : null,
        seen_at: new Date(at).toISOString() });
      // 航跡の点（毎日の記録用）：上昇・降下中（15,000ft 未満）の機体を、1分に1回だけ残す（36時間で消す）
      if (typeof a.alt_baro === "number" && a.alt_baro < 15000 && Math.floor(t / 30_000) % 2 === 0)
        track.set(cs, { callsign: cs, t: new Date(at).toISOString(), lat: Math.round(a.lat * 1e4) / 1e4, lon: Math.round(a.lon * 1e4) / 1e4, alt: Math.round(a.alt_baro / 100) });
    }
  }
  const all = [...rows.values()];
  for (let i = 0; i < all.length; i += 500) { const { error } = await admin.from("live_positions").upsert(all.slice(i, i + 500)); if (error) throw error; }
  const tp = [...track.values()];
  for (let i = 0; i < tp.length; i += 500) { const { error } = await admin.from("track_points").insert(tp.slice(i, i + 500)); if (error) { console.error("track_points", error.message); break; } }
  return all.length;
}

// 特別塗装機を livery_sightings に残す（今回取った円の機体から。運用タブの空港の着陸・離陸中なら、その空港も）
async function recordLiveries(bodies: Map<string, string>) {
  const L = liveryMap(), seen = new Map<string, Record<string, unknown>>();
  // 空港ごとの機体（着陸・離陸の見分けが付いたもの）
  const near = new Map<string, { iata: string; phase: string }>();
  for (const [iata, body] of bodies) for (const p of (JSON.parse(body).planes ?? []) as { reg?: string; phase?: string }[]) {
    if (p.reg && (p.phase === "arr" || p.phase === "dep") && L.has(p.reg)) near.set(p.reg, { iata, phase: p.phase });
  }
  const keys = new Set([...bodies.keys()].map((k) => REGION_OF[k] ?? k));
  for (const k of keys) {
    const c = regionCache.get(k); if (!c || Date.now() - c.at > TTL) continue;
    for (const a of (c.j.ac ?? []) as Record<string, unknown>[]) {
      const reg = typeof a.r === "string" ? a.r : null, l = reg ? L.get(reg) : undefined;
      if (!l || typeof a.lat !== "number" || typeof a.lon !== "number") continue;
      const n = near.get(l.reg);
      seen.set(l.reg, { reg: l.reg, name: l.name, airline: l.airline, src: l.src, kind: l.kind ?? "special", lat: a.lat, lon: a.lon,
        alt_ft: typeof a.alt_baro === "number" ? Math.round(a.alt_baro) : a.alt_baro === "ground" ? 0 : null,
        callsign: typeof a.flight === "string" ? a.flight.trim().slice(0, 10) || null : null,
        iata: n?.iata ?? null, phase: n?.phase ?? null, seen_at: new Date().toISOString() });
    }
  }
  if (seen.size) { const { error } = await admin.from("livery_sightings").upsert([...seen.values()]); if (error) throw error; }
  // 着陸に向かってきた特別塗装機は、その空港を選んでいる人に知らせる（同じ機体・空港は6時間に1回）。アライアンス塗装は毎日飛んでいるので知らせない
  for (const v of seen.values()) if (v.iata && v.phase === "arr" && v.kind !== "alliance") { try { await notifyLivery(v); } catch (e) { console.error("livery push", e); } }
  return seen.size;
}

// deno-lint-ignore no-explicit-any
async function notifyLivery(v: any) {
  const pub = Deno.env.get("VAPID_PUBLIC_KEY"), priv = Deno.env.get("VAPID_PRIVATE_KEY");
  if (!pub || !priv) return;
  const since = new Date(Date.now() - 6 * 3600_000).toISOString();
  const { data: done } = await admin.from("livery_notified").select("reg").eq("reg", v.reg).eq("iata", v.iata).gt("notified_at", since);
  if (done?.length) return;
  await admin.from("livery_notified").upsert({ reg: v.reg, iata: v.iata, notified_at: new Date().toISOString() });
  const { data: subs } = await admin.from("push_subs").select("id, endpoint, p256dh, auth").contains("sp_airports", [v.iata]);
  if (!subs?.length) return;
  webpush.setVapidDetails(Deno.env.get("VAPID_SUBJECT") || "https://soramemo.jp", pub, priv);
  // deno-lint-ignore no-explicit-any
  const name = (OPS_AIRPORTS as any)[v.iata]?.name ?? v.iata;
  const body = JSON.stringify({ title: `そらメモ：★${v.name}`, body: `${v.name}（${v.airline}${v.callsign ? "・" + v.callsign : ""}）が${name}に着陸に向かっています（推定）。`, tag: `sp-${v.reg}`, url: `./#ops-${v.iata}` });
  for (const s of subs) {
    try { await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, body, { TTL: 900 }); }
    catch (e) { const code = (e as { statusCode?: number }).statusCode; if (code === 404 || code === 410) await admin.from("push_subs").delete().eq("id", s.id); }
  }
}

// 運用の判定を ops_log に残す（気象通報は14空港を1回でまとめて取る）
// deno-lint-ignore no-explicit-any
async function logOps(bodies: Map<string, string>) {
  const defs = Object.values(OPS_AIRPORTS) as any[];
  const wx = await fetchMetars(defs.map((d) => d.icao));
  const rows = [];
  for (const d of defs) {
    const body = bodies.get(d.iata); if (!body) continue;
    const planes = (JSON.parse(body).planes ?? []) as any[];
    const m = wx.get(d.icao) ?? null, est = d.estimate(m), obs = observeOps(planes, d) as any;
    rows.push({
      iata: d.iata, wdir: m?.wdir ?? null, wspd: m?.wspd ?? null, metar_at: m?.time ?? null,
      est_mode: est.mode, est_unsure: !!est.unsure,
      obs_mode: obs && !obs.mixed ? obs.mode : null, obs_mixed: !!(obs && obs.mixed),
      obs_arr: obs && !obs.mixed ? Object.values(obs.n ?? {}).reduce((a: number, b) => a + (b as number), 0) : 0,
      obs_dep: obs && !obs.mixed ? obs.dep ?? 0 : 0,
      planes: planes.filter((p) => p.phase === "arr" || p.phase === "dep").length,
    });
  }
  if (rows.length) { const { error } = await admin.from("ops_log").insert(rows); if (error) throw error; }
  return rows.length;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "GET") return new Response(JSON.stringify({ error: "GET only" }), { status: 405, headers: JSON_HEADERS });
  const iata = (new URL(req.url).searchParams.get("iata") || "").toUpperCase();
  // 記録用（pg_cron が30秒ごとに呼ぶ）：東・西の円の12空港は毎回、新千歳は毎分の前半、那覇は後半に線を足す
  if (iata === "RECORD") {
    const first = new Date().getUTCSeconds() < 30;
    // 問い合わせは1回に3つまで：東の円・西の円と、新千歳か那覇
    const list = [...Object.keys(REGION_OF).filter((k) => k !== "CTS" && k !== "OKA"), first ? "CTS" : "OKA"];
    const done: Record<string, string> = {}, bodies = new Map<string, string>();
    // adsb.lol は同時にたくさん問い合わせると断る（429・420）ので、3秒ずつあけて1つずつ
    for (const [i, k] of list.entries()) {
      const key = REGION_OF[k] ?? k, cached = regionCache.get(key);
      if (i && !(cached && Date.now() - cached.at < TTL)) await new Promise((r) => setTimeout(r, 3000));
      try { bodies.set(k, await snapshot(k)); done[k] = "ok"; } catch (e) { done[k] = e instanceof Error ? e.message.slice(0, 40) : "error"; }
    }
    // 日本中の機体の最新の位置を残す（便の見張り用）
    try { await recordPositions(bodies); } catch (e) { console.error("positions", e); }
    // 特別塗装機：今回取った円の中に、一覧の登録記号の機体がいれば残す
    let liveries = 0;
    try { liveries = await recordLiveries(bodies); } catch (e) { console.error("livery", e); }
    // 5分ごと（毎時0・5・10…分）に、運用の判定を記録する（画面と同じ判定の仕方。_shared/ops_core.js）
    let logged = 0;
    // 前半は那覇以外の13空港、後半は那覇（那覇は後半にしか機体を取らないため）
    if (new Date().getUTCMinutes() % 5 === 0) {
      const only = first ? null : ["OKA"];
      try { logged = await logOps(only ? new Map([...bodies].filter(([k]) => only.includes(k))) : bodies); } catch (e) { console.error("ops_log", e); }
    }
    return new Response(JSON.stringify({ recorded: done, logged, liveries }), { headers: JSON_HEADERS });
  }
  if (!AIRPORTS[iata]) return new Response(JSON.stringify({ error: "unsupported airport" }), { status: 404, headers: JSON_HEADERS });
  try {
    return new Response(await snapshot(iata), { headers: { ...JSON_HEADERS, "Cache-Control": "max-age=10" } });
  } catch (e) {
    console.error(e);
    const hit = cache.get(iata);
    if (hit) return new Response(hit.body, { headers: { ...JSON_HEADERS, "X-Stale": "1" } });
    const why = e instanceof Error ? (e.name === "TimeoutError" ? "timeout" : e.message.slice(0, 60)) : "error";
    return new Response(JSON.stringify({ error: "unavailable", why }), { status: 503, headers: JSON_HEADERS });
  }
});
