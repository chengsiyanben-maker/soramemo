// 特別塗装機の一覧（登録記号 → 名前）。いま飛んでいるかを adsb.lol の登録記号（r）で見つけ、運用タブ・「空港のいま」に出す。
// 出典：航空会社の公式ページを優先し、公式に登録記号が書かれていないものは、登録記号を明記した航空専門の報道（Aviation Wire）。
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
];

// 期間が過ぎたものを除いた、登録記号 → 特別塗装機
export function liveryMap(now = new Date()): Map<string, Livery> {
  const day = now.toISOString().slice(0, 10);
  return new Map(LIVERIES.filter((l) => !l.until || l.until >= day).map((l) => [l.reg, l]));
}
