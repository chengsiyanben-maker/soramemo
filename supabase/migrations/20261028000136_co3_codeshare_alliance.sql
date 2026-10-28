-- エアライン経営 co-v3：共同運航（コードシェア）とアライアンス（仕様書「共同運航」「アライアンス」）
-- 共同運航
--   売る会社（販売会社）が、飛ばす会社（運航会社）の路線に自社の便名をつけて席を売る
--   売れる路線：相手が機体を入れて飛ばしている路線。自分がその区間を飛んだことはいらないが、どちらかの空港を自分の路線に持っていること
--   結ぶ相手：友だち（運航会社が認めたら）・アライアンスの仲間（フリーセールは認めなしで始まる。ブロック買い取りは認めが要る）
--   運航会社として認めるのは格付け3から（「共同運航（飛ばす側）」）。売るのはだれでも
--   フリーセール：前払いなし。販売会社はその路線の1日の収益の15%を得る。運航会社は搭乗率が上がり、販売会社1社ごとに収益 +5%
--   ブロック買い取り：始めるときと毎月1日に、販売会社がその路線の1日の収益の5日分を運航会社に払う。その月は収益の35%を得る
--     （欠航などで収益が減ったぶんは販売会社の損。払えなければその月で終わる）
--   乗り継ぎ：販売会社の自分の路線のうち、共同運航の路線と空港でつながる路線は収益 +5%（最大 +15%）
--   上限：1路線の販売会社は3社まで。1社が売れる路線は格付けで 3・5・10・15・20本
--   発着枠は運航会社の枠を使う（販売会社はいらない）
-- アライアンス
--   50社まで。作れるのは格付け3（国内大手）以上の FSC。入るのはだれでも（LCC は入れない。ミドルコストは入れるが作れない）
--   1社が入れるのは1つだけ。抜けたら次に入れるのは7日後。リーダーは作った人（名前の変更・仲間を外す）。
--     リーダーが抜けたとき・30日ゲームに入らないときは、会社の価値がいちばん高い仲間がリーダーになる
--   本物のアライアンスの名前は使えない。名前は報告を受けて運営が直せる
--   仲間とは認めなしでフリーセールの共同運航ができる。仲間の施設がある空港は、その施設の効き目の半分（1段ごとに +3%）が自分の路線にも効く
--     （自分の施設がある空港は自分のものだけ）
--   アライアンスのランキング：仲間の会社の価値の合計と、今月の伸びの合計
--   アライアンス対抗戦（シーズンごと）：期間中の会社の価値の伸びを仲間の1社あたりで比べ、1位の仲間に 20,000・2位 10,000・3位 5,000 と称号、
--     上位3つのアライアンスの全員に印
--   発着枠を仲間に分ける・マイルを共通にするは、あとで足す

create table if not exists public.co3_alliances (
  id bigint generated always as identity primary key,
  name text not null unique check (char_length(btrim(name)) between 1 and 20),
  leader uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now()
);
alter table public.co3_alliances enable row level security;
revoke all on public.co3_alliances from public, anon, authenticated;
grant select on public.co3_alliances to authenticated;
drop policy if exists co3_alliances_read on public.co3_alliances;
create policy co3_alliances_read on public.co3_alliances for select to authenticated using (true);

create table if not exists public.co3_alliance_members (
  user_id uuid primary key references auth.users (id) on delete cascade,
  alliance_id bigint not null references public.co3_alliances (id) on delete cascade,
  joined_at timestamptz not null default now()
);
create index if not exists co3_alliance_members_a on public.co3_alliance_members (alliance_id);
alter table public.co3_alliance_members enable row level security;
revoke all on public.co3_alliance_members from public, anon, authenticated;
grant select on public.co3_alliance_members to authenticated;
drop policy if exists co3_alliance_members_read on public.co3_alliance_members;
create policy co3_alliance_members_read on public.co3_alliance_members for select to authenticated using (true);

alter table public.companies add column if not exists alliance_left_at timestamptz;
alter table public.companies enable row level security;

