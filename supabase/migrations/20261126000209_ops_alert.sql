-- 夜の処理・取り込みが止まったら、運営へ1日1回知らせる（11/26 本人の OK ⑤）
--   元：11/26 の死活の記録 ops.data_health()（取り込みごとの最後の時刻・上限・失敗）
--   流れ：pg_cron（毎時41分）→ Edge Function ops-alert → public.ops_alert_claim()（ng があり、今日まだ届けていなければ送る）
--         → 送り先（Edge Function の秘密の設定 OPS_ALERT_TO。コードにも表にも書かない）へメールか Webhook → public.ops_alert_done()
--   1日1回：日本時間の1日に、届けられたのは1回まで。送れなかったときは1時間ごとに試し直す（1日6回まで）
--   表 ops.ops_alert_log：日・回数・届いたか・ng だった項目（項目の名前と最後の時刻だけ。宛先は書かない）
--   RLS：ops_alert_log は RLS を有効にし、anon / authenticated には何も許さない。2つの関数は service_role だけ呼べる
--   影響：チェックイン・経営とも画面は変わらない（運営だけ）

create table if not exists ops.ops_alert_log (
  day      date primary key,                       -- 日本時間の日
  made_at  timestamptz not null default now(),     -- 最後に試した時刻
  attempts integer not null default 1,
  ok       boolean not null default false,         -- 1つ以上の送り先に届いた
  items    jsonb not null default '[]'::jsonb,     -- ng だった項目（key・label・last・limit_min）
  result   text                                    -- 送った結果の短い文（宛先は書かない）
);
alter table ops.ops_alert_log enable row level security;
revoke all on ops.ops_alert_log from public, anon, authenticated;

-- 送ってよいかを決めて記録する。ng がなければ送らない。今日もう届いていれば送らない。届いていなければ6回まで
create or replace function public.ops_alert_claim() returns jsonb
language plpgsql security definer set search_path = ops, public set statement_timeout = '30s' as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  bad jsonb;
  claimed date;
begin
  select coalesce(jsonb_agg(jsonb_build_object('key', x->>'key', 'label', x->>'label', 'last', x->'last', 'limit_min', x->'limit_min') order by x->>'key'), '[]'::jsonb)
    into bad from jsonb_array_elements(ops.data_health()) x where not coalesce((x->>'ok')::boolean, true);
  if jsonb_array_length(bad) = 0 then return jsonb_build_object('send', false, 'reason', 'ok'); end if;
  insert into ops.ops_alert_log as l (day, items) values (today, bad)
  on conflict (day) do update set attempts = l.attempts + 1, made_at = now(), items = excluded.items
   where not l.ok and l.attempts < 6
  returning day into claimed;
  if claimed is null then return jsonb_build_object('send', false, 'reason', 'already'); end if;
  return jsonb_build_object('send', true, 'day', today, 'items', bad);
end $$;
revoke all on function public.ops_alert_claim() from public, anon, authenticated;
grant execute on function public.ops_alert_claim() to service_role;

-- 送った結果を書く（届いたか・短い文。宛先は書かない）
create or replace function public.ops_alert_done(p_day date, p_ok boolean, p_result text) returns void
language sql security definer set search_path = ops, public set statement_timeout = '10s' as $$
  update ops.ops_alert_log set ok = ok or coalesce(p_ok, false), result = left(p_result, 300) where day = p_day
$$;
revoke all on function public.ops_alert_done(date, boolean, text) from public, anon, authenticated;
grant execute on function public.ops_alert_done(date, boolean, text) to service_role;

-- 毎時41分に Edge Function を呼ぶ（呼ばれても、送るかどうかは ops_alert_claim が決めるので、何度呼ばれても1日1回まで）
do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') or not exists (select 1 from pg_extension where extname = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、運営への知らせの定期実行は設定しない';
    return;
  end if;
  if exists (select 1 from cron.job where jobname = 'ops-alert') then perform cron.unschedule('ops-alert'); end if;
  execute $q$ select cron.schedule('ops-alert', '41 * * * *', $job$ set statement_timeout = '10s'; set lock_timeout = '5s';
    select net.http_get(
      url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/ops-alert',
      headers := '{"User-Agent": "soramemo (ops-alert)"}'::jsonb,
      timeout_milliseconds := 30000) $job$) $q$;
end
$outer$;
