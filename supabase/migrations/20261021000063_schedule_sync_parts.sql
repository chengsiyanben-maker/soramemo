-- ダイヤの取り込み（schedule-sync）を、1回に1空港ずつに分ける。
-- 14空港をまとめて取り込むと、関数の計算の上限（WORKER_RESOURCE_LIMIT）を超えて止まり、10月19日の夕方から新しい便が入っていなかった。
-- ・schedule_sync_runs を空港ごとの行（id 1〜14）にする。呼ばれるたびに、いちばん前に取り込んだ空港を1つ取り込む（同じ空港は1時間に1回まで）
-- ・定期実行は、日本時間4:40〜4:53・16:40〜16:53の1分ごと（14回で14空港）
alter table public.schedule_sync_runs drop constraint if exists schedule_sync_runs_id_check;
alter table public.schedule_sync_runs add constraint schedule_sync_runs_id_check check (id between 1 and 14);
insert into public.schedule_sync_runs (id) select g from generate_series(2, 14) g on conflict do nothing;
update public.schedule_sync_runs set ran_at = 'epoch' where id = 1;   -- 止まっていた取り込みを、すぐやり直せるように

do $outer$
begin
  if not exists (select 1 from pg_extension where extname = 'pg_cron') or not exists (select 1 from pg_extension where extname = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、ダイヤの取り込みの定期実行は変えない';
    return;
  end if;
  execute $q$
    select cron.schedule('schedule-sync', '40-53 7,19 * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/schedule-sync',
        headers := '{"User-Agent": "soramemo (schedule-sync)"}'::jsonb,
        timeout_milliseconds := 60000)
    $job$)
  $q$;
end
$outer$;
