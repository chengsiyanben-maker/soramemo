-- そらメモ：初期スキーマ
-- 方針：利用者は自分の記録を「読む」だけ。チェックインとフライトの書き込みは
--       Edge Function（checkin）がサーバー権限で行う。手入力の記録帳だけは本人が書ける。

-- 空港（国土交通省 空港一覧 2026-09-01 × OurAirports）
create table public.airports (
  id          integer primary key,
  name        text    not null,
  icao        text,
  iata        text,
  category    text    not null,
  prefecture  text    not null,
  lat         double precision not null,
  lon         double precision not null,
  radius_m    integer not null check (radius_m > 0),
  rare        boolean not null default false,
  game_target boolean not null default false
);

-- ターミナル（羽田・成田。座標は OpenStreetMap）
create table public.terminals (
  id         text primary key,                       -- 例: HND-T1
  airport_id integer not null references public.airports(id),
  short      text not null,                          -- 例: 羽田
  name       text not null,                          -- 例: 第1ターミナル
  tag        text not null,                          -- 例: T1
  lat        double precision not null,
  lon        double precision not null
);

-- チェックイン
create table public.checkins (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  airport_id  integer not null references public.airports(id),
  terminal_id text references public.terminals(id),
  lat         double precision not null,
  lon         double precision not null,
  accuracy_m  real not null,
  position_at timestamptz not null,                  -- 端末が位置を取得した時刻（参考）
  created_at  timestamptz not null default now(),    -- サーバーが受け付けた時刻（判定はこちらを使う）
  flags       text[] not null default '{}'           -- 例: impossible_speed, low_accuracy
);
create index checkins_user_time on public.checkins (user_id, created_at desc);
create index checkins_user_airport on public.checkins (user_id, airport_id);
create index checkins_flagged on public.checkins using gin (flags) where flags <> '{}';

-- フライト（2回のチェックインから成立）
create table public.flights (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users(id) on delete cascade,
  from_airport integer not null references public.airports(id),
  to_airport   integer not null references public.airports(id),
  dep_checkin  bigint references public.checkins(id) on delete set null,
  arr_checkin  bigint references public.checkins(id) on delete set null,
  dep_at       timestamptz not null,
  arr_at       timestamptz not null,
  distance_km  real not null,
  status       text not null default 'provisional'
               check (status in ('provisional', 'with_flight_no', 'verified', 'no_data')),
  flight_no    text,
  verified_at  timestamptz,
  check (from_airport <> to_airport),
  check (arr_at > dep_at)
);
create index flights_user_time on public.flights (user_id, arr_at desc);
create index flights_status on public.flights (status) where status in ('provisional', 'with_flight_no');

-- 記録帳（過去のフライトの手入力。印や路線数には入らない）
create table public.manual_flights (
  id           bigint generated always as identity primary key,
  user_id      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  from_airport integer not null references public.airports(id),
  to_airport   integer not null references public.airports(id),
  flown_on     date not null check (flown_on <= current_date + 1),
  created_at   timestamptz not null default now(),
  check (from_airport <> to_airport)
);
create index manual_user on public.manual_flights (user_id, flown_on desc);

-- ---------- 行レベルセキュリティ ----------
alter table public.airports       enable row level security;
alter table public.terminals      enable row level security;
alter table public.checkins       enable row level security;
alter table public.flights        enable row level security;
alter table public.manual_flights enable row level security;

-- 空港とターミナルは誰でも読める
create policy "airports are public"  on public.airports  for select to anon, authenticated using (true);
create policy "terminals are public" on public.terminals for select to anon, authenticated using (true);

-- チェックインとフライトは本人だけが読める（書き込みのポリシーは作らない＝利用者は書けない）
create policy "own checkins" on public.checkins for select to authenticated using (user_id = auth.uid());
create policy "own flights"  on public.flights  for select to authenticated using (user_id = auth.uid());

-- 記録帳は本人が読み書き・削除できる
create policy "read own manual"   on public.manual_flights for select to authenticated using (user_id = auth.uid());
create policy "add own manual"    on public.manual_flights for insert to authenticated with check (user_id = auth.uid());
create policy "delete own manual" on public.manual_flights for delete to authenticated using (user_id = auth.uid());

-- 念のため、利用者ロールからチェックイン・フライトへの書き込み権限そのものを外す
revoke insert, update, delete on public.checkins from anon, authenticated;
revoke insert, update, delete on public.flights  from anon, authenticated;
revoke insert, update, delete on public.airports, public.terminals from anon, authenticated;