create table if not exists public.co3_codeshares (
  id bigint generated always as identity primary key,
  op_id uuid not null references auth.users (id) on delete cascade,
  seller_id uuid not null references auth.users (id) on delete cascade,
  route_key text not null,
  kind text not null check (kind in ('free', 'block')),
  status text not null default 'pending' check (status in ('pending', 'active', 'ended')),
  created_at timestamptz not null default now(),
  active_at timestamptz,
  paid_month date,
  ended_at timestamptz,
  check (op_id <> seller_id)
);
create unique index if not exists co3_codeshares_one on public.co3_codeshares (op_id, seller_id, route_key) where status <> 'ended';
create index if not exists co3_codeshares_op on public.co3_codeshares (op_id, status);
create index if not exists co3_codeshares_seller on public.co3_codeshares (seller_id, status);
alter table public.co3_codeshares enable row level security;
revoke all on public.co3_codeshares from public, anon, authenticated;
grant select on public.co3_codeshares to authenticated;
drop policy if exists co3_codeshares_own on public.co3_codeshares;
create policy co3_codeshares_own on public.co3_codeshares for select to authenticated using (op_id = (select auth.uid()) or seller_id = (select auth.uid()));

alter table public.co3_awards drop constraint if exists co3_awards_kind_check;
alter table public.co3_awards add constraint co3_awards_kind_check check (kind in ('season_top10', 'season_champ', 'ally_top3', 'ally_champ'));
alter table public.co3_awards enable row level security;

-- 仲間か（同じアライアンス）・友だちか
create or replace function public.co3_same_alliance(p_a uuid, p_b uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from co3_alliance_members x join co3_alliance_members y on y.alliance_id = x.alliance_id where x.user_id = p_a and y.user_id = p_b)
$$;
revoke all on function public.co3_same_alliance(uuid, uuid) from public, anon, authenticated;

create or replace function public.co3_is_friend(p_a uuid, p_b uuid) returns boolean
language sql stable security definer set search_path = public as $$ select exists (select 1 from co_friends where user_id = p_a and friend_id = p_b) $$;
revoke all on function public.co3_is_friend(uuid, uuid) from public, anon, authenticated;

-- 路線の両端の空港（iata）
create or replace function public.co3_route_ends(p_route text, out a text, out b text)
language sql stable security definer set search_path = public as $$
  select case when p_route ~ '^[0-9]+-[0-9]+$' then (select iata from airports where id = split_part(p_route, '-', 1)::int) else split_part(p_route, '-', 1) end,
         case when p_route ~ '^[0-9]+-[0-9]+$' then (select iata from airports where id = split_part(p_route, '-', 2)::int) else split_part(p_route, '-', 2) end
$$;
revoke all on function public.co3_route_ends(text) from public, anon, authenticated;

-- 会社の路線の空港（iata）
create or replace function public.co3_my_airports(p_uid uuid) returns setof text
language sql stable security definer set search_path = public as $$
  select distinct x from co_routes(p_uid) r cross join lateral co3_route_ends(r.route_key) e cross join lateral unnest(array[e.a, e.b]) x where x is not null
$$;
revoke all on function public.co3_my_airports(uuid) from public, anon, authenticated;

create or replace function co3.cs_limit(p_rating integer) returns integer
language sql immutable as $$ select (array[3, 5, 10, 15, 20])[greatest(1, least(5, coalesce(p_rating, 1)))] $$;
revoke all on function co3.cs_limit(integer) from public, anon, authenticated;

-- 運航会社のその路線の1日の収益
create or replace function public.co3_op_revenue(p_op uuid, p_route text) returns numeric
language sql stable security definer set search_path = public as $$ select coalesce((select revenue from co3_route_econ(p_op) e where e.route_key = p_route), 0) $$;
revoke all on function public.co3_op_revenue(uuid, text) from public, anon, authenticated;

-- 運航会社の収益の倍率（販売会社1社ごとに +5%）
create or replace function public.co3_cs_op_mult(p_uid uuid, p_route text) returns numeric
language sql stable security definer set search_path = public as $$
  select 1 + 0.05 * (select count(*) from co3_codeshares where op_id = p_uid and route_key = p_route and status = 'active')
$$;
revoke all on function public.co3_cs_op_mult(uuid, text) from public, anon, authenticated;

-- 販売会社の乗り継ぎ（自分の路線が共同運航の路線と空港でつながる：1つごとに +5%、最大 +15%）
create or replace function public.co3_cs_conn_mult(p_uid uuid, p_a text, p_b text) returns numeric
language sql stable security definer set search_path = public as $$
  select 1 + least(0.15, 0.05 * (select count(*) from co3_codeshares s cross join lateral co3_route_ends(s.route_key) e
                                  where s.seller_id = p_uid and s.status = 'active' and (e.a in (p_a, p_b) or e.b in (p_a, p_b))
                                    and not (e.a in (p_a, p_b) and e.b in (p_a, p_b))))
