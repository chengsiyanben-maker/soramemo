// 通知の題と本文の書き方をそろえる（アプリ全体の見直し B の8番・PM の指示 11/24）
//   ・題の頭の「そらメモ：」を外す（iPhone はアプリ名を別に出すので二重になり、ロック画面で大事な語が切れる）
//   ・推定の書き方を、本文の最後に「（推定）」1つにそろえる。
//     「（推定）」「（機体の位置からの推定）」「（実際の機体の動きからの推定）」「（気象通報からの目安。…）」「（…・推定）」などは、
//     推定の語だけを外し（中身が残ればかっこは残す）、推定のあった行の最後（終わりの「。」の前）に「（推定）」を1つ付ける
//   ・送る直前に1か所で通す（送り手：airport-traffic の sendOne・notifyLivery・機体ごとの通知、alert_push の2つ）。
//     画面に出す文（flight_alerts.message など）は変えない
const PREFIX = /^そらメモ[：:]\s*/;
// かっこの中の1つの区切りが、推定の出どころだけか（例「推定」「機体の位置からの推定」「気象通報からの目安」）
const EST_PART = /^(?:.*から(?:の)?)?(?:推定|目安)$/;
const PAREN = /（([^（）]*)）/g;

export function pushTitle(t: string): string {
  return String(t ?? "").replace(PREFIX, "");
}

// 1行の推定の語を外す。推定があったかも返す
function stripLine(line: string): { text: string; est: boolean } {
  let est = false;
  const text = line.replace(PAREN, (all, inner: string) => {
    const parts = inner.split(/[・。]/).map((x) => x.trim()).filter((x) => x);
    const keep = parts.filter((x) => !EST_PART.test(x));
    if (keep.length === parts.length) return all;
    est = true;
    return keep.length ? `（${keep.join("・")}）` : "";
  });
  return { text, est };
}

export function pushBody(b: string): string {
  const lines = String(b ?? "").split("\n").map(stripLine);
  let last = -1;
  lines.forEach((l, i) => { if (l.est) last = i; });
  if (last < 0) return String(b ?? "");
  const out = lines.map((l) => l.text);
  const m = out[last].match(/^(.*?)(。*)$/s)!;
  out[last] = `${m[1]}（推定）${m[2]}`;
  return out.join("\n");
}

// 送る中身（title・body のある形）をそろえる。ほかの鍵（tag・url・renotify など）はそのまま
export function tidyPush<T extends Record<string, unknown>>(p: T): T {
  const o: Record<string, unknown> = { ...p };
  if (typeof o.title === "string") o.title = pushTitle(o.title);
  if (typeof o.body === "string") o.body = pushBody(o.body);
  return o as T;
}
