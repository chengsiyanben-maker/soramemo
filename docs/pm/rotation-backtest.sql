-- そらメモ：機体の運用の予想の当たり具合（読むだけ。表も関数も作らず、何も書き込まない）
--
-- 使い方：Supabase の SQL Editor にこのファイルをまるごと貼って「Run」。結果の表を CSV で書き出すか、全部選んでコピーして貼り返す。
--   重いときは、下の p の d_from を後ろにずらす（測る日を減らす）か、max_per_day を小さくする。
--
-- 測り方：測る日（D）ごとに、その日の機体の便を1つずつ「いまの便」とみなし、D の前の日までの記録だけで（＝前の日の夜の時点で）
--   この先4便を予想して、その日の実際の便（reg_legs、JAL・ANA は flight_history）と比べる。
--
-- 方式：
--   base ＝今の予想（predict_rotation_reg と同じ決め方：前の60日・同じ曜日2倍・3回以上・4割以上）
--   learn＝学ぶ予想（ブランチ data/rotation-predict の rot_predict と同じ決め方）
--   obs  ＝今の JAL・ANA の予想（predict_rotation と同じ決め方：rotation_obs・その日の便で出発の空港と時刻が合うもの）
--          ※ obs は便名（JL・NH）で数えるので、base・learn とは「基準の数」がちがう。比べるのは当たり率で
--
-- 列：方式・何便先・区分（全体／会社／機種／羽田発着／出どころ）・値・基準の数（答えがある数）・予想を出した数・当たり・
--     当たり率（当たり÷基準の数）・出したうちの当たり率（当たり÷予想を出した数）
with recursive
p as (
  select (now() at time zone 'Asia/Tokyo')::date - 7 as d_from,   -- 測る最初の日
         (now() at time zone 'Asia/Tokyo')::date - 1 as d_to,     -- 測る最後の日
         1500 as max_per_day,                                     -- 1日に測る便の数の上限（重さの調整）
         20 as min_n                                              -- 会社・機種の区分は、基準の数がこれ以上のものだけ出す
),
days as (select generate_series(p.d_from, p.d_to, interval '1 day')::date as d from p),

