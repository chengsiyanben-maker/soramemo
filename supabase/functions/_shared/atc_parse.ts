// 管制の交信（英語の聞き取り結果）を読み解いて、だれに・何を（着陸許可・誘導路・高度…）を取り出し、日本語にする（判定だけ）
//   聞き取りは協力者の端末（音声認識AI）。ここは決まった言い回し（管制の用語）をたどるだけで、分からないところは出さない
import { flightOfCallsign } from "./flight_watch.ts";

export type AtcItem =
  | { k: "land" | "takeoff" | "lineup" | "goaround" | "contapp" | "push"; rwy?: string | null }
  | { k: "app"; type: string | null; rwy: string | null }
  | { k: "taxi"; to: string | null; via: string[] }
  | { k: "hold"; at: string }
  | { k: "cross"; rwy: string }
  | { k: "contact"; unit: string; freq: string | null }
  | { k: "alt"; dir: "up" | "down" | "keep"; ft: number | null; fl: number | null }
  | { k: "hdg"; turn: "L" | "R" | null; deg: number }
  | { k: "spd"; kt: number }
  | { k: "wind"; deg: number | null; kt: number };
export type AtcParsed = { callsign: string | null; flight: string | null; items: AtcItem[]; ja: string; tags: string[] };

// 呼び出しの名前（無線での航空会社の呼び方）→ ICAO の記号
const TEL: [string, string][] = [
  ["JAPAN AIR", "JAL"], ["JAPANAIR", "JAL"], ["ALL NIPPON", "ANA"], ["ALL NIPON", "ANA"], ["ALNIPPON", "ANA"], ["AIR JAPAN", "AJX"], ["AIR DO", "ADO"], ["AIRDO", "ADO"], ["AIR DOE", "ADO"],
  ["SKYMARK", "SKY"], ["SKY MARK", "SKY"], ["NEW SKY", "SNJ"], ["NEWSKY", "SNJ"], ["STARFLYER", "SFJ"], ["STAR FLYER", "SFJ"], ["AIR PEACH", "APJ"], ["PEACH", "APJ"],
  ["ORANGE LINER", "JJP"], ["J AIR", "JLJ"], ["JAY AIR", "JLJ"], ["JAI OCEAN", "JTA"], ["COMMUTER", "JAC"], ["FUJI DREAM", "FDA"], ["IBEX", "IBX"], ["ORIENTAL BRIDGE", "ORC"],
  ["ZIPPY", "TZP"], ["NIPPON CARGO", "NCA"],
  ["KOREAN AIR", "KAL"], ["ASIANA", "AAR"], ["AIR BUSAN", "ABL"], ["JEJU AIR", "JJA"], ["JIN AIR", "JNA"], ["TEEWAY", "TWB"], ["DYNASTY", "CAL"], ["EVA", "EVA"], ["CATHAY", "CPA"],
  ["AIR CHINA", "CCA"], ["CHINA EASTERN", "CES"], ["CHINA SOUTHERN", "CSN"], ["THAI", "THA"], ["SINGAPORE", "SIA"], ["SCOOTER", "TGW"], ["PHILIPPINE", "PAL"],
  ["UNITED", "UAL"], ["AMERICAN", "AAL"], ["DELTA", "DAL"], ["HAWAIIAN", "HAL"], ["QANTAS", "QFA"],
];
// 音声認識AIが航空会社の記号で書いたとき（"JAL 123"・"ANA106"）
const ICAO = new Set(["JAL", "ANA", "AJX", "ADO", "SKY", "SNJ", "SFJ", "APJ", "JJP", "JLJ", "JTA", "JAC", "FDA", "IBX", "ORC", "TZP", "NCA", "KAL", "AAR", "ABL", "JJA", "JNA", "TWB",
  "CAL", "EVA", "CPA", "CCA", "CES", "CSN", "THA", "SIA", "TGW", "PAL", "UAL", "AAL", "DAL", "HAL", "QFA"]);
const NUM: Record<string, string> = { ZERO: "0", OH: "0", ONE: "1", WUN: "1", TWO: "2", TOO: "2", THREE: "3", TREE: "3", FOUR: "4", FOWER: "4", FIVE: "5", FIFE: "5",
  SIX: "6", SEVEN: "7", EIGHT: "8", AIT: "8", NINE: "9", NINER: "9" };
