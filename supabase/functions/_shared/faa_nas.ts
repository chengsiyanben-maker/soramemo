// アメリカ FAA の NAS Status（https://nasstatus.faa.gov/api/airport-status-information、公開の XML・1分ごとに更新・登録なし）を読む。
// 取得とは分けて、テストしやすくしている（取り込みは functions/world-status、11/15 本人「OK」：決定事項【11/15】）。
//   ・空港ごとの 地上待機（Ground Stop）・出発の間引き（Ground Delay Program）・閉鎖・15分以上の出発／到着の遅れ・除氷 を取り出す
//   ・日本から直行便のある空港（US_SERVED）だけ残す
//   ・Update_Time が10分より前なら「古い」として使わない（呼ぶ側で判定。stale）
// 出典の書き方：「出典：FAA NAS Status。運航の判断には使えません。遅れることがあります」
// 規約：個別の利用規約の文は見つからず、米国政府の著作物の一般の決まり（17 U.S.C. §105）と FAA のデータの免責による（report-world-ops-sources.md）
// XML の項目は 11/14 に一部しか読めていない（閉鎖だけ）。名前の違う入れ物にも当たるよう、<ARPT> を含むかたまりを広く拾う

export const FAA_URL = "https://nasstatus.faa.gov/api/airport-status-information";
export const FAA_NOTE = "出典：FAA NAS Status。運航の判断には使えません。遅れることがあります";
export const STALE_MIN = 10;

// 日本から直行便のあるアメリカの空港（ハワイ・グアム・北マリアナ含む）。日本語の名前は通知の文に使う。
// 見込みの一覧（report-world-ops-sources.md の 2）。本人が world-destinations.sql を流したら、その結果で直す
export const US_SERVED: Record<string, string> = {
  HNL: "ホノルル", KOA: "コナ", OGG: "カフルイ", GUM: "グアム", SPN: "サイパン", ANC: "アンカレッジ",
  LAX: "ロサンゼルス", SFO: "サンフランシスコ", SJC: "サンノゼ", SAN: "サンディエゴ", SEA: "シアトル", PDX: "ポートランド",
  LAS: "ラスベガス", DEN: "デンバー", DFW: "ダラス", IAH: "ヒューストン", ORD: "シカゴ", MSP: "ミネアポリス", DTW: "デトロイト",
  ATL: "アトランタ", BOS: "ボストン", JFK: "ニューヨーク（JFK）", EWR: "ニューヨーク（ニューアーク）", IAD: "ワシントン",
};

export type FaaKind = "ground_stop" | "gdp" | "closure" | "delay_arr" | "delay_dep" | "deicing";
export type FaaRow = {
  iata: string; kind: FaaKind; reason: string | null;
  starts: string | null; ends: string | null;
  avg_delay: number | null; max_delay: number | null; trend: "increasing" | "decreasing" | "steady" | null;
};

const MON: Record<string, number> = { Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11 };
// 時間帯の略号 → UTC からの時間
const TZ: Record<string, number> = {
  UTC: 0, GMT: 0, Z: 0, EST: -5, EDT: -4, CST: -6, CDT: -5, MST: -7, MDT: -6, PST: -8, PDT: -7,
  AKST: -9, AKDT: -8, HST: -10, HDT: -9, CHST: 10, CHT: 10,
};

const unesc = (s: string) => s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
  .replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
const tag = (xml: string, name: string): string | null => {
  const m = xml.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, "i"));
  return m ? unesc(m[1]) : null;
};

