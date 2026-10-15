-- 誤ったお知らせを消す（2026-10-15）：
--  ・プロペラ機・エンブラエル機の「離陸を確認できず」（受信機に映りにくいだけのことが多い。今後は出さない）
--  ・「到着の定刻から1時間以上たっても、まだ飛行中」（着陸の直前に受信が切れて着陸を見逃したもの。今後は今も見えている便だけに出す）
delete from public.flight_alerts a using public.flight_schedule s
 where a.schedule_id = s.id and a.kind = 'no_takeoff'
   and s.aircraft ~* '^(AT|AR|Q[0-9]|Q4|D[H8]|DHC|SF|SAB|YS|BN|DO|E[0-9]|EM|ER)';
delete from public.flight_alerts where kind = 'delay_arr' and message like '%まだ飛行中%';
