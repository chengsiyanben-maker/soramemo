-- そらメモ：機体の運用の予想の当たり具合（軽い版。読むだけ。表も関数も作らず、何も書き込まない）
--
-- ★ 貼る前に、ブラウザの自動翻訳を切ってください（翻訳がかかったままだと SQL の文字が日本語に置きかわって動きません）。
--
-- 使い方：Supabase の SQL Editor にこのファイルをまるごと貼って「Run」。結果の表を CSV で書き出すか、全部選んでコピーして貼り返す。
--   出る列は rotation-backtest.sql と同じ。決め方も同じ（下の p を 60日・42日にすれば、同じ日・同じ便の数ではまったく同じ数になる）。
--
-- 軽くした仕組み：測る日は1日だけ。「前の便のあとに飛んだ便」の数え方を、全部の機体の記録から先に作らず、
--   予想をたどるときに、その便名の分だけ索引（reg_legs の便名・日、登録記号・日）で引く。大きな中間の表・大きな並べ替えを作らないので、
--   一時ファイルをほとんど使わない。
--
-- 重いとき（時間がかかる・「No space left on device」が出る）は、上から順に下げる：
--   1. max_per_day を 300 → 100
--   2. base_days・learn_days を 21 → 14 → 7
--   3. carrier に会社を1つ入れる（例 'JAL'・'ANA'・'SKY'。呼び出し符号の頭3文字）。
--      絞ると、測る便がその会社の便だけになる（予想の数え方は全部の機体のまま）
--   4. それでも重いときは、d を別の日（便の少ない日）にする
--
-- 列：方式・何便先・区分（全体／会社／機種／羽田発着／出どころ）・値・基準の数（答えがある数）・予想を出した数・当たり・
--     当たり率（当たり÷基準の数）・出したうちの当たり率（当たり÷予想を出した数）
--   方式：base＝今の全機の予想、learn＝学ぶ予想（案）、obs＝今の JAL・ANA の予想（便名で数えるので、比べるのは当たり率で）
with recursive
p as (
  select (now() at time zone 'Asia/Tokyo')::date - 1 as d,   -- 測る日（前の日）
         300 as max_per_day,                                  -- 1日に測る便の数の上限
         21 as base_days,                                     -- 今の予想が見る日数（本物は 60）。obs もこれを使う
         21 as learn_days,                                    -- 学ぶ予想が見る日数（案は 42）
         null::text as carrier,                               -- 会社を1つに絞る（例 'JAL'）。null なら絞らない
         20 as min_n                                          -- 会社・機種の区分は、基準の数がこれ以上のものだけ出す
),

