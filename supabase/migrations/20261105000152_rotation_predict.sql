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
--     あわせて learn_hi（学ぶ予想のうち、学んだ便を出すしきい値だけを「3回以上・4割以上」に上げたもの）も採点し、
--     しきい値を上げると「出したうちの当たり率」が戻るかを見られるようにする（画面には使わない）。
--   軽くする工夫（本番は小さいプランで一時ファイルの余裕がないため）：
--     ・rot_pairs は毎晩まるごと作り直さず、前の日の分だけ足す（まだない古い日は、時間の上限の中で少しずつ足す）。古い日の重みは読むときに計算する
--     ・「次の便」は1日分を並べ替えず、便ごとに索引（reg_legs の主キー：登録記号・日）で引く
--     ・採点は前の日の300便まで。予想は便ごとに索引で引く。大きな中間の表・自己結合・大きな並べ替えを作らない
--     ・毎晩の処理は「つながり」と「採点」で別の pg_cron の仕事にし、それぞれに statement_timeout と lock_timeout を付ける。
--       失敗してもその仕事だけが止まり、ほかの毎晩の処理（daily-archive など）は止めない。時刻もほかの重い処理と重ねない
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
  method    text not null check (method in ('base', 'learn', 'learn_hi')),   -- base＝今の予想、learn＝学ぶ予想、learn_hi＝学ぶ予想でしきい値を上げたもの
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

-- つながりを作り終えた日（足し忘れた日をあとで見つけるため。日ごとに1行）
create table if not exists public.rot_pairs_days (
  day      date primary key,
  pairs    integer not null,
  built_at timestamptz not null default now()
);
alter table public.rot_pairs_days enable row level security;
revoke all on public.rot_pairs_days from public, anon, authenticated;

-- その日の機体のつながりを作る（何度流しても同じになる）
--   1日分をまとめて並べ替えず、その日の便ごとに「同じ機体の、その日の次の便」を主キー（登録記号・日）で1件だけ引く
create or replace function public.rot_pairs_build(p_day date) returns int
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  insert into public.rot_pairs (day, reg, prev_cs, next_cs, prev_arr, next_dep, next_arr, next_type, next_tod, gap_min, ok)
  select p_day, a.reg, a.callsign, nl.callsign, a.arr, nl.dep, nl.arr, nl.type, (nl.first_at at time zone 'Asia/Tokyo')::time,
         round(extract(epoch from (nl.first_at - a.last_at)) / 60)::int,
         (a.arr is null or nl.dep is null or a.arr = nl.dep) and nl.first_at - a.last_at < interval '10 hours' and nl.first_at - a.last_at > interval '-30 minutes'
  from public.reg_legs a
  cross join lateral (select b.callsign, b.dep, b.arr, b.type, b.first_at from public.reg_legs b
                      where b.reg = a.reg and b.day = a.day and (b.first_at, b.callsign) > (a.first_at, a.callsign)
                      order by b.first_at, b.callsign limit 1) nl
  where a.day = p_day
  on conflict (day, reg, prev_cs) do update set next_cs = excluded.next_cs, prev_arr = excluded.prev_arr, next_dep = excluded.next_dep,
    next_arr = excluded.next_arr, next_type = excluded.next_type, next_tod = excluded.next_tod, gap_min = excluded.gap_min, ok = excluded.ok, built_at = now();
  get diagnostics n = row_count;
  insert into public.rot_pairs_days (day, pairs) values (p_day, n)
  on conflict (day) do update set pairs = excluded.pairs, built_at = now();
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
--   p_mode：'base'＝今の予想と同じ決め方、'learn'＝学ぶ予想、'learn_hi'＝学ぶ予想で、学んだ便を出すのを3回以上・4割以上に上げたもの（採点用）
--   返す：[{callsign, dep, arr, time, seen, share, src}]（4便先まで）
create or replace function public.rot_predict(p_mode text, p_reg text, p_day date, p_cs text, p_arr text, p_tod time, p_steps int default 4)
returns jsonb language plpgsql stable security definer set search_path = public as $$
declare
  steps jsonb := '[]'::jsonb; seen text[] := array[p_cs]; prev text := p_cs; a text := p_arr; t time := p_tod;
  rt text; dw int := extract(dow from p_day)::int; i int := 0; lim int := least(greatest(coalesce(p_steps, 4), 1), 4);
  v_cs text; v_dep text; v_arr text; v_tod time; v_n int; v_share numeric; v_src text;
  min_n int := case when p_mode = 'learn_hi' then 3 else 2 end; min_share numeric := case when p_mode = 'learn_hi' then 0.4 else 0.3 end;
