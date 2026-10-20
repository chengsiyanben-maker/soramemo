-- 撮影の知らせ：いつもの空港に、選んだ種類の機体（特別塗装機・大きな機体・海外の航空会社・指定した登録記号・指定した便）が
-- 着陸の数分前（3・5・10分）に近づいたら、スマホへ通知する。運用（滑走路の向き）が変わったときも知らせる。
-- 同じ機体の知らせは1日1回まで（spot_notified）。書くのは push-subscribe と airport-traffic（service_role）だけ
alter table public.push_subs add column if not exists spot_iata text check (spot_iata ~ '^[A-Z]{3}$');
alter table public.push_subs add column if not exists spot_kinds text[] not null default '{}';
alter table public.push_subs add column if not exists spot_lead int not null default 5;
alter table public.push_subs add column if not exists spot_regs text[] not null default '{}';
alter table public.push_subs add column if not exists spot_flights text[] not null default '{}';
alter table public.push_subs drop constraint if exists push_subs_spot_check;
alter table public.push_subs add constraint push_subs_spot_check check (
  spot_lead in (3, 5, 10) and cardinality(spot_kinds) <= 5 and cardinality(spot_regs) <= 10 and cardinality(spot_flights) <= 10
  and spot_kinds <@ array['special', 'big', 'foreign', 'reg', 'ops']::text[]);
create index if not exists push_subs_spot_iata on public.push_subs (spot_iata) where spot_iata is not null;

create table if not exists public.spot_notified (
  sub_id       bigint not null references public.push_subs (id) on delete cascade,
  key          text not null check (length(key) <= 60),
  notified_at  timestamptz not null default now(),
  primary key (sub_id, key)
);
create index if not exists spot_notified_at on public.spot_notified (notified_at);
alter table public.spot_notified enable row level security;
revoke all on public.spot_notified from public, anon, authenticated;