const PHON: Record<string, string> = { ALPHA: "A", ALFA: "A", BRAVO: "B", CHARLIE: "C", DELTA: "D", ECHO: "E", FOXTROT: "F", GOLF: "G", HOTEL: "H", INDIA: "I",
  JULIET: "J", JULIETT: "J", KILO: "K", LIMA: "L", MIKE: "M", NOVEMBER: "N", OSCAR: "O", PAPA: "P", QUEBEC: "Q", ROMEO: "R", SIERRA: "S", TANGO: "T",
  UNIFORM: "U", VICTOR: "V", WHISKEY: "W", WHISKY: "W", XRAY: "X", YANKEE: "Y", ZULU: "Z" };
const UNIT: Record<string, string> = { TOWER: "タワー", GROUND: "グランド", APPROACH: "アプローチ", DEPARTURE: "ディパーチャー", RAMP: "ランプ", DELIVERY: "デリバリー", RADAR: "レーダー", CONTROL: "コントロール" };

// 大文字に、記号を空白に、数の言葉を数字に、続く数字をつなぐ（"ONE TWO THREE" → "123"）。"4 THOUSAND 5 HUNDRED" → "4500"
export function normalize(text: string): string {
  let t = ` ${String(text ?? "").toUpperCase().replace(/X-RAY/g, "XRAY").replace(/(\d)\.(\d)/g, "$1 DECIMAL $2").replace(/[^A-Z0-9 ]+/g, " ")} `;
  // 文字と数字がくっついたものを分ける（"JAL123" → "JAL 123"、"34R" → "34 R"、"FL350" → "FL 350"）
  t = t.replace(/([A-Z])(\d)/g, "$1 $2").replace(/(\d)([A-Z])/g, "$1 $2");
  t = t.split(/\s+/).map((w) => NUM[w] ?? w).join(" ");
  t = t.replace(/(\d) POINT (\d)/g, "$1 DECIMAL $2").replace(/\bRWY\b/g, "RUNWAY").replace(/\bFL (\d)/g, "FLIGHT LEVEL $1").replace(/\bTAKE OFF\b/g, "TAKEOFF")
    .replace(/\bCLEAR (TO LAND|FOR TAKEOFF)\b/g, "CLEARED $1").replace(/\bHOLDING SHORT\b/g, "HOLD SHORT");
  for (let i = 0; i < 5; i++) t = t.replace(/\b(\d+) (\d)\b/g, "$1$2");
  t = t.replace(/\b(\d+) THOUSAND(?: (\d) HUNDRED)?/g, (_m, a, b) => String(Number(a) * 1000 + (b ? Number(b) * 100 : 0)));
  t = t.replace(/\b(\d+) HUNDRED\b/g, (_m, a) => String(Number(a) * 100));
  return t.replace(/\s+/g, " ").trim();
}
const rwyOf = (n: string, side?: string) => {
  const d = n.padStart(2, "0"); if (!/^(0[1-9]|[12]\d|3[0-6])$/.test(d)) return null;
  const s = (side ?? "").charAt(0); return d + (s === "L" || s === "R" || s === "C" ? s : "");
};
const RWY = "RUNWAY (\\d{1,2})(?: (LEFT|RIGHT|CENTER|CENTRE|L|R|C)\\b)?";
// 誘導路の名前（"CHARLIE 5" → C5、"C5" → C5）の並び
function taxiRefs(seg: string): string[] {
  const out: string[] = [];
  const w = seg.split(" ").filter(Boolean);
  for (let i = 0; i < w.length; i++) {
    const x = w[i], L = PHON[x] ?? (/^[A-Z]\d{0,2}$/.test(x) ? x : null);
    if (!L) { if (/^(AND|THEN|TO|VIA|ON|RIGHT|LEFT|TURN)$/.test(x)) continue; break; }
    if (/^[A-Z]$/.test(L) && /^\d{1,2}$/.test(w[i + 1] ?? "")) { out.push(L + w[i + 1]); i++; } else out.push(L);
  }
  return out.slice(0, 8);
}
function callsignOf(t: string): string | null {
  for (const [name, icao] of TEL) {
    const m = new RegExp(`\\b${name}(?:LINES|WAYS| AIRLINES| AIRWAYS| AIR LINES)? (\\d{1,4})(?: ([A-Z]+))?\\b`).exec(t);
    if (m) return icao + m[1] + (m[2] && PHON[m[2]] ? PHON[m[2]] : "");
  }
  const m = /\b([A-Z]{3}) (\d{1,4})\b/.exec(t);
  return m && ICAO.has(m[1]) ? m[1] + m[2] : null;
}