$$;
revoke all on function public.co3_cs_conn_mult(uuid, text, text) from public, anon, authenticated;

-- 販売会社の1日の取り分（フリーセール 15%・ブロック 35%）
create or replace function public.co3_cs_income(p_uid uuid) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce(sum(co3_op_revenue(s.op_id, s.route_key) * case s.kind when 'block' then 0.35 else 0.15 end), 0)
    from co3_codeshares s where s.seller_id = p_uid and s.status = 'active'
$$;
revoke all on function public.co3_cs_income(uuid) from public, anon, authenticated;

-- 仲間の施設（自分の施設がない空港で、1段ごとに +3%）
create or replace function public.co3_ally_fac_mult(p_uid uuid, p_a text, p_b text) returns numeric
language sql stable security definer set search_path = public as $$
  select 1 + coalesce((select sum(0.03 * lv) from (
      select ap.iata, max(f.level) as lv from facilities f join airports ap on ap.id = f.airport_id
        join co3_alliance_members m on m.user_id = f.user_id
       where ap.iata in (p_a, p_b) and f.user_id <> p_uid
         and m.alliance_id = (select alliance_id from co3_alliance_members where user_id = p_uid)
         and not exists (select 1 from facilities g where g.user_id = p_uid and g.airport_id = f.airport_id)
       group by ap.iata) z), 0)
$$;
revoke all on function public.co3_ally_fac_mult(uuid, text, text) from public, anon, authenticated;

-- 売れる路線を探す（友だち・仲間の路線のうち、自分の空港につながるもの）
create or replace function public.co3_cs_candidates() returns jsonb
language sql stable security definer set search_path = public as $$
  with me as (select auth.uid() as uid), ap as (select co3_my_airports((select uid from me)) as x),
  o as (select distinct a.user_id as op, a.route_key from aircraft a, me
         where a.route_key is not null and a.user_id <> me.uid
           and (co3_is_friend(me.uid, a.user_id) or co3_same_alliance(me.uid, a.user_id)))
  select coalesce(jsonb_agg(jsonb_build_object('op_name', c.name, 'op_code', c.friend_code, 'k', o.route_key, 'a', e.a, 'b', e.b,
           'ally', co3_same_alliance((select uid from me), o.op), 'revenue', round(co3_op_revenue(o.op, o.route_key)),
           'sellers', (select count(*) from co3_codeshares s where s.op_id = o.op and s.route_key = o.route_key and s.status <> 'ended'),
           'mine', (select s.status from co3_codeshares s where s.op_id = o.op and s.seller_id = (select uid from me) and s.route_key = o.route_key and s.status <> 'ended' limit 1))
           order by c.name, o.route_key), '[]'::jsonb)
    from o join companies c on c.user_id = o.op cross join lateral co3_route_ends(o.route_key) e
   where e.a in (select x from ap) or e.b in (select x from ap)
$$;
revoke all on function public.co3_cs_candidates() from public, anon;
grant execute on function public.co3_cs_candidates() to authenticated;

-- ブロック買い取りの代金を払う（5日分）。払えなければ false
create or replace function public.co3_cs_pay_block(p_id bigint) returns boolean
language plpgsql security definer set search_path = public as $$
declare s record; amt numeric;
begin
  select * into s from co3_codeshares where id = p_id;
  amt := ceil(co3_op_revenue(s.op_id, s.route_key) * 5);
  update companies set cash = cash - amt where user_id = s.seller_id and cash >= amt;
  if not found then return false; end if;
  update companies set cash = cash + amt where user_id = s.op_id;
  update co3_codeshares set paid_month = date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date where id = p_id;
  return true;
end;
$$;
revoke all on function public.co3_cs_pay_block(bigint) from public, anon, authenticated;

