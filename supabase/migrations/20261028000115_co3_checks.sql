-- エアライン経営 co-v3：定期点検（A点検。仕様書5章「定期点検」）
--   飛んだ時間は、前の日に飛んだ便（co3_leg_status、欠航を除く）の飛ぶ時間を、毎晩0:30（日本時間）に機体ごとに足す
--   A点検の間隔（目安。実際の整備計画は会社ごとに違う）：プロペラ 600時間・リージョナル 700・小型ジェット 800・中型 1,000・大型 1,200
--   費用：機体の値段の0.2%。整備場（施設）がまだないので、どれも「ゲームの整備会社」が引き受ける（標準の1.3倍）
--   格付け1・2：点検はすべて自動（費用は維持費に込みで維持費 +10%、運休なし）
--   格付け3から：「おまかせ」（期限が来た夜に自動で点検。費用は1割高い）か「自分で入れる」（頼んだ機体をその夜に点検）
--     自分で入れる会社で期限を過ぎた機体は飛べない（その機体の便は欠航＝会社のせい、cause 'check'）
--   点検の後30日は、故障が半分。C点検・重整備は格付け4から（あとで作る）

alter table public.aircraft add column if not exists fly_min integer not null default 0;
alter table public.aircraft add column if not exists check_min integer not null default 0;
alter table public.aircraft add column if not exists checked_day date;
alter table public.aircraft add column if not exists check_req boolean not null default false;
alter table public.aircraft enable row level security;
alter table public.companies add column if not exists check_mode text not null default 'auto' check (check_mode in ('auto', 'self'));
alter table public.companies enable row level security;
alter table public.co3_leg_status drop constraint if exists co3_leg_status_cause_check;
alter table public.co3_leg_status add constraint co3_leg_status_cause_check check (cause in ('real', 'breakdown', 'check'));
alter table public.co3_leg_status enable row level security;
alter table public.co3_troubles drop constraint if exists co3_troubles_cause_check;
alter table public.co3_troubles add constraint co3_troubles_cause_check check (cause in ('real', 'breakdown', 'check'));
alter table public.co3_troubles enable row level security;

create or replace function co3.a_interval_min(p_type text) returns integer
language sql immutable as $$ select case p_type when 'prop' then 600 when 'rj' then 700 when 'nb' then 800 when 'wb' then 1000 else 1200 end * 60 $$;
revoke all on function co3.a_interval_min(text) from public, anon, authenticated;

-- 点検の費用（おまかせは1割高い）
create or replace function public.co3_check_cost(p_aircraft bigint) returns numeric
language sql stable security definer set search_path = public as $$
  select round(greatest(a.paid, (ac_spec(a.type)).price) * 0.002 * 1.3 * case when c.check_mode = 'auto' then 1.1 else 1 end, 2)
    from aircraft a join companies c on c.user_id = a.user_id where a.id = p_aircraft
$$;
revoke all on function public.co3_check_cost(bigint) from public, anon, authenticated;

-- 期限を過ぎて飛べないか（格付け3以上で「自分で入れる」の会社だけ）
create or replace function public.co3_check_overdue(p_aircraft bigint) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select c.rating >= 3 and c.check_mode = 'self' and a.fly_min - a.check_min >= co3.a_interval_min(a.type)
                     from aircraft a join companies c on c.user_id = a.user_id where a.id = p_aircraft), false)
$$;
revoke all on function public.co3_check_overdue(bigint) from public, anon, authenticated;

-- 毎晩：飛んだ時間を足して、点検する。p_day は試験用（その日の分を足す。ふだんは前の日）
create or replace function public.co3_checks_run(p_day date default null) returns integer
language plpgsql security definer set search_path = public, ops as $$
declare d date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date - 1); a record; cst numeric; n int := 0;
begin
  if not coalesce((select value::text = 'true' from ops.flags where key = 'co_v3'), false) then return 0; end if;
  update aircraft x set fly_min = x.fly_min + f.m
    from (select s.aircraft_id, sum(co3.leg_block_min(coalesce(co3_km(s.dep, s.arr), 0)))::int as m
            from co3_leg_status s where s.day = d and s.status <> 'cxl' and s.aircraft_id is not null group by s.aircraft_id) f
   where x.id = f.aircraft_id;
  for a in select x.id, x.user_id, x.type, x.fly_min, x.check_min, x.check_req, c.rating, c.check_mode
             from aircraft x join companies c on c.user_id = x.user_id
            where x.check_req or x.fly_min - x.check_min >= co3.a_interval_min(x.type) loop
    if a.rating < 3 then
      update aircraft set check_min = fly_min, checked_day = d + 1, check_req = false where id = a.id;   -- 自動（維持費に込み）
    elsif a.check_mode = 'auto' or a.check_req then
      cst := co3_check_cost(a.id);
      update companies set cash = greatest(0, cash - ceil(cst)) where user_id = a.user_id;
      update aircraft set check_min = fly_min, checked_day = d + 1, check_req = false where id = a.id;
    else
      continue;    -- 自分で入れる会社で、頼んでいない：期限を過ぎて飛べない
    end if;
    n := n + 1;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_checks_run(date) from public, anon, authenticated;

