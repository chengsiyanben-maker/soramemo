-- 攻撃への備え：分離・回数制限・非常停止・運営者の2段階認証
--
-- 1. 分離：運営用の表を、API（PostgREST）から見えない ops スキーマへ移す。
--    Supabase が外に出すのは public スキーマだけなので、ops の表は、RLS の設定を誤っても外から直接は触れない。
--    外から使えるのは、public に置いた決まった関数だけ。
-- 2. 回数制限：ops.rl_take で、1分などの区切りごとに回数を数える（同じ行を更新するので、記録が膨らまない）。
-- 3. 非常停止：ops.flags（メンテナンス中、チェックインの一時停止、記録の停止）。運営画面から切り替える。
-- 4. 運営者の2段階認証：運営の関数は、認証アプリのコードまで確かめたログイン（aal2）でないと動かない。

create schema if not exists ops;
revoke all on schema ops from public, anon, authenticated;

alter table public.admins             set schema ops;
alter table public.admin_actions      set schema ops;
alter table public.usage_events       set schema ops;
alter table public.client_errors      set schema ops;
alter table public.checkin_rejections set schema ops;

-- ---------- 回数制限 ----------
create table ops.rate_limits (
  key    text not null,
  bucket timestamptz not null,
  n      integer not null default 0,
  primary key (key, bucket)
);

-- 区切り（p_window_sec 秒）ごとの回数を1増やし、上限以内なら true
create or replace function ops.rl_take(p_key text, p_limit integer, p_window_sec integer) returns boolean
language plpgsql security definer set search_path = ops, public as $$
declare b timestamptz := to_timestamp(floor(extract(epoch from now()) / p_window_sec) * p_window_sec); c integer;
begin
  insert into ops.rate_limits (key, bucket, n) values (p_key, b, 1)
    on conflict (key, bucket) do update set n = ops.rate_limits.n + 1
    returning n into c;
  return c <= p_limit;
end;
$$;

-- ---------- 非常停止 ----------
create table ops.flags (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now(),
  updated_by uuid
);
insert into ops.flags (key, value) values
  ('maintenance', 'false'),           -- メンテナンス中の表示
  ('maintenance_message', '""'),      -- 利用者に見せる文
  ('checkin_enabled', 'true'),        -- チェックインを受け付けるか
  ('logging_enabled', 'true'),        -- 使われ方・エラー・断られたチェックインを記録するか
  ('admin_mfa_required', 'true');     -- 運営の関数に2段階認証を求めるか（開発中だけ false にできる）

create or replace function ops.flag(p_key text) returns jsonb
language sql stable security definer set search_path = ops as $$ select value from ops.flags where key = p_key $$;

-- アプリが起動時に読む（誰でも呼べる。軽い）
create or replace function public.app_status() returns jsonb
language sql stable security definer set search_path = ops as $$
  select jsonb_build_object('maintenance', ops.flag('maintenance'), 'message', ops.flag('maintenance_message'), 'checkin_enabled', ops.flag('checkin_enabled'))
$$;
grant execute on function public.app_status() to anon, authenticated;

-- ---------- 運営者の確認（2段階認証つき） ----------
create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = ops, public as $$
  select exists (select 1 from ops.admins where user_id = auth.uid())
     and (coalesce((ops.flag('admin_mfa_required'))::boolean, true) = false
          or coalesce(auth.jwt() ->> 'aal', 'aal1') = 'aal2')
$$;
-- 2段階認証の前でも「運営者として登録されているか」だけは分かるようにする（画面の案内用）
create or replace function public.admin_registered() returns boolean
language sql stable security definer set search_path = ops as $$ select exists (select 1 from ops.admins where user_id = auth.uid()) $$;
revoke all on function public.admin_registered() from public, anon;
grant execute on function public.admin_registered() to authenticated;

create or replace function public.admin_flags() returns jsonb
language plpgsql stable security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return (select jsonb_object_agg(key, jsonb_build_object('value', value, 'updated_at', updated_at)) from ops.flags);
end;
$$;