-- ===== 全機（reg_legs） =====
legs as materialized (
  select l.reg, l.day, l.callsign as cs, l.type, l.dep, l.arr, l.first_at, l.last_at,
         (l.first_at at time zone 'Asia/Tokyo')::time as tod,
         row_number() over (partition by l.reg, l.day order by l.first_at, l.callsign) as i
  from public.reg_legs l, p where l.day between p.d_from - 60 and p.d_to
),
pr as materialized (   -- 機体のつながり（rot_pairs と同じ）
  select a.reg, a.day, a.cs as prev, b.cs as nx, b.dep as ndep, b.arr as narr, b.type as ntype, b.tod as ntod,
         extract(dow from a.day)::int as dw,
         (a.arr is null or b.dep is null or a.arr = b.dep) and b.first_at - a.last_at < interval '10 hours' and b.first_at - a.last_at > interval '-30 minutes' as ok
  from legs a join legs b on b.reg = a.reg and b.day = a.day and b.i = a.i + 1
),
sb as materialized (   -- 今の予想の数え方
  select d.d, pr.prev, pr.nx, count(*)::int as n,
         sum(case when pr.dw = extract(dow from d.d)::int then 2 else 1 end)::numeric as sc,
         mode() within group (order by pr.narr) as carr, percentile_disc(0.5) within group (order by pr.ntod) as ctod
  from days d join pr on pr.day >= d.d - 60 and pr.day < d.d group by 1, 2, 3
),
bb as materialized (   -- 今の予想の1歩：いちばん多い次の便
  select s.*, s.sc / nullif(sum(s.sc) over (partition by s.d, s.prev), 0) as share,
         row_number() over (partition by s.d, s.prev order by s.sc desc, s.nx) as rk
  from sb s
),
sl as materialized (   -- 学ぶ予想の数え方（全部の機体）
  select d.d, pr.prev, pr.nx, count(*)::int as n,
         sum(power(0.5, (d.d - pr.day) / 14.0) * (case when pr.dw = extract(dow from d.d)::int then 2 else 1 end)) as g,
         mode() within group (order by pr.ndep) as cdep, mode() within group (order by pr.narr) as carr,
         percentile_disc(0.5) within group (order by pr.ntod) as ctod
  from days d join pr on pr.ok and pr.day >= d.d - 42 and pr.day < d.d group by 1, 2, 3
),
slr as materialized (  -- 学ぶ予想の数え方（その機体だけ）
  select d.d, pr.reg, pr.prev, pr.nx,
         sum(power(0.5, (d.d - pr.day) / 14.0) * (case when pr.dw = extract(dow from d.d)::int then 2 else 1 end)) as r
  from days d join pr on pr.ok and pr.day >= d.d - 42 and pr.day < d.d group by 1, 2, 3, 4
),
ty as materialized (   -- 便ごとに入った機体の型（同じ曜日2倍）
  select d.d, l.cs, l.type, sum(case when extract(dow from l.day) = extract(dow from d.d) then 2 else 1 end)::numeric as w
  from days d join legs l on l.type is not null and l.day >= d.d - 42 and l.day < d.d group by 1, 2, 3
),
tyt as materialized (select t.*, t.w / sum(t.w) over (partition by t.d, t.cs) as share from ty t),
tyh as materialized (select distinct d, cs from ty),
rty as materialized (  -- 機体の型
  select d.d, l.reg, mode() within group (order by l.type) as rt
  from days d join legs l on l.type is not null and l.day between d.d - 42 and d.d group by 1, 2
),
ttcov as materialized (  -- 時刻表がその日をおおっている会社
  select distinct d.d, t.operator from days d join public.timetable t on t.valid_from <= d.d and t.valid_to >= d.d
),
tt as materialized (   -- その日に飛ぶ JAL・ANA の便（呼び出し符号の形で）
  select distinct d.d, t.operator || ltrim(substr(t.flight, 3), '0') as cs, t.dep
  from days d join public.timetable t on t.valid_from <= d.d and t.valid_to >= d.d and (t.days & (1 << extract(dow from d.d)::int)) <> 0
  where left(t.flight, 2) = case t.operator when 'JAL' then 'JL' when 'ANA' then 'NH' end
),
tta as materialized (select distinct d, cs from tt),
lv as materialized (   -- 特別塗装機の予定の便（livery_plans は flight_schedule と一緒に14日で消えるので、それより前の日は出ない）
  select (lp.std at time zone 'Asia/Tokyo')::date as d, s.reg,
         case left(lp.flight, 2) when 'JL' then 'JAL' else 'ANA' end || ltrim(substr(lp.flight, 3), '0') as cs,
         lp.dep, lp.arr, lp.std, (lp.std at time zone 'Asia/Tokyo')::time as tod
  from public.livery_plans lp join public.livery_sightings s
    on (lp.livery = s.name or strpos(lp.livery, s.name) > 0 or strpos(s.name, lp.livery) > 0), p
  where left(lp.flight, 2) in ('JL', 'NH') and (lp.std at time zone 'Asia/Tokyo')::date between p.d_from and p.d_to
),
cand as materialized (  -- 学ぶ予想の候補（key：前の便、特別塗装機は '@'＋登録記号）
  select d, '@' || reg as key, 0 as prio, cs as nx, dep as cdep, arr as carr, tod as ctod, null::int as n, null::numeric as g, null::numeric as bshare, std
  from lv
  union all
  select d, prev, 1, nx, cdep, carr, ctod, n, g, null, null from sl
  union all
  select d, prev, 2, nx, null, carr, ctod, n, null, share, null from bb where rk = 1
),
anc as materialized (  -- 測る便（その日にこの機体の次の便があるもの）
  select a.reg, a.day as d, a.i, a.cs, a.arr, a.tod, r.rt
  from (select a.*, row_number() over (partition by a.day order by md5(a.reg || ':' || a.cs)) as pick
        from legs a join days on days.d = a.day join legs b on b.reg = a.reg and b.day = a.day and b.i = a.i + 1) a
  left join rty r on r.d = a.day and r.reg = a.reg, p
  where a.pick <= p.max_per_day
),
cb as (   -- 今の予想を4便先までたどる
  select reg, d, i, 0 as k, cs, array[cs] as seen from anc
  union all
  select c.reg, c.d, c.i, c.k + 1, b.nx, c.seen || b.nx
  from cb c join bb b on b.d = c.d and b.prev = c.cs and b.rk = 1
  where c.k < 4 and b.n >= 3 and b.share >= 0.4 and not (b.nx = any(c.seen))
),
cl as (   -- 学ぶ予想を4便先までたどる
  select reg, d, i, rt, 0 as k, cs, arr as a, tod as t, array[cs] as seen, 'anchor'::text as src from anc
  union all
  select z.reg, z.d, z.i, z.rt, z.k + 1, z.nx, z.carr, z.ctod, z.seen || z.nx,
         case z.prio when 0 then 'livery' when 1 then 'learn' else 'base' end
  from (
    select y.*, row_number() over (partition by y.reg, y.d, y.i order by y.prio, y.ord) as pick
    from (
      select x.*, row_number() over (partition by x.reg, x.d, x.i, x.prio order by x.score desc nulls last, x.std, x.nx) as rk1,
             x.score / nullif(sum(x.score) over (partition by x.reg, x.d, x.i, x.prio), 0) as lshare,
             case x.prio when 0 then 0 else -x.score end as ord
      from (
        select c.reg, c.d, c.i, c.rt, c.k, c.seen, w.prio, w.nx, w.cdep, w.carr, w.ctod, w.n, w.bshare, w.std,
               case w.prio when 1 then w.g + 2 * coalesce(r.r, 0) when 2 then 1 end as score
        from cl c
        cross join lateral (values (c.cs), ('@' || c.reg)) kk(key)
        join cand w on w.d = c.d and w.key = kk.key
        left join slr r on w.prio = 1 and r.d = c.d and r.reg = c.reg and r.prev = c.cs and r.nx = w.nx
        left join tyt t1 on w.prio = 1 and t1.d = c.d and t1.cs = w.nx and t1.type = c.rt
        left join tyh t0 on w.prio = 1 and t0.d = c.d and t0.cs = w.nx
        left join ttcov tc on w.prio = 1 and tc.d = c.d and tc.operator = left(w.nx, 3) and left(w.nx, 3) in ('JAL', 'ANA')
        left join tt on w.prio = 1 and tt.d = c.d and tt.cs = w.nx and tt.dep = c.a
        left join tta on w.prio = 1 and tta.d = c.d and tta.cs = w.nx
        where c.k < 4 and not (w.nx = any(c.seen))
          and (w.prio <> 0 or ((c.a is null or w.cdep = c.a) and (c.t is null or w.ctod > c.t)))
          and (w.prio <> 1 or (
                (c.a is null or w.cdep is null or w.cdep = c.a) and (c.t is null or w.ctod > c.t)
            and (c.rt is null or t0.cs is null or coalesce(t1.share, 0) >= 0.15)
            and (tc.operator is null or (case when c.a is null then tta.cs is not null else tt.cs is not null end))))
      ) x
    ) y
    where (y.prio = 0 and y.rk1 = 1)
       or (y.prio = 1 and y.rk1 = 1 and y.n >= 2 and y.lshare >= 0.3)
       or (y.prio = 2 and y.n >= 3 and y.bshare >= 0.4)
  ) z
  where z.pick = 1
),
truth as materialized (
  select a.reg, a.d, a.i, a.cs as acs, a.rt, k.k, b.cs, (b.dep = 'HND' or b.arr = 'HND') is true as hnd
  from anc a cross join generate_series(1, 4) k(k) join legs b on b.reg = a.reg and b.day = a.d and b.i = a.i + k.k
),
res_reg as (
  select 'base' as method, t.k, left(t.acs, 3) as carrier, coalesce(t.rt, '?') as rtype, t.hnd,
         case when c.cs is null then 'none' else 'base' end as src, c.cs as guess, t.cs as answer
  from truth t left join cb c on c.reg = t.reg and c.d = t.d and c.i = t.i and c.k = t.k
  union all
  select 'learn', t.k, left(t.acs, 3), coalesce(t.rt, '?'), t.hnd, coalesce(c.src, 'none'), c.cs, t.cs
  from truth t left join cl c on c.reg = t.reg and c.d = t.d and c.i = t.i and c.k = t.k
),

