-- 定期の手入れ 11/11（データ担当）：到着予想の学習（eta-calib）と、それを使う画面の関数を軽くする。表・列・RLS・権限・関数の中身は変えない
--   1. 索引 flight_history_arr_eta を足す（到着空港・運航日。到着予想が付いて着いた便だけの部分索引）
--      これまで「到着空港ごとの便」を引く所は、到着空港から引ける索引がなく、flight_history（消さずに増え続ける）を丸ごと読むか、
--      出発空港が先頭の索引 flight_history_route を端から端まで読んでいた。本物の Postgres 16（26万4千便＝1日2,200便×120日・出発50空港・到着80空港）で
--        refresh_eta_calib（毎晩 20:35 UTC）：約 400ms → 約 52ms
--        eta_daily（誰でも呼べる。60日）：5〜25ms（表を丸ごと読む） → 約 2ms（読む量は表が増えても変わらない）
--      使う所：eta_daily・eta_daily_mode・refresh_eta_calib の空港ごと・使い方ごとの寄り道
--      （refresh_eta_calib を1回読むだけに書き直す案も試したが、索引があれば約 60ms で速くならないので入れない）
--   2. 毎晩の3つの仕事（eta-calib・taxi-out・flight-watch-cleanup）に時間の上限（statement_timeout）と lock_timeout を付ける。
--      時刻と中身は今のまま。上限は仕事の文の先頭で付ける（関数の設定では効かない。20261105000152 の説明のとおり）
-- 影響：チェックイン（運用の画面の到着予想・ずれのグラフ）は値が同じ。経営は使っていない

-- 1
create index if not exists flight_history_arr_eta on public.flight_history (arr, svc_date)
  where eta30 is not null and ata is not null and not cancelled and diverted_to is null;

-- 2
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('eta-calib', '35 20 * * *', $job$ set statement_timeout = '2min'; set lock_timeout = '5s'; select public.refresh_eta_calib() $job$) $q$;
  execute $q$ select cron.schedule('taxi-out', '40 20 * * *', $job$ set statement_timeout = '2min'; set lock_timeout = '5s'; select public.refresh_taxi_out() $job$) $q$;
  execute $q$
    select cron.schedule('flight-watch-cleanup', '20 19 * * *', $job$
      set statement_timeout = '3min'; set lock_timeout = '5s';
      delete from public.flight_alerts where created_at < now() - interval '2 days';
      delete from public.flight_schedule where std < now() - interval '14 days';
    $job$)
  $q$;
end
$outer$;
