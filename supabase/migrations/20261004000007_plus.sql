-- そらメモ＋（月額500円）
-- 加入状態は決済サービス（Stripe）からの通知を受けた Edge Function（plus-webhook）だけが書き込む。
-- 有料機能：年間まとめ（表示はアプリ側）、過去フライトの一括取り込み（下の関数で加入を確かめる）

create table public.subscriptions (
  user_id               uuid primary key references auth.users(id) on delete cascade,
  status                text not null check (status in ('active', 'trialing', 'past_due', 'canceled', 'incomplete', 'unpaid')),
  current_period_end    timestamptz,
  provider              text not null default 'stripe',
  provider_customer     text,
  provider_subscription text,
  updated_at            timestamptz not null default now()
);
alter table public.subscriptions enable row level security;
create policy "own subscription" on public.subscriptions for select to authenticated using (user_id = auth.uid());
revoke insert, update, delete on public.subscriptions from anon, authenticated;

create or replace function public.is_plus(p_uid uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from subscriptions
                  where user_id = p_uid and status in ('active', 'trialing')
                    and (current_period_end is null or current_period_end > now()))
$$;
revoke all on function public.is_plus(uuid) from public, anon, authenticated;

create or replace function public.plus_status() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('plus', is_plus(auth.uid()),
           'status', (select status from subscriptions where user_id = auth.uid()),
           'until', (select current_period_end from subscriptions where user_id = auth.uid()))
$$;

-- 過去フライトの一括取り込み（そらメモ＋）。rows = [{"from":5,"to":6,"date":"2025-08-01","airline":"JL"}, ...]、1回500件まで
create or replace function public.import_manual_flights(p_rows jsonb) returns integer
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); n integer;
begin
  if uid is null then raise exception 'not signed in'; end if;
  if not is_plus(uid) then raise exception 'plus required'; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) = 0 then raise exception 'no rows'; end if;
  if jsonb_array_length(p_rows) > 500 then raise exception 'too many rows'; end if;
  insert into manual_flights (user_id, from_airport, to_airport, flown_on, airline)
  select uid, (r->>'from')::integer, (r->>'to')::integer, (r->>'date')::date, nullif(r->>'airline', '')
    from jsonb_array_elements(p_rows) as r;
  get diagnostics n = row_count;
  return n;
end;
$$;

revoke all on function public.plus_status(), public.import_manual_flights(jsonb) from public, anon;
grant execute on function public.plus_status(), public.import_manual_flights(jsonb) to authenticated;
