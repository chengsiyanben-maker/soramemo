// 不具合・意見の報告（feedback-submit）の、データベースにも網にも触らない部品
//   受け取る形を決まった形だけに絞る。位置・メール・IP は受け取らない（来ても捨てる）
//   表の決まり（移行 feedback）と同じ形にしておく。ずれたら表の check で断られる

export type FeedbackRow = {
  kind: "bug" | "request" | "airport_data";
  body: string;
  session: string;
  app_version: string | null;
  screen: string | null;
  device: string | null;
  last_error: string | null;
  airport: string | null;
};

const KINDS = new Set(["bug", "request", "airport_data"]);
const pick = (v: unknown, re: RegExp) => (typeof v === "string" && re.test(v) ? v : null);

// 正しければ表に入れる行、だめなら理由（短い英字の札。画面で文に直す）
export function parseFeedback(v: unknown): { ok: true; row: FeedbackRow } | { ok: false; error: string } {
  const o = (v && typeof v === "object" && !Array.isArray(v) ? v : {}) as Record<string, unknown>;
  if (typeof o.kind !== "string" || !KINDS.has(o.kind)) return { ok: false, error: "bad_kind" };
  const body = typeof o.body === "string" ? o.body.trim() : "";
  if (!body) return { ok: false, error: "empty" };
  if ([...body].length > 2000) return { ok: false, error: "too_long" };
  const session = pick(o.session, /^[a-z0-9]{8,32}$/);
  if (!session) return { ok: false, error: "bad_session" };
  return {
    ok: true,
    row: {
      kind: o.kind as FeedbackRow["kind"],
      body,
      session,
      // 自動の付けたしは、形が違えば捨てるだけ（報告そのものは受け付ける）
      app_version: pick(o.app_version, /^[0-9A-Za-z._+-]{1,24}$/),
      screen: pick(o.screen, /^[a-z0-9_:.-]{1,40}$/),
      device: pick(o.device, /^[a-z0-9_.-]{1,24}$/),
      last_error: pick(o.last_error, /^[a-z_]{1,20}$/),
      airport: typeof o.airport === "string" ? pick(o.airport.toUpperCase(), /^[A-Z0-9]{3,4}$/) : null,
    },
  };
}
