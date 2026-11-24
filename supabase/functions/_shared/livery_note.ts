// 特別塗装機の知らせをまとめる決まり（11/25 見直し2回目の4番）
//  ・1便で1つの tag：予定（odpt-status）→ 飛んでいる（機体ごとの知らせ）→ 着陸に向かっている（空港の知らせ）を、端末の上で同じ通知の書き換えにする
//    tag は「sp-便名」。予定の便は機体（登録記号）が分からないので、3つのどれでも分かる便名でそろえる（同じ時間に同じ便名で飛ぶ機体は1機だけ）
//    便名が分からないとき（呼び出し符号なし）だけ「sp-登録記号」
//  ・夜の静かな時間（23時〜7時、日本時間）：push_subs.quiet_night（はじめ true）の人には送らない。ゴーアラウンドは前からの ga_quiet のまま
import { flightOfCallsign, normCallsign } from "./flight_watch.ts";
import { quietNow } from "./go_around.ts";

// 便名の形をそろえる（JL0123 → JL123）
export function normFlight(f: string): string {
  const m = /^([A-Z0-9]{2})0*(\d{1,4})([A-Z]?)$/.exec(String(f ?? "").trim().toUpperCase());
  return m ? m[1] + m[2] + m[3] : String(f ?? "").trim().toUpperCase();
}

export function liveryTag(o: { flight?: string | null; callsign?: string | null; reg?: string | null }): string {
  const f = o.flight ? normFlight(o.flight) : o.callsign ? (flightOfCallsign(o.callsign) ?? normCallsign(o.callsign)) : null;
  return `sp-${f || o.reg || "x"}`;
}

// 夜の静かな時間を選んだ人を外す。列がない・null のときは「選んでいる」とみなす（はじめ ON）
export function awake<T extends { quiet_night?: boolean | null }>(subs: T[], now = Date.now()): T[] {
  return quietNow(now) ? subs.filter((s) => s.quiet_night === false) : subs;
}

// 夜の間に見つかった予定を、朝（7時すぎ）に静かな時間を選んだ人へ送り直すときの幅（日本時間の前の日23時〜今日7時。ISO）
export function quietWindow(now = Date.now()): { from: string; to: string } {
  const H = 3600_000, j = now + 9 * H, day = Math.floor(j / 864e5) * 864e5;
  const to = day + 7 * H - 9 * H;
  return { from: new Date(to - 8 * H).toISOString(), to: new Date(to).toISOString() };
}
