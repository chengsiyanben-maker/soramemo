-- フライトの記録で、出発・到着の時刻（チェックインの時刻）にいちばん近い予定の便を選べるようにする。
-- ・予定の便（flight_schedule。ODPT のフライト時刻表）は、記録をあとから付ける人のために14日残す（これまで2日）
-- ・public.flight_candidates：出発空港・到着空港と、出発・到着の時刻から、近い便を5つまで返す（ログインしていなくても読める公開の時刻表）
create or replace function public.flight_candidates(p_dep text, p_arr text, p_dep_at timestamptz, p_arr_at timestamptz)
returns jsonb language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', flight, 'std', std, 'sta', sta, 'aircraft', aircraft, 'source', source, 'diff_min', diff) order by diff, std), '[]'::jsonb)
  from (
    select flight, std, sta, aircraft, source,
           round((abs(extract(epoch from (std - p_dep_at))) + abs(extract(epoch from (sta - p_arr_at)))) / 60)::int as diff
    from public.flight_schedule
    where p_dep ~ '^[A-Z]{3}$' and p_arr ~ '^[A-Z]{3}$'
      and p_arr_at > p_dep_at and p_arr_at - p_dep_at < interval '24 hours'
      and dep = p_dep and arr = p_arr
      and std between p_dep_at - interval '3 hours' and p_arr_at
      and sta between p_dep_at and p_arr_at + interval '3 hours'
    order by diff, std
    limit 5
  ) c
$$;
revoke all on function public.flight_candidates(text, text, timestamptz, timestamptz) from public;
grant execute on function public.flight_candidates(text, text, timestamptz, timestamptz) to anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron') then return; end if;
  execute 'create extension if not exists pg_cron';
  execute $q$
    select cron.schedule('flight-watch-cleanup', '20 19 * * *', $job$
      delete from public.flight_alerts where created_at < now() - interval '2 days';
      delete from public.flight_schedule where std < now() - interval '14 days';
    $job$)
  $q$;
end
$outer$;
