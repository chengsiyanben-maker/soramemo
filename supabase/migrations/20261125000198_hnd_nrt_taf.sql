-- 羽田・成田を優先して取る＋滑走路の予想の当たり具合（PM の指示 11/25 18時45分。本人「羽田、成田の滑走路の使い方を気象と関連付けて予想できそう？」→「羽田、成田は優先的に取って」）
--   1. taf_obs：羽田（RJTT）・成田（RJAA）の飛行場予報（TAF）の原文。発表ごとに1行（wx-archive が1時間ごとに足す。同じ発表は重ねない）
--   2. taf_hours：その発表の1時間ごとの風（ふだんの状態の風向・風速・突風・視程と、その時間に重なる TEMPO・PROB の強い風）
--   3. rwy_wx_eval(空港, 日数)：実際の機体で決めた運用（ops_log の obs_mode）を、①その時刻の風（METAR）②数時間前の TAF でどのくらい当てられるか。
--      時刻別（深夜・15〜19時・ほかの昼）・風の強さ別・切り替わりの前後で分ける。羽田は追い風の上限と「すぐ切り替えない粘り」の組を並べて比べる
--   出どころ：aviationweather.gov（米国の航空気象センター。パブリックドメイン）。利用者の情報は含まない
--   権限：表はどちらも利用者からは読めない・書けない（RLS は ON・方針0。書くのは wx-archive（service_role）だけ）。関数は service_role だけ（本人は SQL Editor で流す）
--   影響：チェックインも経営も関係しない（画面には出さない。構想段階）。運用を集める印・バッジにはしない（却下済み）
--   記録は消さない（表を足すだけ。TAF は1日に約10発表・約300時間行で小さいので、ずっと残す）
set lock_timeout = '5s';

create table if not exists public.taf_obs (
  icao       text not null check (icao ~ '^[A-Z]{4}$'),
  issued_at  timestamptz not null,           -- 発表の時刻
  valid_from timestamptz not null,
  valid_to   timestamptz not null check (valid_to > valid_from),
  raw        text not null check (length(raw) <= 1000),
  fetched_at timestamptz not null default now(),
  primary key (icao, issued_at)
);
comment on table public.taf_obs is '羽田・成田の飛行場予報（TAF）の原文。aviationweather.gov（パブリックドメイン）。wx-archive が1時間ごとに足す';

create table if not exists public.taf_hours (
  icao      text not null check (icao ~ '^[A-Z]{4}$'),
  hr        timestamptz not null,            -- 予報の対象の1時間の始まり（その時間の30分の時点の状態）
  issued_at timestamptz not null,            -- どの発表の予報か
  wdir      smallint check (wdir between 0 and 360),   -- 風向（度）。風向きが定まらない（VRB）ときは null
  wspd      smallint check (wspd between 0 and 200),   -- 風速（ノット）
  wgst      smallint check (wgst between 0 and 250),   -- 突風（ノット）
  vis_m     integer,
  t_wdir    smallint check (t_wdir between 0 and 360), -- その時間に重なる TEMPO・PROB のうち、風のいちばん強いもの
  t_wspd    smallint check (t_wspd between 0 and 200),
  t_wgst    smallint check (t_wgst between 0 and 250),
  primary key (icao, hr, issued_at)          -- 「その時間の、○時間以上前に出た予報」を索引で引く
);
comment on table public.taf_hours is '飛行場予報（TAF）の1時間ごとの風。滑走路の予想の当たり具合（rwy_wx_eval）が使う';

alter table public.taf_obs enable row level security;
alter table public.taf_hours enable row level security;
revoke all on public.taf_obs from public, anon, authenticated;
revoke all on public.taf_hours from public, anon, authenticated;
grant select, insert, update on public.taf_obs, public.taf_hours to service_role;

