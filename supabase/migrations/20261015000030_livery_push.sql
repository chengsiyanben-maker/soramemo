-- 特別塗装機が近づいたらスマホへ通知する：空港ごとに申し込む（sp_airports）。同じ機体・同じ空港の通知は6時間に1回まで（livery_notified）
alter table public.push_subs add column if not exists sp_airports text[] not null default '{}';
alter table public.push_subs drop constraint if exists push_subs_sp_airports_check;
alter table public.push_subs add constraint push_subs_sp_airports_check check (cardinality(sp_airports) <= 14);

create table if not exists public.livery_notified (
  reg          text not null,
  iata         text not null,
  notified_at  timestamptz not null default now(),
  primary key (reg, iata)
);
alter table public.livery_notified enable row level security;
revoke all on public.livery_notified from public, anon, authenticated;
