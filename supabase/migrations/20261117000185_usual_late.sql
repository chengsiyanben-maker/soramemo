-- 「いつもより○分遅い（推定）」の画面に要る読むだけの関数（データ担当・11/17）
--   決定事項【11/17】いつもより遅いは案A（design/usual-late 2版）。画面（乗る便のカード・案内板・便のくわしく）が、
--   時刻表にない便（海外の会社・ODPT にない日本の会社）の「いつもの到着」「着く見込み」「いつもより○分」「出典」「曜日とばらつき」を読む。
--   usual_late(p_flight, p_reg, p_day, p_arr, p_land) → jsonb
--     ・便名（BA5・BA005）か登録記号（G-XWBA）のどちらかで引く（両方あれば便名）。登録記号は全機の記録（reg_legs）のその日と前の日の、いちばん新しい呼び出し符号
--     ・いつもの到着：foreign_usual（前の8週の実績の着陸の時刻の中央値。その曜日 → 曜日を問わない、の順）。dow（0＝日曜…6＝土曜、曜日を問わないときは null）・n・spread を返す
--     ・着く見込み（着陸）：①その日の実績（foreign_legs。着いたあと）②画面が flight-live から受け取った land_pred を p_land で渡したとき
--       ③見張り（foreign_watch.eta。10分以内に書かれたものだけ。見張りの関数をつないだあと）、の順。どれもなければ null（画面は U1n-v2「見込みはまだ出せません」）
--     ・いつもより○分：見込み − いつも（0時をまたいでも ±12時間で比べる）。kind は late（15分以上遅い）・usual（前後14分以内）・early（15分以上早い）。
--       ダイバート・引き返しのときは比べない（null）
--     ・JAL・ANA など ODPT で見られる会社の便は reason 'odpt' だけを返す（画面は今までどおり ODPT の定刻と遅れを使う）
--   形のちがう値（便名も登録記号も読めない・空港や日の形がちがう）は null を返す。誰が乗るか・誰が選んだかは返さない
--   読むのは索引（主キー）で引く数か所だけで、表を全部読まない。anon・authenticated は実行だけ（表には今までどおり何も許さない）
--   影響：チェックイン（画面案のあと renderRideIntl・foreignHTML・spDetailHTML から呼ぶ）。経営は使わない。表は変えない（RLS も今のまま）
set lock_timeout = '10s';

create or replace function public.usual_late(p_flight text default null, p_reg text default null, p_day date default null,
                                             p_arr text default null, p_land timestamptz default null) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  v_today date := (now() at time zone 'Asia/Tokyo')::date;
  v_day   date := coalesce(p_day, (now() at time zone 'Asia/Tokyo')::date);
  v_fl    text := nullif(upper(regexp_replace(coalesce(p_flight, ''), '\s', '', 'g')), '');
  v_reg   text := nullif(upper(trim(coalesce(p_reg, ''))), '');
  v_arr   text := nullif(upper(trim(coalesce(p_arr, ''))), '');
  v_cs    text;
  v_dow   int;
  w       record;
  u       record;
  l       record;
  v_seen  timestamptz;
  v_mid   timestamptz;
  v_win   interval;
  v_ground boolean;
  v_eta   timestamptz;
  v_src   text;
  v_late  int;
  v_kind  text;
  v_event text;
  v_to    text;
  hhmm    constant text := 'HH24:MI';
