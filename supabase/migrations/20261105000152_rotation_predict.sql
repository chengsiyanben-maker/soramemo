-- 機体の運用の予想を、たまった記録から学ぶ（案。本人が「反映して」と言うまで本番に流さない）
--
--   今の予想（predict_rotation_reg）：reg_legs の「この便のあとに同じ機体が飛んだ便」を前の60日で数え、同じ曜日は2倍。
--     3回以上・4割以上の便だけを、4便先までたどる。
--   学ぶ予想（この移行）：毎晩、reg_legs から「機体のつながり」（rot_pairs）を作り、次の順で1便ずつ決める。
--     1. 特別塗装機の予定の便（livery_plans）があれば、それを先に
--     2. 前の42日のつながり。新しい日ほど重く（14日で半分）、同じ曜日は2倍、その機体自身のつながりはさらに3倍
--        ・その便にいつも入る機体の型に、この機体の型が入っているか（2割未満の型なら外す。型の記録がなければ外さない）
--        ・JAL・ANA は時刻表（timetable）でその日に飛ぶ便か、出発の空港が合うか
--        ・前の便の到着の空港・時刻より後か
--        2回以上・3割以上のときだけ出す
--     3. 2で出せないとき（記録が少ないとき）は、今の予想と同じ決め方に戻す
--
--   予想は実績と分けて持つ（rot_pairs は reg_legs から作り直せる控え、予想そのものは表に残さず関数で出す）。
--   rot_eval：毎晩、前の日の分を「前の日の夜の時点の記録だけで予想した」として採点した数（今の予想と学ぶ予想）。
--   rot_pairs は adsb.lol（ODbL）由来だけで作る。ODPT（時刻表・特別塗装機の予定）は予想を出すときに見るだけで、表には混ぜない。
--   reg_legs・rotation_obs・flight_history は読むだけで、消さない。

