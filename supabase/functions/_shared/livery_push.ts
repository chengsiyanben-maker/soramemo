// 機体ごとの通知：選んだ特別塗装機が新しい便（便名）で飛んでいるのを見つけたら、その機体を選んでいる人に1便に1回知らせる。
// 送る・記録するところは外から渡す（airport-traffic はデータベースと web-push、テストは作り物）
export type RegFlySeen = { reg: string; name: string; airline: string; callsign: string | null; alt_ft: number | null; kind?: string };
export type RegFlySub = { id: number; endpoint: string; p256dh: string; auth: string };
export type RegFlyDeps = {
  notifiedSince: (reg: string, key: string, sinceIso: string) => Promise<boolean>;   // この便をもう知らせたか
  markNotified: (reg: string, key: string, atIso: string) => Promise<void>;
  subsFor: (reg: string) => Promise<RegFlySub[]>;
  send: (sub: RegFlySub, payload: string) => Promise<number | null>;   // 失敗したときは配信サービスの状態の番号
  drop: (id: number) => Promise<void>;   // 使われなくなった購読（404・410）を消す
};

// 知らせる対象：アライアンス塗装ではなく、便名があり、地上ではなく飛んでいる（1,000ft より上）
export const wantsRegFly = (v: RegFlySeen) => v.kind !== "alliance" && !!v.callsign && typeof v.alt_ft === "number" && v.alt_ft > 1000;
export const regFlyKey = (callsign: string) => `F:${callsign}`;
export const regFlyMessage = (v: RegFlySeen) => ({
  title: `そらメモ：★${v.name}`,
  body: `${v.name}（${v.airline}・${v.callsign}）が飛んでいます（推定）。`,
  tag: `spr-${v.reg}`,
  url: `./#special-${v.reg}`,
});

// 送った数を返す。同じ便は12時間のうちに1回だけ（便名が変われば新しい便）
export async function notifyRegFly(v: RegFlySeen, deps: RegFlyDeps, now = Date.now()): Promise<number> {
  if (!wantsRegFly(v)) return 0;
  const key = regFlyKey(v.callsign!);
  if (await deps.notifiedSince(v.reg, key, new Date(now - 12 * 3600_000).toISOString())) return 0;
  await deps.markNotified(v.reg, key, new Date(now).toISOString());
  const subs = await deps.subsFor(v.reg);
  if (!subs.length) return 0;
  const payload = JSON.stringify(regFlyMessage(v));
  let sent = 0;
  for (const s of subs) {
    const code = await deps.send(s, payload);
    if (code == null) sent++;
    else if (code === 404 || code === 410) await deps.drop(s.id);
  }
  return sent;
}