begin
  if v_fl is not null and v_fl !~ '^[A-Z0-9]{2}[0-9]{1,4}$' then v_fl := null; end if;
  if v_reg is not null and v_reg !~ '^[A-Z0-9-]{2,10}$' then v_reg := null; end if;
  if (v_fl is null and v_reg is null) or (v_arr is not null and v_arr !~ '^[A-Z]{3}$')
     or v_day not between v_today - 7 and v_today + 1 then
    return null;
  end if;
  if v_fl is not null then v_fl := regexp_replace(v_fl, '^([A-Z0-9]{2})0+([0-9])', '\1\2'); end if;   -- BA005 → BA5

  -- 呼び出し符号
  if v_fl is not null then
    if exists (select 1 from public.airline_codes c where c.iata = left(v_fl, 2) and c.odpt) then
      return jsonb_build_object('flight', v_fl, 'day', v_day, 'reason', 'odpt');
    end if;
    select c.icao || substring(v_fl from 3) into v_cs
      from public.airline_codes c where c.iata = left(v_fl, 2) and not c.odpt order by c.icao limit 1;
  else
    select r.callsign into v_cs from public.reg_legs r
     where r.reg = v_reg and r.day between v_day - 1 and v_day order by r.last_at desc limit 1;   -- 主キー（reg, day, …）で引く
    if v_cs is not null then
      if exists (select 1 from public.airline_codes c where c.icao = left(v_cs, 3) and c.odpt) then
        return jsonb_build_object('reg', v_reg, 'day', v_day, 'callsign', v_cs, 'reason', 'odpt');
      end if;
      select c.iata || substring(v_cs from '^[A-Z]{3}0*([0-9]{1,4})') into v_fl
        from public.airline_codes c where c.icao = left(v_cs, 3);
    end if;
  end if;
  if v_cs is null then
    return jsonb_build_object('flight', v_fl, 'reg', v_reg, 'day', v_day, 'reason', 'unknown', 'usual', null, 'eta', null,
                              'late_min', null, 'kind', null, 'source', 'adsb.lol（ODbL）',
                              'note', '推定です。定刻や航空会社の発表ではありません');
  end if;

  -- 見張りの行（乗る便に選ばれた便だけ）。行がなくても record に null を入れるため、いつも select する
  select * into w from public.foreign_watch fw where fw.flight = v_fl and fw.svc_date = v_day;

  -- 着く日本の空港：渡された空港 → 見張りの行 → いつもの時刻のある空港（その曜日を先に・回数の多いもの）
  v_dow := extract(dow from v_day)::int;
  if v_arr is null and w.flight is not null then v_arr := w.arr; end if;
  if v_arr is null then
    select fu.iata into v_arr from public.foreign_usual fu
     where fu.callsign = v_cs and fu.dep_here = 0 and fu.dow in (v_dow, -1)
     order by (fu.dow = -1), fu.n desc, fu.iata limit 1;
  end if;

  -- いつもの到着
  select fu.mins, fu.n, fu.spread, fu.dow into u from public.foreign_usual fu
   where fu.callsign = v_cs and fu.iata = v_arr and fu.dep_here = 0 and fu.dow in (v_dow, -1)
   order by fu.dow desc limit 1;

  -- その日の実績（着いたあと）。いつもの時刻があればその前後6時間、なければその日の12時（日本時間）の前後12時間で、いちばん近い着陸
  --   （毎日飛ぶ便で、前の日・次の日の同じ便を取らないため。0時をまたいで遅れた便も、いつもの時刻の近くなら取る）
  v_mid := (v_day::timestamp + make_interval(mins => coalesce(u.mins, 720))) at time zone 'Asia/Tokyo';
  v_win := case when u.mins is not null then interval '6 hours' else interval '12 hours' end;
  select fl.iata, fl.at, fl.event, fl.other into l from public.foreign_legs fl
   where fl.callsign = v_cs and fl.dep_here = 0 and fl.at >= v_mid - v_win and fl.at < v_mid + v_win
     and (v_arr is null or fl.iata = v_arr or fl.event is not null)
   order by abs(extract(epoch from fl.at - v_mid)), fl.at limit 1;

  -- いまの位置（記録の処理が残した最新の位置。15分より古いものは消えている）
  select lp.seen_at, lp.ground into v_seen, v_ground from public.live_positions lp
   where lp.callsign = v_cs and lp.seen_at > now() - interval '15 minutes';

  if l.at is not null then
    v_eta := l.at; v_src := 'track'; v_event := l.event;
    if l.event = 'divert' then v_to := l.iata; end if;
  elsif p_land is not null and p_land between now() - interval '15 minutes' and now() + interval '20 hours' then
    v_eta := p_land; v_src := 'live';
  elsif w.flight is not null and w.eta is not null and w.updated_at > now() - interval '10 minutes' then
    v_eta := w.eta; v_src := 'watch';
  end if;
  if v_event is null and w.flight is not null then v_event := w.event; end if;

  if u.mins is not null and v_eta is not null and v_event is null then
    v_late := ((((extract(hour from v_eta at time zone 'Asia/Tokyo') * 60 + extract(minute from v_eta at time zone 'Asia/Tokyo'))::int
               - u.mins + 720) % 1440 + 1440) % 1440) - 720;
    v_kind := case when v_late >= 15 then 'late' when v_late <= -15 then 'early' else 'usual' end;
  end if;

  return jsonb_build_object(
    'flight', v_fl, 'reg', v_reg, 'callsign', v_cs, 'day', v_day, 'arr', v_arr, 'reason', null,
    'usual', case when u.mins is not null then jsonb_build_object(
        'time', lpad((u.mins / 60)::text, 2, '0') || ':' || lpad((u.mins % 60)::text, 2, '0'), 'mins', u.mins,
        'n', u.n, 'dow', case when u.dow >= 0 then u.dow end, 'spread', u.spread, 'weeks', 8) end,
    'eta', case when v_eta is not null then jsonb_build_object(
        'at', v_eta, 'time', to_char(v_eta at time zone 'Asia/Tokyo', hhmm), 'src', v_src, 'landed', v_src = 'track',
        'iata', case when v_src = 'track' then l.iata else v_arr end) end,
    'late_min', v_late, 'kind', v_kind,
    'event', v_event, 'divert_to', v_to,
    'curfew_near', case when w.flight is not null and jsonb_typeof(w.state->'curfew_near') = 'boolean' then (w.state->>'curfew_near')::boolean end,
    'seen_at', v_seen, 'ground', v_ground,
    'source', 'adsb.lol（ODbL）',
    'note', '推定です。定刻や航空会社の発表ではありません');
end $$;
revoke all on function public.usual_late(text, text, date, text, timestamptz) from public;
grant execute on function public.usual_late(text, text, date, text, timestamptz) to anon, authenticated, service_role;
