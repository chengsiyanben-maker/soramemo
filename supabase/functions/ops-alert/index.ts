// 運営への知らせ：夜の処理・取り込みが止まったら、1日1回メールか Webhook で知らせる（11/26 本人の OK ⑤）
//   11/27：新しい不具合・意見の報告の数（種類ごと）も載せる。止まった処理がなく報告だけの日は20時以降に送る（ops_alert_claim が決める）
//   pg_cron が毎時41分に呼ぶ（移行 ops_alert）。送るかどうかは ops_alert_claim が決める（ng があり、今日まだ届いていないときだけ）ので、
//   誰がいつ何度呼んでも、届くのは1日1回まで
//   送り先：秘密の設定 OPS_ALERT_TO（メールアドレスか https:// の Webhook。カンマ区切り）。メールは OPS_SMTP_USER・OPS_SMTP_PASS（ほかは任意）
//   ログには宛先・鍵を出さない（何通届いたかだけ）
import { createClient } from "npm:@supabase/supabase-js@2.117.2";
import nodemailer from "npm:nodemailer@6.9.16";
import { alertText, type HealthItem, parseTargets, resultText, smtpConfig } from "../_shared/ops_alert.ts";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });

Deno.serve(async () => {
  const { data, error } = await admin.rpc("ops_alert_claim");
  if (error) { console.error("ops_alert_claim", error.message); return json({ ok: false }, 500); }
  if (!data?.send) return json({ ok: true, sent: 0, reason: data?.reason ?? "none" });

  const targets = parseTargets(Deno.env.get("OPS_ALERT_TO"));
  const smtp = smtpConfig((k) => Deno.env.get(k));
  const msg = alertText((data.items ?? []) as HealthItem[], new Date(), Number(data.feedback_new ?? 0), (data.feedback_kinds ?? null) as Record<string, number> | null);
  const r = { mail: 0, hook: 0, failed: 0, skipped: [] as string[] };
  if (!targets.length) r.skipped.push("no_target");

  const mails = targets.filter((t) => t.kind === "mail") as { kind: "mail"; to: string }[];
  if (mails.length && !smtp) r.skipped.push("no_smtp");
  if (mails.length && smtp) {
    try {
      const tr = nodemailer.createTransport({ host: smtp.host, port: smtp.port, secure: smtp.port === 465, auth: { user: smtp.user, pass: smtp.pass },
        connectionTimeout: 10000, greetingTimeout: 10000, socketTimeout: 15000 });
      await tr.sendMail({ from: smtp.from, to: mails.map((m) => m.to).join(", "), subject: msg.subject, text: msg.text });
      r.mail = mails.length;
    } catch (e) {
      r.failed += mails.length;
      console.error("ops-alert mail", (e as Error)?.name ?? "error");   // 中身（宛先が入りうる）は出さない
    }
  }
  for (const t of targets) {
    if (t.kind !== "hook") continue;
    try {
      // Slack は text、Discord は content を読む。どちらにも同じ文を入れる
      const body = `${msg.subject}\n${msg.text}`;
      const res = await fetch(t.url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: body, content: body.slice(0, 1900) }),
        signal: AbortSignal.timeout(10000) });
      if (res.ok) r.hook++; else r.failed++;
    } catch { r.failed++; }
  }
  const ok = r.mail + r.hook > 0;
  const { error: de } = await admin.rpc("ops_alert_done", { p_day: data.day, p_ok: ok, p_result: resultText(r) });
  if (de) console.error("ops_alert_done", de.message);
  const nSmtp = r.mail, nHook = r.hook;
  console.log(JSON.stringify({ ev: "ops_alert", ok, n_smtp: nSmtp, n_hook: nHook, failed: r.failed, skipped: r.skipped }));   // 届いた数だけ
  return json({ ok: true, sent: r.mail + r.hook, failed: r.failed });
});