export function parseAtc(text: string): AtcParsed {
  const t = normalize(text), items: AtcItem[] = [];
  const cs = callsignOf(t), fl = cs ? flightOfCallsign(cs) : null;
  const rw = (re: string) => { const m = new RegExp(re + " " + RWY).exec(t) ?? new RegExp(RWY + " " + re).exec(t); return m ? rwyOf(m[1] ?? m[m.length - 2], m[2] ?? m[m.length - 1]) : null; };
  const anyRwy = () => { const m = new RegExp(RWY).exec(t); return m ? rwyOf(m[1], m[2]) : null; };
  if (/\bCLEARED TO LAND\b/.test(t)) items.push({ k: "land", rwy: rw("CLEARED TO LAND") ?? anyRwy() });
  if (/\bCLEARED FOR TAKE ?OFF\b/.test(t)) items.push({ k: "takeoff", rwy: rw("CLEARED FOR TAKE ?OFF") ?? anyRwy() });
  if (/\bLINE ?UP AND WAIT\b/.test(t)) items.push({ k: "lineup", rwy: anyRwy() });
  if (/\bGO AROUND\b|\bGOING AROUND\b|\bEXECUTE MISSED APPROACH\b/.test(t)) items.push({ k: "goaround", rwy: null });
  if (/\bCONTINUE APPROACH\b/.test(t)) items.push({ k: "contapp", rwy: anyRwy() });
  if (/\bPUSH ?BACK (AND START UP )?APPROVED\b/.test(t)) items.push({ k: "push" });
  // 進入の許可："CLEARED ILS Z APPROACH RUNWAY 34 L" と、日本でよく使う "CLEARED ILS Z RUNWAY 34 L APPROACH" の両方
  const ap = /\bCLEARED (?:FOR )?(?:THE )?(ILS|RNAV|RNP|LDA|VOR|VISUAL)(?: [XYZ])?(?: (?:RUNWAY )?(\d{1,2})(?: (LEFT|RIGHT|CENTER|L|R|C)\b)?)? APPROACH(?: (?:RUNWAY )?(\d{1,2})(?: (LEFT|RIGHT|CENTER|L|R|C)\b)?)?/.exec(t);
  if (ap) items.push({ k: "app", type: ap[1], rwy: ap[2] ? rwyOf(ap[2], ap[3]) : ap[4] ? rwyOf(ap[4], ap[5]) : null });
  const ti = t.search(/\bTAXI\b/);
  if (ti >= 0) {
    const seg = t.slice(ti).replace(/ (HOLD SHORT|CROSS|CONTACT|MONITOR)\b.*$/, "");
    const sp = /\bSPOT (\d{1,3})\b/.exec(seg), rr = new RegExp(RWY).exec(seg.split(" VIA ")[0]) ?? new RegExp("\\bTO " + RWY).exec(seg);
    const to = sp ? `SPOT ${sp[1]}` : rr ? rwyOf(rr[1], rr[2]) : null;
    const vi = seg.indexOf(" VIA "), via = vi >= 0 ? taxiRefs(seg.slice(vi + 5)) : [];
    if (to || via.length) items.push({ k: "taxi", to, via });
  }
  for (const m of t.matchAll(/\bHOLD SHORT(?: OF)? (?:RUNWAY (\d{1,2})(?: (LEFT|RIGHT|CENTER|L|R|C)\b)?|([A-Z]+(?: \d{1,2})?))/g)) {
    const at = m[1] ? rwyOf(m[1], m[2]) : taxiRefs(m[3] ?? "")[0] ?? null; if (at) items.push({ k: "hold", at: m[1] ? `RWY ${at}` : at });
  }
  for (const m of t.matchAll(new RegExp("\\bCROSS " + RWY, "g"))) { const r = rwyOf(m[1], m[2]); if (r) items.push({ k: "cross", rwy: r }); }
  const ct = /\b(?:CONTACT|MONITOR) (?:[A-Z]+ )?(TOWER|GROUND|APPROACH|DEPARTURE|RAMP|DELIVERY|RADAR|CONTROL)(?: (\d{3}) DECIMAL (\d{1,3}))?/.exec(t);
  if (ct) items.push({ k: "contact", unit: ct[1], freq: ct[2] ? `${ct[2]}.${ct[3]}` : null });
  const al = /\b(CLIMB|DESCEND)(?: AND MAINTAIN| TO)? (?:FLIGHT LEVEL (\d{2,3})|(\d{3,5})(?: FEET)?)\b/.exec(t) ?? /\b(MAINTAIN) (?:FLIGHT LEVEL (\d{2,3})|(\d{3,5}) FEET)\b/.exec(t);
  if (al) items.push({ k: "alt", dir: al[1] === "CLIMB" ? "up" : al[1] === "DESCEND" ? "down" : "keep", fl: al[2] ? Number(al[2]) : null, ft: al[3] ? Number(al[3]) : null });
  const hd = /\b(?:TURN (LEFT|RIGHT) )?(?:FLY )?HEADING (\d{3})\b/.exec(t);
  if (hd && Number(hd[2]) <= 360) items.push({ k: "hdg", turn: hd[1] ? (hd[1].charAt(0) as "L" | "R") : null, deg: Number(hd[2]) });
  const sp = /\b(?:REDUCE |INCREASE |MAINTAIN )?SPEED (?:TO )?(\d{3})(?: KNOTS)?\b/.exec(t) ?? /\b(?:REDUCE TO |INCREASE TO |MAINTAIN )(\d{3}) KNOTS\b/.exec(t);
  if (sp && Number(sp[1]) >= 120 && Number(sp[1]) <= 350) items.push({ k: "spd", kt: Number(sp[1]) });
  const wd = /\bWIND (?:(\d{3})(?: DEGREES)?|CALM|VARIABLE)(?: (?:AT )?(\d{1,2}))?/.exec(t);
  if (wd && wd[2]) items.push({ k: "wind", deg: wd[1] ? Number(wd[1]) : null, kt: Number(wd[2]) });
  return { callsign: cs, flight: fl && /^[A-Z0-9]{2}[0-9]{1,4}$/.test(fl) ? fl : null, items, ja: toJa(items), tags: tagsOf(items) };
}

