-- エアライン経営 co-v3：朝のまとめ（画面案「朝のまとめ」のうち、いま出せるもの）
--   毎晩 23:50（日本時間）に、その日の1日の収益・維持費・もうけ・満足度を会社ごとに記録する（co3_daily）
--   朝のまとめ（co_state の morning）＝ 前の日の記録・その前の日とのちがい・前の日の欠航（トラブル）・対応が必要なトラブルの数・
--     神対応の数（前の24時間）・自社の国内線の「実際の空」（前の日、倍率が1でない路線）
--   遅れの波・定時率・点検の期限・発着枠の申し込みは、便の時刻・格付け・申し込みを作るときに足す

create table if not exists public.co3_daily (
  user_id      uuid not null references auth.users(id) on delete cascade,
  day          date not null,
  gross        bigint not null,
  upkeep       bigint not null,
  profit       bigint not null,
  satisfaction numeric not null,
  routes       integer not null,
  fleet        integer not null,
  primary key (user_id, day)
);
alter table public.co3_daily enable row level security;
revoke all on public.co3_daily from public, anon, authenticated;
grant select on public.co3_daily to authenticated;
drop policy if exists "own daily" on public.co3_daily;
create policy "own daily" on public.co3_daily for select to authenticated using (user_id = auth.uid());

create or replace function public.co3_daily_record(p_day date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date); n integer;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  insert into co3_daily (user_id, day, gross, upkeep, profit, satisfaction, routes, fleet)
  select c.user_id, d, x.g, x.u, x.g - x.u, c.satisfaction,
         (select count(*) from co_routes(c.user_id)), (select count(*) from aircraft a where a.user_id = c.user_id)
    from companies c cross join lateral (select co_gross(c.user_id) as g, co_upkeep(c.user_id) as u) x
  on conflict (user_id, day) do update set gross = excluded.gross, upkeep = excluded.upkeep, profit = excluded.profit,
    satisfaction = excluded.satisfaction, routes = excluded.routes, fleet = excluded.fleet;
  get diagnostics n = row_count;
  return n;
end;
$$;
revoke all on function public.co3_daily_record(date) from public, anon, authenticated;

create or replace function public.co3_morning(p_uid uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with t as (select (now() at time zone 'Asia/Tokyo')::date as today),
  y as (select d.* from co3_daily d, t where d.user_id = p_uid and d.day = t.today - 1),
  p as (select d.* from co3_daily d, t where d.user_id = p_uid and d.day = t.today - 2)
  select jsonb_build_object(
    'day', (select today - 1 from t),
    'profit', (select profit from y), 'gross', (select gross from y), 'upkeep', (select upkeep from y),
    'prev_profit', (select profit from p),
    'sat', (select satisfaction from y), 'prev_sat', (select satisfaction from p),
    'cancelled', (select coalesce(sum(x.cancelled), 0) from co3_troubles x, t where x.user_id = p_uid and x.day = t.today - 1),
    'open', (select count(*) from co3_troubles x where x.user_id = p_uid and x.result is null and x.deadline > now()),
    'god', (select count(*) from co3_troubles x where x.user_id = p_uid and x.result = 'god' and x.done_at > now() - interval '24 hours'),
    'sky', (select coalesce(jsonb_agg(jsonb_build_object('k', s.route_key, 'mult', s.mult, 'n', s.n, 'cxl', s.cxl, 'avg4', s.avg4) order by abs(s.mult - 1) desc), '[]'::jsonb)
              from co_routes(p_uid) r join co_sky s on s.route_key = r.route_key, t
             where s.day = t.today - 1 and not r.intl and s.mult <> 1))
$$;
revoke all on function public.co3_morning(uuid) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_morning' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、朝のまとめを入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'morning', case when v3 then co3_morning(uid) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-daily', '50 14 * * *', $job$ select public.co3_daily_record() $job$) $q$;
  end if;
end
$$;
