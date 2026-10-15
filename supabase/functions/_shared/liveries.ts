// 特別塗装機の一覧（登録記号 → 名前）。いま飛んでいるかを adsb.lol の登録記号（r）で見つけ、運用タブ・「空港のいま」に出す。
// 出典：航空会社の公式ページを優先し、公式に登録記号が書かれていないものは、登録記号を明記した航空専門の報道（Aviation Wire・TRAICY など）。
// 海外の航空会社の機体も、日本に乗り入れている便に使われるものは入れる（2026-10-15）。
// 特別塗装は期間限定のものが多い。終わったものは消し、新しいものは出典を付けて足す（運航期間の終わりが分かっているものは until に書く）。
export type Livery = { reg: string; name: string; airline: string; src: string; until?: string };

export const LIVERIES: Livery[] = [
  { reg: "JA819A", name: "ポケモンジェット 赤", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/promotion/pokemonjet/" },
  { reg: "JA923A", name: "ポケモンジェット 緑", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/promotion/pokemonjet/" },
  { reg: "JA56AN", name: "ポケモンジェット 青", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/promotion/pokemonjet/" },
  { reg: "JA894A", name: "ピカチュウジェットNH", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/international/theme/pikachujet/" },
  { reg: "JA784A", name: "イーブイジェットNH", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/international/theme/pikachujet/" },
  { reg: "JA381A", name: "FLYING HONU（青）", airline: "ANA", src: "https://www.aviationwire.jp/archives/208555" },
  { reg: "JA382A", name: "FLYING HONU（緑）", airline: "ANA", src: "https://www.aviationwire.jp/archives/208555" },
  { reg: "JA383A", name: "FLYING HONU（オレンジ）", airline: "ANA", src: "https://www.aviationwire.jp/archives/208555" },
  { reg: "JA339J", name: "JAL Jubilee Express", airline: "JAL", src: "https://press.jal.co.jp/ja/release/202604/009482.html", until: "2027-04-30" },
  { reg: "JA01XJ", name: "A350 1号機（赤のロゴ）", airline: "JAL", src: "https://www.aviationwire.jp/archives/173663" },
  { reg: "JA02XJ", name: "A350 2号機（銀のロゴ）", airline: "JAL", src: "https://www.aviationwire.jp/archives/173663" },
  { reg: "JA03XJ", name: "A350 3号機（緑のロゴ）", airline: "JAL", src: "https://www.aviationwire.jp/archives/173663" },
  { reg: "JA05RK", name: "ジンベエジェット", airline: "JTA", src: "https://www.aviationwire.jp/archives/336787" },
  { reg: "JA06RK", name: "さくらジンベエ", airline: "JTA", src: "https://www.aviationwire.jp/archives/336787" },
  { reg: "JA07RK", name: "結ジンベエ", airline: "JTA", src: "https://www.aviationwire.jp/archives/336787" },
  { reg: "JA73AB", name: "ピカチュウジェットBC1", airline: "スカイマーク", src: "https://www.aviationwire.jp/archives/344457" },
  { reg: "JA73NG", name: "ピカチュウジェットBC2", airline: "スカイマーク", src: "https://www.aviationwire.jp/archives/344457" },
  { reg: "JA607A", name: "ロコンジェット", airline: "AIRDO", src: "https://www.aviationwire.jp/archives/tag/ja607a" },
  { reg: "JA803X", name: "ナッシージェット", airline: "ソラシドエア", src: "https://www.aviationwire.jp/archives/tag/ja803x" },
  // 海外の航空会社（日本に乗り入れている便に使われるもの。登録記号は adsb.lol の r と同じ書き方：9V-OJJ・B-18101 など）
  { reg: "9V-OJJ", name: "ピカチュウジェットTR", airline: "スクート", src: "https://www.aviationwire.jp/archives/258613" },
  { reg: "B-18101", name: "ピカチュウジェットCI", airline: "チャイナエアライン", src: "https://www.aviationwire.jp/archives/261093" },
  { reg: "B-18916", name: "ピカチュウジェットCI2", airline: "チャイナエアライン", src: "https://www.traicy.com/posts/20260402366966/" },
  { reg: "B-LRJ", name: "80周年記念塗装（A350）", airline: "キャセイパシフィック航空", src: "https://en.traicy.com/posts/2026021032635/" },
  { reg: "B-LJE", name: "80周年記念塗装（747貨物機）", airline: "キャセイパシフィック航空", src: "https://en.traicy.com/posts/2026021032635/" },
  { reg: "D-AIFA", name: "100周年記念塗装（A350-1000）", airline: "ルフトハンザ", src: "https://newsroom.lufthansagroup.com/en/lufthansas-first-airbus-a350-1000-arrives-with-a-special-livery/" },
  // 日本便に使われる機種（A380・777・787・A350）の特別塗装機。日本の上空で見えたときだけ表示に出る
  { reg: "A6-EVG", name: "UAE国旗塗装（A380）", airline: "エミレーツ航空", src: "https://en.traicy.com/posts/2026050835328/" },
  { reg: "N91007", name: "Stars and Stripes（787-10）", airline: "ユナイテッド航空", src: "https://www.flightradar24.com/blog/flight-tracking-news/special-aircraft-tracking/united-adds-two-stars-and-stripes-special-livery-aircraft/" },
  { reg: "N735AT", name: "Flagship 100周年塗装（777-300ER）", airline: "アメリカン航空", src: "https://news.aa.com/centennial/our-stories/flagship-livery/" },
  { reg: "N527DN", name: "100周年記念塗装（A350）", airline: "デルタ航空", src: "https://airlinegeeks.com/2025/03/17/delta-officially-debuts-100-year-livery/" },
  { reg: "A7-BEH", name: "FIFAワールドカップ2026塗装（777-300ER）", airline: "カタール航空", src: "https://en.traicy.com/posts/2026052635894/" },
  { reg: "VH-ZND", name: "Emily Kame Kngwarreye（787-9）", airline: "カンタス航空", src: "https://www.qantas.com/au/en/about-us/our-company/fleet/flying-art.html" },
];

// アライアンスの塗装機（スターアライアンス・ワンワールド）。日本に乗り入れている会社の機体だけ。
// 出典：日本の会社は Aviation Wire。海外の会社は Flightradar24 のアライアンス塗装機の一覧（2020年11月更新）から、
// 退役した機種（747・A340 など）と日本に来ない小さな機体を除いたもの。塗り替え・退役で古くなっているものもあるが、見えなければ表示に出ないだけ
const AW_ANA = "https://www.aviationwire.jp/archives/156984", AW_JAL = "https://www.aviationwire.jp/archives/247025";
const FR24_ALLIANCE = "https://www.flightradar24.com/blog/flight-tracking-news/special-aircraft-tracking/tracking-special-alliance-liveries/";
const ALLIANCE: [string, string, string, string][] = [   // 登録記号・航空会社・機種・出典
  ["JA899A", "ANA", "787-9", AW_ANA], ["JA731A", "ANA", "777-300ER", AW_ANA], ["JA711A", "ANA", "777-200", AW_ANA], ["JA712A", "ANA", "777-200", AW_ANA],
  ["JA614A", "ANA", "767-300ER", AW_ANA], ["JA51AN", "ANA", "737-800", AW_ANA],
  ["B-16206", "エバー航空", "A321", FR24_ALLIANCE], ["B-16701", "エバー航空", "777-300ER", FR24_ALLIANCE],
  ["B-6091", "中国国際航空", "A330-200", FR24_ALLIANCE], ["B-6093", "中国国際航空", "A330-200", FR24_ALLIANCE], ["B-2032", "中国国際航空", "777-300ER", FR24_ALLIANCE],
  ["VT-ALJ", "エア・インディア", "777-300ER", FR24_ALLIANCE], ["VT-ANU", "エア・インディア", "787-8", FR24_ALLIANCE],
  ["C-GHLM", "エア・カナダ", "A330-300", FR24_ALLIANCE], ["HL7730", "アシアナ航空", "A321", FR24_ALLIANCE],
  ["B-6296", "深圳航空", "A320", FR24_ALLIANCE], ["B-6297", "深圳航空", "A320", FR24_ALLIANCE],
  ["9V-SWI", "シンガポール航空", "777-300ER", FR24_ALLIANCE], ["9V-SWJ", "シンガポール航空", "777-300ER", FR24_ALLIANCE], ["9V-SRI", "シンガポール航空", "777-200", FR24_ALLIANCE],
  ["HS-TEL", "タイ国際航空", "A330-300", FR24_ALLIANCE],
  ["N76021", "ユナイテッド航空", "777-200", FR24_ALLIANCE], ["N77022", "ユナイテッド航空", "777-200", FR24_ALLIANCE], ["N78017", "ユナイテッド航空", "777-200", FR24_ALLIANCE],
  ["N218UA", "ユナイテッド航空", "777-200", FR24_ALLIANCE], ["N794UA", "ユナイテッド航空", "777-200", FR24_ALLIANCE],
  ["JA861J", "JAL", "787-9", AW_JAL], ["JA15XJ", "JAL", "A350-900", AW_JAL], ["JA13HC", "北海道エアシステム", "ATR42-600", AW_JAL], ["JA604J", "JAL", "767-300", FR24_ALLIANCE],
  ["N791AN", "アメリカン航空", "777-200", FR24_ALLIANCE], ["N796AN", "アメリカン航空", "777-200", FR24_ALLIANCE],
  ["B-KPL", "キャセイパシフィック航空", "777-300ER", FR24_ALLIANCE], ["B-HLU", "キャセイパシフィック航空", "A330-300", FR24_ALLIANCE],
  ["VH-EBL", "カンタス航空", "A330-200", FR24_ALLIANCE], ["VH-EBV", "カンタス航空", "A330-200", FR24_ALLIANCE],
  ["A7-BAA", "カタール航空", "777-300ER", FR24_ALLIANCE], ["A7-BAB", "カタール航空", "777-300ER", FR24_ALLIANCE], ["A7-BAF", "カタール航空", "777-300ER", FR24_ALLIANCE], ["A7-BAG", "カタール航空", "777-300ER", FR24_ALLIANCE],
  ["9M-MTE", "マレーシア航空", "A330-300", FR24_ALLIANCE], ["9M-MTO", "マレーシア航空", "A330-300", FR24_ALLIANCE], ["4R-ALH", "スリランカ航空", "A330-200", FR24_ALLIANCE],
];
const ONEWORLD = new Set(["JAL", "北海道エアシステム", "アメリカン航空", "キャセイパシフィック航空", "カンタス航空", "カタール航空", "マレーシア航空", "スリランカ航空"]);
for (const [reg, airline, type, src] of ALLIANCE) {
  if (LIVERIES.some((l) => l.reg === reg)) continue;
  LIVERIES.push({ reg, airline, src, name: `${ONEWORLD.has(airline) ? "ワンワールド" : "スターアライアンス"}塗装（${type}）` });
}

// 期間が過ぎたものを除いた、登録記号 → 特別塗装機
export function liveryMap(now = new Date()): Map<string, Livery> {
  const day = now.toISOString().slice(0, 10);
  return new Map(LIVERIES.filter((l) => !l.until || l.until >= day).map((l) => [l.reg, l]));
}