-- 申し込む（販売会社から）
create or replace function public.co3_cs_request(p_op_code text, p_route text, p_kind text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); op uuid; e record; ally boolean; v_id bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if p_kind not in ('free', 'block') then raise exception 'invalid kind'; end if;
  select user_id into op from companies where friend_code = upper(btrim(coalesce(p_op_code, '')));
  if op is null or op = uid then raise exception 'code not found'; end if;
  ally := co3_same_alliance(uid, op);
  if not (ally or co3_is_friend(uid, op)) then raise exception 'not partner'; end if;
  if not exists (select 1 from aircraft a where a.user_id = op and a.route_key = p_route) then raise exception 'route not found'; end if;
  select * into e from co3_route_ends(p_route);
  if not exists (select 1 from co3_my_airports(uid) x where x in (e.a, e.b)) then raise exception 'not connected'; end if;
  if (select count(*) from co3_codeshares where op_id = op and route_key = p_route and status <> 'ended') >= 3 then raise exception 'sellers full'; end if;
  if (select count(*) from co3_codeshares where seller_id = uid and status <> 'ended') >= co3.cs_limit((select rating from companies where user_id = uid)) then raise exception 'codeshare limit'; end if;
  if exists (select 1 from co3_codeshares where op_id = op and seller_id = uid and route_key = p_route and status <> 'ended') then raise exception 'already requested'; end if;
  insert into co3_codeshares (op_id, seller_id, route_key, kind) values (op, uid, p_route, p_kind) returning co3_codeshares.id into v_id;
  -- 仲間のフリーセールは認めなしで始まる
  if ally and p_kind = 'free' then update co3_codeshares set status = 'active', active_at = now() where co3_codeshares.id = v_id; end if;
  return co_state();
end;
$$;
revoke all on function public.co3_cs_request(text, text, text) from public, anon;
grant execute on function public.co3_cs_request(text, text, text) to authenticated;

-- 認める・断る（運航会社。格付け3から）
create or replace function public.co3_cs_answer(p_id bigint, p_ok boolean) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); s record;
begin
  perform co_check(uid);
  perform co_settle(uid);
  select * into s from co3_codeshares where id = p_id and op_id = uid and status = 'pending';
  if not found then raise exception 'codeshare not found'; end if;
  if not p_ok then update co3_codeshares set status = 'ended', ended_at = now() where id = p_id; return co_state(); end if;
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if s.kind = 'block' and not co3_cs_pay_block(p_id) then raise exception 'seller cannot pay'; end if;
  update co3_codeshares set status = 'active', active_at = now() where id = p_id;
  return co_state();
end;
$$;
revoke all on function public.co3_cs_answer(bigint, boolean) from public, anon;
grant execute on function public.co3_cs_answer(bigint, boolean) to authenticated;

