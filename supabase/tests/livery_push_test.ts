// 機体ごとの通知：1便に1回、地上やアライアンス塗装は知らせない、使われなくなった購読は消す
import { assertEquals } from "jsr:@std/assert@1";
import { notifyRegFly, regFlyMessage, type RegFlyDeps, type RegFlySub, wantsRegFly } from "../functions/_shared/livery_push.ts";

function fake(subs: Record<string, RegFlySub[]>, fail: Record<number, number> = {}) {
  const notified = new Map<string, string>(), sent: [number, string][] = [], dropped: number[] = [];
  const deps: RegFlyDeps = {
    notifiedSince: (reg, key, since) => Promise.resolve((notified.get(`${reg}|${key}`) ?? "") > since),
    markNotified: (reg, key, at) => { notified.set(`${reg}|${key}`, at); return Promise.resolve(); },
    subsFor: (reg) => Promise.resolve(subs[reg] ?? []),
    send: (s, p) => { if (fail[s.id]) return Promise.resolve(fail[s.id]); sent.push([s.id, p]); return Promise.resolve(null); },
    drop: (id) => { dropped.push(id); return Promise.resolve(); },
  };
  return { deps, sent, dropped };
}
const sub = (id: number): RegFlySub => ({ id, endpoint: `https://fcm.googleapis.com/x/${id}`, p256dh: "k", auth: "a" });
const v = { reg: "JA339J", name: "JAL Jubilee Express", airline: "JAL", callsign: "JAL113", alt_ft: 24300 };

Deno.test("機体を選んでいる人に知らせ、同じ便は12時間に1回だけ", async () => {
  const f = fake({ JA339J: [sub(1), sub(2)], JA819A: [sub(3)] });
  const t0 = Date.parse("2026-10-26T09:00:00Z");
  assertEquals(await notifyRegFly(v, f.deps, t0), 2);
  assertEquals(await notifyRegFly(v, f.deps, t0 + 30_000), 0);   // 30秒後の記録でも同じ便は送らない
  assertEquals(await notifyRegFly({ ...v, callsign: "JAL114" }, f.deps, t0 + 3 * 3600_000), 2);   // 折り返しの新しい便は送る
  assertEquals(await notifyRegFly(v, f.deps, t0 + 13 * 3600_000), 2);   // 12時間たてば同じ便名でも次の日の便
  assertEquals(f.sent.every(([id]) => id !== 3), true);   // ほかの機体を選んだ人には送らない
  const m = JSON.parse(f.sent[0][1]);
  assertEquals(m.url, "./#special-JA339J");
  assertEquals(m.body.includes("JAL113") && m.body.includes("推定"), true);
});

Deno.test("地上・便名なし・アライアンス塗装は知らせない", async () => {
  const f = fake({ JA339J: [sub(1)] });
  assertEquals(wantsRegFly({ ...v, alt_ft: 0 }), false);
  assertEquals(wantsRegFly({ ...v, alt_ft: null }), false);
  assertEquals(wantsRegFly({ ...v, callsign: null }), false);
  assertEquals(wantsRegFly({ ...v, kind: "alliance" }), false);
  assertEquals(await notifyRegFly({ ...v, alt_ft: 500 }, f.deps), 0);
  assertEquals(f.sent.length, 0);
});

Deno.test("使われなくなった購読（404・410）は消し、ほかの失敗では消さない", async () => {
  const f = fake({ JA339J: [sub(1), sub(2), sub(3)] }, { 2: 410, 3: 500 });
  assertEquals(await notifyRegFly(v, f.deps), 1);
  assertEquals(f.dropped, [2]);
});

Deno.test("通知の文は、海外の登録記号でも開くリンクが作れる", () => {
  assertEquals(regFlyMessage({ ...v, reg: "B-16740" }).url, "./#special-B-16740");
  // サービスワーカーが受け付けるリンクの形（src/sw.js と同じ）
  assertEquals(/^\.\/#special-[A-Z0-9-]{2,10}$/.test(regFlyMessage({ ...v, reg: "B-16740" }).url), true);
});