create or replace function public.admin_set_flag(p_key text, p_value jsonb) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_key not in ('maintenance', 'maintenance_message', 'checkin_enabled', 'logging_enabled') then raise exception 'unknown flag'; end if;
  if p_key = 'maintenance_message' and (jsonb_typeof(p_value) <> 'string' or length(p_value #>> '{}') > 200) then raise exception 'bad value'; end if;
  if p_key <> 'maintenance_message' and jsonb_typeof(p_value) <> 'boolean' then raise exception 'bad value'; end if;
  update ops.flags set value = p_value, updated_at = now(), updated_by = auth.uid() where key = p_key;
  insert into ops.admin_actions (admin_id, action, target, detail) values (auth.uid(), 'set_flag', p_key, jsonb_build_object('value', p_value));
end;
$$;
revoke all on function public.admin_flags(), public.admin_set_flag(text, jsonb) from public, anon;
grant execute on function public.admin_flags(), public.admin_set_flag(text, jsonb) to authenticated;

-- ---------- 記録の受け口：回数制限と非常停止を追加 ----------
create or replace function public.log_events(p_session text, p_platform text, p_version text, p_events jsonb) returns integer
language plpgsql security definer set search_path = ops, public as $$
declare n integer;
begin
  if not coalesce((ops.flag('logging_enabled'))::boolean, true) then return 0; end if;
  if p_session !~ '^[a-z0-9]{8,32}$' then raise exception 'bad session'; end if;
  if jsonb_typeof(p_events) <> 'array' or jsonb_array_length(p_events) = 0 or jsonb_array_length(p_events) > 50 then raise exception 'bad events'; end if;
  -- 1つの起動から1分に6回まで、全体で1分に3,000回まで（超えた分は黙って捨てる）
  if not ops.rl_take('ev:' || p_session, 6, 60) or not ops.rl_take('ev:all', 3000, 60) then return 0; end if;
  insert into ops.usage_events (session, platform, version, event, prop)
  select p_session, left(p_platform, 12), left(p_version, 16), e->>'e', left(e->>'p', 60)
    from jsonb_array_elements(p_events) as e
   where (e->>'e') ~ '^[a-z][a-z0-9_:.-]{0,39}$';
  get diagnostics n = row_count;
  return n;
end;
$$;

create or replace function public.log_error(p_session text, p_platform text, p_version text, p_kind text, p_message text, p_detail jsonb) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  if not coalesce((ops.flag('logging_enabled'))::boolean, true) then return; end if;
  if p_session !~ '^[a-z0-9]{8,32}$' or p_kind !~ '^[a-z_]{1,20}$' then raise exception 'bad input'; end if;
  if not ops.rl_take('er:' || p_session, 10, 3600) or not ops.rl_take('er:all', 600, 60) then return; end if;
  insert into ops.client_errors (session, platform, version, kind, message, detail)
  values (p_session, left(p_platform, 12), left(p_version, 16), p_kind, left(coalesce(p_message, ''), 300),
          case when p_detail is null or length(p_detail::text) > 1000 then null else p_detail end);
end;
$$;

-- 断られたチェックインの記録（checkin 関数だけが呼ぶ）
create or replace function public.log_rejection(p_reason text, p_airport integer, p_dist_km numeric, p_accuracy integer, p_queued boolean) returns void
language plpgsql security definer set search_path = ops, public as $$
begin
  if not coalesce((ops.flag('logging_enabled'))::boolean, true) then return; end if;
  if not ops.rl_take('rj:all', 3000, 60) then return; end if;
  insert into ops.checkin_rejections (reason, airport_id, dist_km, accuracy_m, queued) values (left(p_reason, 30), p_airport, p_dist_km, p_accuracy, p_queued);
end;
$$;
revoke all on function public.log_rejection(text, integer, numeric, integer, boolean) from public, anon, authenticated;

-- サーバーの処理（Edge Function）から使う回数制限
create or replace function public.rl_check(p_key text, p_limit integer, p_window_sec integer) returns boolean
language sql security definer set search_path = ops as $$ select ops.rl_take(p_key, p_limit, p_window_sec) $$;
revoke all on function public.rl_check(text, integer, integer) from public, anon, authenticated;

-- サーバーの処理がチェックイン前に読む（非常停止）
create or replace function public.checkin_allowed() returns boolean
language sql stable security definer set search_path = ops as $$ select coalesce((ops.flag('checkin_enabled'))::boolean, true) and not coalesce((ops.flag('maintenance'))::boolean, false) $$;
revoke all on function public.checkin_allowed() from public, anon, authenticated;

-- service_role（Edge Function）には使わせる
do $$ begin
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    grant execute on function public.log_rejection(text, integer, numeric, integer, boolean), public.rl_check(text, integer, integer), public.checkin_allowed() to service_role;
  end if;
end $$;

-- 回数制限の古い区切りと、記録を消す
create or replace function public.insights_cleanup() returns void
language sql security definer set search_path = ops, public as $$
  delete from ops.usage_events where created_at < now() - interval '180 days';
  delete from ops.client_errors where created_at < now() - interval '180 days';
  delete from ops.checkin_rejections where created_at < now() - interval '365 days';
  delete from ops.rate_limits where bucket < now() - interval '1 day';
$$;
revoke all on function public.insights_cleanup() from public, anon, authenticated;

-- 移した表を参照している関数の search_path に ops を足す（表の名前の解決のため）
alter function public.admin_stats()                     set search_path = ops, public, auth;
alter function public.admin_flagged(integer)            set search_path = ops, public, auth;
alter function public.admin_clear_flags(bigint)         set search_path = ops, public;
alter function public.admin_void_checkin(bigint, text)  set search_path = ops, public;
alter function public.admin_metrics(integer)            set search_path = ops, public, auth;
alter function public.admin_usage(integer)              set search_path = ops, public;
alter function public.admin_errors(integer)             set search_path = ops, public;
alter function public.admin_quality(integer)            set search_path = ops, public;

-- admin_metrics は使われ方の表を「public.」付きで参照していたので、ops に合わせて作り直す
create or replace function public.admin_metrics(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = ops, public, auth as $$
declare d integer := least(greatest(p_days, 7), 120);
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'daily', (select coalesce(jsonb_agg(x order by x.day), '[]'::jsonb) from (
        select g.day::date as day,
               (select count(distinct user_id) from public.checkins c where (c.created_at at time zone 'Asia/Tokyo')::date = g.day) as active,
               (select count(*) from public.checkins c where (c.created_at at time zone 'Asia/Tokyo')::date = g.day) as checkins,
               (select count(*) from public.flights f where (f.arr_at at time zone 'Asia/Tokyo')::date = g.day) as flights,
               (select count(*) from auth.users u where (u.created_at at time zone 'Asia/Tokyo')::date = g.day) as signups,
               (select count(distinct session) from ops.usage_events e where (e.created_at at time zone 'Asia/Tokyo')::date = g.day and e.event = 'open') as opens
          from generate_series((now() at time zone 'Asia/Tokyo')::date - (d - 1), (now() at time zone 'Asia/Tokyo')::date, interval '1 day') as g(day)) x),
    'active7',  (select count(distinct user_id) from public.checkins where created_at > now() - interval '7 days'),
    'active30', (select count(distinct user_id) from public.checkins where created_at > now() - interval '30 days'),
    -- 30日以上前に登録した人のうち、この30日にチェックインした人の割合
    'retention30', (select case when count(*) = 0 then null else round(100.0 * count(*) filter (where exists (
                        select 1 from public.checkins c where c.user_id = u.id and c.created_at > now() - interval '30 days')) / count(*), 1) end
                      from auth.users u where u.created_at < now() - interval '30 days'),
    'top_airports', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select a.name, count(*) as checkins, count(distinct c.user_id) as users from public.checkins c join public.airports a on a.id = c.airport_id
         where c.created_at > now() - make_interval(days => d) group by a.name order by 2 desc limit 15) x),
    'top_routes', (select coalesce(jsonb_agg(x), '[]'::jsonb) from (
        select x1.name || ' ⇄ ' || x2.name as route, count(*) as flights from public.flights f
          join public.airports x1 on x1.id = least(f.from_airport, f.to_airport) join public.airports x2 on x2.id = greatest(f.from_airport, f.to_airport)
         where f.arr_at > now() - make_interval(days => d) group by 1 order by 2 desc limit 15) x),
    'plus', jsonb_build_object(
        'active', (select count(*) from public.subscriptions where status in ('active', 'trialing')),
        'canceled_30', (select count(*) from public.subscriptions where status = 'canceled' and updated_at > now() - interval '30 days')));
end;
$$;
