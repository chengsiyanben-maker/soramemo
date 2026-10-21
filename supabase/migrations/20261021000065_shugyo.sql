-- 修行の画面：予定の便・会員情報（ステイタス・カード）・予算・乗れる日を1人1行で保存し、フライトに運賃の金額を入れられるようにする。
-- ・shugyo_prefs：本人だけが読み書きできる。中身はアプリが決めた形の JSON（大きさは 64KB まで）
-- ・flights / manual_flights の price：その便に払った運賃（円）。修行の「1ポイントあたり」と予算の計算に使う
create table if not exists public.shugyo_prefs (
  user_id     uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  data        jsonb not null default '{}'::jsonb check (jsonb_typeof(data) = 'object' and pg_column_size(data) <= 65536),
  updated_at  timestamptz not null default now()
);
alter table public.shugyo_prefs enable row level security;
revoke all on public.shugyo_prefs from public, anon;
grant select, insert, update, delete on public.shugyo_prefs to authenticated;
drop policy if exists "own shugyo prefs" on public.shugyo_prefs;
create policy "own shugyo prefs" on public.shugyo_prefs for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

alter table public.flights        add column if not exists price integer check (price is null or price between 0 and 10000000);
alter table public.manual_flights add column if not exists price integer check (price is null or price between 0 and 10000000);
grant update (price) on public.manual_flights to authenticated;

-- フライト（位置から記録した便）の運賃の金額は、本人だけがあとから入れられる（空港・時刻・距離は変えられないまま）
create or replace function public.set_flight_price(p_flight_id bigint, p_price integer) returns void
language plpgsql security definer set search_path = public as $$
begin
  if p_price is not null and (p_price < 0 or p_price > 10000000) then raise exception 'bad price'; end if;
  update public.flights set price = p_price where id = p_flight_id and user_id = auth.uid();
  if not found then raise exception 'flight not found'; end if;
end;
$$;
revoke all on function public.set_flight_price(bigint, integer) from public, anon;
grant execute on function public.set_flight_price(bigint, integer) to authenticated;

-- バックアップに修行の保存を足す
create or replace function public.admin_backup() returns jsonb
language plpgsql security definer set search_path = ops, public, auth as $$
declare out jsonb;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  out := jsonb_build_object(
    'app', 'soramemo', 'format', 1, 'created_at', now(),
    'users',           (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'email', email, 'created_at', created_at) order by created_at), '[]') from auth.users),
    'checkins',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.checkins t),
    'flights',         (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.flights t),
    'manual_flights',  (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.manual_flights t),
    'intl_flights',    (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.intl_flights t),
    'shugyo_prefs',    (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.shugyo_prefs t),
    'companies',       (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.companies t),
    'route_levels',    (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.route_levels t),
    'aircraft',        (select coalesce(jsonb_agg(to_jsonb(t) order by t.id), '[]') from public.aircraft t),
    'facilities',      (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.facilities t),
    'subscriptions',   (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from public.subscriptions t),
    'admins',          (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from ops.admins t),
    'flags',           (select coalesce(jsonb_agg(to_jsonb(t)), '[]') from ops.flags t));
  insert into ops.admin_actions (admin_id, action, target, detail)
  values (auth.uid(), 'backup', 'all', jsonb_build_object('users', jsonb_array_length(out->'users'), 'checkins', jsonb_array_length(out->'checkins'), 'flights', jsonb_array_length(out->'flights')));
  return out;
end;
$$;
revoke all on function public.admin_backup() from public, anon;
grant execute on function public.admin_backup() to authenticated;

-- 修行の路線の運航状況：その路線（出発→到着）の今日（日本時間）の便を、定刻・見込み・実際の時刻・欠航つきで返す（JAL・ANA の時刻表と運航情報）
create or replace function public.route_today(p_dep text, p_arr text) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', f.flight, 'std', f.std, 'sta', f.sta, 'etd', f.etd, 'eta', f.eta, 'atd', f.atd, 'ata', f.ata,
      'atd_inf', case when coalesce((w.state ->> 'takeoff_est')::boolean, true) = false then public.inferred_time(w.state, 'takeoff_at') end,
      'ata_inf', case when w.state ->> 'landed_iata' = f.arr then public.inferred_time(w.state, 'landed_at') end,
      'eta_inf', case when w.state ->> 'phase' = 'air' then public.inferred_time(w.state, 'eta') end,
      'aircraft', f.aircraft, 'cancelled', coalesce(f.dep_status ~* 'cancel' or f.arr_status ~* 'cancel', false)) order by f.std), '[]'::jsonb)
  from public.flight_schedule f left join public.flight_watch w on w.schedule_id = f.id
  where p_dep ~ '^[A-Z]{3}$' and p_arr ~ '^[A-Z]{3}$' and f.dep = p_dep and f.arr = p_arr and f.svc_date = (now() at time zone 'Asia/Tokyo')::date
$$;
revoke all on function public.route_today(text, text) from public;
grant execute on function public.route_today(text, text) to anon, authenticated;
