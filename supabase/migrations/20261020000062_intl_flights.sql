-- 国際線の記録：日本の空港と海外の空港を結ぶフライトを、本人が残す（記録帳と同じく、印や路線の数・図鑑には入らない）。
--   海外の空港は public.airports にないので、空港は IATA の記号（3文字）で持つ。どちらか一方は日本の空港（public.airports にある記号）にする
--   距離はアプリが世界の空港の位置（OpenFlights）から計算して入れる。出発・到着の時刻は、乗る便を追っていたときだけ入る
create table if not exists public.intl_flights (
  id          bigint generated always as identity primary key,
  user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
  flown_on    date not null check (flown_on >= date '1950-01-01' and flown_on <= current_date + 1),
  dep         text not null check (dep ~ '^[A-Z]{3}$'),
  arr         text not null check (arr ~ '^[A-Z]{3}$'),
  flight_no   text check (flight_no ~ '^[A-Z0-9]{2}[0-9]{1,4}[A-Z]?$'),
  airline     text check (length(airline) <= 40),
  seat        text check (length(seat) <= 8),
  dep_at      timestamptz,
  arr_at      timestamptz,
  distance_km real check (distance_km >= 0 and distance_km <= 20000),
  created_at  timestamptz not null default now(),
  check (dep <> arr),
  check (dep_at is null or arr_at is null or arr_at > dep_at)
);
create index if not exists intl_flights_user on public.intl_flights (user_id, flown_on desc);
alter table public.intl_flights enable row level security;
revoke all on public.intl_flights from public, anon;
grant select, insert, delete on public.intl_flights to authenticated;

-- 日本の空港の記号か（空港の表は利用者から直接は読めないので、関数で確かめる）
create or replace function public.is_japan_iata(p text) returns boolean
language sql stable security definer set search_path = public as $$ select exists (select 1 from public.airports where iata = p) $$;
revoke all on function public.is_japan_iata(text) from public;
grant execute on function public.is_japan_iata(text) to anon, authenticated;

drop policy if exists "intl flights: read own" on public.intl_flights;
create policy "intl flights: read own" on public.intl_flights for select to authenticated using (user_id = auth.uid());
drop policy if exists "intl flights: delete own" on public.intl_flights;
create policy "intl flights: delete own" on public.intl_flights for delete to authenticated using (user_id = auth.uid());
-- 書けるのは本人の行だけ。日本の空港をどちらか一方に含むこと（国内線どうしは記録帳へ）、1人2,000件まで
drop policy if exists "intl flights: insert own" on public.intl_flights;
create policy "intl flights: insert own" on public.intl_flights for insert to authenticated with check (
  user_id = auth.uid()
  and public.is_japan_iata(dep) <> public.is_japan_iata(arr)
  and (select count(*) from public.intl_flights x where x.user_id = auth.uid()) < 2000
);

-- バックアップに国際線の記録を足す（ほかは 20261004000014_backup.sql と同じ）
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
