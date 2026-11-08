-- 本番の健康診断（読むだけ。月曜に本人が SQL Editor に全部貼って Run）。データ担当 11/7
--   1つの表で出る：区分・項目・値・目安・判定（「要確認」の行だけ見ればよい）。CSV で保存して docs/pm/maint/<日付>-health.csv に置くか、データ担当の回に貼る
--   重くしない：索引で引ける列だけを見る。いちばん重いのは前の24時間の航跡の点（track_points）を分ごとに数える所（1440組の数え上げで、一時ファイルは使わない）
--   20秒で止まる（この画面の中だけの設定）。止まったら「11.」の行を消して流し直す
--   ※ Supabase の SQL Editor は先頭に「ブラウザの自動翻訳」が効いていると SQL が壊れることがある。翻訳は切って貼る
set statement_timeout = '20s';

with
-- 1. ODPT（便の情報）
odpt as (
  select '1 ODPT' as k, '運航情報（odpt-status）の最後の問い合わせ' as item, to_char((select ran_at from public.odpt_status_runs where id = 1) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') as v,
         '10分以内' as rule, case when (select ran_at from public.odpt_status_runs where id = 1) > now() - interval '10 minutes' then 'よい' else '要確認' end as ok
  union all
  select '1 ODPT', '今日の予定の便（flight_schedule）の数', count(*)::text, '0 でない', case when count(*) > 0 then 'よい' else '要確認' end
  from public.flight_schedule where svc_date = (now() at time zone 'Asia/Tokyo')::date
  union all
  select '1 ODPT', '予定の便の取り込み（schedule-sync）の最後', to_char((select ran_at from public.schedule_sync_runs where id = 1) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI'),
         '13時間以内（1日2回）', case when (select ran_at from public.schedule_sync_runs where id = 1) > now() - interval '13 hours' then 'よい' else '要確認' end
  union all
  select '1 ODPT', '時刻表（timetable-sync）の最後・誤りのある会社', to_char(max(ran_at) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') || ' / ' || coalesce(string_agg(iata, ',') filter (where result::text ~ '_error|_truncated'), 'なし'),
         '25時間以内・誤りなし', case when max(ran_at) > now() - interval '25 hours' and count(*) filter (where result::text ~ '_error|_truncated') = 0 then 'よい' else '要確認' end
  from public.timetable_sync_runs
),
-- 2. 機体の位置（adsb.lol）
pos as (
  select '2 位置' as k, '機体の位置（live_positions）の最後の記録' as item, to_char(max(seen_at) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI:SS') as v,
         '2分以内' as rule, case when max(seen_at) > now() - interval '2 minutes' then 'よい' else '要確認' end as ok
  from public.live_positions where seen_at > now() - interval '1 day'
  union all
  select '2 位置', '今いる機体の数（2分以内・地域ごと 東/西/北/南）',
         count(*) filter (where lat >= 30 and lat < 40 and lon >= 134) || ' / ' || count(*) filter (where lat >= 30 and lat < 40 and lon < 134) || ' / ' || count(*) filter (where lat >= 40) || ' / ' || count(*) filter (where lat < 30),
         '昼はどれも 0 でない', case when (count(*) filter (where lat < 30) > 0 and count(*) filter (where lat >= 40) > 0) or extract(hour from now() at time zone 'Asia/Tokyo') between 1 and 5 then 'よい' else '要確認' end
  from public.live_positions where seen_at > now() - interval '2 minutes'
  union all
  select '2 位置', '機体ごとの便の記録（reg_legs）の最後', to_char(max(last_at) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI'),
         '5分以内（夜中は除く）', case when max(last_at) > now() - interval '5 minutes' or extract(hour from now() at time zone 'Asia/Tokyo') between 0 and 5 then 'よい' else '要確認' end
  from public.reg_legs where day >= (now() at time zone 'Asia/Tokyo')::date - 1
),
-- 3. 前の24時間の航跡の点（track_points）：点が1つもない分の数（地域ごと）。南（沖縄）は 11/7 の直し（PR）が入るまで、ほぼ全部抜けている見込み
tp as (
  select case when lat < 30 then '南' when lat >= 40 then '北' when lon < 134 then '西' else '東' end as rg, date_trunc('minute', t) as m
  from public.track_points where t > now() - interval '24 hours' group by 1, 2
),
gaps as (
  select '3 抜け' as k, '航跡の点がない分（前の24時間・' || r.rg || '）' as item,
         (1440 - count(tp.m)) || ' 分（点のある分 ' || count(tp.m) || '）' as v,
         '夜中の数時間ぶんだけ' as rule,
         case when 1440 - count(tp.m) <= 360 then 'よい' else '要確認' end as ok
  from (values ('東'), ('西'), ('北'), ('南')) r(rg) left join tp on tp.rg = r.rg group by r.rg
),
-- 4. 30秒ごとの記録の処理（traffic-record）の返事：adsb.lol が断った回（pg_net の返事は6時間ほど残る）
rec as (
  select '4 adsb.lol' as k, '記録の処理の返事のうち 429 を含む回（残っている分）' as item,
         count(*) filter (where content like '%adsb.lol 429%') || ' / ' || count(*) || ' 回（420：' || count(*) filter (where content like '%adsb.lol 420%') || '、時間切れ：' || count(*) filter (where content like '%TimeoutError%' or content like '%timed out%' or timed_out) || '）' as v,
         '429 が1割未満' as rule,
         case when count(*) = 0 then '要確認' when count(*) filter (where content like '%adsb.lol 42%') * 10 < count(*) then 'よい' else '要確認' end as ok
  from net._http_response where content like '%"recorded"%'
  union all
  select '4 adsb.lol', '記録の処理の最後の返事', coalesce(to_char(max(created) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI:SS'), 'なし'), '1分以内',
         case when max(created) > now() - interval '1 minute' then 'よい' else '要確認' end
  from net._http_response where content like '%"recorded"%'
),
-- 5. pg_cron：前の24時間の失敗と、毎晩の処理の最後の成功（cron.job_run_details には jobname がないので cron.job と jobid でつなぐ）
cr as (
  select j.jobname, j.schedule, j.active,
         count(d.*) filter (where d.status = 'failed' and d.start_time > now() - interval '24 hours') as fails,
         max(d.end_time) filter (where d.status = 'succeeded') as last_ok,
         (array_agg(left(d.return_message, 80) order by d.start_time desc) filter (where d.status = 'failed'))[1] as last_err
  from cron.job j left join cron.job_run_details d on d.jobid = j.jobid group by j.jobid, j.jobname, j.schedule, j.active
),
crs as (
  select '5 cron' as k, '前の24時間に失敗した処理' as item,
         coalesce(string_agg(jobname || '×' || fails, ', ' order by fails desc) filter (where fails > 0), 'なし') as v, 'なし' as rule,
         case when count(*) filter (where fails > 0) = 0 then 'よい' else '要確認' end as ok
  from cr
  union all
  select '5 cron', '毎晩の処理の最後の成功：' || jobname, coalesce(to_char(last_ok at time zone 'Asia/Tokyo', 'MM-DD HH24:MI'), '記録なし') || coalesce('（最後の失敗：' || last_err || '）', ''),
         '26時間以内', case when last_ok > now() - interval '26 hours' then 'よい' else '要確認' end
  from cr where jobname in ('daily-archive', 'rot-pairs', 'rot-eval', 'eta-calib', 'taxi-out', 'cold-archive', 'archive-cleanup-daily', 'verify-flights-nightly', 'rwy-learn', 'wx-archive', 'timetable-sync', 'schedule-sync')
  union all
  select '5 cron', '止めてある処理', coalesce(string_agg(jobname, ', '), 'なし'), 'なし（わざと止めたものだけ）', case when count(*) = 0 then 'よい' else '要確認' end
  from cr where not active
  union all
  select '5 cron', '毎晩のまとめ（archive_runs）の最後の日', coalesce((select max(day)::text from public.archive_runs), 'なし'), '昨日',
         case when (select max(day) from public.archive_runs) >= (now() at time zone 'Asia/Tokyo')::date - 1 then 'よい' else '要確認' end
),
-- 6. 天気
wx as (
  select '6 天気' as k, '天気の記録（wx_obs、1時間ごと）の最後の観測' as item, to_char(max(at) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') as v,
         '2時間以内' as rule, case when max(at) > now() - interval '2 hours' then 'よい' else '要確認' end as ok
  from public.wx_obs where icao in ('RJTT', 'RJAA', 'RJBB', 'RJCC', 'RJFF', 'ROAH') and at > now() - interval '3 days'
  union all
  select '6 天気', '運用の記録（ops_log、5分ごと）の最後と、そこでの気象通報の時刻', to_char(max(at) at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') || ' / 通報 ' || coalesce(to_char(max(metar_at) at time zone 'Asia/Tokyo', 'HH24:MI'), 'なし'),
         '10分以内・通報は1時間以内', case when max(at) > now() - interval '10 minutes' and max(metar_at) > now() - interval '70 minutes' then 'よい' else '要確認' end
  from public.ops_log where at > now() - interval '1 day'
  union all
  -- 長崎・鹿児島などは1時間ごとの発表で、空港が閉まっている夜は出ない（11/7 に配信元で確かめた）。ここでは14空港の最後の観測を並べるだけ
  select '6 天気', '14空港の最後の観測（wx_obs）', string_agg(icao || ' ' || to_char(last_at at time zone 'Asia/Tokyo', 'HH24:MI'), ', ' order by icao), '参考', '参考'
  from (select icao, max(at) as last_at from public.wx_obs where icao in ('RJTT','RJAA','RJBB','RJOO','RJGG','RJCC','RJFF','ROAH','RJSS','RJOA','RJOM','RJFT','RJFU','RJFK') and at > now() - interval '1 day' group by icao) x
)
select * from odpt union all select * from pos union all select * from gaps union all select * from rec union all select * from crs union all select * from wx
order by 1, 2;
