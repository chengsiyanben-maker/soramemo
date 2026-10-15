-- 「離陸を確認できず」のお知らせを消す（2026-10-15）。共同運航便などで誤りばかりだったため、いまは出していない
delete from public.flight_alerts where kind = 'no_takeoff';
