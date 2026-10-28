// 特別塗装機の一覧（登録記号 → 名前）。いま飛んでいるかを adsb.lol の登録記号（r）で見つけ、運用タブ・「空港のいま」に出す。
// 出典：航空会社の公式ページを優先し、公式に登録記号が書かれていないものは、登録記号を明記した航空専門の報道（Aviation Wire・TRAICY など）。
// 海外の航空会社の機体も、日本に乗り入れている便に使われるものは入れる（2026-10-15）。
// 特別塗装は期間限定のものが多い。終わったものは消し、新しいものは出典を付けて足す（運航期間の終わりが分かっているものは until に書く）。
export type Livery = { reg: string; name: string; airline: string; src: string; from?: string; until?: string; kind?: "special" | "alliance" };   // kind：alliance はアライアンス塗装（通知はしない）。from：塗装が始まる日（まだ普通の塗装で飛んでいる機体を、名前で出さないため）

export const LIVERIES: Livery[] = [
  { reg: "JA819A", name: "ポケモンジェット 赤", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/promotion/pokemonjet/" },
  { reg: "JA923A", name: "ポケモンジェット 緑", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/promotion/pokemonjet/" },
  { reg: "JA56AN", name: "ポケモンジェット 青", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/promotion/pokemonjet/", from: "9999-12-31" },   // 冬に就航予定（日は未発表）。発表されたら from をその日に
  { reg: "JA894A", name: "ピカチュウジェットNH", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/international/theme/pikachujet/" },
  { reg: "JA784A", name: "イーブイジェットNH", airline: "ANA", src: "https://www.ana.co.jp/ja/jp/international/theme/pikachujet/" },
  { reg: "JA381A", name: "FLYING HONU（青）", airline: "ANA", src: "https://www.aviationwire.jp/archives/208555" },
  { reg: "JA382A", name: "FLYING HONU（緑）", airline: "ANA", src: "https://www.aviationwire.jp/archives/208555" },
  { reg: "JA383A", name: "FLYING HONU（オレンジ）", airline: "ANA", src: "https://www.aviationwire.jp/archives/208555" },
  { reg: "JA339J", name: "JAL Jubilee Express", airline: "JAL", src: "https://press.jal.co.jp/ja/release/202604/009482.html", until: "2027-04-30" },
  { reg: "JA01XJ", name: "A350 1号機（赤のロゴ）", airline: "JAL", src: "https://www.aviationwire.jp/archives/173663" },
  { reg: "JA02XJ", name: "A350 2号機（銀のロゴ）", airline: "JAL", src: "https://www.aviationwire.jp/archives/308931" },   // 2024-09 の記事でも銀のロゴ
  { reg: "JA03XJ", name: "A350 3号機（緑のロゴ）", airline: "JAL", src: "https://www.aviationwire.jp/archives/173663" },
  { reg: "JA05RK", name: "ジンベエジェット", airline: "JTA", src: "https://www.aviationwire.jp/archives/336787" },
  { reg: "JA06RK", name: "さくらジンベエ", airline: "JTA", src: "https://www.aviationwire.jp/archives/336787" },
  { reg: "JA07RK", name: "結ジンベエ", airline: "JTA", src: "https://www.aviationwire.jp/archives/336787" },
  { reg: "JA73AB", name: "ピカチュウジェットBC1", airline: "スカイマーク", src: "https://www.aviationwire.jp/archives/344457" },
  { reg: "JA73NG", name: "ピカチュウジェットBC2", airline: "スカイマーク", src: "https://www.aviationwire.jp/archives/344457" },
  { reg: "JA607A", name: "ロコンジェット", airline: "AIRDO", src: "https://www.aviationwire.jp/archives/tag/ja607a" },
  { reg: "JA803X", name: "ナッシージェット", airline: "ソラシドエア", src: "https://www.aviationwire.jp/archives/tag/ja803x" },
  // 2026-10-26 に足した国内の機体（出典の本文で登録記号を確かめたもの）
  { reg: "JA609A", name: "ちいかわジェット", airline: "ANA", src: "https://www.aviationwire.jp/archives/352660" },
  { reg: "JA58AN", name: "ふるさとJET", airline: "ANA", src: "https://www.aviationwire.jp/archives/334647" },
  { reg: "JA807X", name: "Go!forward くまもと号", airline: "ソラシドエア", src: "https://www.traicy.com/posts/20260418367997/" },
  { reg: "JA828J", name: "脱炭素PRデカール機", airline: "ZIPAIR", src: "https://www.aviationwire.jp/archives/351162", until: "2026-12-31" },   // 9/28から約3か月（目安）
  { reg: "JA14RJ", name: "むすび丸ジェット", airline: "IBEX", src: "https://www.aviationwire.jp/archives/303301" },
  { reg: "JA10RJ", name: "ベガルタ仙台ジェット", airline: "IBEX", src: "https://www.aviationwire.jp/archives/328081" },
  { reg: "JA01AM", name: "みぞか号（親子イルカ）", airline: "天草エアライン", src: "https://www.aviationwire.jp/archives/335582" },
  // FDA は機体ごとに色が違う（公式の機材のページ）
  { reg: "JA01FJ", name: "FDA ドリームレッド（1号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA02FJ", name: "FDA ライトブルー（2号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA03FJ", name: "FDA ピンク（3号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA05FJ", name: "FDA オレンジ（5号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA06FJ", name: "FDA パープル（6号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA07FJ", name: "FDA イエロー（7号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA08FJ", name: "FDA ティーグリーン（8号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA09FJ", name: "FDA ゴールド（9号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA10FJ", name: "FDA シルバー（10号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA11FJ", name: "FDA グリーン（11号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA12FJ", name: "FDA ホワイト（12号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA13FJ", name: "FDA ネイビー（13号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA14FJ", name: "FDA ワインレッド（14号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA15FJ", name: "FDA ローズピンク（15号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
  { reg: "JA16FJ", name: "FDA バイオレット（16号機）", airline: "FDA", src: "https://www.fujidream.co.jp/flight/kizai.html" },
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
  // 2026-10-26 に足した海外の機体。多くは「その会社が日本便に使う機種」というだけで入れたもの（日本の空港の近くで見えたときだけ出る）
  { reg: "B-58553", name: "AIRSORAYAMA 銀（A350-1000）", airline: "スターラックス航空", src: "https://www.aviationwire.jp/archives/349184" },
  { reg: "B-58554", name: "AIRSORAYAMA 金（A350-1000）", airline: "スターラックス航空", src: "https://www.aviationwire.jp/archives/349184" },
  { reg: "B-KQU", name: "80周年 Spirit of Hong Kong（777-300ER）", airline: "キャセイパシフィック航空", src: "https://www.aviationwire.jp/archives/341749" },
  { reg: "A7-BEG", name: "F1塗装（777-300ER）", airline: "カタール航空", src: "https://www.aviationwire.jp/archives/334196" },
  { reg: "A7-BED", name: "UEFAチャンピオンズリーグ塗装（777-300ER）", airline: "カタール航空", src: "https://www.planespotters.net/photo/news/archive/2025/05" },
  { reg: "D-AIXL", name: "100周年記念塗装（A350-900）", airline: "ルフトハンザ", src: "https://newsroom.lufthansagroup.com/en/lufthansa-anniversary-fleet-grows-now-also-includes-a320-and-a350-with-xxl-crane/" },
  { reg: "A6-EUH", name: "テニス4大大会塗装（A380）", airline: "エミレーツ航空", src: "https://www.aviationwire.jp/archives/336511" },
  { reg: "A6-EXR", name: "This Flag Will Always Fly（A350）", airline: "エミレーツ航空", src: "https://www.planespotters.net/photo/news/archive/2026/06" },
  { reg: "A6-EOE", name: "アーセナル優勝塗装（A380）", airline: "エミレーツ航空", src: "https://www.planespotters.net/photo/news/archive/2026/05" },
  { reg: "A6-EUE", name: "スカイワーズ25周年（A380）", airline: "エミレーツ航空", src: "https://www.planespotters.net/photo/news/archive/2025/10" },
  { reg: "A6-EET", name: "Emirates Courier Express（A380）", airline: "エミレーツ航空", src: "https://www.planespotters.net/photo/news/archive/2025/05" },
  { reg: "A6-EEP", name: "Emirates Airline Foundation（A380）", airline: "エミレーツ航空", src: "https://www.planespotters.net/photo/news/archive/2024/08" },
  { reg: "B-50005", name: "岡山PR ももたろう×フーちゃん", airline: "タイガーエア台湾", src: "https://www.planespotters.net/photo/news/archive/2026/06" },   // 岡山－台北線
  { reg: "B-18918", name: "カーボン柄（A350）", airline: "チャイナエアライン", src: "https://samchui.com/2018/10/23/china-airlines-receives-final-airbus-a350-with-special-livery/" },
  { reg: "HL8018", name: "大韓航空との統合の途中の塗装（A321）", airline: "アシアナ航空", src: "https://www.planespotters.net/photo/news/archive/2026/09" },
  { reg: "B-8865", name: "開放号（A330）", airline: "深圳航空", src: "https://www.planespotters.net/photo/news/archive/2026/10" },
  { reg: "9M-MTJ", name: "Visit Malaysia 塗装（A330）", airline: "マレーシア航空", src: "https://www.planespotters.net/photo/news/archive/2025/01" },
  { reg: "9M-MTL", name: "マンチェスター・ユナイテッド塗装（A330）", airline: "マレーシア航空", src: "https://www.planespotters.net/photo/news/archive/2025/05" },
  { reg: "9M-MTM", name: "ムンバイ・インディアンズ塗装（A330）", airline: "マレーシア航空", src: "https://www.planespotters.net/photo/news/archive/2026/08" },
  { reg: "9M-MAC", name: "国旗ヌガラク塗装（A350）", airline: "マレーシア航空", src: "https://malaysiaairlines.com/vn/en/news-article/2017/second-A350-XWB.html" },
  { reg: "OH-LWO", name: "ムーミン塗装（A350）", airline: "フィンエアー", src: "https://airwaysmag.com/finnair-a350s-moomin-special-livery/" },
  { reg: "OH-LWP", name: "ムーミン塗装 2（A350）", airline: "フィンエアー", src: "https://airwaysmag.com/finnair-a350s-moomin-special-livery/" },
  { reg: "VN-A868", name: "Chim Lạc 塗装（787-9）", airline: "ベトナム航空", src: "https://www.planespotters.net/photo/news/archive/2025/04" },
  { reg: "B-7349", name: "上海博物館塗装（777-300ER）", airline: "中国東方航空", src: "https://www.planespotters.net/photo/news/archive/2025/04" },
  { reg: "B-7882", name: "中国国家博物館塗装（777-300ER）", airline: "中国東方航空", src: "https://www.planespotters.net/photo/news/archive/2025/09" },
  { reg: "B-6520", name: "アジアビーチゲームズ塗装（A330）", airline: "海南航空", src: "https://www.planespotters.net/photo/news/archive/2026/01" },
  { reg: "B-16740", name: "ハローキティ Lolly Jet（777）", airline: "エバー航空", src: "https://www.planespotters.net/photo/news/archive/2024/12" },
  { reg: "B-16722", name: "ハローキティ Besties Jet（777）", airline: "エバー航空", src: "https://www.planespotters.net/photo/news/archive/2024/08" },
  { reg: "B-LHR", name: "大公報塗装（A330）", airline: "香港航空", src: "https://www.planespotters.net/photo/news/archive/2024/12" },
  { reg: "B-LPP", name: "オーシャンパーク・パンダ塗装（A320）", airline: "香港航空", src: "https://www.planespotters.net/photo/news/archive/2026/03" },
  { reg: "RP-C3510", name: "85周年ステッカー（A350-1000）", airline: "フィリピン航空", src: "https://www.planespotters.net/photo/news/archive/2025/12" },
  { reg: "TC-LHH", name: "500機目記念（A350）", airline: "ターキッシュ エアラインズ", src: "https://www.planespotters.net/photo/news/archive/2026/01" },
  { reg: "TC-JOD", name: "Nexus of the World（A330）", airline: "ターキッシュ エアラインズ", src: "https://www.planespotters.net/photo/news/archive/2026/05" },
  { reg: "C-FIVM", name: "社員表彰2026 塗装（777-300ER）", airline: "エア・カナダ", src: "https://www.planespotters.net/photo/news/archive/2026/04" },
  { reg: "N24988", name: "The future is SAF（787-9）", airline: "ユナイテッド航空", src: "https://www.planespotters.net/photo/news/archive/2024/10" },
  { reg: "N61101", name: "100周年ステッカー（787-9）", airline: "ユナイテッド航空", src: "https://www.planespotters.net/photo/news/archive/2026/03" },
  { reg: "N784HA", name: "オーロラ Global 塗装（787-9）", airline: "アラスカ航空", src: "https://www.planespotters.net/photo/news/archive/2026/01" },
  { reg: "HL8322", name: "ZEROBASEONE ステッカー", airline: "チェジュ航空", src: "https://www.planespotters.net/photo/news/archive/2026/6?page=2" },
  { reg: "A6-BMA", name: "ワーナー・ブラザース・ワールド塗装（787-10）", airline: "エティハド航空", src: "https://www.planespotters.net/photo/news/archive/2024/07" },
];

// アライアンスの塗装機（スターアライアンス・ワンワールド・スカイチーム）。日本に乗り入れている会社の機体だけ。
// 出典：日本の会社は Aviation Wire。海外の会社は Flightradar24 のアライアンス塗装機の一覧（2020年11月更新）から、
// 退役した機種（747・A340 など）と日本に来ない小さな機体を除いたもの。塗り替え・退役で古くなっているものもあるが、見えなければ表示に出ないだけ
const AW_ANA = "https://www.aviationwire.jp/archives/156984", AW_JAL = "https://www.aviationwire.jp/archives/247025";
const FR24_ALLIANCE = "https://www.flightradar24.com/blog/flight-tracking-news/special-aircraft-tracking/tracking-special-alliance-liveries/";
const PS = (m: string) => `https://www.planespotters.net/photo/news/archive/${m}`;
const ALLIANCE: [string, string, string, string, string?][] = [   // 登録記号・航空会社・機種・出典・終わる日
  // 2026-10-26：JA731A（2021年に ANA を離れた）・9V-SRI（777-200 は2021年に退役）・JA604J（JAL の今のワンワールド塗装機の一覧にない）を消した
  ["JA899A", "ANA", "787-9", AW_ANA], ["JA711A", "ANA", "777-200", AW_ANA], ["JA712A", "ANA", "777-200", AW_ANA],
  ["JA614A", "ANA", "767-300ER", AW_ANA], ["JA51AN", "ANA", "737-800", AW_ANA],
  ["B-16206", "エバー航空", "A321", FR24_ALLIANCE], ["B-16701", "エバー航空", "777-300ER", FR24_ALLIANCE],
  ["B-6091", "中国国際航空", "A330-200", FR24_ALLIANCE], ["B-6093", "中国国際航空", "A330-200", FR24_ALLIANCE], ["B-2032", "中国国際航空", "777-300ER", FR24_ALLIANCE],
  ["VT-ALJ", "エア・インディア", "777-300ER", FR24_ALLIANCE], ["VT-ANU", "エア・インディア", "787-8", FR24_ALLIANCE],
  ["C-GHLM", "エア・カナダ", "A330-300", FR24_ALLIANCE], ["HL7730", "アシアナ航空", "A321", FR24_ALLIANCE, "2026-12-16"],   // アシアナは12/17に大韓航空と統合してスカイチームへ（https://www.aviationwire.jp/archives/345972）
  ["B-6296", "深圳航空", "A320", FR24_ALLIANCE], ["B-6297", "深圳航空", "A320", FR24_ALLIANCE],
  ["9V-SWI", "シンガポール航空", "777-300ER", FR24_ALLIANCE], ["9V-SWJ", "シンガポール航空", "777-300ER", FR24_ALLIANCE],
  ["HS-TEL", "タイ国際航空", "A330-300", FR24_ALLIANCE], ["HS-TKQ", "タイ国際航空", "777-300ER", PS("2026/02")], ["HS-TEO", "タイ国際航空", "A330-300", PS("2026/02")],
  ["N76021", "ユナイテッド航空", "777-200", FR24_ALLIANCE], ["N77022", "ユナイテッド航空", "777-200", FR24_ALLIANCE], ["N78017", "ユナイテッド航空", "777-200", FR24_ALLIANCE],
  ["N218UA", "ユナイテッド航空", "777-200", FR24_ALLIANCE], ["N794UA", "ユナイテッド航空", "777-200", FR24_ALLIANCE],
  ["JA861J", "JAL", "787-9", AW_JAL], ["JA15XJ", "JAL", "A350-900", AW_JAL], ["JA13HC", "北海道エアシステム", "ATR42-600", AW_JAL],
  ["N791AN", "アメリカン航空", "777-200", FR24_ALLIANCE], ["N796AN", "アメリカン航空", "777-200", FR24_ALLIANCE],
  ["B-KPL", "キャセイパシフィック航空", "777-300ER", FR24_ALLIANCE], ["B-HLU", "キャセイパシフィック航空", "A330-300", FR24_ALLIANCE],
  ["VH-EBL", "カンタス航空", "A330-200", FR24_ALLIANCE], ["VH-EBV", "カンタス航空", "A330-200", FR24_ALLIANCE],
  ["A7-BAA", "カタール航空", "777-300ER", FR24_ALLIANCE], ["A7-BAB", "カタール航空", "777-300ER", FR24_ALLIANCE], ["A7-BAF", "カタール航空", "777-300ER", FR24_ALLIANCE], ["A7-BAG", "カタール航空", "777-300ER", FR24_ALLIANCE],
  ["9M-MTE", "マレーシア航空", "A330-300", FR24_ALLIANCE], ["9M-MTO", "マレーシア航空", "A330-300", FR24_ALLIANCE], ["4R-ALH", "スリランカ航空", "A330-200", FR24_ALLIANCE],
  ["N375HA", "ハワイアン航空", "A330-200", "https://www.aviationwire.jp/archives/346352"],
  ["VN-A897", "ベトナム航空", "A350-900", "https://vietnamtourism.vn/en/index.php/news/items/14063"],
];
const ONEWORLD = new Set(["JAL", "北海道エアシステム", "アメリカン航空", "キャセイパシフィック航空", "カンタス航空", "カタール航空", "マレーシア航空", "スリランカ航空", "ハワイアン航空"]);
const SKYTEAM = new Set(["ベトナム航空", "大韓航空", "中国東方航空", "デルタ航空", "エールフランス", "KLM"]);
for (const [reg, airline, type, src, until] of ALLIANCE) {
  if (LIVERIES.some((l) => l.reg === reg)) continue;
  const name = `${ONEWORLD.has(airline) ? "ワンワールド" : SKYTEAM.has(airline) ? "スカイチーム" : "スターアライアンス"}塗装（${type}）`;
  LIVERIES.push({ reg, airline, src, kind: "alliance", name, ...(until ? { until } : {}) });
}

// 期間が過ぎたものを除いた、登録記号 → 特別塗装機
export function liveryMap(now = new Date()): Map<string, Livery> {
  const day = now.toISOString().slice(0, 10);
  return new Map(LIVERIES.filter((l) => (!l.until || l.until >= day) && (!l.from || l.from <= day)).map((l) => [l.reg, l]));
}
