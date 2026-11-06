-- 管制の交信：7日で消えているか・同意の記録がどうなっているかを見る（読むだけ・データ担当 11/6）
--   SQL Editor に貼って流す。表は書き換えない。atc_msgs は7日分だけなので小さく、一時ファイルは使わない。20秒で止まる
--   1つの表（項目・値）で出る。結果は docs/pm/atc-retention-result.csv に貼るか、そのまま渡してください
--   ブラウザの自動翻訳は切ってから貼る
set statement_timeout = '20s';
set lock_timeout = '2s';

with m as (
  select count(*)                                             as n,
         count(*) filter (where verified)                     as n_ok,
         count(*) filter (where not verified)                 as n_ng,
         count(*) filter (where feeder is null)               as n_nofeeder,
         count(*) filter (where text_en is not null)          as n_text,
         min(at)                                              as oldest,
         count(*) filter (where at < now() - interval '7 days') as n_over7
  from public.atc_msgs
), f as (
  select count(*)                                                  as n,
         count(*) filter (where last_seen > now() - interval '30 days') as n_30d,
         count(*) filter (where last_seen is null or last_seen < now() - interval '90 days') as n_idle90,
         min(consent_at)                                           as first_consent,
         count(distinct user_id)                                   as people
  from public.atc_feeders
), a as (  -- 地域ごとの協力者の数のうち、1〜2人しかいない地域（atc_coverage でだれでも見える）
  select count(*) filter (where k < 3) as small, count(*) as areas
  from (select area, count(*) as k from public.atc_feeders where area is not null and last_seen > now() - interval '7 days' group by area) z
), j as (  -- 毎晩の掃除（記録は今の設定では1日だけ残る）
  select (select schedule from cron.job where jobname = 'atc-cleanup')                as schedule,
         (select active from cron.job where jobname = 'atc-cleanup')                  as active,
         (select d.status || ' ' || to_char(d.start_time at time zone 'Asia/Tokyo', 'MM-DD HH24:MI') || ' ' || coalesce(d.return_message, '')
            from cron.job_run_details d join cron.job c on c.jobid = d.jobid
           where c.jobname = 'atc-cleanup' order by d.start_time desc limit 1)        as last_run
)
select '交信の行数' as 項目, m.n::text as 値 from m
union all select '  うち画面に出したもの（verified）', m.n_ok::text from m
union all select '  うち出していないもの', m.n_ng::text from m
union all select '  うち協力をやめた人・退会した人の分（feeder が空）', m.n_nofeeder::text from m
union all select '  うち英語の文字が残っているもの', m.n_text::text from m
union all select 'いちばん古い交信（日本時間）', coalesce(to_char(m.oldest at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI'), 'なし') from m
union all select '7日を過ぎた交信の数（0 でなければ掃除が止まっている）', m.n_over7::text from m
union all select '協力の登録（台）', f.n::text from f
union all select '  協力している人の数', f.people::text from f
union all select '  30日以内に動いた台', f.n_30d::text from f
union all select '  90日以上動いていない台', f.n_idle90::text from f
union all select 'いちばん古い同意（日本時間）', coalesce(to_char(f.first_consent at time zone 'Asia/Tokyo', 'YYYY-MM-DD HH24:MI'), 'なし') from f
union all select '協力者のいる地域', a.areas::text from a
union all select '  そのうち1〜2人だけの地域', a.small::text from a
union all select '掃除の時刻（UTC）', coalesce(j.schedule, '登録なし') from j
union all select '掃除は有効か', coalesce(j.active::text, '登録なし') from j
union all select '掃除の最後の実行', coalesce(j.last_run, '記録なし') from j;