// 「Sat Nov 14 03:12:45 2026 GMT」 → ミリ秒（読めなければ null）
export function parseUpdateTime(s: string | null): number | null {
  if (!s) return null;
  const m = s.match(/([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(\d{4})\s*([A-Za-z]+)?/);
  if (m && MON[m[1]] != null) {
    const off = TZ[(m[7] ?? "GMT").toUpperCase()] ?? 0;
    return Date.UTC(+m[6], MON[m[1]], +m[2], +m[3], +m[4], +m[5]) - off * 3600_000;
  }
  const t = Date.parse(s);
  return Number.isFinite(t) ? t : null;
}

// 「1 hour and 3 minutes」「45 minutes」 → 分
export function parseMinutes(s: string | null): number | null {
  if (!s) return null;
  const h = s.match(/(\d+)\s*hour/i), mi = s.match(/(\d+)\s*min/i);
  if (!h && !mi) return null;
  return (h ? +h[1] * 60 : 0) + (mi ? +mi[1] : 0);
}

// 「3:30 pm EDT」 → 取った時刻より後のいちばん近いその時刻（ミリ秒）。日付のない時刻なので、過ぎていれば次の日
export function parseClock(s: string | null, ref: number): number | null {
  if (!s) return null;
  const m = s.match(/(\d{1,2}):(\d{2})\s*(am|pm)?\s*([A-Za-z]{1,5})?/i);
  if (!m) return null;
  let h = +m[1] % 12; if (!m[3]) h = +m[1]; else if (/pm/i.test(m[3])) h += 12;
  const off = TZ[(m[4] ?? "UTC").toUpperCase()];
  if (off == null) return null;
  const local = new Date(ref + off * 3600_000);
  let t = Date.UTC(local.getUTCFullYear(), local.getUTCMonth(), local.getUTCDate(), h, +m[2]) - off * 3600_000;
  if (t < ref - 3600_000) t += 864e5;     // 1時間より前なら次の日（少し過ぎた終わりの見込みはそのまま）
  return t;
}

// 「Nov 13 at 20:00 UTC.」「Nov 14 at 0400 UTC」 → ミリ秒。年は取った時刻から（年をまたぐときは近い方）
export function parseDayTime(s: string | null, ref: number): number | null {
  if (!s) return null;
  const m = s.match(/([A-Z][a-z]{2})\s+(\d{1,2})\s+(?:at\s+)?(\d{1,2}):?(\d{2})\s*([A-Za-z]+)?/);
  if (!m || MON[m[1]] == null) return null;
  const off = TZ[(m[5] ?? "UTC").toUpperCase()] ?? 0;
  const y = new Date(ref).getUTCFullYear();
  const cand = [y - 1, y, y + 1].map((yy) => Date.UTC(yy, MON[m[1]], +m[2], +m[3], +m[4]) - off * 3600_000);
  return cand.sort((a, b) => Math.abs(a - ref) - Math.abs(b - ref))[0];
}

const kindOf = (name: string): FaaKind | "delay" | null => {
  if (/ground\s*stop/i.test(name)) return "ground_stop";
  if (/ground\s*delay/i.test(name)) return "gdp";
  if (/closure/i.test(name)) return "closure";
  if (/de-?icing/i.test(name)) return "deicing";
  if (/arrival|departure|general/i.test(name)) return "delay";
  return null;   // 空域の流れの制限（Airspace Flow）などは空港ごとでないので使わない
};
const trendOf = (s: string | null) => !s ? null : /incr/i.test(s) ? "increasing" : /decr/i.test(s) ? "decreasing" : /steady|same/i.test(s) ? "steady" : null;
const iso = (t: number | null) => t == null ? null : new Date(t).toISOString();

export type FaaParsed = { updatedAt: number | null; rows: FaaRow[] };

// XML を読む。served を渡せば、その空港だけ残す
export function parseNas(xml: string, served: Record<string, string> | null = US_SERVED): FaaParsed {
  const updatedAt = parseUpdateTime(tag(xml, "Update_Time"));
  const ref = updatedAt ?? Date.now();
  const rows: FaaRow[] = [];
  for (const block of xml.match(/<Delay_type>[\s\S]*?<\/Delay_type>/gi) ?? []) {
    const k = kindOf(tag(block, "Name") ?? "");
    if (!k) continue;
    const body = block.replace(/<Name>[\s\S]*?<\/Name>/i, "");
    // <ARPT> を含むいちばん内側のかたまり（入れ物の名前は種類で違う：Ground_Delay・Program・Delay・Airport など）
    for (const m of body.matchAll(/<([A-Za-z_]+)(?:\s[^>]*)?>\s*<ARPT>([\s\S]*?)<\/ARPT>([\s\S]*?)<\/\1>/g)) {
      const iata = unesc(m[2]).toUpperCase();
      if (!/^[A-Z]{3}$/.test(iata)) continue;
      if (served && !(iata in served)) continue;
      const it = m[3];
      const reason = tag(it, "Reason")?.slice(0, 300) ?? null;
      if (k === "delay") {
        // 出発・到着ごとに1行（<Arrival_Departure Type="Arrival">）
        for (const ad of it.matchAll(/<Arrival_Departure\s+Type="([^"]+)"\s*>([\s\S]*?)<\/Arrival_Departure>/gi)) {
          rows.push({ iata, kind: /dep/i.test(ad[1]) ? "delay_dep" : "delay_arr", reason, starts: null, ends: null,
            avg_delay: parseMinutes(tag(ad[2], "Min")), max_delay: parseMinutes(tag(ad[2], "Max")), trend: trendOf(tag(ad[2], "Trend")) });
        }
        continue;
      }
      const row: FaaRow = { iata, kind: k, reason, starts: null, ends: null, avg_delay: null, max_delay: null, trend: trendOf(tag(it, "Trend")) };
      if (k === "ground_stop" || k === "gdp") row.ends = iso(parseClock(tag(it, "End_Time"), ref));
      if (k === "gdp") { row.avg_delay = parseMinutes(tag(it, "Avg")); row.max_delay = parseMinutes(tag(it, "Max")); }
      if (k === "closure") { row.starts = iso(parseDayTime(tag(it, "Start"), ref)); row.ends = iso(parseDayTime(tag(it, "Reopen"), ref)); }
      rows.push(row);
    }
  }
  // 同じ空港・種類は1つ（あとから出た方を捨てる）
  const seen = new Set<string>();
  return { updatedAt, rows: rows.filter((r) => !seen.has(`${r.iata}|${r.kind}`) && seen.add(`${r.iata}|${r.kind}`)) };
}

export const isStale = (updatedAt: number | null, now: number) => updatedAt == null || now - updatedAt > STALE_MIN * 60_000;
