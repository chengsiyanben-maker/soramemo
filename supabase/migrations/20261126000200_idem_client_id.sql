-- 印と便の「送り直しても二重にならない」仕組み（PM の指示 11/26 0時10分・data/idem）
--   電波が詰まって「サーバーでは記録できたのに返事だけ届かなかった」とき、端末が同じ印をもう一度送っても
--   印・便が2つにならないように、端末が作る ID（client_id。UUIDv7 か v4）を一緒に覚えておく
--   1. checkins.client_id：関数 checkin が受け取った ID。同じ人・同じ ID は1行だけ（一意の索引）
--      2回目が来たら、関数 checkin は判定をやり直さず、1回目の印を「もう記録済み」（ok: true, again: true）で返す
--   2. flights.client_id：その印でできた便に、着いた印と同じ ID を書く。同じ人・同じ ID の便は1つだけ
--   3. manual_flights・intl_flights の client_id：記録帳・国際線の記録を画面から足すとき、端末が ID を付けて
--      upsert（on conflict (user_id, client_id) do nothing）で送れば、送り直しても1行のまま
--   ・列は空（null）でもよい。今までの行・ID を付けない送り方は前のまま（null どうしはぶつからない）
--   ・一意の索引は条件なし（null は重ならない扱い）。条件付きにすると画面の upsert（on conflict の列の指定）で使えないため
--   ・RLS と権限は前のまま：checkins・flights は利用者から書けない（書くのは関数 checkin の service_role だけ）。
--     manual_flights・intl_flights は本人が足せる（insert のときに client_id も入れられる。update では変えられない）
--   影響：チェックイン（画面の送る所で ID を作って送る・送り直しで同じ ID を使う依頼を出す）。経営は関係しない
--   航路と機体の記録は消さない（列と索引を足すだけ）
set lock_timeout = '5s';

alter table public.checkins       add column if not exists client_id uuid;
alter table public.flights        add column if not exists client_id uuid;
alter table public.manual_flights add column if not exists client_id uuid;
alter table public.intl_flights   add column if not exists client_id uuid;

comment on column public.checkins.client_id       is '端末が作った印の ID（送り直しで二重にしない）。同じ人で一意。null は ID なしで送った印';
comment on column public.flights.client_id        is 'この便ができた着いた印の client_id（送り直しで便を二重にしない）。同じ人で一意';
comment on column public.manual_flights.client_id is '端末が作った記録の ID（送り直しで二重にしない）。同じ人で一意';
comment on column public.intl_flights.client_id   is '端末が作った記録の ID（送り直しで二重にしない）。同じ人で一意';

create unique index if not exists checkins_user_cid       on public.checkins       (user_id, client_id);
create unique index if not exists flights_user_cid        on public.flights        (user_id, client_id);
create unique index if not exists manual_flights_user_cid on public.manual_flights (user_id, client_id);
create unique index if not exists intl_flights_user_cid   on public.intl_flights   (user_id, client_id);

-- RLS と権限（前と同じ形をもう一度はっきり書く）
alter table public.checkins       enable row level security;
alter table public.flights        enable row level security;
alter table public.manual_flights enable row level security;
alter table public.intl_flights   enable row level security;
revoke insert, update, delete on public.checkins from anon, authenticated;
revoke insert, update, delete on public.flights  from anon, authenticated;
reset lock_timeout;