-- 当たり具合。返す行：kind（どの当て方か）・part（区分）・n（数）・hit（当たり）・pct（％）
--   正解：ops_log の obs_mode（実際の機体からの判定。分かれていた・判定できなかった回は除く）を、向きの2つに直したもの
--     羽田：北風（north・nightN）／南風（south・city・nightS）。成田：34 向き（b）／16 向き（a）
--   風からの当て方：34 滑走路（羽田・成田とも真方位およそ330°）への追い風 = −風速×cos(風向−330°) が T ノットより大きければ南風（成田は16向き）
--     粘り：K 分続くまで切り替えない。戻りの幅：南風から戻るのは追い風が T−H ノットより小さくなってから。記録が60分より空いたら最初から
--     T＝3・5・7・9・11、K＝0・30・60、H＝0・3 の30組。いまの決まり（羽田）は T7・K0・H0
--   TAF からの当て方：その時間について、1・3・6・12時間以上前に出た予報のうち一番新しいものの風で、T7 と「いちばん良い組の T」で当てる（粘りはなし）
--   重さ：ops_log を空港と時刻の索引で読み（90日でも約2.6万行）、TAF は主キーで1行ずつ引く。一時ファイルは使わない
create or replace function public.rwy_wx_eval(p_iata text, p_days int default 30)
returns table (kind text, part text, n int, hit int, pct numeric)
language plpgsql stable security definer set search_path = public as $$
declare
  v_iata text := upper(coalesce(p_iata, ''));
  v_icao text := case upper(coalesce(p_iata, '')) when 'HND' then 'RJTT' when 'NRT' then 'RJAA' end;
  v_days int := least(greatest(coalesce(p_days, 30), 1), 90);
  pn text[] := array['すべて', '深夜 23〜6時', '15〜19時', 'ほかの昼', '風 0〜4kt', '風 5〜9kt', '風 10〜14kt', '風 15kt以上', '切り替わりの前後30分', '切り替わりから離れた時間'];
  ts int[] := array[3, 5, 7, 9, 11]; ks int[] := array[0, 30, 60]; hs int[] := array[0, 3]; ls int[] := array[1, 3, 6, 12];
  np constant int := 10; nc constant int := 30;
  a_at timestamptz[]; a_obs boolean[]; a_est boolean[]; a_tail double precision[]; a_wspd int[];
  sw timestamptz[] := '{}';
  m int; i int; j int; c int; p int; q int; t int; kk int; hh int;
  cn int[]; chit int[]; ln int[]; lh int[]; tn int[]; th int[];
  st boolean[]; pend timestamptz[]; want boolean; reset boolean;
  pt int[]; hr_jst int; near boolean;
  c_def int; c_best int; best_rate double precision := -1; t_best int;
  first_taf timestamptz; tw double precision; tsp double precision; ttail double precision;
