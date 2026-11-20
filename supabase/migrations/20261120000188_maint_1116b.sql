-- 定期の手入れ 11/16（月）の2回目（データ担当）：引く索引のない「つながり」と「よく引く列」に索引を足す
--   （11/20 data/redo-1120：main が 182→184… と進み 183 が入らなかったので、番号を 188 に付け直した。中身は同じ）
--   本番の数字（点検の結果）はまだ来ていないので、main の移行を全部流した模擬のデータベースで、
--   (1) 外部キーなのに先頭がその列の索引がないもの (2) 同じ表で列が前に重なる索引 を洗い出した（docs/pm/maint/2026-11-16-2-report.md）
--
-- 1. aircraft (user_id)：経営の関数・RLS（user_id = auth.uid()）が「自分の機体」を引く所が約50か所あるが、
--    user_id で始まる索引は「route_key がある機体だけ」「ride がある機体だけ」の部分索引しかなく、ほかは全部の機体を読んでいた
-- 2. flights (dep_checkin)・(arr_checkin)：チェックインを1件消すたびに（退会・admin_void_checkin）、
--    on delete set null の確かめで flights を全部読んでいた（チェックイン500件の退会なら全部読みが1000回）。null の行は入れない部分索引
-- 3. aircraft を指す経営の5つの表（co3_extra・co3_market・co3_orders・co3_breakdowns・co3_heavy の aircraft_id・spare_id）：
--    機体を売る（co_sell）・退会で機体を1機消すたびに、5つの表を全部読んでいた。unique (aircraft_id, start_day) がある2つの aircraft_id は足さない
--
-- 表・列・行・RLS・権限・関数は変えない。足すのは索引だけ（記録は消さない）。どれも小さい表なので作るのは一瞬
-- 影響：エアライン経営（自分の機体の読み出し・機体を売る・毎晩の処理が速くなるだけ。値は変わらない）、
--       チェックイン（退会・管理の取り消しが速くなるだけ。画面と値は変わらない）
set lock_timeout = '5s';

-- 1
create index if not exists aircraft_user on public.aircraft (user_id);

-- 2
create index if not exists flights_dep_checkin on public.flights (dep_checkin) where dep_checkin is not null;
create index if not exists flights_arr_checkin on public.flights (arr_checkin) where arr_checkin is not null;

-- 3
create index if not exists co3_market_aircraft on public.co3_market (aircraft_id) where aircraft_id is not null;
create index if not exists co3_orders_aircraft on public.co3_orders (aircraft_id) where aircraft_id is not null;
create index if not exists co3_breakdowns_spare on public.co3_breakdowns (spare_id) where spare_id is not null;
create index if not exists co3_heavy_spare on public.co3_heavy (spare_id) where spare_id is not null;
create index if not exists co3_extra_aircraft on public.co3_extra (aircraft_id);

reset lock_timeout;
