-- チェックインしたときの空港の運用（運用タブの14空港だけ）。運用の判定の記録（ops_log）の直近10分のものから、
-- 実際の機体での判定があればそれを、なければ風からの推定（決められたときだけ）を、運用の名前（「北風運用」など）で残す
alter table public.checkins add column if not exists ops text check (length(ops) <= 40);
