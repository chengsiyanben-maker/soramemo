// チェックインのときの天気を、待たせずに決める（data/stamp-fast）
//   前は印を押すたびに aviationweather.gov へ取りに行き、最大2.5秒待っていた（入れ物ごとの記憶にない空港では毎回）。
//   今は ① 関数の中の記憶 ② 関数どうしの置き場（edge_cache の now:wx:ICAO。空港の今が5分ごとに書く）
//   ③ 天気の記録（wx_obs。1時間ごと）の順に、データベースの中だけで決める。どれもなければ空のまま記録し、
//   印を返したあとで配信元に取りに行って書き足す（checkin/index.ts）。
import { skyOf, wxCode } from "./airport_now.ts";

export type CheckinWx = { weather: string | null; wind_kt: number | null };
export const WX_NONE: CheckinWx = { weather: null, wind_kt: null };
export const SHARED_MAX_MS = 15 * 60_000;   // 置き場の通報はこの古さまで使う
export const OBS_MAX_MS = 75 * 60_000;      // 天気の記録（1時間ごと）はこの古さまで使う

const kt = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? Math.min(200, Math.max(0, Math.round(v))) : null;

// METAR の原文から雲の層（FEW030・BKN012・OVC005・VV002 など）を取り出す。skyOf に渡す形
export function cloudsFromRaw(raw: string): { cover: string }[] {
  const body = String(raw ?? "").split(/\s(?:RMK|TEMPO|BECMG|NOSIG)\b/)[0];
  const out: { cover: string }[] = [];
  for (const w of body.split(/\s+/)) {
    const m = w.match(/^(FEW|SCT|BKN|OVC|VV)(\d{3}|\/\/\/)/);
    if (m) out.push({ cover: m[1] === "VV" ? "OVX" : m[1] });
  }
  return out;
}

// 置き場の1件（空港の今の weather() の形：sky・wspd を持つ）→ チェックインの天気
export function fromShared(e: { at: number; v: unknown } | undefined, now: number): CheckinWx | null {
  if (!e || !Number.isFinite(e.at) || now - e.at > SHARED_MAX_MS) return null;
  const v = e.v as { sky?: unknown; wspd?: unknown } | null;
  if (!v || typeof v !== "object") return null;
  const weather = wxCode(typeof v.sky === "string" ? v.sky : null), wind_kt = kt(v.wspd);
  return weather == null && wind_kt == null ? null : { weather, wind_kt };
}

// 天気の記録の1行（wx_obs）→ チェックインの天気。原文から空模様を決める（前と同じ skyOf・wxCode）
export function fromObs(o: { at: string; raw: string; wspd: number | null } | undefined, now: number): CheckinWx | null {
  if (!o) return null;
  const at = Date.parse(o.at);
  if (!Number.isFinite(at) || now - at > OBS_MAX_MS) return null;
  const raw = String(o.raw ?? "");
  const weather = wxCode(skyOf(" " + raw + " ", cloudsFromRaw(raw))), wind_kt = kt(o.wspd);
  return weather == null && wind_kt == null ? null : { weather, wind_kt };
}

// 置き場を先に、なければ記録。どちらもなければ null（あとで配信元から書き足す）
export function pickWx(shared: { at: number; v: unknown } | undefined, obs: { at: string; raw: string; wspd: number | null } | undefined, now = Date.now()): CheckinWx | null {
  return fromShared(shared, now) ?? fromObs(obs, now);
}