-- ===== 全機（reg_legs） =====
anc as materialized (  -- 測る便（その日にこの機体の次の便があるもの）
  select a.reg, a.callsign as cs, a.arr, a.first_at, (a.first_at at time zone 'Asia/Tokyo')::time as tod, r.rt
  from public.reg_legs a cross join p
  left join lateral (
    select mode() within group (order by l.type) as rt from public.reg_legs l
    where l.reg = a.reg and l.type is not null and l.day between p.d - p.learn_days and p.d
  ) r on true
  where a.day = p.d and (p.carrier is null or left(a.callsign, 3) = p.carrier)
    and exists (select 1 from public.reg_legs b where b.reg = a.reg and b.day = a.day and (b.first_at, b.callsign) > (a.first_at, a.callsign))
  order by md5(a.reg || ':' || a.callsign)
  limit (select max_per_day from p)
),
ttcov as materialized (  -- 時刻表がその日をおおっている会社
  select distinct t.operator from public.timetable t, p where t.valid_from <= p.d and t.valid_to >= p.d
),
tt as materialized (   -- その日に飛ぶ JAL・ANA の便（呼び出し符号の形で）
  select distinct t.operator || ltrim(substr(t.flight, 3), '0') as cs, t.dep
  from public.timetable t, p
  where t.valid_from <= p.d and t.valid_to >= p.d and (t.days & (1 << extract(dow from p.d)::int)) <> 0
    and left(t.flight, 2) = case t.operator when 'JAL' then 'JL' when 'ANA' then 'NH' end
),
lv as materialized (   -- 特別塗装機の予定の便
  select s.reg, case left(lp.flight, 2) when 'JL' then 'JAL' else 'ANA' end || ltrim(substr(lp.flight, 3), '0') as cs,
         lp.dep, lp.arr, lp.std, (lp.std at time zone 'Asia/Tokyo')::time as tod
  from public.livery_plans lp join public.livery_sightings s
    on (lp.livery = s.name or strpos(lp.livery, s.name) > 0 or strpos(s.name, lp.livery) > 0), p
  where left(lp.flight, 2) in ('JL', 'NH') and (lp.std at time zone 'Asia/Tokyo')::date = p.d
),
cb as (   -- 今の予想を4便先までたどる（前の base_days 日・同じ曜日2倍・3回以上・4割以上）
  select reg, cs as aid, 0 as k, cs, array[cs] as seen from anc
  union all
  select c.reg, c.aid, c.k + 1, b.nx, c.seen || b.nx
  from cb c cross join p
  cross join lateral (
    select s.nx, s.n, s.sc / nullif(sum(s.sc) over (), 0) as share, row_number() over (order by s.sc desc, s.nx) as rk
    from (
      select nl.callsign as nx, count(*)::int as n, sum(case when extract(dow from pl.day)::int = extract(dow from p.d)::int then 2 else 1 end)::numeric as sc
      from public.reg_legs pl
      cross join lateral (select b.callsign from public.reg_legs b where b.reg = pl.reg and b.day = pl.day and (b.first_at, b.callsign) > (pl.first_at, pl.callsign)
                          order by b.first_at, b.callsign limit 1) nl
      where pl.callsign = c.cs and pl.day >= p.d - p.base_days and pl.day < p.d
      group by nl.callsign
    ) s
  ) b
  where c.k < 4 and b.rk = 1 and b.n >= 3 and b.share >= 0.4 and not (b.nx = any(c.seen))
),
cl as (   -- 学ぶ予想を4便先までたどる（特別塗装機の予定 → 学ぶ → 今の予想）
  select reg, cs as aid, rt, 0 as k, cs, arr as a, tod as t, array[cs] as seen, 'anchor'::text as src from anc
  union all
  select z.reg, z.aid, z.rt, z.k + 1, z.nx, z.carr, z.ctod, z.seen || z.nx,
         case z.prio when 0 then 'livery' when 1 then 'learn' else 'base' end
  from (
    select y.*, row_number() over (partition by y.reg, y.aid order by y.prio, y.ord) as pick
    from (
      select x.*, row_number() over (partition by x.reg, x.aid, x.prio order by x.score desc nulls last, x.std, x.nx) as rk1,
             x.score / nullif(sum(x.score) over (partition by x.reg, x.aid, x.prio), 0) as lshare,
             case x.prio when 0 then 0 else -x.score end as ord
      from (
        select c.reg, c.aid, c.rt, c.k, c.seen, w.prio, w.nx, w.cdep, w.carr, w.ctod, w.n, w.score, w.bshare, w.std
        from cl c cross join p
        cross join lateral (
          -- 特別塗装機の予定の便（出発の空港・時刻が合うもの）
          select 0 as prio, v.cs as nx, v.dep as cdep, v.arr as carr, v.tod as ctod, null::int as n, null::numeric as score, null::numeric as bshare, v.std
          from lv v where v.reg = c.reg and (c.a is null or v.dep = c.a) and (c.t is null or v.tod > c.t)
          union all
          -- 学ぶ（前の learn_days 日・新しい日ほど重く・同じ曜日2倍・その機体自身は3倍・型・時刻表）
          select 1, s.nx, s.cdep, s.carr, s.ctod, s.n, s.g + 2 * coalesce(s.r, 0), null, null
          from (
            select q.nx, count(*)::int as n, sum(q.w) as g, sum(q.w) filter (where q.reg = c.reg) as r,
                   mode() within group (order by q.ndep) as cdep, mode() within group (order by q.narr) as carr,
                   percentile_disc(0.5) within group (order by q.ntod) as ctod
            from (
              select pl.reg, nl.callsign as nx, nl.dep as ndep, nl.arr as narr, (nl.first_at at time zone 'Asia/Tokyo')::time as ntod,
                     power(0.5, (p.d - pl.day) / 14.0) * (case when extract(dow from pl.day)::int = extract(dow from p.d)::int then 2 else 1 end) as w
              from public.reg_legs pl
              cross join lateral (select b.* from public.reg_legs b where b.reg = pl.reg and b.day = pl.day and (b.first_at, b.callsign) > (pl.first_at, pl.callsign)
                                  order by b.first_at, b.callsign limit 1) nl
              where pl.callsign = c.cs and pl.day >= p.d - p.learn_days and pl.day < p.d
                and (pl.arr is null or nl.dep is null or pl.arr = nl.dep)
                and nl.first_at - pl.last_at < interval '10 hours' and nl.first_at - pl.last_at > interval '-30 minutes'
            ) q group by q.nx
          ) s
          left join lateral (   -- その便にいつも入る機体の型
            select count(*) as cnt,
                   sum((case when extract(dow from l.day) = extract(dow from p.d) then 2 else 1 end)::numeric) filter (where l.type = c.rt)
                     / sum((case when extract(dow from l.day) = extract(dow from p.d) then 2 else 1 end)::numeric) as share
            from public.reg_legs l where l.callsign = s.nx and l.type is not null and l.day >= p.d - p.learn_days and l.day < p.d
          ) ty on true
          where (c.a is null or s.cdep is null or s.cdep = c.a) and (c.t is null or s.ctod > c.t)
            and (c.rt is null or ty.cnt = 0 or coalesce(ty.share, 0) >= 0.15)
            and (left(s.nx, 3) not in ('JAL', 'ANA') or not exists (select 1 from ttcov where ttcov.operator = left(s.nx, 3))
                 or (case when c.a is null then exists (select 1 from tt where tt.cs = s.nx)
                          else exists (select 1 from tt where tt.cs = s.nx and tt.dep = c.a) end))
          union all
          -- 今の予想（記録が少ないとき）
          select 2, b.nx, null, b.carr, b.ctod, b.n, 1, b.share, null
          from (
            select s.*, s.sc / nullif(sum(s.sc) over (), 0) as share, row_number() over (order by s.sc desc, s.nx) as rk
            from (
              select nl.callsign as nx, count(*)::int as n,
                     sum(case when extract(dow from pl.day)::int = extract(dow from p.d)::int then 2 else 1 end)::numeric as sc,
                     mode() within group (order by nl.arr) as carr,
                     percentile_disc(0.5) within group (order by (nl.first_at at time zone 'Asia/Tokyo')::time) as ctod
              from public.reg_legs pl
              cross join lateral (select b.* from public.reg_legs b where b.reg = pl.reg and b.day = pl.day and (b.first_at, b.callsign) > (pl.first_at, pl.callsign)
                                  order by b.first_at, b.callsign limit 1) nl
              where pl.callsign = c.cs and pl.day >= p.d - p.base_days and pl.day < p.d
              group by nl.callsign
            ) s
          ) b where b.rk = 1
        ) w
        where c.k < 4 and not (w.nx = any(c.seen))
      ) x
    ) y
    where (y.prio = 0 and y.rk1 = 1)
       or (y.prio = 1 and y.rk1 = 1 and y.n >= 2 and y.lshare >= 0.3)
       or (y.prio = 2 and y.n >= 3 and y.bshare >= 0.4)
  ) z
  where z.pick = 1
),
truth as materialized (
  select a.reg, a.cs as aid, a.rt, b.k, b.callsign as cs, (b.dep = 'HND' or b.arr = 'HND') is true as hnd
  from anc a cross join p
  cross join lateral (
    select l.callsign, l.dep, l.arr, row_number() over (order by l.first_at, l.callsign)::int as k
    from (select * from public.reg_legs l where l.reg = a.reg and l.day = p.d and (l.first_at, l.callsign) > (a.first_at, a.cs)
          order by l.first_at, l.callsign limit 4) l
  ) b
),
res_reg as (
  select 'base' as method, t.k, left(t.aid, 3) as carrier, coalesce(t.rt, '?') as rtype, t.hnd,
         case when c.cs is null then 'none' else 'base' end as src, c.cs as guess, t.cs as answer
  from truth t left join cb c on c.reg = t.reg and c.aid = t.aid and c.k = t.k
  union all
  select 'learn', t.k, left(t.aid, 3), coalesce(t.rt, '?'), t.hnd, coalesce(c.src, 'none'), c.cs, t.cs
  from truth t left join cl c on c.reg = t.reg and c.aid = t.aid and c.k = t.k
),

