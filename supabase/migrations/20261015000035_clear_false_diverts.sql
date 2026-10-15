-- 誤った「ダイバートの可能性」と、関数を入れ替える前に出た「まだ飛行中」を消す（2026-10-15）：
--  ・近い空港への進入（北九州と山口宇部、出雲と美保）や、同じ番号の別の会社の便（JL552 と JTA552）を取り違えたもの
delete from public.flight_alerts where kind = 'divert' and created_at < '2026-10-15T06:00:00+00:00';
delete from public.flight_alerts where kind = 'delay_arr' and message like '%まだ飛行中%' and created_at < '2026-10-15T06:00:00+00:00';