begin
  if p_mode is null or p_mode not in ('base', 'learn', 'learn_hi') or p_cs is null then return steps; end if;
  if p_mode <> 'base' then
    select mode() within group (order by type) into rt from public.reg_legs
    where reg = p_reg and day between p_day - 42 and p_day and type is not null;
  end if;
  while i < lim loop
    v_cs := null; v_src := null;
    if p_mode <> 'base' then
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
        if v_cs is not null and (v_n < min_n or v_share < min_share) then v_cs := null; end if;
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
--   1日に p_max 件まで（登録記号と便から決まる順で選ぶので、何度流しても同じ）。毎晩は300件（rot_eval_nightly の定数）
--   軽くする工夫：測る便は「登録記号・便名」だけを上位 p_max 件残す並べ替え（小さな山）で選ぶ。そのあとは1便ずつ、
--   機体の型・実際の次の4便・3通りの予想を索引で引き、数を rot_eval に足していく（大きな中間の表を持たない）。
--   p_budget を過ぎたら、そこまでの数を残して止める（全部の方式を同じ便で採点しているので、比べるのには困らない）
create or replace function public.rot_eval_day(p_day date, p_max int default 300, p_budget interval default interval '4 minutes') returns int
language plpgsql security definer set search_path = public as $$
declare vcnt int; lim int := least(greatest(coalesce(p_max, 300), 1), 3000); t0 timestamptz := clock_timestamp();
  a record; vrt text; tr jsonb; pj jsonb; vm text; ki int; vg text; vh boolean; v_arr text; v_first timestamptz;
begin
  delete from public.rot_eval where day = p_day;   -- 採点の数だけを作り直す（記録そのものは消さない）
  for a in
    select x.reg, x.callsign as cs from public.reg_legs x
    cross join lateral (select 1 from public.reg_legs b where b.reg = x.reg and b.day = x.day and (b.first_at, b.callsign) > (x.first_at, x.callsign) limit 1) nb
    where x.day = p_day
    order by md5(x.reg || ':' || x.callsign)
    limit lim
  loop
    exit when clock_timestamp() - t0 >= coalesce(p_budget, interval '4 minutes');
    begin
      select l.arr, l.first_at into v_arr, v_first from public.reg_legs l where l.reg = a.reg and l.day = p_day and l.callsign = a.cs;
      select mode() within group (order by l.type) into vrt from public.reg_legs l
      where l.reg = a.reg and l.day between p_day - 42 and p_day and l.type is not null;
      select jsonb_agg(jsonb_build_array(l.callsign, (l.dep = 'HND' or l.arr = 'HND') is true) order by l.first_at, l.callsign) into tr
      from (select l.callsign, l.dep, l.arr, l.first_at from public.reg_legs l
            where l.reg = a.reg and l.day = p_day and (l.first_at, l.callsign) > (v_first, a.cs)
            order by l.first_at, l.callsign limit 4) l;
      foreach vm in array array['base', 'learn', 'learn_hi'] loop
        pj := public.rot_predict(vm, a.reg, p_day, a.cs, v_arr, (v_first at time zone 'Asia/Tokyo')::time, 4);
        for ki in 1 .. jsonb_array_length(tr) loop
          vg := pj -> (ki - 1) ->> 'callsign'; vh := (tr -> (ki - 1) ->> 1)::boolean;
          insert into public.rot_eval (day, method, k, carrier, rtype, hnd, src, n, predicted, hit)
          values (p_day, vm, ki, left(a.cs, 3), coalesce(vrt, '?'), vh, coalesce(pj -> (ki - 1) ->> 'src', 'none'), 1,
                  (vg is not null)::int, (vg is not distinct from (tr -> (ki - 1) ->> 0) and vg is not null)::int)
          on conflict (day, method, k, carrier, rtype, hnd, src) do update
            set n = rot_eval.n + 1, predicted = rot_eval.predicted + excluded.predicted, hit = rot_eval.hit + excluded.hit, made_at = now();
        end loop;
      end loop;
    exception when query_canceled then exit;   -- 時間切れ（statement_timeout）でも、そこまでの便の数は残す
    end;
  end loop;
  select count(*) into vcnt from public.rot_eval where day = p_day;
  return vcnt;
end $$;
revoke all on function public.rot_eval_day(date, int, interval) from public, anon, authenticated;