begin
  if v_icao is null then raise exception '空港は HND か NRT'; end if;
  select array_agg(o.at order by o.at),
         array_agg(o.obs_mode in ('south', 'city', 'nightS', 'a') order by o.at),
         array_agg(o.est_mode in ('south', 'city', 'nightS', 'a') order by o.at),
         array_agg(case when o.wspd is null then null when o.wdir is null then 0 else -o.wspd * cos(radians(o.wdir - 330)) end order by o.at),
         array_agg(o.wspd::int order by o.at)
    into a_at, a_obs, a_est, a_tail, a_wspd
    from public.ops_log o
   where o.iata = v_iata and o.at > now() - make_interval(days => v_days) and o.obs_mode is not null and not o.obs_mixed;
  m := coalesce(array_length(a_at, 1), 0);
  if m = 0 then return; end if;

  -- 切り替わった時刻（となりの判定との間が30分以内で向きが変わったところ）
  for i in 2..m loop
    if a_obs[i] <> a_obs[i - 1] and a_at[i] - a_at[i - 1] <= interval '30 minutes' then sw := sw || a_at[i]; end if;
  end loop;

  cn := array_fill(0, array[nc * np]); chit := array_fill(0, array[nc * np]);
  ln := array_fill(0, array[np]); lh := array_fill(0, array[np]);
  st := array_fill(null::boolean, array[nc]); pend := array_fill(null::timestamptz, array[nc]);
  c_def := (3 - 1) * 6 + (1 - 1) * 2 + 1;   -- T7・K0・H0
  j := 1;
  for i in 1..m loop
    -- 区分：すべて・時刻・風・切り替わりの前後
    hr_jst := extract(hour from a_at[i] at time zone 'Asia/Tokyo')::int;
    while j <= coalesce(array_length(sw, 1), 0) and sw[j] < a_at[i] - interval '30 minutes' loop j := j + 1; end loop;
    near := j <= coalesce(array_length(sw, 1), 0) and sw[j] <= a_at[i] + interval '30 minutes';
    pt := array[1, case when hr_jst >= 23 or hr_jst < 6 then 2 when hr_jst >= 15 and hr_jst < 19 then 3 else 4 end,
                case when a_wspd[i] is null then 0 when a_wspd[i] < 5 then 5 when a_wspd[i] < 10 then 6 when a_wspd[i] < 15 then 7 else 8 end,
                case when near then 9 else 10 end];
    foreach p in array pt loop
      if p > 0 then ln[p] := ln[p] + 1; if a_est[i] = a_obs[i] then lh[p] := lh[p] + 1; end if; end if;
    end loop;
    if a_tail[i] is null then continue; end if;
    reset := i = 1 or a_at[i] - a_at[i - 1] > interval '60 minutes';
    for c in 1..nc loop
      t := ts[(c - 1) / 6 + 1]; kk := ks[((c - 1) / 2) % 3 + 1]; hh := hs[(c - 1) % 2 + 1];
      if reset or st[c] is null then
        st[c] := a_tail[i] > t; pend[c] := null;
      else
        want := case when st[c] then a_tail[i] >= t - hh else a_tail[i] > t end;
        if want <> st[c] then
          if pend[c] is null then pend[c] := a_at[i]; end if;
          if a_at[i] - pend[c] >= make_interval(mins => kk) then st[c] := want; pend[c] := null; end if;
        else pend[c] := null; end if;
      end if;
      foreach p in array pt loop
        if p > 0 then
          q := (c - 1) * np + p; cn[q] := cn[q] + 1;
          if st[c] = a_obs[i] then chit[q] := chit[q] + 1; end if;
        end if;
      end loop;
    end loop;
  end loop;

  -- いちばん良い組（すべての区分の当たりの割合。同じなら番号の小さいほう）
  for c in 1..nc loop
    q := (c - 1) * np + 1;
    if cn[q] > 0 and chit[q]::double precision / cn[q] > best_rate then best_rate := chit[q]::double precision / cn[q]; c_best := c; end if;
  end loop;
  t_best := ts[(c_best - 1) / 6 + 1];

  -- TAF から（予報がある時刻だけ）
  tn := array_fill(0, array[8 * np]); th := array_fill(0, array[8 * np]);
  select min(h.issued_at) into first_taf from public.taf_obs h where h.icao = v_icao;
  if first_taf is not null then
    j := 1;
    for i in 1..m loop
      if a_at[i] < first_taf then continue; end if;
      hr_jst := extract(hour from a_at[i] at time zone 'Asia/Tokyo')::int;
      while j <= coalesce(array_length(sw, 1), 0) and sw[j] < a_at[i] - interval '30 minutes' loop j := j + 1; end loop;
      near := j <= coalesce(array_length(sw, 1), 0) and sw[j] <= a_at[i] + interval '30 minutes';
      for kk in 1..4 loop
        select h.wdir, h.wspd into tw, tsp from public.taf_hours h
         where h.icao = v_icao and h.hr = date_trunc('hour', a_at[i]) and h.issued_at <= a_at[i] - make_interval(hours => ls[kk])
         order by h.issued_at desc limit 1;
        if not found or tsp is null then continue; end if;
        ttail := case when tw is null then 0 else -tsp * cos(radians(tw - 330)) end;
        pt := array[1, case when hr_jst >= 23 or hr_jst < 6 then 2 when hr_jst >= 15 and hr_jst < 19 then 3 else 4 end,
                    case when tsp < 5 then 5 when tsp < 10 then 6 when tsp < 15 then 7 else 8 end, case when near then 9 else 10 end];
        foreach p in array pt loop
          q := (kk - 1) * np + p; tn[q] := tn[q] + 1; if (ttail > 7) = a_obs[i] then th[q] := th[q] + 1; end if;
          q := (kk + 3) * np + p; tn[q] := tn[q] + 1; if (ttail > t_best) = a_obs[i] then th[q] := th[q] + 1; end if;
        end loop;
      end loop;
    end loop;
  end if;

  -- 返す
  for p in 1..np loop
    if ln[p] > 0 then kind := '1. いまの推定（記録の est_mode）'; part := pn[p]; n := ln[p]; hit := lh[p]; pct := round(100.0 * lh[p] / ln[p], 1); return next; end if;
  end loop;
  for p in 1..np loop
    q := (c_def - 1) * np + p;
    if cn[q] > 0 then kind := '2. 実況の風（追い風7kt・粘りなし）'; part := pn[p]; n := cn[q]; hit := chit[q]; pct := round(100.0 * chit[q] / cn[q], 1); return next; end if;
  end loop;
  for p in 1..np loop
    q := (c_best - 1) * np + p;
    if cn[q] > 0 then
      kind := format('3. 実況の風（いちばん良い組：追い風%skt・粘り%s分・戻り幅%skt）', ts[(c_best - 1) / 6 + 1], ks[((c_best - 1) / 2) % 3 + 1], hs[(c_best - 1) % 2 + 1]);
      part := pn[p]; n := cn[q]; hit := chit[q]; pct := round(100.0 * chit[q] / cn[q], 1); return next;
    end if;
  end loop;
  for c in 1..nc loop
    foreach p in array array[1, 9] loop
      q := (c - 1) * np + p;
      if cn[q] > 0 then
        kind := format('4. 組 追い風%skt・粘り%s分・戻り幅%skt', ts[(c - 1) / 6 + 1], ks[((c - 1) / 2) % 3 + 1], hs[(c - 1) % 2 + 1]);
        part := pn[p]; n := cn[q]; hit := chit[q]; pct := round(100.0 * chit[q] / cn[q], 1); return next;
      end if;
    end loop;
  end loop;
  for kk in 1..8 loop
    for p in 1..np loop
      q := (kk - 1) * np + p;
      if tn[q] > 0 then
        kind := format('5. TAF %s時間以上前の発表（追い風%skt）', ls[(kk - 1) % 4 + 1], case when kk <= 4 then 7 else t_best end);
        part := pn[p]; n := tn[q]; hit := th[q]; pct := round(100.0 * th[q] / tn[q], 1); return next;
      end if;
    end loop;
  end loop;
end
$$;
comment on function public.rwy_wx_eval(text, int) is '滑走路の運用を実況の風・TAF でどのくらい当てられるか（羽田・成田。運営の分析用。画面には出さない）';
revoke all on function public.rwy_wx_eval(text, int) from public, anon, authenticated;
grant execute on function public.rwy_wx_eval(text, int) to service_role;

reset lock_timeout;
