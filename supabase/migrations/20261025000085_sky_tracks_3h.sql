-- 空の道すじを3時間ごとにまとめる
--   ・rwy-learn を3時間ごと（日本時間 0:15・3:15・…・21:15）に、前の5時間を読む形にする（前後の回と2時間重なる）
--   ・airport_tracks：今日の分も返す（まとめた所まで）。線ごとに、空港のいちばん近くにいた時刻（日本時間の「時」）も返す（時間帯ごとに見るため）
create or replace function public.airport_tracks(p_iata text, p_day date) returns jsonb
language sql stable security definer set search_path = public as $$
  with d as (select (now() at time zone 'Asia/Tokyo')::date as today),
  a as (select dep_here, pts, extract(hour from at at time zone 'Asia/Tokyo')::int as h from public.airport_tracks_all, d where iata = p_iata and day = p_day and p_day <= d.today order by at limit 3000)
  select case when exists (select 1 from a) then (select jsonb_agg(jsonb_build_object('d', dep_here, 'p', pts, 'h', h)) from a)
  else coalesce((select jsonb_agg(jsonb_build_object('d', q.dep_here, 'p', q.pts)) from (
    select case when h.dep = p_iata then 1 else 0 end as dep_here, t.pts
    from d, public.flight_history h join public.flight_tracks t on t.svc_date = h.svc_date and t.flight = h.flight and t.dep = h.dep
    where h.svc_date = p_day and p_day < d.today and (h.dep = p_iata or h.arr = p_iata)
    order by h.std limit 2000) q), '[]'::jsonb) end
$$;
revoke all on function public.airport_tracks(text, date) from public;
grant execute on function public.airport_tracks(text, date) to anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  execute $q$ select cron.schedule('rwy-learn', '15 */3 * * *', $job$
    select net.http_get(url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/rwy-learn?hours=5&part=' || p, headers := '{"User-Agent": "soramemo (rwy-learn)"}'::jsonb, timeout_milliseconds := 150000)
    from generate_series(0, 7) p
  $job$) $q$;
end
$outer$;
