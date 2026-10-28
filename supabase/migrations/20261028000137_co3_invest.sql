-- エアライン経営 co-v3：出資（資本提携。仕様書「買収のかわり」。格付け3から）
--   出す側が申し込み、相手が認めたら成立。相手の会社の価値の20%まで（成立したときの価値で割合を決める）
--   相手には資金が入り、出した側は相手の毎日のもうけ（収益 − 維持費。マイナスなら0）のうち出資した割合を受け取る（相手の受け取りから引く）
--   1社が受け入れられる出資は合計49%まで。同じ相手への出資は1つだけ
--   引き上げは成立から30日後から。そのときの相手の会社の価値 × 割合が戻る（相手の資金から。足りなければ相手の資金のぶんだけ）
--   出資したお金は、出した側の会社の価値に数えない（会社の価値の決め方は変えない）

create table if not exists public.co3_invest (
  id bigint generated always as identity primary key,
  investor uuid not null references auth.users (id) on delete cascade,
  target uuid not null references auth.users (id) on delete cascade,
  amount bigint not null check (amount > 0),
  pct numeric(6, 4),
  status text not null default 'offer' check (status in ('offer', 'active', 'withdrawn', 'declined')),
  created_at timestamptz not null default now(),
  accepted_at timestamptz,
  closed_at timestamptz,
  returned bigint,
  check (investor <> target)
);
create unique index if not exists co3_invest_one on public.co3_invest (investor, target) where status in ('offer', 'active');
alter table public.co3_invest enable row level security;
revoke all on public.co3_invest from public, anon, authenticated;
grant select on public.co3_invest to authenticated;
drop policy if exists co3_invest_own on public.co3_invest;
create policy co3_invest_own on public.co3_invest for select to authenticated using (investor = (select auth.uid()) or target = (select auth.uid()));

-- いままでの1日の稼ぎ（出資の受け渡しの前）を co3_gross_pre として残す
do $do$
declare src text;
begin
  if to_regprocedure('public.co3_gross_pre(uuid)') is null then
    select pg_get_functiondef('public.co3_gross(uuid)'::regprocedure) into src;
    src := replace(src, 'FUNCTION public.co3_gross(', 'FUNCTION public.co3_gross_pre(');
    execute src;
    execute 'revoke all on function public.co3_gross_pre(uuid) from public, anon, authenticated';
  end if;
end
$do$;

-- その会社の1日のもうけ（出資の受け渡しの前。マイナスなら0）
create or replace function public.co3_profit_pre(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$ select greatest(0, co3_gross_pre(p_uid) - co_upkeep(p_uid))::numeric $$;
revoke all on function public.co3_profit_pre(uuid) from public, anon, authenticated;

-- 出資の受け渡し（受け取る − 渡す）
create or replace function public.co3_inv_flow(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select sum(i.pct * co3_profit_pre(i.target)) from co3_invest i where i.investor = p_uid and i.status = 'active'), 0)
       - coalesce((select sum(i.pct) from co3_invest i where i.target = p_uid and i.status = 'active'), 0) * co3_profit_pre(p_uid)
$$;
revoke all on function public.co3_inv_flow(uuid) from public, anon, authenticated;

create or replace function public.co3_gross(p_uid uuid) returns bigint
language sql stable security definer set search_path = public as $$ select (co3_gross_pre(p_uid) + round(co3_inv_flow(p_uid)))::bigint $$;
revoke all on function public.co3_gross(uuid) from public, anon, authenticated;

-- 申し込む（出す側）
create or replace function public.co3_inv_offer(p_code text, p_amount bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); t uuid;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  select user_id into t from companies where friend_code = upper(btrim(coalesce(p_code, '')));
  if t is null or t = uid then raise exception 'code not found'; end if;
  if p_amount is null or p_amount <= 0 then raise exception 'invalid amount'; end if;
  if p_amount > floor(co_value(t) * 0.2) then raise exception 'invest limit'; end if;
  if (select cash from companies where user_id = uid) < p_amount then raise exception 'not enough cash'; end if;
  if exists (select 1 from co3_invest where investor = uid and target = t and status in ('offer', 'active')) then raise exception 'already invested'; end if;
  insert into co3_invest (investor, target, amount) values (uid, t, p_amount);
  return co_state();
end;
$$;
revoke all on function public.co3_inv_offer(text, bigint) from public, anon;
grant execute on function public.co3_inv_offer(text, bigint) to authenticated;

-- 認める・断る（受ける側）
create or replace function public.co3_inv_answer(p_id bigint, p_ok boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); i record; v bigint; p numeric;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into i from co3_invest where id = p_id and target = uid and status = 'offer' for update;
  if not found then raise exception 'invest not found'; end if;
  if not p_ok then update co3_invest set status = 'declined', closed_at = now() where id = p_id; return co_state(); end if;
  v := co_value(uid);
  p := round(i.amount::numeric / greatest(v, 1), 4);
  if p > 0.2 then raise exception 'invest limit'; end if;
  if coalesce((select sum(pct) from co3_invest where target = uid and status = 'active'), 0) + p > 0.49 then raise exception 'invest total limit'; end if;
  update companies set cash = cash - i.amount where user_id = i.investor and cash >= i.amount;
  if not found then raise exception 'investor cannot pay'; end if;
  update companies set cash = cash + i.amount where user_id = uid;
  update co3_invest set status = 'active', pct = p, accepted_at = now() where id = p_id;
  return co_state();
end;
$$;
revoke all on function public.co3_inv_answer(bigint, boolean) from public, anon;
grant execute on function public.co3_inv_answer(bigint, boolean) to authenticated;

-- 引き上げる（出す側。成立から30日後から）・申し込みを取り消す
create or replace function public.co3_inv_withdraw(p_id bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); i record; back bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into i from co3_invest where id = p_id and investor = uid and status in ('offer', 'active') for update;
  if not found then raise exception 'invest not found'; end if;
  if i.status = 'offer' then update co3_invest set status = 'declined', closed_at = now() where id = p_id; return co_state(); end if;
  if i.accepted_at > now() - interval '30 days' then raise exception 'invest locked'; end if;
  perform co_settle(i.target);
  back := least(floor(co_value(i.target) * i.pct), (select cash from companies where user_id = i.target))::bigint;
  update companies set cash = cash - back where user_id = i.target;
  update companies set cash = cash + back where user_id = uid;
  update co3_invest set status = 'withdrawn', closed_at = now(), returned = back where id = p_id;
  return co_state();
end;
$$;
revoke all on function public.co3_inv_withdraw(bigint) from public, anon;
grant execute on function public.co3_inv_withdraw(bigint) to authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_invest' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、出資を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'invest', case when v3 then jsonb_build_object(
        'flow', round(co3_inv_flow(uid)), 'taken', coalesce((select sum(pct) from co3_invest where target = uid and status = 'active'), 0),
        'list', coalesce((select jsonb_agg(jsonb_build_object('id', i.id, 'role', case when i.investor = uid then 'out' else 'in' end,
                     'partner', (select name from companies where user_id = case when i.investor = uid then i.target else i.investor end),
                     'amount', i.amount, 'pct', i.pct, 'status', i.status, 'accepted_at', i.accepted_at,
                     'daily', case when i.status = 'active' then round(i.pct * co3_profit_pre(i.target)) end,
                     'unlock', case when i.status = 'active' then i.accepted_at + interval '30 days' end) order by i.created_at desc)
                   from co3_invest i where uid in (i.investor, i.target) and i.status in ('offer', 'active')), '[]'::jsonb)) end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;
