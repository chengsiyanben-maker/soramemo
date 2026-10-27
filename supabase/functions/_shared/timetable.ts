// 計画の画面で使う時刻表：ODPT のフライト時刻表（odpt:FlightSchedule）を、曜日と有効な期間つきの行にする。取得とは分けて、テストしやすくしている。
//   ODPT の1件：出発空港・到着空港・曜日（odpt:calendar）と、期間ごとの便（odpt:flightScheduleObject）
//   同じ便・同じ期間・同じ時刻が曜日ごとに別の件で来るので、曜日を1つの数（日曜=1, 月曜=2, … 土曜=64 の足し算）にまとめる。
//   国内線だけ（出発・到着とも日本の空港）。時刻は日本時間の "HH:MM"。日付をまたいで着く便は arr_day = 1。
export type TimetableRow = {
  operator: string; dep: string; arr: string; flight: string; days: number;
  valid_from: string; valid_to: string; dep_time: string; arr_time: string; arr_day: number; aircraft: string | null;
};

const DAY: Record<string, number> = { Sunday: 1, Monday: 2, Tuesday: 4, Wednesday: 8, Thursday: 16, Friday: 32, Saturday: 64 };
const apt = (s: unknown) => typeof s === "string" ? (/^odpt\.Airport:([A-Z]{3})$/.exec(s) ?? [])[1] ?? null : null;
const hm = (s: unknown) => typeof s === "string" && /^\d{1,2}:\d{2}$/.test(s) ? s.padStart(5, "0") : null;
const day = (s: unknown) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}/.test(s) ? s.slice(0, 10) : null;

// 曜日の書き方を数にする（曜日の名前・毎日・平日・土日祝）。知らない書き方は 0（使わない）
export function calendarDays(cal: unknown): number {
  const c = String(cal ?? "").replace("odpt.Calendar:", "");
  if (DAY[c]) return DAY[c];
  if (c === "Everyday") return 127;
  if (c === "Weekday") return 2 | 4 | 8 | 16 | 32;
  if (c === "SaturdayHoliday" || c === "Holiday") return 1 | 64;
  return 0;
}

// deno-lint-ignore no-explicit-any
export function timetableRows(items: any[], operator: string, isDomestic: (iata: string) => boolean): TimetableRow[] {
  const out = new Map<string, TimetableRow>();
  for (const it of Array.isArray(items) ? items : []) {
    const dep = apt(it?.["odpt:originAirport"]), arr = apt(it?.["odpt:destinationAirport"]), days = calendarDays(it?.["odpt:calendar"]);
    if (!dep || !arr || dep === arr || !days || !isDomestic(dep) || !isDomestic(arr)) continue;
    for (const f of Array.isArray(it["odpt:flightScheduleObject"]) ? it["odpt:flightScheduleObject"] : []) {
      const no = Array.isArray(f?.["odpt:flightNumber"]) ? String(f["odpt:flightNumber"][0] ?? "") : "";
      const t1 = hm(f?.["odpt:originTime"]), t2 = hm(f?.["odpt:destinationTime"]);
      const from = day(f?.["odpt:isValidFrom"]) ?? "2000-01-01", to = day(f?.["odpt:isValidTo"]) ?? "2099-12-31";
      if (!/^[A-Z0-9]{2}\d{1,4}[A-Z]?$/.test(no) || !t1 || !t2 || from > to) continue;
      const key = `${dep}|${no}|${from}|${to}|${t1}`, cur = out.get(key);
      if (cur){ cur.days |= days; continue; }
      out.set(key, { operator, dep, arr, flight: no, days, valid_from: from, valid_to: to, dep_time: t1, arr_time: t2,
        arr_day: t2 < t1 ? 1 : 0, aircraft: typeof f["odpt:aircraftType"] === "string" ? f["odpt:aircraftType"].slice(0, 20) : null });
    }
  }
  return [...out.values()];
}

// 時刻表を取り込む日本の空港（JAL・ANA のグループが飛ぶ空港。飛んでいない空港は ODPT が空で返すだけ）
export const TT_AIRPORTS = [
  "CTS", "HKD", "AKJ", "MMB", "KUH", "OBO", "WKJ", "RIS", "OKD", "SHB", "MBE", "OIR", "AOJ", "MSJ", "AXT", "ONJ", "HNA", "SYO", "GAJ", "SDJ", "FKS",
  "NRT", "HND", "KIJ", "TOY", "KMQ", "NTQ", "NGO", "NKM", "FSZ", "MMJ", "ITM", "KIX", "UKB", "SHM", "TTJ", "YGJ", "IZO", "OKI", "HIJ", "IWK", "UBJ", "OKJ",
  "TKS", "TAK", "KCZ", "MYJ", "FUK", "KKJ", "HSG", "NGS", "KMJ", "OIT", "KMI", "KOJ", "ASJ", "TNE", "KUM", "KKX", "TKN", "OKE", "RNJ", "OKA", "MMY",
  "ISG", "KTD", "MMD", "UEO", "OGN", "FUJ", "IKI", "TSJ", "AXJ", "SDS", "HAC", "MYE", "OIM", "TRA", "SHI", "KJP",
];
export const isJpAirport = (iata: string) => TT_AIRPORTS.includes(iata);
