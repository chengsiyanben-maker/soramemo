// エアライン経営 co-v3：気象庁の「台風解析・予報情報（５日予報）」（防災情報XML の VPTW61）を読み、
// 予報の進路（中心の位置）が、ある日にその空港の近くを通るかを決める（co3-typhoon 関数と試験で使う）
//   出典：気象庁ホームページ（防災情報XML）。ゲームで「近づきそう」を決めるために加工して使う
//   ・進路は、実況と予報の中心の位置を時刻で直線につないだもの（予報円の大きさは見ない）
//   ・「台風」の階級の点から先だけを見る（熱帯低気圧・温帯低気圧に変わったあとは見ない）
//   ・訓練・試験の電文、取り消しの電文は使わない

// 防災情報XML の一覧（随時の情報）から、台風の電文の URL を台風ごとに1つ（いちばん新しいもの）だけ取る
export function typhoonFeedUrls(feedXml) {
  const out = new Map();
  for (const e of String(feedXml || "").split(/<entry>/).slice(1)) {
    const title = (e.match(/<title>([^<]*)<\/title>/) || [])[1] || "";
    if (!title.startsWith("台風解析・予報情報")) continue;
    const url = (e.match(/<id>([^<]*VPTW6[0-9]_[^<]*\.xml)<\/id>/) || [])[1];
    const upd = (e.match(/<updated>([^<]*)<\/updated>/) || [])[1] || "";
    if (!url || !/^https:\/\/www\.data\.jma\.go\.jp\//.test(url)) continue;
    // 同じ台風の電文の見分けは本文を読むまでわからないので、URL ごとに残し、本文の EventID で絞る
    out.set(url, upd);
  }
  return [...out.entries()].sort((a, b) => (a[1] < b[1] ? 1 : -1)).map(([u]) => u);
}

const tag = (s, name) => { const m = s.match(new RegExp(`<${name}>([^<]*)</${name}>`)); return m ? m[1].trim() : null; };
const coord = (v) => { const m = String(v || "").match(/^([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)/); return m ? [Number(m[1]), Number(m[2])] : null; };

// 電文1つを読む。使えない電文（訓練・取り消し・形が違う）は null
export function parseTyphoon(xml) {
  const s = String(xml || "");
  const control = (s.match(/<Control>([\s\S]*?)<\/Control>/) || [])[1] || "";
  if (tag(control, "Status") !== "通常") return null;
  const head = (s.match(/<Head\b[\s\S]*?<\/Head>/) || [])[0] || "";
  const event = tag(head, "EventID"), reported = tag(head, "ReportDateTime"), infoType = tag(head, "InfoType");
  if (!event || !/^TC\d{4}$/.test(event) || !reported) return null;
  if (infoType === "取消") return { event, reported, cancelled: true, name: null, number: null, points: [] };
  const name = tag(s, "Name"), number = tag(s, "Number");
  const points = [];
  for (const blk of s.split(/<MeteorologicalInfo>/).slice(1)) {
    const dt = (blk.match(/<DateTime type="([^"]*)">([^<]*)<\/DateTime>/) || []);
    const t = Date.parse(dt[2] || "");
    if (!Number.isFinite(t)) continue;
    const cls = (blk.match(/<jmx_eb:TyphoonClass[^>]*>([^<]*)</) || [])[1] || "";
    const pos = coord((blk.match(/<jmx_eb:(?:Coordinate|BasePoint)[^>]*type="中心位置（度）"[^>]*>([^<]*)</) || [])[1]);
    if (!pos) continue;
    points.push({ t, lat: pos[0], lon: pos[1], typhoon: cls.startsWith("台風"), kind: (dt[1] || "").startsWith("実況") ? "now" : "fcst" });
  }
  points.sort((a, b) => a.t - b.t);
  return { event, reported, cancelled: false, name, number, points };
}

// 2点の距離（km）
export function distKm(lat1, lon1, lat2, lon2) {
  const r = Math.PI / 180, a = Math.sin((lat2 - lat1) * r / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin((lon2 - lon1) * r / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.min(1, Math.sqrt(a)));
}

// 日本時間の日付（YYYY-MM-DD）
export const jstDay = (ms) => new Date(ms + 9 * 3600_000).toISOString().slice(0, 10);

// 進路が、空港から radiusKm 以内を通る日（日本時間）を空港ごとに返す。{ HND: ["2026-10-30"], ... }
//   進路は30分ごとに見る。台風の階級の点から次の点までの間だけ（最後の点が台風なら、その点だけ）
export function approachDays(storm, airports, radiusKm = 300) {
  const out = {};
  if (!storm || storm.cancelled) return out;
  const pts = storm.points || [];
  const samples = [];
  for (let i = 0; i < pts.length; i++) {
    const p = pts[i], q = pts[i + 1];
    if (!p.typhoon) continue;
    if (!q) { samples.push(p); continue; }
    const steps = Math.max(1, Math.ceil((q.t - p.t) / 1800_000));
    for (let k = 0; k < steps; k++) {
      const f = k / steps;
      samples.push({ t: p.t + (q.t - p.t) * f, lat: p.lat + (q.lat - p.lat) * f, lon: p.lon + (q.lon - p.lon) * f });
    }
    if (!q.typhoon) samples.push(q);
  }
  for (const a of airports || []) {
    if (!a || !/^[A-Z]{3}$/.test(a.iata || "") || !Number.isFinite(a.lat) || !Number.isFinite(a.lon)) continue;
    const days = new Set();
    for (const s of samples) if (distKm(a.lat, a.lon, s.lat, s.lon) <= radiusKm) days.add(jstDay(s.t));
    if (days.size) out[a.iata] = [...days].sort();
  }
  return out;
}

// 台風ごとにいちばん新しい電文だけ残す
export function latestPerEvent(storms) {
  const m = new Map();
  for (const s of storms || []) {
    if (!s) continue;
    const cur = m.get(s.event);
    if (!cur || Date.parse(s.reported) > Date.parse(cur.reported)) m.set(s.event, s);
  }
  return [...m.values()];
}