-- ===== JAL・ANA（便の実績 flight_history と rotation_obs） =====
fh as materialized (
  select h.svc_date as d, h.flight, h.dep, h.arr, h.std, h.sta, h.reg, h.type, h.callsign, h.cancelled
  from public.flight_history h, p where h.svc_date between p.d_from and p.d_to
),
ob as materialized (
  select d.d, o.prev_flight as prev, o.next_flight as nx, sum(case when extract(dow from o.svc_date) = extract(dow from d.d) then 2 else 1 end)::numeric as sc
  from days d join public.rotation_obs o on o.svc_date >= d.d - 60 and o.svc_date < d.d group by 1, 2, 3
),
oleg as materialized (
  select f.*, row_number() over (partition by f.d, f.reg order by f.std, f.flight) as i
  from fh f where f.reg is not null and not f.cancelled
),
oanc as materialized (
  select a.* from (select a.*, row_number() over (partition by a.d order by md5(a.reg || ':' || a.flight)) as pick
                   from oleg a join oleg b on b.d = a.d and b.reg = a.reg and b.i = a.i + 1) a, p
  where a.pick <= p.max_per_day
),
co as (
  select reg, d, i, 0 as k, flight, arr, sta from oanc
  union all
  select z.reg, z.d, z.i, z.k + 1, z.nx, z.narr, z.nsta
  from (
    select c.reg, c.d, c.i, c.k, o.nx, s.arr as narr, s.sta as nsta,
           row_number() over (partition by c.reg, c.d, c.i order by o.sc desc, s.std, o.nx) as rk
    from co c join ob o on o.d = c.d and o.prev = c.flight
    join fh s on s.d = c.d and s.flight = o.nx and s.dep = c.arr and s.std > c.sta + interval '20 minutes'
    where c.k < 4
  ) z where z.rk = 1
),
otruth as materialized (
  select a.reg, a.d, a.i, coalesce(left(a.callsign, 3), left(a.flight, 2)) as carrier, coalesce(a.type, '?') as rtype, k.k, b.flight,
         (b.dep = 'HND' or b.arr = 'HND') is true as hnd
  from oanc a cross join generate_series(1, 4) k(k) join oleg b on b.d = a.d and b.reg = a.reg and b.i = a.i + k.k
),
res as (
  select * from res_reg
  union all
  select 'obs', t.k, t.carrier, t.rtype, t.hnd, case when c.flight is null then 'none' else 'obs' end, c.flight, t.flight
  from otruth t left join co c on c.reg = t.reg and c.d = t.d and c.i = t.i and c.k = t.k
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
