-- 空港の周りの機体の「通ってきた線」を、サーバーの関数（airport-traffic）の呼び出しをまたいで残す。
-- 書き読みするのはサーバーの関数（service_role）だけ。利用者からは直接読めない。20分より古い位置は関数が消す。
create table if not exists public.traffic_trails (
  iata       text not null,
  hex        text not null,
  pts        jsonb not null default '[]'::jsonb,   -- [[時刻ミリ秒, 緯度, 経度], ...]
  updated_at timestamptz not null default now(),
  primary key (iata, hex)
);
alter table public.traffic_trails enable row level security;
revoke all on public.traffic_trails from public, anon, authenticated;
