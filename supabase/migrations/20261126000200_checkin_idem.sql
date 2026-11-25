-- 印と便の「送り直しても二重にならない」仕組み（PM の指示 11/26 0時10分・data/idem。元は本人が貼った Gemini のデータの作りの案）
--   電波が詰まって「サーバーでは記録できたのに、返事だけ端末に届かなかった」とき、端末が同じ印・同じ便をもう一度送っても
--   印・便が2つにならないようにする。端末が作る ID（client_id。UUID）を一緒に送ってもらい、同じ ID の2回目は「もう記録済み」として成功で返す
--   1. checkins.client_id：関数 checkin が端末から受け取った ID。(user_id, client_id) で一意（null は何件でもよい＝今までの印と、ID を送らない古い画面）
--   2. flights：1つの到着の印から便は1つだけ（索引 flights_arr_checkin を一意に置き換える。null は何件でもよい）。今の本番に同じ arr_checkin が2行あれば、置き換えずに知らせる（行は消さない）
--   3. manual_flights.client_id：記録帳（画面から直接足す便）の ID。(user_id, client_id) で一意。画面は upsert（on_conflict=user_id,client_id・ignore-duplicates）で送る
--   RLS と権限は前と同じ（checkins・flights は利用者から書けない。manual_flights は本人が足せる・直せるのは fare・seat・airline・price だけで client_id は直せない）
--   判定（範囲・30分・20秒）は変えない。印は現地で押したものだけ・最後の判定はサーバー、のまま
--   影響：チェックイン（関数 checkin が client_id を受け付ける。画面が ID を送るのはチェックイン担当への依頼）。経営は関係しない
--   航路と機体の記録は消さない（列と索引を足すだけ）
set lock_timeout = '5s';

-- 1. 印
alter table public.checkins add column if not exists client_id uuid;
comment on column public.checkins.client_id is '端末が作った ID（送り直しで二重にしないため）。null は ID を送らなかった印';
create unique index if not exists checkins_user_client on public.checkins (user_id, client_id);

-- 2. 便（チェックインから作る便）：1つの到着の印から便は1つだけ
--   前からある同じ形の索引 flights_arr_checkin（移行188・一意でない）を一意のものに置き換え、名前は同じ flights_arr_checkin のままにする
do $$
begin
  if exists (select 1 from pg_index i where i.indexrelid = to_regclass('public.flights_arr_checkin') and i.indisunique) then
    return;  -- もう置き換えてある
  end if;
  if exists (select arr_checkin from public.flights where arr_checkin is not null group by arr_checkin having count(*) > 1) then
    raise notice 'flights に同じ arr_checkin の行があるので、索引 flights_arr_checkin は一意にしませんでした（idem-b-check.sql の 1 で見られます）';
    return;
  end if;
  create unique index flights_arr_checkin_uq on public.flights (arr_checkin) where arr_checkin is not null;
  drop index if exists public.flights_arr_checkin;
  alter index public.flights_arr_checkin_uq rename to flights_arr_checkin;
end $$;

-- 3. 記録帳
alter table public.manual_flights add column if not exists client_id uuid;
comment on column public.manual_flights.client_id is '端末が作った ID（送り直しで二重にしないため）。null は ID を送らなかった便';
create unique index if not exists manual_user_client on public.manual_flights (user_id, client_id);

-- RLS と権限（前と同じ形をもう一度はっきり書く）
alter table public.checkins enable row level security;
alter table public.flights enable row level security;
alter table public.manual_flights enable row level security;
revoke insert, update, delete on public.checkins from anon, authenticated;
revoke insert, update, delete on public.flights from anon, authenticated;
-- manual_flights の列ごとの直す権限（fare・seat・airline・price）は触らない。client_id は列ごとの権限に入らないので直せない
reset lock_timeout;
