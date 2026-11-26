-- 三沢空港・岩国空港の民間ターミナルを判定の範囲に入れる（本人の OK：11/26。CLAUDE.md の 11/26 の決定）
--   わけ：どちらも空港の点（airports）が滑走路のあたりにあり、民間のターミナルビルが判定の円（半径 1,500m）の外にある
--         （三沢 1,821m・岩国 1,779m。docs/pm/ap-shape-compare.md・report-ap-shape.md）
--   やり方：terminals に1行ずつ足す。判定は「ターミナルから 800m 以内も空港の範囲」（judge.ts の termRadiusM）なので、ビルのまわりが範囲に入る
--   ・airports の radius_m は変えない（経営の airport_size・co_size に効くので、経営の数字は動かない）
--   ・ターミナルの印は出さない：stamp_m = 0（ターミナルの印は「stamp_m 以内」のときだけ。0 は範囲を広げるだけの行の印）
--     そのため stamp_m の制約を 100〜1500 から 0〜1500 に広げる（今の行の値は変えない）
--   座標の根拠：国土数値情報「空港データ」（C28）のターミナルビルの位置（製品仕様書 第3.0版の terminalBuilding「ターミナルビルの位置」）。
--     小数4桁（約10m）に丸めた。C28 の使用許諾条件は未確認なので、反映の前に本人が確かめる（report-term-misawa-iwakuni.md の 3）
--   RLS：terminals の今の決まりのまま（だれでも読める・anon / authenticated は書けない）。権限も変えない
--   影響：チェックイン（三沢・岩国のターミナルビルで印が押せるようになる）。経営は関係しない

alter table public.terminals drop constraint if exists terminals_stamp_m_check;
alter table public.terminals add constraint terminals_stamp_m_check check (stamp_m between 0 and 1500);

insert into public.terminals (id, airport_id, short, name, tag, lat, lon, stamp_m) values
  ('MSJ-T', 92, '三沢', 'ターミナルビル', 'ビル', 40.6966, 141.3878, 0),
  ('IWK-T', 96, '岩国', 'ターミナルビル', 'ビル', 34.1588, 132.2351, 0)
on conflict (id) do nothing;
