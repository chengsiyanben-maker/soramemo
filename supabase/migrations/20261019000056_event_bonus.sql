-- 行事に合わせた期間限定のボーナス：期間中に空港でチェックインすると、エアライン経営の資金がもらえる（空港ごとに1回）。
--   game_events   ：行事（名前・期間・1空港あたりの資金〔万円〕・珍しい空港の倍率）。運営画面（admin_set_event）で足す・直す
--   event_bonuses ：もらったボーナス。チェックインのとき（checkin 関数、service_role）に作り、
--                   経営の「受け取る」（co_collect）で資金に入れる。経営の公開前にもらった分も、公開後に受け取れる
create table if not exists public.game_events (
  id        text primary key check (id ~ '^[a-z0-9-]{3,40}$'),
  name      text not null check (length(name) between 1 and 40),
  starts_at timestamptz not null,
  ends_at   timestamptz not null,
  bonus     bigint not null check (bonus between 0 and 1000000),
  rare_mult numeric not null default 2 check (rare_mult between 1 and 5),
  note      text check (length(note) <= 200),
  check (ends_at > starts_at and ends_at - starts_at <= interval '31 days')
);
create table if not exists public.event_bonuses (
  user_id     uuid not null references auth.users(id) on delete cascade,
  event_id    text not null references public.game_events(id) on delete cascade,
  airport_id  integer not null references public.airports(id),
  amount      bigint not null check (amount >= 0),
  created_at  timestamptz not null default now(),
  credited_at timestamptz,
  primary key (user_id, event_id, airport_id)
);
create index if not exists event_bonuses_open on public.event_bonuses (user_id) where credited_at is null;
alter table public.game_events enable row level security;
alter table public.event_bonuses enable row level security;
revoke all on public.game_events, public.event_bonuses from public, anon, authenticated;

-- 開いている行事と、14日以内に始まる行事（誰でも見られる）
create or replace function public.current_events() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'name', name, 'starts_at', starts_at, 'ends_at', ends_at, 'bonus', bonus, 'rare_mult', rare_mult, 'note', note,
           'open', now() >= starts_at) order by starts_at), '[]'::jsonb)
  from public.game_events where ends_at > now() and starts_at < now() + interval '14 days'
$$;
revoke all on function public.current_events() from public;
grant execute on function public.current_events() to anon, authenticated;

-- チェックインのときに呼ぶ（service_role だけ）：その時刻に開いている行事のボーナスを、空港ごとに1回だけ作る。作った分を返す
create or replace function public.grant_event_bonus(p_uid uuid, p_airport integer, p_at timestamptz) returns jsonb
language sql volatile security definer set search_path = public as $$
  with ins as (
    insert into public.event_bonuses (user_id, event_id, airport_id, amount, created_at)
    select p_uid, e.id, p_airport, round(e.bonus * case when a.rare then e.rare_mult else 1 end), p_at
    from public.game_events e join public.airports a on a.id = p_airport
    where p_at >= e.starts_at and p_at < e.ends_at
    on conflict do nothing
    returning event_id, amount
  )
  select coalesce(jsonb_agg(jsonb_build_object('event', ins.event_id, 'name', e.name, 'amount', ins.amount)), '[]'::jsonb)
  from ins join public.game_events e on e.id = ins.event_id
$$;
revoke all on function public.grant_event_bonus(uuid, integer, timestamptz) from public, anon, authenticated;

-- 自分のまだ受け取っていないボーナスの合計（経営の画面に出す）
create or replace function public.my_event_bonus() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('pending', coalesce(sum(amount) filter (where credited_at is null), 0), 'total', coalesce(sum(amount), 0), 'count', count(*))
  from public.event_bonuses where user_id = auth.uid()
$$;
revoke all on function public.my_event_bonus() from public, anon;
grant execute on function public.my_event_bonus() to authenticated;

-- 受け取る：これまでどおり貯まった収益に、まだ受け取っていないボーナスを足す
create or replace function public.co_collect() returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); c companies; pend bigint; bon bigint;
begin
  if uid is null then raise exception 'not signed in'; end if;
  perform co_state();
  select * into c from companies where user_id = uid for update;
  pend := floor(co_daily(uid) * extract(epoch from (now() - greatest(c.last_collect, now() - interval '7 days'))) / 86400);
  with b as (update event_bonuses set credited_at = now() where user_id = uid and credited_at is null returning amount)
  select coalesce(sum(amount), 0) into bon from b;
  update companies set cash = cash + greatest(pend, 0) + bon, last_collect = now() where user_id = uid;
  return co_state();
end;
$$;
revoke all on function public.co_collect() from public, anon;
grant execute on function public.co_collect() to authenticated;

-- 運営画面から行事を足す・直す・消す（p_bonus が null なら消す）
create or replace function public.admin_set_event(p_id text, p_name text, p_starts_at timestamptz, p_ends_at timestamptz, p_bonus bigint, p_rare_mult numeric default 2, p_note text default null)
returns void language plpgsql security definer set search_path = ops, public as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_bonus is null then delete from public.game_events where id = p_id;
  else
    insert into public.game_events (id, name, starts_at, ends_at, bonus, rare_mult, note) values (p_id, p_name, p_starts_at, p_ends_at, p_bonus, coalesce(p_rare_mult, 2), p_note)
    on conflict (id) do update set name = excluded.name, starts_at = excluded.starts_at, ends_at = excluded.ends_at, bonus = excluded.bonus, rare_mult = excluded.rare_mult, note = excluded.note;
  end if;
  insert into ops.admin_actions (admin_id, action, target, detail) values (auth.uid(), 'set_event', p_id,
    jsonb_build_object('name', p_name, 'starts_at', p_starts_at, 'ends_at', p_ends_at, 'bonus', p_bonus, 'rare_mult', p_rare_mult));
end;
$$;
revoke all on function public.admin_set_event(text, text, timestamptz, timestamptz, bigint, numeric, text) from public, anon;
grant execute on function public.admin_set_event(text, text, timestamptz, timestamptz, bigint, numeric, text) to authenticated;

-- 最初の行事：年末年始（日本時間 12月27日〜1月4日）。1空港 5,000万円（プロペラ機の半分）、珍しい空港は2倍
insert into public.game_events (id, name, starts_at, ends_at, bonus, rare_mult, note) values
  ('newyear-2027', '年末年始ボーナス', '2026-12-27T00:00:00+09:00', '2027-01-05T00:00:00+09:00', 5000, 2, '帰省や旅行で空港へ行く人が多い時期')
on conflict (id) do nothing;
