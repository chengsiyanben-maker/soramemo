-- 海外の会社の特別塗装機が来るのも知らせる（データ担当・11/16 14時 PM の指示の 2。本人「おすすめ」＝案1-A・案2-A・案3-A）
--   1. livery_extra：特別塗装機の一覧の「足し分」。本人（運営）が Supabase の Table Editor で1行足せば、次の機体の記録（30秒ごと）から
--      運用タブ・「空港のいま」・特別塗装機の知らせに出る（コードの変更と反映が要らない）。関数は _shared/liveries.ts の一覧と合わせて読み、
--      同じ登録記号は表のほうを使う（塗装の名前の直し・終わる日の書き足しにも使える）
--      出典（src）は必ず入れる。https で始まり、Flightradar24 は入れられない（データ・画面・ブログとも使わない決まり）
--      終わった塗装は消さずに until_day を入れる（一覧から外れるだけ）
--   2. livery_inbound_usual(p_callsigns)：日本のまわりで見えた海外の塗装機の便が、ふだん日本のどの空港に何時ごろ着くか
--      （foreign_usual、前の8週の実績の中央値）。行き先の推定に使う。外への問い合わせは増えない
-- RLS：livery_extra は誰でも読める（塗装の名前・会社・出典の事実だけ。本人の記録は入らない）。書くのは service_role（関数）と
--      Table Editor（運営）だけ。2 は service_role だけが呼べる
-- 影響：チェックイン（運用タブ・空港のいま・特別塗装機の欄に表の機体も出る。返す形は同じ）・撮る人用（注目の機体に表の機体も入る）。経営は使わない
set lock_timeout = '5s';

-- 1
create table if not exists public.livery_extra (
  reg        text primary key check (reg ~ '^[A-Z0-9]{1,3}-?[A-Z0-9]{2,6}$' and length(reg) <= 10),   -- livery_sightings と同じ形（adsb.lol の r の書き方：9V-OJJ・B-18101・N24988）
  name       text not null check (length(btrim(name)) between 1 and 60),
  airline    text not null check (length(btrim(airline)) between 1 and 40),
  kind       text not null default 'special' check (kind in ('special', 'alliance')),
  src        text not null check (src ~ '^https://[^ ]+$' and length(src) <= 300 and src !~* '(flightradar24|fr24)\.'),
  from_day   date,                                              -- 塗装が始まる日（前の日までは名前で出さない）
  until_day  date,                                              -- 終わる日（この日まで出す）
  note       text check (length(note) <= 200),
  added_at   timestamptz not null default now(),
  check (until_day is null or from_day is null or until_day >= from_day)
);
comment on table public.livery_extra is '特別塗装機の一覧の足し分（運営が Table Editor で足す）。_shared/liveries.ts と合わせて読み、同じ登録記号は表を使う。出典は必須・Flightradar24 は不可。終わった塗装は消さず until_day を入れる';

alter table public.livery_extra enable row level security;
revoke all on public.livery_extra from public, anon, authenticated;
grant select on public.livery_extra to anon, authenticated;
grant all on public.livery_extra to service_role;
drop policy if exists livery_extra_read on public.livery_extra;
create policy livery_extra_read on public.livery_extra for select to anon, authenticated using (true);

-- 2
create or replace function public.livery_inbound_usual(p_callsigns text[])
returns table (callsign text, iata text, mins smallint, n smallint)
language sql stable security definer set search_path = public as $$
  select distinct on (u.callsign, u.iata) u.callsign, u.iata, u.mins, u.n
    from public.foreign_usual u
   where u.callsign = any (p_callsigns[1:50])
     and u.dep_here = 0
     and u.dow in (extract(dow from (now() at time zone 'Asia/Tokyo'))::smallint, -1)
   order by u.callsign, u.iata, u.dow desc
$$;
revoke all on function public.livery_inbound_usual(text[]) from public, anon, authenticated;
grant execute on function public.livery_inbound_usual(text[]) to service_role;

reset lock_timeout;
