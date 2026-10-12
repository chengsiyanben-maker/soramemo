// 「空港の今」の材料の整形。配信元の形を、アプリが使う小さな形にそろえる（テストしやすいように、取得とは分けている）。
//   便：公共交通オープンデータセンター（ODPT）の FlightInformationArrival / FlightInformationDeparture（JAL・ANA）
//   天気：気象通報（METAR。米国の航空気象センターの JSON）

export type FlightKind = "ok" | "late" | "board" | "done" | "cancel";
export type FlightRow = {
  time: string;          // 予定の時刻 "HH:MM"（日本時間）
  newTime: string | null; // 変更後の時刻（見込み・実際）。予定と同じなら null
  place: string;         // 相手の空港の IATA（到着便は出発地、出発便は行き先）
  airline: string;       // 航空会社の2文字（JL・NH など）
  no: string;            // 便名（"JL116"）
  term: string | null;   // ターミナル（"T1" など）
  kind: FlightKind;
};

const last = (v: unknown): string => { const s = Array.isArray(v) ? String(v[0] ?? "") : String(v ?? ""); const i = s.lastIndexOf(":"); return i >= 0 ? s.slice(i + 1) : s; };
const hhmm = (v: unknown): string | null => { const m = String(v ?? "").match(/(\d{1,2}):(\d{2})/); return m ? `${m[1].padStart(2, "0")}:${m[2]}` : null; };

// 便名：ODPT は "JL0116" や "JL116" の形。先頭2文字を航空会社、数字の頭の0は落とす
export function flightNo(v: unknown): { airline: string; no: string } | null {
  const s = (Array.isArray(v) ? String(v[0] ?? "") : String(v ?? "")).toUpperCase().replace(/\s/g, "");
  const m = s.match(/^([A-Z0-9]{2})0*(\d{1,4})$/);
  return m ? { airline: m[1], no: m[1] + m[2] } : null;
}

// ターミナル："odpt.AirportTerminal:HND.Terminal1" → "T1"、"…:CTS.Domestic" → null（区別しない）
export function terminal(v: unknown): string | null {
  const m = String(v ?? "").match(/Terminal\s*(\d)/i);
  return m ? "T" + m[1] : null;
}

// 状況：ODPT の "odpt.FlightStatus:Arrived" などを5つにまとめる。知らない値は「定刻」扱いにせず、時刻のずれで決める
export function kindOf(status: unknown, time: string, newTime: string | null): FlightKind {
  const s = last(status).toLowerCase();
  if (/cancel/.test(s)) return "cancel";
  if (/arrived|landed|departed|takeoff|airborne/.test(s)) return "done";
  if (/boarding|finalcall|gateclosed|gateclose/.test(s)) return "board";
  if (/delay|changed/.test(s)) return "late";
  if (newTime && newTime > time) return "late";
  return "ok";
}

// 1件を整形する。dir="arr" は到着便（相手は出発地）、"dep" は出発便（相手は行き先）
export function normalize(raw: Record<string, unknown>, dir: "arr" | "dep"): FlightRow | null {
  const fn = flightNo(raw["odpt:flightNumber"]);
  const time = hhmm(raw[dir === "arr" ? "odpt:scheduledArrivalTime" : "odpt:scheduledDepartureTime"]);
  if (!fn || !time) return null;
  const actual = hhmm(raw[dir === "arr" ? "odpt:actualArrivalTime" : "odpt:actualDepartureTime"]);
  const est = hhmm(raw[dir === "arr" ? "odpt:estimatedArrivalTime" : "odpt:estimatedDepartureTime"]);
  const changed = actual ?? est;
  const newTime = changed && changed !== time ? changed : null;
  const placeRaw = dir === "arr" ? (raw["odpt:departureAirport"] ?? raw["odpt:originAirport"]) : (raw["odpt:arrivalAirport"] ?? raw["odpt:destinationAirport"]);
  const place = last(placeRaw).slice(0, 3).toUpperCase();
  return {
    time, newTime, place, airline: fn.airline, no: fn.no,
    term: terminal(raw[dir === "arr" ? "odpt:arrivalAirportTerminal" : "odpt:departureAirportTerminal"]),
    kind: kindOf(raw["odpt:flightStatus"], time, newTime),
  };
}

