-- 航空会社の運航情報（ODPT）から欠航と出発の大きな遅れを知らせる（odpt-status。5分ごと）と、お知らせの急増の見張り。
-- ・flight_alerts.kind に「欠航（cancel）」を足す
-- ・同じ便・同じ種類のお知らせは1つだけ（機体の位置からの推定と、航空会社の運航情報が重ならないように）
-- ・お知らせが急に増えたら（直近1時間に20件以上）、運営画面のエラーの一覧（ops.client_errors）に載せる（3時間に1回まで）
alter table public.flight_alerts drop constraint if exists flight_alerts_kind_check;
alter table public.flight_alerts add constraint flight_alerts_kind_check check (kind in ('delay_dep','no_takeoff','delay_arr','divert','return','divert_landed','cancel'));
delete from public.flight_alerts a using public.flight_alerts b
 where a.schedule_id is not null and a.schedule_id = b.schedule_id and a.kind = b.kind and a.id > b.id;
create unique index if not exists flight_alerts_once on public.flight_alerts (schedule_id, kind);

create table if not exists public.odpt_status_runs (
  id     int primary key default 1 check (id = 1),
  ran_at timestamptz not null default 'epoch'
);
insert into public.odpt_status_runs (id) values (1) on conflict do nothing;
alter table public.odpt_status_runs enable row level security;
revoke all on public.odpt_status_runs from public, anon, authenticated;

create or replace function ops.alert_watchdog() returns int
language plpgsql security definer set search_path = public, ops as $$
declare n int; by_kind text;
begin
  select coalesce(sum(c), 0)::int, string_agg(kind || ' ' || c, '、' order by c desc) into n, by_kind
    from (select kind, count(*) c from public.flight_alerts where created_at > now() - interval '1 hour' group by kind) k;
  if n >= 20
     and not exists (select 1 from ops.client_errors where kind = 'alert_surge' and created_at > now() - interval '3 hours') then
    insert into ops.client_errors (session, platform, version, kind, message, detail)
    values ('server', 'server', 'alert_watchdog', 'alert_surge',
            left('遅れ・ダイバートのお知らせが直近1時間に急に増えています（誤報の可能性。種類ごと：' || coalesce(by_kind, '') || '）', 300),
            jsonb_build_object('since', now() - interval '1 hour'));
    return 1;
  end if;
  return 0;
end $$;
revoke all on function ops.alert_watchdog() from public, anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then return; end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  execute $q$
    select cron.schedule('odpt-status', '*/5 * * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/odpt-status',
        headers := '{"User-Agent": "soramemo (odpt-status)"}'::jsonb,
        timeout_milliseconds := 60000)
    $job$)
  $q$;
  execute $q$ select cron.schedule('alert-watchdog', '*/15 * * * *', $job$ select ops.alert_watchdog() $job$) $q$;
end
$outer$;