create or replace function public.co3_set_check_mode(p_mode text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if p_mode not in ('auto', 'self') then raise exception 'invalid mode'; end if;
  update companies set check_mode = p_mode where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co3_set_check_mode(text) from public, anon;
grant execute on function public.co3_set_check_mode(text) to authenticated;

-- 今夜点検する（自分で入れる）。取り消しもできる
create or replace function public.co3_request_check(p_aircraft bigint, p_on boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  update aircraft set check_req = coalesce(p_on, true) where id = p_aircraft and user_id = uid;
  if not found then raise exception 'aircraft not found'; end if;
  return co_state();
end;
$$;
revoke all on function public.co3_request_check(bigint, boolean) from public, anon;
grant execute on function public.co3_request_check(bigint, boolean) to authenticated;

do $do$
declare src text;
begin
  -- 期限を過ぎた機体は飛べない（便ごとの判定）
  select pg_get_functiondef('public.co3_ac_grounded(bigint,date)'::regprocedure) into src;
  if position('co3_check_overdue' in src) = 0 then
    if position($r$select case when b.spare_id is null then 'down' else 'spare' end$r$ in src) = 0 then raise exception 'co3_ac_grounded の形が変わっていて、点検を入れられない'; end if;
    src := replace(src, $r$  select case when b.spare_id is null then 'down' else 'spare' end
    from co3_breakdowns b where b.aircraft_id = p_aircraft and p_day between b.start_day and b.end_day limit 1$r$,
      $r$  select coalesce((select case when b.spare_id is null then 'down' else 'spare' end
    from co3_breakdowns b where b.aircraft_id = p_aircraft and p_day between b.start_day and b.end_day limit 1),
    case when co3_check_overdue(p_aircraft) then 'check' end)$r$);
    execute src;
  end if;
  select pg_get_functiondef('public.co3_legs_check(timestamptz)'::regprocedure) into src;
  if position($r$g in ('down', 'check')$r$ in src) = 0 then
    if position($r$if g = 'down' then$r$ in src) = 0 or position($r$cs := 'breakdown';$r$ in src) = 0 then raise exception 'co3_legs_check の形が変わっていて、点検を入れられない'; end if;
    src := replace(src, $r$if g = 'down' then$r$, $r$if g in ('down', 'check') then$r$);
    src := replace(src, $r$cs := 'breakdown';$r$, $r$cs := case when g = 'check' then 'check' else 'breakdown' end;$r$);
    src := replace(src, $r$brk_first := cs is distinct from 'breakdown' or not exists (select 1 from co3_troubles t where t.user_id = c.user_id and t.route_key = l.route_key and t.day = today and t.cause = 'breakdown');$r$,
                        $r$brk_first := cs is null or cs = 'real' or not exists (select 1 from co3_troubles t where t.user_id = c.user_id and t.route_key = l.route_key and t.day = today and t.cause = cs);$r$);
    execute src;
  end if;
  -- 定時率：点検切れの欠航も会社のせい
  select pg_get_functiondef('public.co3_ontime(uuid)'::regprocedure) into src;
  if position($r$cause in ('breakdown', 'check')$r$ in src) = 0 then
    src := replace(src, $r$cause = 'breakdown'$r$, $r$cause in ('breakdown', 'check')$r$);
    execute src;
  end if;
  -- 点検の後30日は故障が半分
  select pg_get_functiondef('public.co3_breakdown_rate(bigint)'::regprocedure) into src;
  if position('checked_day' in src) = 0 then
    if position($r$* case when c.roles ? 'maint'$r$ in src) = 0 then raise exception 'co3_breakdown_rate の形が変わっていて、点検を入れられない'; end if;
    src := replace(src, $r$* case when c.roles ? 'maint'$r$, $r$* case when a.checked_day > (now() at time zone 'Asia/Tokyo')::date - 30 then 0.5 else 1 end
         * case when c.roles ? 'maint'$r$);
    execute src;
  end if;
  -- 格付け1・2：自動の点検の分、維持費 +10%
  select pg_get_functiondef('public.co3_ac_upkeep(bigint)'::regprocedure) into src;
  if position('co3_rating_need' in src) = 0 then
    if position('* case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end' in src) = 0 then raise exception 'co3_ac_upkeep の形が変わっていて、点検を入れられない'; end if;
    src := replace(src, '* case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end',
      '* case when co3_ac_earn(a.id) < 1 then 1.3 else 1 end * case when coalesce(co3_rating_need(a.user_id), 1) < 3 then 1.1 else 1 end');
    execute src;
  end if;
  -- 会社の状態：機体の飛んだ時間・点検までの時間・点検の日、会社の点検のやり方
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''check_mode''' in src) = 0 then
    if position($r$'lease', lease, 'lease_fee', lease_fee,$r$ in src) = 0 or position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、点検を入れられない'; end if;
    src := replace(src, $r$'lease', lease, 'lease_fee', lease_fee,$r$,
      $r$'lease', lease, 'lease_fee', lease_fee, 'fly_hours', round(fly_min / 60.0), 'check_left_hours', round((co3.a_interval_min(type) - (fly_min - check_min)) / 60.0),
                 'checked_day', checked_day, 'check_req', check_req, 'check_cost', co3_check_cost(id),$r$);
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'check_mode', c.check_mode,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-checks', '30 15 * * *', $job$ select public.co3_checks_run() $job$) $q$;
  end if;
end
$$;
