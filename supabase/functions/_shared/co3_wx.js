// エアライン経営 co-v3：気象通報（METAR）の原文と風・視程から、その時間の天気（雪・強風・霧・雷）を読む（co3-weather 関数と試験で使う）
//   雪・凍った雨：SN・PL・GS（シャワー・地吹雪を含む）、FZRA・FZDZ
//   強風：平均 25ノット以上か、最大瞬間 35ノット以上
//   霧：視程 800m 未満か、FG（浅い霧・霧の切れ間・凍った霧を含む）
//   雷：TS（近くの雷を含む）
export function wxFlags(m) {
  const wx = ` ${String((m && m.raw) || "")} `.replace(/\sRMK\s.*$/, " ");   // 備考の欄は読まない
  return {
    snow: /\s[-+]?(?:VC)?(?:SH|BL|DR)?(?:RA|DZ)?(?:SN|PL|GS)(?=\s|[A-Z])|\s[-+]?FZ(?:RA|DZ)/.test(wx),
    wind: (m.wspd ?? 0) >= 25 || (m.wgst ?? 0) >= 35,
    fog: (m.vis_m != null && m.vis_m < 800) || /\s(?:MI|BC|PR|FZ)?FG\s/.test(wx),
    ts: /\s[-+]?(?:VC)?TS/.test(wx),
  };
}