const RJ = (r?: string | null) => r ? `${r}滑走路` : "滑走路";
export function toJa(items: AtcItem[]): string {
  const s: string[] = [];
  for (const i of items) {
    switch (i.k) {
      case "land": s.push(`${RJ(i.rwy)}への着陸を許可。`); break;
      case "takeoff": s.push(`${RJ(i.rwy)}からの離陸を許可。`); break;
      case "lineup": s.push(`${RJ(i.rwy)}に入って待機。`); break;
      case "goaround": s.push("ゴーアラウンド（着陸をやめて上昇）。"); break;
      case "contapp": s.push("そのまま進入を続ける。"); break;
      case "push": s.push("プッシュバック（後ろへ押し出す）を許可。"); break;
      case "app": s.push(`${i.type === "VISUAL" ? "目で見ての" : i.type + "の"}進入を許可${i.rwy ? `（${i.rwy}滑走路）` : ""}。`); break;
      case "taxi": s.push(`${i.to ? (i.to.startsWith("SPOT") ? `スポット ${i.to.slice(5)} へ` : `${i.to}滑走路へ`) : "地上走行"}${i.via.length ? `。誘導路 ${i.via.join("・")} を通る` : ""}。`); break;
      case "hold": s.push(`${i.at.startsWith("RWY") ? i.at.slice(4) + "滑走路" : "誘導路 " + i.at}の手前で待機。`); break;
      case "cross": s.push(`${i.rwy}滑走路を横切ってよい。`); break;
      case "contact": s.push(`${UNIT[i.unit] ?? i.unit}${i.freq ? `（${i.freq}）` : ""}に切り替え。`); break;
      case "alt": s.push(`${i.fl ? `高度 FL${i.fl}` : `高度 ${(i.ft ?? 0).toLocaleString("en-US")}ft`}${i.dir === "up" ? "まで上昇" : i.dir === "down" ? "まで降下" : "を保つ"}。`); break;
      case "hdg": s.push(`${i.turn === "L" ? "左に旋回して" : i.turn === "R" ? "右に旋回して" : ""}${String(i.deg).padStart(3, "0")}度の方向へ。`); break;
      case "spd": s.push(`速度 ${i.kt}ノットに。`); break;
      case "wind": s.push(`風は${i.deg != null ? `${String(i.deg).padStart(3, "0")}度から` : ""}${i.kt}ノット。`); break;
    }
  }
  return s.join("");
}
function tagsOf(items: AtcItem[]): string[] {
  const T: Record<string, string> = { land: "着陸許可", takeoff: "離陸許可", lineup: "滑走路で待機", goaround: "ゴーアラウンド", taxi: "地上走行", hold: "手前で待機", cross: "横切り", app: "進入許可", alt: "高度", hdg: "方向", spd: "速度", contact: "周波数の切り替え", push: "プッシュバック" };
  return [...new Set(items.map((i) => T[i.k]).filter(Boolean))].slice(0, 4);
}