create table if not exists public.rot_pairs (
  day       date not null,
  reg       text not null check (reg ~ '^[A-Z0-9-]{2,10}$'),
  prev_cs   text not null check (prev_cs ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  next_cs   text not null check (next_cs ~ '^[A-Z]{3}[0-9]{1,4}[A-Z]?$'),
  prev_arr  text check (prev_arr ~ '^[A-Z]{3}$'),
  next_dep  text check (next_dep ~ '^[A-Z]{3}$'),
  next_arr  text check (next_arr ~ '^[A-Z]{3}$'),
  next_type text check (length(next_type) <= 8),
  next_tod  time not null,                -- 次の便が見えはじめた時刻（日本時間）
  gap_min   integer,                      -- 前の便が最後に見えてから、次の便が見えはじめるまでの分
  ok        boolean not null,             -- 到着と出発の空港が食い違わず、間が10時間未満（学ぶ予想はこれだけを使う）
  built_at  timestamptz not null default now(),
  primary key (day, reg, prev_cs)
);
create index if not exists rot_pairs_prev on public.rot_pairs (prev_cs, day);
create index if not exists rot_pairs_reg on public.rot_pairs (reg, prev_cs, day);
alter table public.rot_pairs enable row level security;
revoke all on public.rot_pairs from public, anon, authenticated;

create table if not exists public.rot_eval (
  day       date not null,
  method    text not null check (method in ('base', 'learn')),   -- base＝今の予想、learn＝学ぶ予想
  k         smallint not null check (k between 1 and 4),         -- 何便先
  carrier   text not null check (length(carrier) <= 3),          -- 呼び出し符号の頭3文字（JAL・ANA・SKY など）
  rtype     text not null check (length(rtype) <= 8),            -- 機体の型（分からないときは '?'）
  hnd       boolean not null,                                    -- 答えの便が羽田発着
  src       text not null check (src in ('livery', 'learn', 'base', 'none')),  -- その便先の予想の出どころ（none＝出さなかった）
  n         integer not null,                                    -- 答えがある数
  predicted integer not null,                                    -- 予想を出した数
  hit       integer not null,                                    -- 当たった数
  made_at   timestamptz not null default now(),
  primary key (day, method, k, carrier, rtype, hnd, src)
);
alter table public.rot_eval enable row level security;
revoke all on public.rot_eval from public, anon, authenticated;

-- その日の機体のつながりを作る（何度流しても同じになる）
create or replace function public.rot_pairs_build(p_day date) returns int
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  with l as (
    select reg, callsign, arr, last_at,
           lead(callsign) over w as nx, lead(dep) over w as ndep, lead(arr) over w as narr,
           lead(type) over w as ntype, lead(first_at) over w as nfirst
    from public.reg_legs where day = p_day
    window w as (partition by reg order by first_at, callsign)
  )
  insert into public.rot_pairs (day, reg, prev_cs, next_cs, prev_arr, next_dep, next_arr, next_type, next_tod, gap_min, ok)
  select p_day, reg, callsign, nx, arr, ndep, narr, ntype, (nfirst at time zone 'Asia/Tokyo')::time,
         round(extract(epoch from (nfirst - last_at)) / 60)::int,
         (arr is null or ndep is null or arr = ndep) and nfirst - last_at < interval '10 hours' and nfirst - last_at > interval '-30 minutes'
  from l where nx is not null
  on conflict (day, reg, prev_cs) do update set next_cs = excluded.next_cs, prev_arr = excluded.prev_arr, next_dep = excluded.next_dep,
    next_arr = excluded.next_arr, next_type = excluded.next_type, next_tod = excluded.next_tod, gap_min = excluded.gap_min, ok = excluded.ok, built_at = now();
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.rot_pairs_build(date) from public, anon, authenticated;

-- その便にいつも入る機体の型に、この型が入っているか（前の42日、同じ曜日は2倍。2割未満なら外す。型の記録がなければ外さない）
create or replace function public.rot_type_ok(p_day date, p_cs text, p_type text) returns boolean
language sql stable security definer set search_path = public as $$
  select p_type is null or coalesce(
    coalesce(sum(w) filter (where type = p_type), 0) / nullif(sum(w), 0) >= 0.15, true)
  from (select type, case when extract(dow from day) = extract(dow from p_day) then 2 else 1 end::numeric as w
        from public.reg_legs where callsign = p_cs and day >= p_day - 42 and day < p_day and type is not null) x
$$;
revoke all on function public.rot_type_ok(date, text, text) from public, anon, authenticated;

-- JAL・ANA の便は、時刻表でその日に飛ぶ便か（出発の空港が分かれば、それも）。時刻表がその日をおおっていなければ外さない
create or replace function public.rot_tt_ok(p_day date, p_cs text, p_dep text) returns boolean
language sql stable security definer set search_path = public as $$
  select case
    when x.op is null then true
    when not exists (select 1 from public.timetable t where t.operator = x.opn and t.valid_from <= p_day and t.valid_to >= p_day) then true
    else exists (select 1 from public.timetable t where t.operator = x.opn and t.valid_from <= p_day and t.valid_to >= p_day
                   and left(t.flight, 2) = x.op and ltrim(substr(t.flight, 3), '0') = x.num
                   and (t.days & (1 << extract(dow from p_day)::int)) <> 0 and (p_dep is null or t.dep = p_dep))
  end
  from (select case left(p_cs, 3) when 'JAL' then 'JL' when 'ANA' then 'NH' end as op,
               case left(p_cs, 3) when 'JAL' then 'JAL' when 'ANA' then 'ANA' end as opn,
               ltrim(substr(p_cs, 4), '0') as num) x
$$;
revoke all on function public.rot_tt_ok(date, text, text) from public, anon, authenticated;

-- 予想の本体。p_day の前の日までの記録だけを使う（過去の日を渡せば、その日の前の夜の時点の予想になる）
--   p_mode：'base'＝今の予想と同じ決め方、'learn'＝学ぶ予想
--   返す：[{callsign, dep, arr, time, seen, share, src}]（4便先まで）
create or replace function public.rot_predict(p_mode text, p_reg text, p_day date, p_cs text, p_arr text, p_tod time, p_steps int default 4)
returns jsonb language plpgsql stable security definer set search_path = public as $$
declare
  steps jsonb := '[]'::jsonb; seen text[] := array[p_cs]; prev text := p_cs; a text := p_arr; t time := p_tod;
  rt text; dw int := extract(dow from p_day)::int; i int := 0; lim int := least(greatest(coalesce(p_steps, 4), 1), 4);
  v_cs text; v_dep text; v_arr text; v_tod time; v_n int; v_share numeric; v_src text;
begin
  if p_mode not in ('base', 'learn') or p_cs is null then return steps; end if;
  if p_mode = 'learn' then
    select mode() within group (order by type) into rt from public.reg_legs
    where reg = p_reg and day between p_day - 42 and p_day and type is not null;
  end if;
  while i < lim loop
    v_cs := null; v_src := null;
    if p_mode = 'learn' then
      -- 1. 特別塗装機の予定の便
      select case left(lp.flight, 2) when 'JL' then 'JAL' else 'ANA' end || ltrim(substr(lp.flight, 3), '0'), lp.dep, lp.arr,
             (lp.std at time zone 'Asia/Tokyo')::time, null::int, null::numeric
        into v_cs, v_dep, v_arr, v_tod, v_n, v_share
      from public.livery_plans lp join public.livery_sightings s on s.reg = p_reg
        and (lp.livery = s.name or strpos(lp.livery, s.name) > 0 or strpos(s.name, lp.livery) > 0)
      where left(lp.flight, 2) in ('JL', 'NH') and (lp.std at time zone 'Asia/Tokyo')::date = p_day
        and (a is null or lp.dep = a) and (t is null or (lp.std at time zone 'Asia/Tokyo')::time > t)
        and not ((case left(lp.flight, 2) when 'JL' then 'JAL' else 'ANA' end || ltrim(substr(lp.flight, 3), '0')) = any(seen))
      order by lp.std, 1 limit 1;
      if v_cs is not null then v_src := 'livery'; end if;
      -- 2. 学ぶ
      if v_cs is null then
        select z.cs, z.dep, z.arr, z.tod, z.n, z.share into v_cs, v_dep, v_arr, v_tod, v_n, v_share
        from (
          select c.*, c.score / nullif(sum(c.score) over (), 0) as share
          from (
            select x.next_cs as cs, mode() within group (order by x.next_dep) as dep, mode() within group (order by x.next_arr) as arr,
                   percentile_disc(0.5) within group (order by x.next_tod) as tod, count(*)::int as n,
                   sum(x.w) + 2 * coalesce(sum(x.w) filter (where x.reg = p_reg), 0) as score
            from (select r.*, power(0.5, (p_day - r.day) / 14.0) * (case when extract(dow from r.day)::int = dw then 2 else 1 end) as w
                  from public.rot_pairs r where r.prev_cs = prev and r.ok and r.day >= p_day - 42 and r.day < p_day) x
            group by x.next_cs
          ) c
          where not (c.cs = any(seen)) and (a is null or c.dep is null or c.dep = a) and (t is null or c.tod > t)
            and public.rot_type_ok(p_day, c.cs, rt) and public.rot_tt_ok(p_day, c.cs, a)
        ) z
        order by z.score desc, z.cs limit 1;
        if v_cs is not null and (v_n < 2 or v_share < 0.3) then v_cs := null; end if;
        if v_cs is not null then v_src := 'learn'; end if;
      end if;
    end if;
    -- 3. 今の予想と同じ決め方（学ぶ予想では、記録が少ないときの戻り先）
    if v_cs is null then
      select z.cs, z.dep, z.arr, z.tod, z.n, z.share into v_cs, v_dep, v_arr, v_tod, v_n, v_share
      from (
        select c.*, c.score / nullif(sum(c.score) over (), 0) as share
        from (
          select r.next_cs as cs, mode() within group (order by r.next_dep) as dep, mode() within group (order by r.next_arr) as arr,
                 percentile_disc(0.5) within group (order by r.next_tod) as tod, count(*)::int as n,
                 sum(case when extract(dow from r.day)::int = dw then 2 else 1 end)::numeric as score
          from public.rot_pairs r where r.prev_cs = prev and r.day >= p_day - 60 and r.day < p_day
          group by r.next_cs
        ) c
      ) z
      order by z.score desc, z.cs limit 1;
      exit when v_cs is null or v_n < 3 or v_share < 0.4 or v_cs = any(seen);
      v_src := 'base';
    end if;
    steps := steps || jsonb_build_object('callsign', v_cs, 'dep', v_dep, 'arr', v_arr, 'time', to_char(v_tod, 'HH24:MI'),
      'seen', v_n, 'share', round(v_share, 2), 'src', v_src);
    seen := seen || v_cs; prev := v_cs; a := v_arr; t := v_tod; i := i + 1;
  end loop;
  return steps;
end $$;
revoke all on function public.rot_predict(text, text, date, text, text, time, int) from public, anon, authenticated;

-- 画面向け（まだ画面にはつながない）：機体（登録記号）の、学ぶ予想。返す形は predict_rotation_reg と同じで、
-- 'estimate': true（「予想」と出す）と、便ごとの出どころ src を足す
create or replace function public.predict_rotation_v2(p_reg text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare cur record;
begin
  if p_reg is null or p_reg !~ '^[A-Z0-9-]{2,10}$' then return null; end if;
  select day, callsign, dep, arr, first_at, last_at, type into cur from public.reg_legs
  where reg = p_reg and day >= (now() at time zone 'Asia/Tokyo')::date - 1 order by last_at desc limit 1;
  if cur is null then return jsonb_build_object('reg', p_reg, 'known', null, 'next', '[]'::jsonb, 'src', 'reg', 'method', 'learn', 'estimate', true); end if;
  return jsonb_build_object('reg', p_reg, 'src', 'reg', 'method', 'learn', 'estimate', true, 'type', cur.type,
    'known', jsonb_build_object('callsign', cur.callsign, 'dep', cur.dep, 'arr', cur.arr, 'first', cur.first_at, 'last', cur.last_at),
    'next', public.rot_predict('learn', p_reg, cur.day, cur.callsign, cur.arr, (cur.first_at at time zone 'Asia/Tokyo')::time, 4));
end $$;
revoke all on function public.predict_rotation_v2(text) from public;
grant execute on function public.predict_rotation_v2(text) to anon, authenticated;

-- その日を採点する：その日の機体の便を1つずつ「いまの便」とみなし、前の日までの記録だけで予想して、その日の実際の次の便と比べる。
--   1日に p_max 件まで（登録記号と便から決まる順で選ぶので、何度流しても同じ）
create or replace function public.rot_eval_day(p_day date, p_max int default 1500) returns int
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  delete from public.rot_eval where day = p_day;   -- 採点の数だけを作り直す（記録そのものは消さない）
  with legs as (
    select reg, callsign as cs, type, dep, arr, (first_at at time zone 'Asia/Tokyo')::time as tod,
           row_number() over (partition by reg order by first_at, callsign) as i
    from public.reg_legs where day = p_day
  ), anc as (
    select a.*, (select mode() within group (order by l.type) from public.reg_legs l
                 where l.reg = a.reg and l.day between p_day - 42 and p_day and l.type is not null) as rt
    from (select a.*, row_number() over (order by md5(a.reg || ':' || a.cs)) as pick
          from legs a join legs b on b.reg = a.reg and b.i = a.i + 1) a
    where a.pick <= greatest(coalesce(p_max, 1500), 1)
  ), pred as materialized (
    select a.reg, a.i, a.cs, a.rt, m.method, public.rot_predict(m.method, a.reg, p_day, a.cs, a.arr, a.tod, 4) as pj
    from anc a cross join (values ('base'), ('learn')) m(method)
  ), sc as (
    select p.method, k.k, left(p.cs, 3) as carrier, coalesce(p.rt, '?') as rtype, (b.dep = 'HND' or b.arr = 'HND') is true as hnd,
           coalesce(p.pj -> (k.k - 1) ->> 'src', 'none') as src, p.pj -> (k.k - 1) ->> 'callsign' as guess, b.cs as truth
    from pred p cross join generate_series(1, 4) k(k)
    join legs b on b.reg = p.reg and b.i = p.i + k.k
  )
  insert into public.rot_eval (day, method, k, carrier, rtype, hnd, src, n, predicted, hit)
  select p_day, method, k, carrier, rtype, hnd, src, count(*), count(guess), count(*) filter (where guess = truth)
  from sc group by method, k, carrier, rtype, hnd, src;
  get diagnostics n = row_count;
  return n;
end $$;
revoke all on function public.rot_eval_day(date, int) from public, anon, authenticated;

-- 毎晩：前の日と前の前の日のつながりを作り直し（空港は rwy-learn があとから入れるため）、前の日を採点する
create or replace function public.rot_nightly() returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := (now() at time zone 'Asia/Tokyo')::date - 1; a int; b int; e int;
begin
  a := public.rot_pairs_build(d - 1);
  b := public.rot_pairs_build(d);
  e := public.rot_eval_day(d, 1500);
  return jsonb_build_object('day', d, 'pairs_prev', a, 'pairs', b, 'eval_rows', e);
end $$;
revoke all on function public.rot_nightly() from public, anon, authenticated;

-- これまでの日のつながりを作る（1回だけ）
do $$
declare d date;
begin
  for d in select distinct day from public.reg_legs order by 1 loop
    perform public.rot_pairs_build(d);
  end loop;
end $$;

-- 毎晩 日本時間 4:55（rwy-learn の 3:15 のあと、daily-archive と同じころ）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  perform cron.unschedule('rot-learn') where exists (select 1 from cron.job where jobname = 'rot-learn');
  execute $q$ select cron.schedule('rot-learn', '55 19 * * *', $job$ select public.rot_nightly() $job$) $q$;
end
$outer$;