-- やめる（どちらからでも）
create or replace function public.co3_cs_end(p_id bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  update co3_codeshares set status = 'ended', ended_at = now() where id = p_id and status <> 'ended' and uid in (op_id, seller_id);
  if not found then raise exception 'codeshare not found'; end if;
  return co_state();
end;
$$;
revoke all on function public.co3_cs_end(bigint) from public, anon;
grant execute on function public.co3_cs_end(bigint) to authenticated;

-- 毎日：運航会社が路線から機体を外したら終わる。毎月1日にブロック買い取りの代金を払う（払えなければ終わる）
create or replace function public.co3_cs_daily() returns integer
language plpgsql security definer set search_path = public as $$
declare s record; n int := 0; m date := date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date;
begin
  update co3_codeshares c set status = 'ended', ended_at = now()
   where c.status <> 'ended' and not exists (select 1 from aircraft a where a.user_id = c.op_id and a.route_key = c.route_key);
  for s in select * from co3_codeshares where status = 'active' and kind = 'block' and (paid_month is null or paid_month < m) loop
    if not co3_cs_pay_block(s.id) then update co3_codeshares set status = 'ended', ended_at = now() where id = s.id; end if;
    n := n + 1;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_cs_daily() from public, anon, authenticated;

-- ── アライアンス ───────────────────────────────────────────
create or replace function co3.real_alliance_name(p_name text) returns boolean
language sql immutable as $$
  select lower(regexp_replace(p_name, '[\s・･\-_　]', '', 'g')) ~ '(staralliance|スターアライアンス|oneworld|ワンワールド|skyteam|スカイチーム|valuealliance|バリューアライアンス|uflyalliance|ユーフライ)'
$$;
revoke all on function co3.real_alliance_name(text) from public, anon, authenticated;

create or replace function public.co3_ally_check_join(p_uid uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from co3_alliance_members where user_id = p_uid) then raise exception 'already in alliance'; end if;
  if (select alliance_left_at from companies where user_id = p_uid) > now() - interval '7 days' then raise exception 'alliance cooldown'; end if;
  if (select policy from companies where user_id = p_uid) = 'lcc' then raise exception 'lcc cannot join'; end if;
end;
$$;
revoke all on function public.co3_ally_check_join(uuid) from public, anon, authenticated;

create or replace function public.co3_ally_create(p_name text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); aid bigint;
begin
  perform co_check(uid);
  perform co_settle(uid);
  if coalesce(co3_rating_need(uid), 1) < 3 then raise exception 'rating required 3'; end if;
  if (select policy from companies where user_id = uid) <> 'fsc' then raise exception 'fsc only'; end if;
  perform co3_ally_check_join(uid);
  if char_length(btrim(coalesce(p_name, ''))) not between 1 and 20 then raise exception 'invalid name'; end if;
  if co3.real_alliance_name(p_name) then raise exception 'real alliance name'; end if;
  insert into co3_alliances (name, leader) values (btrim(p_name), uid) returning id into aid;
  insert into co3_alliance_members (user_id, alliance_id) values (uid, aid);
  return co_state();
end;
$$;
revoke all on function public.co3_ally_create(text) from public, anon;
grant execute on function public.co3_ally_create(text) to authenticated;

create or replace function public.co3_ally_join(p_id bigint) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  perform co3_ally_check_join(uid);
  if not exists (select 1 from co3_alliances where id = p_id) then raise exception 'alliance not found'; end if;
  perform 1 from co3_alliances where id = p_id for update;
  if (select count(*) from co3_alliance_members where alliance_id = p_id) >= 50 then raise exception 'alliance full'; end if;
  insert into co3_alliance_members (user_id, alliance_id) values (uid, p_id);
  return co_state();
end;
$$;
revoke all on function public.co3_ally_join(bigint) from public, anon;
grant execute on function public.co3_ally_join(bigint) to authenticated;

-- 抜けた・外された会社：仲間のフリーセール（認めなしで始まったもの）は終わる
create or replace function public.co3_ally_out(p_uid uuid) returns void
language plpgsql security definer set search_path = public as $$
declare aid bigint;
begin
  select alliance_id into aid from co3_alliance_members where user_id = p_uid;
  if aid is null then return; end if;
  update co3_codeshares s set status = 'ended', ended_at = now()
   where s.status = 'active' and s.kind = 'free' and p_uid in (s.op_id, s.seller_id)
     and not co3_is_friend(s.op_id, s.seller_id)
     and exists (select 1 from co3_alliance_members m where m.alliance_id = aid and m.user_id = case when s.op_id = p_uid then s.seller_id else s.op_id end);
  delete from co3_alliance_members where user_id = p_uid;
  update companies set alliance_left_at = now() where user_id = p_uid;
  -- だれもいなければ消す。リーダーが抜けたら、会社の価値がいちばん高い仲間がリーダーに
  if not exists (select 1 from co3_alliance_members where alliance_id = aid) then delete from co3_alliances where id = aid;
  elsif (select leader from co3_alliances where id = aid) = p_uid then
    update co3_alliances set leader = (select m.user_id from co3_alliance_members m where m.alliance_id = aid order by co_value(m.user_id) desc limit 1) where id = aid;
  end if;
end;
$$;
revoke all on function public.co3_ally_out(uuid) from public, anon, authenticated;

create or replace function public.co3_ally_leave() returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  perform co_settle(uid);
  if not exists (select 1 from co3_alliance_members where user_id = uid) then raise exception 'not in alliance'; end if;
  perform co3_ally_out(uid);
  return co_state();
end;
$$;
revoke all on function public.co3_ally_leave() from public, anon;
grant execute on function public.co3_ally_leave() to authenticated;

create or replace function public.co3_ally_kick(p_code text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid(); t uuid; aid bigint;
begin
  perform co_check(uid);
  select a.id into aid from co3_alliances a where a.leader = uid;
  if aid is null then raise exception 'not leader'; end if;
  select user_id into t from companies where friend_code = upper(btrim(coalesce(p_code, '')));
  if t is null or t = uid or not exists (select 1 from co3_alliance_members where user_id = t and alliance_id = aid) then raise exception 'member not found'; end if;
  perform co3_ally_out(t);
  return co_state();
end;
$$;
revoke all on function public.co3_ally_kick(text) from public, anon;
grant execute on function public.co3_ally_kick(text) to authenticated;

create or replace function public.co3_ally_rename(p_name text) returns jsonb
language plpgsql security definer set search_path = public, ops as $$
declare uid uuid := auth.uid();
begin
  perform co_check(uid);
  if char_length(btrim(coalesce(p_name, ''))) not between 1 and 20 then raise exception 'invalid name'; end if;
  if co3.real_alliance_name(p_name) then raise exception 'real alliance name'; end if;
  update co3_alliances set name = btrim(p_name) where leader = uid;
  if not found then raise exception 'not leader'; end if;
  return co_state();
end;
$$;
revoke all on function public.co3_ally_rename(text) from public, anon;
grant execute on function public.co3_ally_rename(text) to authenticated;

-- 30日ゲームに入らないリーダーは代わる（毎日）
create or replace function public.co3_ally_daily() returns integer
language plpgsql security definer set search_path = public as $$
declare a record; n int := 0; nl uuid;
begin
  for a in select x.* from co3_alliances x join companies c on c.user_id = x.leader where c.last_collect < now() - interval '30 days' loop
    select m.user_id into nl from co3_alliance_members m join companies c on c.user_id = m.user_id
     where m.alliance_id = a.id and m.user_id <> a.leader and c.last_collect >= now() - interval '30 days' order by co_value(m.user_id) desc limit 1;
    if nl is not null then update co3_alliances set leader = nl where id = a.id; n := n + 1; end if;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_ally_daily() from public, anon, authenticated;

-- 一覧（公開）と、自分のアライアンス
create or replace function public.co3_ally_list() returns jsonb
language sql stable security definer set search_path = public as $$
  with m as (select date_trunc('month', (now() at time zone 'Asia/Tokyo'))::date as m),
  x as (select a.id, a.name, (select name from companies where user_id = a.leader) as leader, count(mm.user_id) as n,
               sum(co_value(mm.user_id)) as value,
               sum(co_value(mm.user_id) - coalesce((select r.value from co_rank_days r, m where r.user_id = mm.user_id and r.day >= m.m order by r.day limit 1), co_value(mm.user_id))) as growth
          from co3_alliances a join co3_alliance_members mm on mm.alliance_id = a.id group by a.id)
  select coalesce(jsonb_agg(jsonb_build_object('id', id, 'name', name, 'leader', leader, 'n', n, 'value', value, 'growth', growth,
           'mine', exists (select 1 from co3_alliance_members z where z.user_id = auth.uid() and z.alliance_id = x.id)) order by value desc), '[]'::jsonb) from x
$$;
revoke all on function public.co3_ally_list() from public, anon;
grant execute on function public.co3_ally_list() to authenticated;

-- アライアンス対抗戦（シーズンを締めるときに呼ぶ）
create or replace function public.co3_ally_season_close(p_start date) returns integer
language plpgsql security definer set search_path = public as $$
declare n int := 0; r record; prize int;
begin
  for r in
    select a.id, a.name, rank() over (order by avg(g.growth) desc) as no
      from co3_alliances a join co3_alliance_members m on m.alliance_id = a.id
      join co3_season_growth(p_start, (p_start + interval '3 months' - interval '1 day')::date) g on g.user_id = m.user_id
     group by a.id, a.name
  loop
    exit when r.no > 3;
    prize := (array[20000, 10000, 5000])[r.no];
    insert into co3_awards (user_id, kind, ref, label)
      select m.user_id, 'ally_top3', to_char(p_start, 'YYYY-MM'), co3.season_name(p_start) || ' アライアンス対抗戦 ' || r.no || '位（' || r.name || '）'
        from co3_alliance_members m where m.alliance_id = r.id on conflict do nothing;
    if found then
      update companies c set cash = cash + prize where c.user_id in (select user_id from co3_alliance_members where alliance_id = r.id);
      if r.no = 1 then
        insert into co3_awards (user_id, kind, ref, label)
          select m.user_id, 'ally_champ', to_char(p_start, 'YYYY-MM'), co3.season_name(p_start) || ' アライアンス対抗戦 優勝（' || r.name || '）'
            from co3_alliance_members m where m.alliance_id = r.id on conflict do nothing;
      end if;
      n := n + 1;
    end if;
  end loop;
  return n;
end;
$$;
revoke all on function public.co3_ally_season_close(date) from public, anon, authenticated;

do $do$
declare src text; n0 text;
begin
  -- 旅客の収益：運航会社 +5%/販売会社・販売会社の乗り継ぎ・仲間の施設
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('co3_cs_op_mult' in src) = 0 then
    n0 := src;
    src := replace(src, '* co3_typhoon_mult(p_uid, k2.route_key, k2.a, k2.b, k2.ac_id) as rev,',
      '* co3_typhoon_mult(p_uid, k2.route_key, k2.a, k2.b, k2.ac_id) * co3_cs_op_mult(p_uid, k2.route_key) * co3_cs_conn_mult(p_uid, k2.a, k2.b) * co3_ally_fac_mult(p_uid, k2.a, k2.b) as rev,');
    if src = n0 then raise exception 'co3_route_econ の形が変わっていて、共同運航を入れられない'; end if;
    execute src;
  end if;
  -- 1日の稼ぎ：販売会社の取り分
  select pg_get_functiondef('public.co3_gross(uuid)'::regprocedure) into src;
  if position('co3_cs_income' in src) = 0 then
    n0 := src;
    src := replace(src, '+ coalesce((select round(sum(profit)) from co3_extra_econ(p_uid)), 0))::bigint',
                        '+ coalesce((select round(sum(profit)) from co3_extra_econ(p_uid)), 0)' || chr(10) || '        + round(co3_cs_income(p_uid)))::bigint');
    if src = n0 then raise exception 'co3_gross の形が変わっていて、共同運航を入れられない'; end if;
    execute src;
  end if;
  -- シーズンを締めるときに、アライアンス対抗戦も
  select pg_get_functiondef('public.co3_season_close(date)'::regprocedure) into src;
  if position('co3_ally_season_close' in src) = 0 then
    n0 := src;
    src := replace(src, '  n := n + coalesce(k, 0);', '  n := n + coalesce(k, 0);' || chr(10) || '  n := n + co3_ally_season_close(s);');
    if src = n0 then raise exception 'co3_season_close の形が変わっていて、対抗戦を入れられない'; end if;
    execute src;
  end if;
  -- 会社の状態
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('co3_codeshares' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、共同運航を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$, $r$'cs', case when v3 then jsonb_build_object(
        'limit', co3.cs_limit(c.rating), 'income', round(co3_cs_income(uid)),
        'list', coalesce((select jsonb_agg(jsonb_build_object('id', s.id, 'k', s.route_key, 'kind', s.kind, 'status', s.status, 'role', case when s.op_id = uid then 'op' else 'seller' end,
                      'partner', (select name from companies where user_id = case when s.op_id = uid then s.seller_id else s.op_id end),
                      'a', (co3_route_ends(s.route_key)).a, 'b', (co3_route_ends(s.route_key)).b,
                      'share', case when s.seller_id = uid and s.status = 'active' then round(co3_op_revenue(s.op_id, s.route_key) * case s.kind when 'block' then 0.35 else 0.15 end) end,
                      'block_price', case when s.kind = 'block' then ceil(co3_op_revenue(s.op_id, s.route_key) * 5) end) order by s.created_at desc)
                    from co3_codeshares s where uid in (s.op_id, s.seller_id) and s.status <> 'ended'), '[]'::jsonb)) end,
    'ally', case when v3 then (select jsonb_build_object('id', a.id, 'name', a.name, 'leader', a.leader = uid, 'leader_name', (select name from companies where user_id = a.leader),
        'members', (select jsonb_agg(jsonb_build_object('name', cc.name, 'code', cc.friend_code, 'policy', cc.policy, 'value', co_value(m2.user_id), 'me', m2.user_id = uid) order by co_value(m2.user_id) desc)
                      from co3_alliance_members m2 join companies cc on cc.user_id = m2.user_id where m2.alliance_id = a.id))
        from co3_alliance_members m join co3_alliances a on a.id = m.alliance_id where m.user_id = uid) end,
    'ally_cooldown', case when v3 and c.alliance_left_at > now() - interval '7 days' then c.alliance_left_at + interval '7 days' end,
    'satisfaction', c.satisfaction,$r$);
    execute src;
  end if;
end
$do$;

do $$
begin
  if exists (select 1 from pg_extension where extname = 'pg_cron') then
    execute $q$ select cron.schedule('co3-codeshare', '15 19 * * *', $job$ select public.co3_cs_daily(); select public.co3_ally_daily(); $job$) $q$;
  end if;
end
$$;
