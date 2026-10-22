-- 航跡・機体・滑走路の記録をずっと残す（これまで：便の航跡31日・便の実績365日・滑走路の学習90日・機体の運用の観察60日）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  -- 便の実績・便の航跡・機体の運用の観察は消さない（毎日の記録の作り直しの記録だけ1年）
  execute $q$ select cron.schedule('archive-cleanup-daily', '40 20 * * *', $job$
      delete from public.archive_runs where day < (now() at time zone 'Asia/Tokyo')::date - 366;
  $job$) $q$;
  -- 滑走路の学習の記録は消さない（見張りの途中の記録だけ30分で消す）
  execute $q$ select cron.schedule('rwy-samples-cleanup', '23 19 * * *', $job$ delete from public.arr_watch where updated_at < now() - interval '30 minutes' $job$) $q$;
  -- ゴーアラウンド（推定）と運用の記録（5分ごとの滑走路の判定・風）も消さない（見張りの途中の記録だけ1時間で消す）
  execute $q$ select cron.schedule('ga-cleanup', '17 19 * * *', $job$ delete from public.ga_watch where updated_at < now() - interval '1 hour' $job$) $q$;
  perform cron.unschedule('ops-log-cleanup') where exists (select 1 from cron.job where jobname = 'ops-log-cleanup');
  -- 全機の航跡と機体の記録は消さない
  perform cron.unschedule('all-planes-cleanup') where exists (select 1 from cron.job where jobname = 'all-planes-cleanup');
end
$outer$;

-- 滑走路の学習の数・記録は何日でもさかのぼれる（上限は10年）
create or replace function public.rwy_learned(p_iata text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('iata', p_iata, 'n', coalesce(sum(n), 0), 'rows', coalesce(jsonb_agg(jsonb_build_object('dir', dir, 'rwy', rwy, 'sec', sec, 'n', n) order by dir, rwy, sec), '[]'::jsonb))
  from (
    select dir, rwy, case when b is null then null else (((b + 22) % 360) / 45)::int end as sec, count(*) as n
    from (select dir, rwy, case when dir = 'arr' then coalesce(ent60, ent30, ent120, first_brg) else coalesce(ex60, ex30) end as b
          from public.rwy_samples where iata = p_iata and (src = 'live' or iata not in ('HND', 'NRT')) and at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 3660))) s
    group by 1, 2, 3
  ) q
$$;
create or replace function public.rwy_samples_recent(p_iata text, p_days int default 14) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_array(extract(epoch from at)::bigint, rwy, ent120, ent60, ent30, first_brg, dir, ex30, ex60) order by at), '[]'::jsonb)
  from public.rwy_samples where iata = p_iata and at > now() - make_interval(days => least(greatest(coalesce(p_days, 14), 1), 3660))
$$;
