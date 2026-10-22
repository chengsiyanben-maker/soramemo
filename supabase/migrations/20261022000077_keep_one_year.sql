-- 航跡・機体・滑走路の記録を1年残す（これまで：便の航跡31日・滑走路の学習90日・機体の運用の観察60日）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('archive-cleanup-daily', '40 20 * * *', $job$
      delete from public.flight_tracks where svc_date < (now() at time zone 'Asia/Tokyo')::date - 366;
      delete from public.flight_history where svc_date < (now() at time zone 'Asia/Tokyo')::date - 366;
      delete from public.archive_runs where day < (now() at time zone 'Asia/Tokyo')::date - 366;
      delete from public.rotation_obs where svc_date < (now() at time zone 'Asia/Tokyo')::date - 366;
  $job$) $q$;
  execute $q$ select cron.schedule('rwy-samples-cleanup', '23 19 * * *', $job$ delete from public.rwy_samples where at < now() - interval '366 days'; delete from public.arr_watch where updated_at < now() - interval '30 minutes' $job$) $q$;
end
$outer$;

-- 滑走路の学習の数・記録は1年までさかのぼれる
create or replace function public.rwy_learned(p_iata text, p_days int default 30) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('iata', p_iata, 'n', coalesce(sum(n), 0), 'rows', coalesce(jsonb_agg(jsonb_build_object('dir', dir, 'rwy', rwy, 'sec', sec, 'n', n) order by dir, rwy, sec), '[]'::jsonb))
  from (
    select dir, rwy, case when b is null then null else (((b + 22) % 360) / 45)::int end as sec, count(*) as n
    from (select dir, rwy, case when dir = 'arr' then coalesce(ent60, ent30, ent120, first_brg) else coalesce(ex60, ex30) end as b
          from public.rwy_samples where iata = p_iata and (src = 'live' or iata not in ('HND', 'NRT')) and at > now() - make_interval(days => least(greatest(coalesce(p_days, 30), 1), 366))) s
    group by 1, 2, 3
  ) q
$$;
create or replace function public.rwy_samples_recent(p_iata text, p_days int default 14) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_array(extract(epoch from at)::bigint, rwy, ent120, ent60, ent30, first_brg, dir, ex30, ex60) order by at), '[]'::jsonb)
  from public.rwy_samples where iata = p_iata and at > now() - make_interval(days => least(greatest(coalesce(p_days, 14), 1), 366))
$$;
