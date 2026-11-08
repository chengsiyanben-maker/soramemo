// POST /functions/v1/delete-account  body: { confirm: "削除" }
// 本人のアカウントと、すべての記録（チェックイン・フライト・記録帳・会社・機材・施設・加入情報・表示の設定 user_view_prefs）を消す。
// まずエアライン経営の精算（co3_leave_settle）をし、失敗したら消さない。そらメモ＋に加入中なら、次に Stripe の定期支払いを止める。各表は auth.users を on delete cascade で参照している。
import { admin, CORS, json, rateOk, STRIPE_READY, stripe, userFrom } from "../_shared/plus.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POSTのみ" }, 405);
  const user = await userFrom(req);
  if (!user) return json({ error: "ログインしてください。" }, 401);
  if (!(await rateOk("delete-account:" + user.id, 3, 3600))) return json({ error: "短い時間に何度も操作されています。少し待ってから試してください。" }, 429);
  let body: { confirm?: string } = {};
  try { body = await req.json(); } catch { /* 空のまま */ }
  if (body.confirm !== "削除") return json({ error: "確認の文字が違います。" }, 400);

  try {
    // エアライン経営の相手（出資・共同運航・アライアンスの仲間）が損をしないように、消す前に精算する（2回目は何もしない）。
    // 定期支払いを止めるより先にする：精算で失敗したときに、支払いだけ止まってアカウントが残ることがないように
    // 失敗したら削除を止める（精算のあとに auth.users の on delete cascade で経営の表が消えるのが正しい順番）
    const { error: settleError } = await admin.rpc("co3_leave_settle", { p_uid: user.id });
    if (settleError) throw settleError;
    const { data: sub } = await admin.from("subscriptions").select("status, provider_subscription").eq("user_id", user.id).maybeSingle();
    if (sub?.provider_subscription && ["active", "trialing", "past_due", "unpaid", "incomplete"].includes(sub.status)) {
      if (!STRIPE_READY) return json({ error: "定期支払いを止められませんでした。時間をおいて試してください。" }, 500);
      await stripe.subscriptions.cancel(sub.provider_subscription);
    }
    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) throw error;
    return json({ ok: true });
  } catch (e) {
    console.error(e);
    return json({ error: "削除できませんでした。時間をおいてもう一度試してください。" }, 500);
  }
});
