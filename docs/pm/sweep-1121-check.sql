-- 11/21 見回りの直し（data/sweep-1121）の確かめ。読むだけ。SQL Editor に貼って流す（軽い。表は十数行〜数十行）
-- ① ODPT のデータの時刻：種類と航空会社ごとの dc:date（運航情報は数分以内、時刻表は数日以内なら正常）
select feed, dc_date at time zone 'Asia/Tokyo' as dc_date_jst, fetched_at at time zone 'Asia/Tokyo' as fetched_jst, n
  from public.odpt_feed_dates order by feed;

-- ② 反映のあと：画面が読む関数の答え（{"status_at": …, "timetable_at": …}）
-- select public.odpt_feed_at();

-- ③ 機体の位置の置き場：空港ごとの答えの大きさと時刻（反映の前と後で bytes が減るか。trafficseen は見る人のしるし）
select key, at at time zone 'Asia/Tokyo' as at_jst, pg_column_size(body) as bytes,
       case when body ? 'planes' then jsonb_array_length(body->'planes') end as planes
  from public.edge_cache where key like 'traffic%' order by key;
