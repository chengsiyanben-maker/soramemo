// 運営への知らせ（ops-alert）の、データベースにも網にも触らない部品
//   送り先は Edge Function の秘密の設定 OPS_ALERT_TO（カンマか改行で区切る。メールアドレスか https:// の Webhook）。コードには書かない
//   メールは SMTP（OPS_SMTP_*）。新しい外部のアカウントは作らない（本人の今の Gmail のアプリパスワードなど。手順は docs/pm/report-job-alert.md）

export type Target = { kind: "mail"; to: string } | { kind: "hook"; url: string };
export type HealthItem = { key: string; label: string; last: string | null; limit_min: number | null };
export type Smtp = { host: string; port: number; user: string; pass: string; from: string };

const MAIL = /^[^\s@,;<>"]+@[^\s@,;<>"]+\.[^\s@,;<>"]+$/;

// 送り先を読む。形の違うものは捨てる。同じものは1つに。最大5つ
export function parseTargets(raw: string | undefined | null): Target[] {
  const out: Target[] = [];
  const seen = new Set<string>();
  for (const s0 of String(raw ?? "").split(/[,\n]/)) {
    const s = s0.trim();
    if (!s || seen.has(s.toLowerCase())) continue;
    let t: Target | null = null;
    if (MAIL.test(s)) t = { kind: "mail", to: s };
    else if (/^https:\/\/[^\s]+$/.test(s)) t = { kind: "hook", url: s };
    if (!t) continue;
    seen.add(s.toLowerCase());
    out.push(t);
    if (out.length >= 5) break;
  }
  return out;
}

const jst = (iso: string | null) => {
  if (!iso) return "記録なし";
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return "記録なし";
  const d = new Date(t + 9 * 3600e3);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getUTCMonth() + 1)}/${p(d.getUTCDate())} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
};

// 報告の種類の名前（夜の知らせに数だけ載せる。本文は載せない）
export const FEEDBACK_KIND: Record<string, string> = { bug: "不具合", request: "ほしい機能", airport_data: "空港データの直し" };

// 新しい報告の行（種類ごとの数だけ。本文・利用者の情報は入らない）
export function feedbackLine(n: number, kinds: Record<string, number> | null | undefined): string {
  const parts = Object.entries(kinds ?? {}).filter(([, v]) => Number(v) > 0)
    .sort(([a], [b]) => Object.keys(FEEDBACK_KIND).indexOf(a) - Object.keys(FEEDBACK_KIND).indexOf(b))
    .map(([k, v]) => `${FEEDBACK_KIND[k] ?? k} ${v}`);
  return `新しい不具合・意見の報告：${n}件${parts.length ? `（${parts.join("・")}）` : ""}`;
}

// 件名と本文（日本語）。項目の名前と最後の時刻、新しい報告の数だけ。利用者の情報は入らない
export function alertText(items: HealthItem[], now: Date, fbNew = 0, fbKinds: Record<string, number> | null = null): { subject: string; text: string } {
  const fb = fbNew > 0 ? ["", feedbackLine(fbNew, fbKinds), "中身は運営コンソールか、SQL Editor の select public.admin_feedback_list(); で見てください。"] : [];
  if (!items.length) {
    return {
      subject: `そらメモ：新しい不具合・意見の報告（${fbNew}件）`,
      text: [
        `${jst(now.toISOString())} 時点で、止まっている処理はありません。`,
        ...fb,
        "",
        "この知らせは1日1回までです。",
      ].join("\n"),
    };
  }
  const list = items.slice(0, 20);
  const lines = list.map((x) => {
    const lim = x.limit_min != null ? `・上限 ${x.limit_min >= 120 ? `${Math.round(x.limit_min / 60)}時間` : `${x.limit_min}分`}` : "";
    return `・${x.label}（最後：${jst(x.last)}${lim}）`;
  });
  if (items.length > list.length) lines.push(`・ほか ${items.length - list.length} 件`);
  return {
    subject: `そらメモ：夜の処理・取り込みが止まっています（${items.length}件）`,
    text: [
      `${jst(now.toISOString())} 時点で、次の処理が止まっているか失敗しています。`,
      "",
      ...lines,
      "",
      "くわしくは Supabase の SQL Editor で select public.admin_data_health(); か、cron.job_run_details を見てください。",
      ...fb,
      "",
      "この知らせは1日1回までです（届かなかったときは1時間ごとに試し直します）。",
    ].join("\n"),
  };
}

// SMTP の設定を読む。足りなければ null（メールは送らず、Webhook だけ）
export function smtpConfig(get: (k: string) => string | undefined): Smtp | null {
  const user = get("OPS_SMTP_USER")?.trim(), pass = get("OPS_SMTP_PASS")?.trim();
  if (!user || !pass) return null;
  const port = Number(get("OPS_SMTP_PORT") || 465);
  return { host: get("OPS_SMTP_HOST")?.trim() || "smtp.gmail.com", port: Number.isFinite(port) ? port : 465, user, pass, from: get("OPS_SMTP_FROM")?.trim() || user };
}

// 結果の短い文（宛先は書かない。何通・どの種類が届いたかだけ）
export function resultText(r: { mail: number; hook: number; failed: number; skipped: string[] }): string {
  const s = [`mail ${r.mail}`, `hook ${r.hook}`, `failed ${r.failed}`];
  if (r.skipped.length) s.push(`skip ${r.skipped.join(",")}`);
  return s.join(" / ");
}
