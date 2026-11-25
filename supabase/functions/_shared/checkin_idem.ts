// 送り直しても二重にならない印（data/idem・移行200）。データベースに触れない純粋な関数だけを置く
//   端末が作った ID（client_id）を一緒に送ってもらい、同じ ID の2回目は「もう記録済み」として成功で返す

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// 送られた ID を読む。UUID の形（v4・v7 どちらでも）でなければ null（今までどおり ID なしで記録する）
export function parseClientId(v: unknown): string | null {
  if (typeof v !== "string") return null;
  const s = v.trim().toLowerCase();
  if (!UUID_RE.test(s) || s === "00000000-0000-0000-0000-000000000000") return null;
  return s;
}

// 一意の索引にぶつかった（同じ ID が同時に2回届いた）か
export function isUniqueViolation(e: unknown): boolean {
  // deno-lint-ignore no-explicit-any
  const c = (e as any)?.code;
  return c === "23505";
}

export type CheckinRow = {
  id: number | string; airport_id: number; terminal_id: string | null; created_at: string;
  flags: string[] | null; weather: string | null; wind_kt: number | null; ops: string | null;
};
export type FlightRow = { id: number | string; from_airport: number; to_airport: number; dep_at: string; arr_at: string; distance_km: number } | null;

// 記録済みの印から、1回目と同じ形の返事を作る。dup: true を足す（画面は ok だけ見れば今までどおり動く）
//   first_airport・first_terminal は「この印より前に同じ空港・ターミナルの印がないか」で決める（1回目の返事と同じ値になる）
//   行事のボーナスは1回目で渡し済みなので空にする（2回は払わない）
export function replayBody(row: CheckinRow, flight: FlightRow, earlierAirport: number, earlierTerminal: number) {
  return {
    ok: true, dup: true, at: row.created_at,
    airport_id: row.airport_id, terminal_id: row.terminal_id ?? null,
    first_airport: earlierAirport === 0, first_terminal: row.terminal_id ? earlierTerminal === 0 : false,
    flight: flight ?? null, flags: row.flags ?? [], weather: row.weather ?? null, wind_kt: row.wind_kt ?? null, ops: row.ops ?? null,
    bonus: [] as unknown[],
  };
}