// 分に直す（日付をまたぐ便は、いまの時刻から見て近いほうの日に寄せる）
const toMin = (t: string) => +t.slice(0, 2) * 60 + +t.slice(3, 5);
function rel(t: string, now: number): number { let d = toMin(t) - now; if (d < -720) d += 1440; if (d > 720) d -= 1440; return d; }

// 直近の便：いまの60分前から180分後まで、予定の時刻の順。同じ便名の重複（共同運航の二重掲載）は1つにする
export function recent(rows: FlightRow[], nowMin: number, before = 60, after = 180, max = 30): FlightRow[] {
  const seen = new Set<string>(), out: (FlightRow & { r: number })[] = [];
  for (const x of rows) {
    const r = rel(x.time, nowMin);
    if (r < -before || r > after || seen.has(x.no)) continue;
    seen.add(x.no); out.push({ ...x, r });
  }
  return out.sort((a, b) => a.r - b.r || a.no.localeCompare(b.no)).slice(0, max).map(({ r: _r, ...x }) => x);
}

// ---------- 天気（METAR） ----------
export type Weather = { time: string | null; wdir: number | null; wspd: number | null; wgst: number | null; vis_m: number | null; vis_plus: boolean; sky: string | null };

// 空模様：降っているもの（雷・雪・雨・霧）を先に見て、なければ雲の量で決める
export function skyOf(raw: string, clouds: { cover?: string }[] = []): string | null {
  const wx = raw.replace(/\s(RMK|TEMPO|BECMG|NOSIG)\b.*$/, "");
  if (/\s[-+]?(VC)?TS/.test(wx)) return "雷";
  if (/\s[-+]?(SH)?(SN|SG|PL)/.test(wx)) return "雪";
  if (/\s[-+]?(SH|FZ)?(RA|DZ)/.test(wx)) return "雨";
  if (/\s(FG|BR)(\s|$)/.test(wx)) return "霧";
  if (/\sCAVOK(\s|$)/.test(wx)) return "晴れ";
  const covers = clouds.map((c) => String(c.cover ?? "").toUpperCase());
  if (covers.some((c) => c === "OVC" || c === "BKN" || c === "OVX")) return "くもり";
  if (covers.length || /\s(SKC|CLR|NSC|FEW|SCT)/.test(wx)) return "晴れ";
  return null;
}

export function weather(m: Record<string, unknown>): Weather {
  const raw = String(m.rawOb ?? "");
  const mv = raw.match(/KT\s+(?:\d{3}V\d{3}\s+)?(\d{4})(?:\s|$)/) || raw.match(/\s(CAVOK)\s/);
  const visRaw = String(m.visib ?? ""), visMi = parseFloat(visRaw);
  const visM = mv ? (mv[1] === "CAVOK" || mv[1] === "9999" ? 10000 : parseInt(mv[1], 10)) : Number.isFinite(visMi) ? Math.round(visMi * 1609) : null;
  return {
    time: typeof m.reportTime === "string" ? m.reportTime : null,
    wdir: typeof m.wdir === "number" ? m.wdir : null,
    wspd: typeof m.wspd === "number" ? m.wspd : null,
    wgst: typeof m.wgst === "number" ? m.wgst : null,
    vis_m: visM,
    vis_plus: mv ? mv[1] === "9999" || mv[1] === "CAVOK" : visRaw.endsWith("+"),
    sky: skyOf(" " + raw + " ", Array.isArray(m.clouds) ? m.clouds as { cover?: string }[] : []),
  };
}
