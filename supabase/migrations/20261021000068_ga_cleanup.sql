-- ゴーアラウンド（推定）の誤り：離陸した直後の機体（降りてくるところを見ていない）を数えていたものを消す
-- 残すのは、いちばん低い所より前に、それより 400ft 以上高い点があるものだけ（_shared/go_around.ts の判定と同じ）
delete from public.ga_events e
where e.low_at is not null and not exists (
  select 1 from jsonb_array_elements(e.pts) q
  where jsonb_typeof(q) = 'array' and (q->>0)::numeric < extract(epoch from e.low_at) and (q->>1)::numeric >= e.low_ft + 400
);
