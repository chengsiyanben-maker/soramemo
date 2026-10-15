-- 特別塗装機で飛ぶ予定の便（航空会社の運航情報の文に「〇〇で運航いたします」とあるもの）。odpt-status が見つけて入れ、
-- その空港の特別塗装機の通知を申し込んでいる人に、飛ぶ前に1回だけ知らせる。利用者は public.livery_plans_upcoming() で読む
create table if not exists public.livery_plans (
  schedule_id bigint primary key references public.flight_schedule(id) on delete cascade,
  flight      text not null,
  dep         text not null check (dep ~ '^[A-Z]{3}$'),
  arr         text not null check (arr ~ '^[A-Z]{3}$'),
  std         timestamptz not null,
  livery      text not null check (length(livery) between 1 and 60),
  note        text check (length(note) <= 120),
  created_at  timestamptz not null default now()
);
create index if not exists livery_plans_std on public.livery_plans (std);
alter table public.livery_plans enable row level security;
revoke all on public.livery_plans from public, anon, authenticated;

-- これから飛ぶ予定（定刻が1時間前〜36時間後）。空港を渡すと、その空港を出発・到着する便を先に並べる
create or replace function public.livery_plans_upcoming(p_iata text default null) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('flight', p.flight, 'dep', p.dep, 'arr', p.arr, 'std', p.std, 'sta', s.sta,
           'livery', p.livery, 'note', p.note, 'atd', s.atd, 'cancelled', coalesce(s.dep_status ~* 'cancel', false))
           order by (p_iata is not null and (p.dep = p_iata or p.arr = p_iata)) desc, p.std), '[]'::jsonb)
  from public.livery_plans p join public.flight_schedule s on s.id = p.schedule_id
  where p.std > now() - interval '1 hour' and p.std < now() + interval '36 hours'
$$;
revoke all on function public.livery_plans_upcoming(text) from public;
grant execute on function public.livery_plans_upcoming(text) to anon, authenticated;
