-- 番外編の判定範囲を「近づかずに公道から押せる」形に広げる（案。PM が見てから出す。本人の OK：11/26）
--   作り方：tools/extra_safe_range.py（敷地の端の見込み＝中心から滑走路のいちばん遠い端＋種類ごとの余白。今より小さくはしない）
--   一覧と理由：docs/pm/report-extra-safe-range.md
--   番外編（game_target でない・extra_kind のある行）だけを変える。86空港の radius_m は変えない（経営の airport_size・co_size は動かない）
--   今の値が案を作ったときと違う行は変えない（手で直した値を上書きしない）
--   RLS・権限は airports の今のまま（だれでも読める・anon / authenticated は書けない）
--   影響：チェックイン（番外編の印を押せる範囲が少し広がる）。経営は関係しない（番外編は便にも路線にもならない）

update public.airports a set radius_m = v.new_m
  from (values
  (1001, 2000, 2700),
  (1006, 2000, 2800),
  (1021, 1500, 1700),
  (1022, 1500, 1700),
  (1015, 2000, 2200),
  (1029, 2000, 2600),
  (76, 1000, 1100),
  (89, 1500, 1600),
  (3017, 800, 900),
  (3020, 800, 1100)
  ) as v(id, old_m, new_m)
 where a.id = v.id and a.radius_m = v.old_m and a.extra_kind is not null and not a.game_target;