-- 毎晩その1（つながり）：前の日の分を足す。そのあと、前の60日のうちまだ作っていない日を、新しい日から順に時間の上限まで足す
--   （反映した最初の夜に、これまでの日をここで少しずつ埋める。1日ずつ別の区切りにするので、途中で時間切れになっても前の日の分は残る）
create or replace function public.rot_pairs_nightly(p_budget interval default interval '60 seconds', p_days int default 60) returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := (now() at time zone 'Asia/Tokyo')::date - 1; t0 timestamptz := clock_timestamp(); n int; g date;
  filled date[] := '{}'; stopped text := null; left_n int;
begin
  n := public.rot_pairs_build(d);
  for g in select x::date from generate_series(d - 1, d - least(greatest(coalesce(p_days, 60), 0), 60), interval '-1 day') x loop
    if clock_timestamp() - t0 >= p_budget then stopped := 'budget'; exit; end if;
    continue when exists (select 1 from public.rot_pairs_days r where r.day = g)
               or not exists (select 1 from public.reg_legs l where l.day = g);
    begin
      perform public.rot_pairs_build(g);
      filled := filled || g;
    exception when query_canceled then stopped := 'timeout'; exit;
    end;
  end loop;
  select count(*) into left_n from generate_series(d - 1, d - 60, interval '-1 day') x
  where not exists (select 1 from public.rot_pairs_days r where r.day = x::date) and exists (select 1 from public.reg_legs l where l.day = x::date);
  return jsonb_build_object('day', d, 'pairs', n, 'filled', to_jsonb(filled), 'left', left_n, 'stopped', stopped,
                            'ms', round(extract(epoch from clock_timestamp() - t0) * 1000));
end $$;
revoke all on function public.rot_pairs_nightly(interval, int) from public, anon, authenticated;

-- 毎晩その2（採点）：前の日を、今の予想・学ぶ予想（2回以上・3割以上）・学ぶ予想の厳しい版（3回以上・4割以上）の3通りで採点する
create or replace function public.rot_eval_nightly(p_max int default 300) returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := (now() at time zone 'Asia/Tokyo')::date - 1; t0 timestamptz := clock_timestamp(); e int;
begin
  e := public.rot_eval_day(d, p_max, interval '4 minutes');
  return jsonb_build_object('day', d, 'eval_rows', e, 'max', p_max,
    'legs', (select coalesce(sum(n), 0) from public.rot_eval where day = d and method = 'base' and k = 1),
    'ms', round(extract(epoch from clock_timestamp() - t0) * 1000));
end $$;
revoke all on function public.rot_eval_nightly(int) from public, anon, authenticated;

-- 手で流すとき用：その1とその2を続けて流す。片方が失敗しても、もう片方は流す（失敗したことは返す）
create or replace function public.rot_nightly() returns jsonb
language plpgsql security definer set search_path = public as $$
declare a jsonb; b jsonb;
begin
  begin a := public.rot_pairs_nightly(); exception when others then a := jsonb_build_object('error', sqlerrm); end;
  begin b := public.rot_eval_nightly(); exception when others then b := jsonb_build_object('error', sqlerrm); end;
  return jsonb_build_object('day', coalesce(a ->> 'day', b ->> 'day'), 'pairs', (a ->> 'pairs')::int, 'eval_rows', (b ->> 'eval_rows')::int,
                            'pairs_job', a, 'eval_job', b);
end $$;
revoke all on function public.rot_nightly() from public, anon, authenticated;

-- これまでの日のつながりは、移行では作らない（移行を軽くするため）。反映した最初の夜から rot_pairs_nightly が時間の上限の中で埋める

-- 毎晩：日本時間 6:33 につながり、6:48 に採点（rwy-learn の 6:15 のあと。daily-archive 4:50・cold-archive 6:10・経営の毎晩の処理とは重ねない）
--   それぞれ別の仕事なので、片方が止まってもほかの処理は止めない。statement_timeout で長引いたら打ち切り、lock_timeout で待ち続けない
--   上限は仕事の文の先頭で付ける。関数の設定（create function ... set statement_timeout）は、呼ばれた時点で時計がもう決まっているので効かない（本物の Postgres 16 で確かめた）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') then return; end if;
  perform cron.unschedule(jobname) from cron.job where jobname in ('rot-learn', 'rot-pairs', 'rot-eval');
  execute $q$ select cron.schedule('rot-pairs', '33 21 * * *', $job$ set statement_timeout = '3min'; set lock_timeout = '5s'; select public.rot_pairs_nightly(interval '60 seconds', 60) $job$) $q$;
  execute $q$ select cron.schedule('rot-eval', '48 21 * * *', $job$ set statement_timeout = '5min'; set lock_timeout = '5s'; select public.rot_eval_nightly(300) $job$) $q$;
end
$outer$;
