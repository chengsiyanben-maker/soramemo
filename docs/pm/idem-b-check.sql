-- 印と便の送り直し対策（data/idem・移行200）の確かめ。本人が SQL Editor で流す読むだけの SQL（どれも軽い。一時ファイルを使わない）

-- 1. 反映の前に：同じ到着の印から便が2つできている行があるか（0 なら索引 flights_arr_checkin が一意に置き換わる。1以上なら移行は止まらずに置き換えだけしない）
select count(*) as dup_arr_checkin
from (select arr_checkin from public.flights where arr_checkin is not null group by arr_checkin having count(*) > 1) x;

-- 2. 反映のあとに：3つの索引が一意か（3行とも is_unique が true なら OK。flights_arr_checkin が false なら 1 の行が残っている）
select c.relname as index_name, i.indisunique as is_unique
from pg_index i join pg_class c on c.oid = i.indexrelid join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relname in ('checkins_user_client', 'flights_arr_checkin', 'manual_user_client')
order by 1;

-- 3. 画面が ID を送り始めたあとに（チェックイン担当の直しのあと）：前の7日の印のうち、ID の付いた割合
select (created_at at time zone 'Asia/Tokyo')::date as day, count(*) as stamps, count(client_id) as with_id
from public.checkins
where created_at > now() - interval '7 days'
group by 1 order by 1;

-- 送り直しで助かった回数は SQL ではなく、Edge Functions の checkin のログで「checkin_dup」を探すと見られる（where は last・decide・insert）
