// 送り直しても二重にならない仕組み（data/idem・移行200）
// 端末が作った印の ID（client_id）を読み、同じ ID の2回目には1回目の印をそのまま返す形を作る

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

// 送られた ID を読む。UUID（v1〜v8。端末は v7 か v4 を作る）の形でなければ null（ID なしで前と同じ動き）
export function parseCid(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const s = v.trim().toLowerCase();
  return UUID.test(s) ? s : null;
}

// 一意の索引にぶつかった（同じ ID が同時に2回来た）か
// deno-lint-ignore no-explicit-any
export function isUniqueViolation(e: any): boolean {
  return !!e && (e.code === "23505" || /duplicate key/i.test(String(e.message ?? "")));
}

export type CheckinRow = {
  id: number | string; airport_id: number; terminal_id: string | null; created_at: string;
  flags: string[] | null; weather: string | null; wind_kt: number | null; ops: string | null;
};
export type FlightRow = { id: number | string; from_airport: number; to_airport: number; dep_at: string; arr_at: string; distance_km: number } | null;

// 「もう記録済み」の返事。初めての空港・ターミナルの演出と行事のボーナスは1回目で済んでいるので出さない
export function againBody(ci: CheckinRow, flight: FlightRow) {
  return {
    ok: true, again: true, at: ci.created_at,
    airport_id: ci.airport_id, terminal_id: ci.terminal_id ?? null,
    first_airport: false, first_terminal: false,
    flight: flight ?? null, flags: ci.flags ?? [], weather: ci.weather ?? null, wind_kt: ci.wind_kt ?? null, ops: ci.ops ?? null, bonus: [],
  };
}
