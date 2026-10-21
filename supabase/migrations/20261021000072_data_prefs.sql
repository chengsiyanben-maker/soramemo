-- データの使い方（利用者が選ぶ）：統計に使う（はじめからオン）・カードやホテルの案内を受け取る・研究や調査への協力（どちらもはじめはオフ）
--   統計は、個人が分からない集計だけ。10人未満の区切りは出さない（admin_stats_report）。統計をオフにした人の記録は集計に入れない
create table if not exists public.user_data_prefs (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  stats      boolean not null default true,
  offers     boolean not null default false,
  research   boolean not null default false,
  updated_at timestamptz not null default now()
);
alter table public.user_data_prefs enable row level security;
revoke all on public.user_data_prefs from public, anon, authenticated;

create or replace function public.my_data_prefs() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce((select jsonb_build_object('stats', stats, 'offers', offers, 'research', research, 'updated_at', updated_at) from public.user_data_prefs where user_id = auth.uid()),
                  jsonb_build_object('stats', true, 'offers', false, 'research', false, 'updated_at', null))
$$;
revoke all on function public.my_data_prefs() from public, anon;
grant execute on function public.my_data_prefs() to authenticated;

create or replace function public.set_data_prefs(p_stats boolean, p_offers boolean, p_research boolean) returns jsonb
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'login required'; end if;
  insert into public.user_data_prefs (user_id, stats, offers, research, updated_at) values (auth.uid(), coalesce(p_stats, true), coalesce(p_offers, false), coalesce(p_research, false), now())
  on conflict (user_id) do update set stats = excluded.stats, offers = excluded.offers, research = excluded.research, updated_at = now();
  return public.my_data_prefs();
end $$;
revoke all on function public.set_data_prefs(boolean, boolean, boolean) from public, anon;
grant execute on function public.set_data_prefs(boolean, boolean, boolean) to authenticated;

-- 統計レポート（運営者だけ）：その空港の期間のチェックイン（月ごと・時間帯ごと）、修行の計画に入った路線、ゴーアラウンド（推定）。
--   人の数を数える区切りは、10人以上のときだけ数を出し、それより少なければ null。統計をオフにした人は数えない
create or replace function public.admin_stats_report(p_iata text, p_from date, p_to date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare k constant int := 10; ap int; r jsonb;
begin
  if not public.is_admin() then raise exception 'admin only'; end if;
  select id into ap from public.airports where iata = p_iata limit 1;
  with c as (
    select ci.user_id, ci.created_at at time zone 'Asia/Tokyo' as t from public.checkins ci
    where ci.airport_id = ap and ci.created_at >= (p_from::timestamp at time zone 'Asia/Tokyo') and ci.created_at < ((p_to + 1)::timestamp at time zone 'Asia/Tokyo')
      and not exists (select 1 from public.user_data_prefs d where d.user_id = ci.user_id and not d.stats)
  ), sg as (
    select s.user_id, least(p->>'from', p->>'to') || '-' || greatest(p->>'from', p->>'to') as route
    from public.shugyo_prefs s, jsonb_array_elements(coalesce(s.data->'plans', '[]'::jsonb)) p
    where (p->>'from' = p_iata or p->>'to' = p_iata)
      and not exists (select 1 from public.user_data_prefs d where d.user_id = s.user_id and not d.stats)
  )
  select jsonb_build_object('iata', p_iata, 'from', p_from, 'to', p_to, 'k', k,
    'checkins', (select jsonb_build_object('n', case when count(distinct user_id) >= k then count(*) end, 'users', case when count(distinct user_id) >= k then count(distinct user_id) end) from c),
    'by_month', coalesce((select jsonb_object_agg(m, n) from (select to_char(t, 'YYYY-MM') as m, case when count(distinct user_id) >= k then count(*) end as n from c group by 1) x), '{}'::jsonb),
    'by_hour', coalesce((select jsonb_object_agg(h, n) from (select extract(hour from t)::int as h, case when count(distinct user_id) >= k then count(*) end as n from c group by 1) x), '{}'::jsonb),
    'shugyo_routes', coalesce((select jsonb_agg(jsonb_build_object('route', route, 'users', n) order by n desc) from (select route, count(distinct user_id) as n from sg group by 1 having count(distinct user_id) >= k) x), '[]'::jsonb),
    'go_arounds', coalesce((select jsonb_object_agg(coalesce(rwy, '?'), n) from (select rwy, count(*) as n from public.ga_events where iata = p_iata and at >= (p_from::timestamp at time zone 'Asia/Tokyo') and at < ((p_to + 1)::timestamp at time zone 'Asia/Tokyo') group by 1) x), '{}'::jsonb)
  ) into r;
  return r;
end $$;
revoke all on function public.admin_stats_report(text, date, date) from public, anon;
grant execute on function public.admin_stats_report(text, date, date) to authenticated;