-- ===== JAL・ANA（便の実績 flight_history と rotation_obs） =====
fh as materialized (
  select h.flight, h.dep, h.arr, h.std, h.sta, h.reg, h.type, h.callsign, h.cancelled
  from public.flight_history h, p where h.svc_date = p.d
),
oleg as materialized (
  select f.*, row_number() over (partition by f.reg order by f.std, f.flight) as i
  from fh f where f.reg is not null and not f.cancelled
),
oanc as materialized (
  select a.* from oleg a, p
  where exists (select 1 from oleg b where b.reg = a.reg and b.i = a.i + 1)
    and (p.carrier is null or coalesce(left(a.callsign, 3), left(a.flight, 2)) = p.carrier)
  order by md5(a.reg || ':' || a.flight)
  limit (select max_per_day from p)
),
co as (
  select reg, i, 0 as k, flight, arr, sta from oanc
  union all
  select z.reg, z.i, z.k + 1, z.nx, z.narr, z.nsta
  from (
    select c.reg, c.i, c.k, o.nx, s.arr as narr, s.sta as nsta,
           row_number() over (partition by c.reg, c.i order by o.sc desc, s.std, o.nx) as rk
    from co c cross join p
    cross join lateral (
      select r.next_flight as nx, sum(case when extract(dow from r.svc_date) = extract(dow from p.d) then 2 else 1 end)::numeric as sc
      from public.rotation_obs r where r.prev_flight = c.flight and r.svc_date >= p.d - p.base_days and r.svc_date < p.d
      group by r.next_flight
    ) o
    join fh s on s.flight = o.nx and s.dep = c.arr and s.std > c.sta + interval '20 minutes'
    where c.k < 4
  ) z where z.rk = 1
),
otruth as materialized (
  select a.reg, a.i, coalesce(left(a.callsign, 3), left(a.flight, 2)) as carrier, coalesce(a.type, '?') as rtype, k.k, b.flight,
         (b.dep = 'HND' or b.arr = 'HND') is true as hnd
  from oanc a cross join generate_series(1, 4) k(k) join oleg b on b.reg = a.reg and b.i = a.i + k.k
),
res as (
  select * from res_reg
  union all
  select 'obs', t.k, t.carrier, t.rtype, t.hnd, case when c.flight is null then 'none' else 'obs' end, c.flight, t.flight
  from otruth t left join co c on c.reg = t.reg and c.i = t.i and c.k = t.k
),
agg as (
  select method, k,
         case when grouping(carrier) = 0 then '会社' when grouping(rtype) = 0 then '機種' when grouping(hnd) = 0 then '羽田発着'
              when grouping(src) = 0 then '出どころ' else '全体' end as kind,
         coalesce(carrier, rtype, case when grouping(hnd) = 0 then case when hnd then '羽田発着' else '羽田以外' end end, src, '') as val,
         count(*) as n, count(guess) as predicted, count(*) filter (where guess = answer) as hit
  from res
  group by grouping sets ((method, k), (method, k, carrier), (method, k, rtype), (method, k, hnd), (method, k, src))
)
select a.method as "方式", a.k as "何便先", a.kind as "区分", a.val as "値", a.n as "基準の数", a.predicted as "予想を出した数", a.hit as "当たり",
       round(100.0 * a.hit / nullif(a.n, 0), 1) as "当たり率%",
       round(100.0 * a.hit / nullif(a.predicted, 0), 1) as "出したうちの当たり率%"
from agg a, p
where a.kind in ('全体', '羽田発着', '出どころ') or a.n >= p.min_n
order by case a.kind when '全体' then 0 when '羽田発着' then 1 when '出どころ' then 2 when '会社' then 3 else 4 end,
         a.val, a.k, case a.method when 'base' then 0 when 'learn' then 1 else 2 end;
