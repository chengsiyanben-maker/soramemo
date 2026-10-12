-- 実際に飛んだ航路：運航を確認できた便について、OpenSky の航跡を間引いて残す（地図にその線を描く）
--   形：[[緯度, 経度], ...]（2〜200点）。書くのはサーバーの照合（verify-flights）だけ。利用者は自分のフライトの分を読める（既存の select の決まりのまま）
alter table public.flights add column if not exists track jsonb
  check (track is null or (jsonb_typeof(track) = 'array' and jsonb_array_length(track) between 2 and 200));
