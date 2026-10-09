// 非常停止（emergency-stop）の判定。合言葉の照合と、利用者に見せる文の整形だけを置く（テストしやすいように分けている）。

// 合言葉を比べる。長さが違えば即座に false、同じ長さなら全文字を比べ終えてから答える（比べる時間で中身が漏れないように）。
export function tokenOk(given: string | null, expected: string): boolean {
  if (!expected || !given) return false;          // 合言葉が未設定のときは必ず拒否（閉じる側に倒す）
  if (given.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < given.length; i++) diff |= given.charCodeAt(i) ^ expected.charCodeAt(i);
  return diff === 0;
}

export const DEFAULT_MESSAGE = "メンテナンス中です。しばらくしてから開き直してください。";

// 利用者に見せる文。空なら既定の文、長すぎれば200字で切る（運営画面の上限と同じ）
export function cleanMessage(v: unknown): string {
  const s = typeof v === "string" ? v.trim() : "";
  return s ? s.slice(0, 200) : DEFAULT_MESSAGE;
}
