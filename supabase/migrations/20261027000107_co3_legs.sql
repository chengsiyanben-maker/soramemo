-- エアライン経営 co-v3：便の時刻（おまかせのスケジュール）と便ごとの客
--   1日の便数（往復の数）を 6:30〜23:30 の17時間に並べる（co3.legs_per_day と同じ考え：1便 ＝ 距離÷820km/h ＋ 40分、折り返し 40分）
--   間隔 ＝ max(1便＋折り返し, (17時間 − 1便) ÷ (便数 − 1))、5分単位。本拠地が路線の端なら本拠地から、ほかは路線の a から出る
--   客の振り分け：仕事の客は朝（〜9:30）×1.6・夕方（16:30〜20:00）×1.4・昼 ×0.6・夜 ×0.7、旅行の客は昼（9:30〜16:30）×1.25・ほか ×0.85
--     満席（その便の席）を超えた分は、ほかの便に回す。合計は路線の計算の「運んだ客」と同じ
--   路線の計算（co3_route_econ）に「運んだ客のうち仕事の客」（biz_pax）の列を足す（列が増えるので作り直す）
--   これは「おまかせ」の形。自分で組むスケジュール・便ごとのトラブル・遅れは、この上に作る

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  if position('biz_pax numeric' in src) = 0 then
    if position('economy_pax numeric)' in src) = 0 or position('round(m.car_e, 1)' || chr(10) || '    from m' in src) = 0 then
      raise exception 'co3_route_econ の形が変わっていて、仕事の客の列を足せない';
    end if;
    src := replace(src, 'economy_pax numeric)', 'economy_pax numeric, biz_pax numeric)');
    src := replace(src, 'round(m.car_e, 1)' || chr(10) || '    from m',
      'round(m.car_e, 1),' || chr(10) ||
      '         round(m.car_p + m.car_e * least(1, greatest(0, m.own * coalesce(m.biz_frac, 0) - m.car_p) / nullif(m.own - m.car_p, 0)), 1)' || chr(10) || '    from m');
    drop function public.co3_route_econ(uuid);
    execute src;
    revoke all on function public.co3_route_econ(uuid) from public, anon, authenticated;
  end if;
end
$do$;

create or replace function co3.leg_block_min(p_km numeric) returns integer
language sql immutable as $$ select (round(p_km / 820 * 60) + 40)::int $$;
create or replace function co3.biz_weight(p_min integer) returns numeric
language sql immutable as $$ select case when p_min < 570 then 1.6 when p_min < 990 then 0.6 when p_min < 1200 then 1.4 else 0.7 end::numeric $$;
create or replace function co3.leisure_weight(p_min integer) returns numeric
language sql immutable as $$ select case when p_min >= 570 and p_min < 990 then 1.25 else 0.85 end::numeric $$;
revoke all on function co3.leg_block_min(numeric), co3.biz_weight(integer), co3.leisure_weight(integer) from public, anon, authenticated;

-- 便ごと：出発・到着（日本時間の0時からの分）・向き・席・仕事の客・旅行の客
create or replace function public.co3_route_legs(p_uid uuid)
returns table (route_key text, leg integer, dep_min integer, arr_min integer, dep text, arr text, seats numeric, biz numeric, leisure numeric)
language plpgsql stable security definer set search_path = public as $$
declare e record; home text; blk int; gap int; n int; i int; it int;
        d int[]; cap numeric[]; b numeric[]; l numeric[]; w numeric[]; act boolean[]; rest numeric; sw numeric; x numeric;
begin
  select a.iata into home from companies c left join airports a on a.id = c.home_airport where c.user_id = p_uid;
  for e in select * from co3_route_econ(p_uid) r where r.flights > 0 loop
    n := e.flights; blk := co3.leg_block_min(e.km);
    gap := case when n > 1 then greatest(blk + 40, ((1020 - blk) / (n - 1) / 5) * 5) else 0 end;
    d := array[]::int[]; cap := array[]::numeric[];
    for i in 1..n loop d := d || (390 + (i - 1) * gap); cap := cap || e.seats; end loop;
    -- 仕事の客 → 旅行の客の順に、重みで分けて満席を超えた分を回す（5回まで）
    for it in 1..2 loop
      rest := case when it = 1 then coalesce(e.biz_pax, 0) else greatest(0, e.carried - coalesce(e.biz_pax, 0)) end;
      w := array[]::numeric[]; act := array[]::boolean[];
      for i in 1..n loop
        w := w || case when it = 1 then co3.biz_weight(d[i]) else co3.leisure_weight(d[i]) end;
        act := act || true;
        if it = 1 then b[i] := 0; else l[i] := 0; end if;
      end loop;
      for x in 1..5 loop
        exit when rest <= 0.001;
        sw := 0; for i in 1..n loop if act[i] then sw := sw + w[i]; end if; end loop;
        exit when sw = 0;
        declare give numeric := rest; add numeric; room numeric;
        begin
          for i in 1..n loop
            continue when not act[i];
            room := cap[i] - coalesce(b[i], 0) - coalesce(l[i], 0);
            add := least(room, give * w[i] / sw);
            if it = 1 then b[i] := coalesce(b[i], 0) + add; else l[i] := coalesce(l[i], 0) + add; end if;
            rest := rest - add;
            if add >= room - 0.001 then act[i] := false; end if;
          end loop;
        end;
      end loop;
    end loop;
    for i in 1..n loop
      route_key := e.route_key; leg := i; dep_min := d[i]; arr_min := d[i] + blk;
      if (home is not null and home = e.b) then
        dep := case when i % 2 = 1 then e.b else e.a end; arr := case when i % 2 = 1 then e.a else e.b end;
      else
        dep := case when i % 2 = 1 then e.a else e.b end; arr := case when i % 2 = 1 then e.b else e.a end;
      end if;
      seats := cap[i]; biz := round(coalesce(b[i], 0), 1); leisure := round(coalesce(l[i], 0), 1);
      return next;
    end loop;
  end loop;
end;
$$;
revoke all on function public.co3_route_legs(uuid) from public, anon, authenticated;

do $do$
declare src text;
begin
  select pg_get_functiondef('public.co_state()'::regprocedure) into src;
  if position('''biz'', e.biz_pax' in src) = 0 then
    if position($r$'e_pax', e.economy_pax$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、仕事の客を入れられない'; end if;
    src := replace(src, $r$'e_pax', e.economy_pax$r$, $r$'e_pax', e.economy_pax, 'biz', e.biz_pax$r$);
  end if;
  if position('co3_route_legs' in src) = 0 then
    if position($r$'satisfaction', c.satisfaction,$r$ in src) = 0 then raise exception 'co_state の形が変わっていて、便の時刻を入れられない'; end if;
    src := replace(src, $r$'satisfaction', c.satisfaction,$r$,
      $r$'legs', case when v3 and c.policy in ('fsc', 'mcc', 'lcc', 'regional') then (
        select coalesce(jsonb_object_agg(g.route_key, g.legs), '{}'::jsonb) from (
          select x.route_key, jsonb_agg(jsonb_build_object('n', x.leg, 't', x.dep_min, 'ta', x.arr_min, 'f', x.dep, 'to', x.arr,
                   'seats', x.seats, 'biz', x.biz, 'lei', x.leisure) order by x.leg) as legs
            from co3_route_legs(uid) x group by x.route_key) g) end,
    'satisfaction', c.satisfaction,$r$);
  end if;
  execute src;
end
$do$;
