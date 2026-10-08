-- 運営用の確認画面（web/admin.html）
-- 運営者は admins 表に登録した利用者だけ。登録は SQL Editor から手で行う：
--   insert into public.admins (user_id) select id from auth.users where email = '<運営者のメールアドレス>';

create table public.admins (
  user_id  uuid primary key references auth.users(id) on delete cascade,
  added_at timestamptz not null default now()
);
alter table public.admins enable row level security;     -- ポリシーを作らない＝利用者からは見えない
revoke all on public.admins from anon, authenticated;

-- 運営の操作の記録
create table public.admin_actions (
  id         bigint generated always as identity primary key,
  admin_id   uuid not null,
  action     text not null,
  target     text not null,
  detail     jsonb,
  created_at timestamptz not null default now()
);
alter table public.admin_actions enable row level security;
revoke all on public.admin_actions from anon, authenticated;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from admins where user_id = auth.uid())
$$;

create or replace function public.admin_stats() returns jsonb
language plpgsql stable security definer set search_path = public, auth as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'users', (select count(*) from auth.users),
    'checkins_today', (select count(*) from public.checkins where created_at >= date_trunc('day', now() at time zone 'Asia/Tokyo') at time zone 'Asia/Tokyo'),
    'checkins_total', (select count(*) from public.checkins),
    'flagged', (select count(*) from public.checkins where flags <> '{}'),
    'plus', (select count(*) from public.subscriptions where status in ('active', 'trialing')),
    'verified', (select count(*) from public.flights where status = 'verified'),
    'flights', (select count(*) from public.flights));
end;
$$;

create or replace function public.admin_flagged(p_limit integer default 100) returns jsonb
language plpgsql stable security definer set search_path = public, auth as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return coalesce((
    select jsonb_agg(x order by x.created_at desc) from (
      select c.id, c.created_at, c.position_at, c.flags, c.accuracy_m, c.lat, c.lon,
             c.airport_id, a.name as airport, c.terminal_id, u.email,
             (select count(*) from public.checkins c2 where c2.user_id = c.user_id) as user_checkins,
             (select count(*) from public.checkins c3 where c3.user_id = c.user_id and c3.flags <> '{}') as user_flagged
        from public.checkins c
        join public.airports a on a.id = c.airport_id
        join auth.users u on u.id = c.user_id
       where c.flags <> '{}'
       order by c.created_at desc
       limit least(greatest(p_limit, 1), 500)
    ) x), '[]'::jsonb);
end;
$$;

-- 問題なし：印を外す
create or replace function public.admin_clear_flags(p_checkin bigint) returns void
language plpgsql security definer set search_path = public as $$
declare old text[];
begin
  if not is_admin() then raise exception 'admin only'; end if;
  update checkins set flags = '{}' where id = p_checkin returning flags into old;
  if not found then raise exception 'not found'; end if;
  insert into admin_actions (admin_id, action, target) values (auth.uid(), 'clear_flags', p_checkin::text);
end;
$$;

-- 取り消す：チェックインと、それを出発・到着に使ったフライトを消す
create or replace function public.admin_void_checkin(p_checkin bigint, p_reason text) returns integer
language plpgsql security definer set search_path = public as $$
declare c checkins; n integer;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  select * into c from checkins where id = p_checkin;
  if not found then raise exception 'not found'; end if;
  delete from flights where dep_checkin = p_checkin or arr_checkin = p_checkin;
  get diagnostics n = row_count;
  delete from checkins where id = p_checkin;
  insert into admin_actions (admin_id, action, target, detail)
    values (auth.uid(), 'void_checkin', p_checkin::text,
            jsonb_build_object('user_id', c.user_id, 'airport_id', c.airport_id, 'flags', c.flags, 'flights_removed', n, 'reason', p_reason));
  return n;
end;
$$;

revoke all on function public.is_admin(), public.admin_stats(), public.admin_flagged(integer), public.admin_clear_flags(bigint), public.admin_void_checkin(bigint, text) from public, anon;
grant execute on function public.is_admin(), public.admin_stats(), public.admin_flagged(integer), public.admin_clear_flags(bigint), public.admin_void_checkin(bigint, text) to authenticated;
