-- 遅れの通知を1つの便につき1件にまとめ、遅れが出たらすぐ知らせる（11/13 本人「遅れが二重にくる時があるので、きちんとまとめて、遅れが発生次第通知が来るようにして」）
-- ・flight_alerts に遅れの分（late）・航空会社の運航情報か（official）・書き直した時刻（updated_at）を足す
--   遅れのお知らせは15分から残す（「この便に乗る」の人へ15分から知らせるため）。画面のお知らせの一覧（public.flight_alerts()）は
--   今までどおり60分以上の遅れ（と遅れ以外）だけを返す（返す形も同じ）
-- ・flight_alerts_put：お知らせを入れる・書き直す（同じ便・同じ種類は1行。航空会社の運航情報は推定を上書きし、推定は運航情報を上書きしない）
-- ・alert_push_log：どの購読に・どの便の・どの中身を送ったか。同じ中身を二度送らない（読み書きは関数だけ）
-- ・alert_push_claim：送ってよいかを1件ずつ決めて記録する（同時に動く flight-watch と odpt-status が同じ便を二度送らない）
--   送るのは「はじめて」「門限・0時前後・欠航・ダイバート・引き返しになった」「航空会社の運航情報がはじめて届いた」「遅れが30分以上ふえた」ときだけ
--   （空港ごとの通知は主要空港の、門限に間に合わないおそれ・遅れで0時前後に着く便と、欠航・ダイバート・引き返しだけ。決めるのは alert_merge.ts）
-- ・odpt_status_runs に2行目（「この便に乗る」で選ばれた便だけを毎分見る回の、最後に動いた時刻）
-- ・急増の見張り（ops.alert_watchdog）は、今までどおり60分以上の遅れと遅れ以外だけを数える
-- 影響：チェックイン（通知の中身と回数。画面のお知らせの一覧は変わらない）。経営は関係なし
set lock_timeout = '10s';

alter table public.flight_alerts add column if not exists late int check (late is null or late between -1440 and 2880);
alter table public.flight_alerts add column if not exists official boolean not null default false;
alter table public.flight_alerts add column if not exists updated_at timestamptz;
-- 今までのお知らせ：文に「航空会社の運航情報」とあれば運航情報
update public.flight_alerts set official = true where not official and message like '%航空会社の運航情報%';

create or replace function public.flight_alerts(p_iata text default null) returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', a.id, 'kind', a.kind, 'flight', a.flight, 'dep', a.dep, 'arr', a.arr,
           'iata', a.iata, 'message', a.message, 'at', a.created_at) order by a.created_at desc), '[]'::jsonb)
  from (select * from public.flight_alerts
        where created_at > now() - interval '12 hours' and (p_iata is null or upper(p_iata) = any(iata))
          and (late is null or late >= 60)   -- 15〜59分の遅れは「この便に乗る」の通知だけに使い、一覧には出さない
        order by created_at desc limit 100) a
$$;
revoke all on function public.flight_alerts(text) from public;
grant execute on function public.flight_alerts(text) to anon, authenticated;

-- お知らせを入れる・書き直す。p は [{schedule_id, kind, flight, dep, arr, iata, message, late, official}]。
-- 入った行と書き直した行の (schedule_id, kind) を返す（変わらなかった行は返さない）
create or replace function public.flight_alerts_put(p jsonb) returns table (schedule_id bigint, kind text)
language sql security definer set search_path = public as $$
  insert into public.flight_alerts as t (schedule_id, kind, flight, dep, arr, iata, message, late, official)
  select (x->>'schedule_id')::bigint, x->>'kind', x->>'flight', x->>'dep', x->>'arr',
         array(select jsonb_array_elements_text(x->'iata')), left(x->>'message', 300),
         (x->>'late')::int, coalesce((x->>'official')::boolean, false)
    from jsonb_array_elements(coalesce(p, '[]'::jsonb)) x
   where x->>'schedule_id' is not null
  on conflict (schedule_id, kind) do update
     set message = excluded.message, late = excluded.late, official = excluded.official, iata = excluded.iata, updated_at = now()
   where (excluded.official or not t.official)                    -- 推定で運航情報を上書きしない
     and (t.message is distinct from excluded.message or t.late is distinct from excluded.late or excluded.official <> t.official)
  returning t.schedule_id, t.kind
$$;
revoke all on function public.flight_alerts_put(jsonb) from public, anon, authenticated;
grant execute on function public.flight_alerts_put(jsonb) to service_role;

create table if not exists public.alert_push_log (
  sub_id    bigint not null references public.push_subs(id) on delete cascade,
  gkey      text not null check (length(gkey) between 3 and 40),   -- 便名@運航日@出発空港（共同運航は運航する便にまとめた代表の便名）
  svc_date  date not null,
  rank      smallint not null check (rank between 1 and 5),       -- 1 遅れ・2 門限に間に合わないおそれ／0時前後に着く遅れ・3 引き返し・4 ダイバート・5 欠航
  late      int,
  official  boolean not null default false,
  body      text not null check (length(body) <= 400),
  n         int not null default 1,                                -- 送った回数
  sent_at   timestamptz not null default now(),
  primary key (sub_id, gkey)
);
create index if not exists alert_push_log_date on public.alert_push_log (svc_date);
alter table public.alert_push_log enable row level security;
revoke all on public.alert_push_log from public, anon, authenticated;

-- 送ってよいものを決めて記録する。p は [{sub_id, gkey, svc_date, rank, late, official, body}]。送ってよいものだけを返す（更新なら again = true）
create or replace function public.alert_push_claim(p jsonb) returns table (sub_id bigint, gkey text, again boolean)
language sql security definer set search_path = public as $$
  insert into public.alert_push_log as t (sub_id, gkey, svc_date, rank, late, official, body)
  select (x->>'sub_id')::bigint, x->>'gkey', (x->>'svc_date')::date, (x->>'rank')::smallint, (x->>'late')::int,
         coalesce((x->>'official')::boolean, false), left(x->>'body', 400)
    from jsonb_array_elements(coalesce(p, '[]'::jsonb)) x
   where exists (select 1 from public.push_subs s where s.id = (x->>'sub_id')::bigint)
  on conflict on constraint alert_push_log_pkey do update
     set rank = greatest(t.rank, excluded.rank), late = excluded.late, official = t.official or excluded.official,
         body = excluded.body, n = t.n + 1, sent_at = now()
   where excluded.rank > t.rank                                                       -- 欠航・ダイバート・引き返しになった
      or (excluded.official and not t.official and excluded.rank >= t.rank)            -- 航空会社の運航情報がはじめて届いた
      or (excluded.rank <= 2 and excluded.rank = t.rank and coalesce(excluded.late, 0) >= coalesce(t.late, 0) + 30)   -- 遅れが30分以上ふえた
  returning t.sub_id, t.gkey, (t.n > 1) as again
$$;
revoke all on function public.alert_push_claim(jsonb) from public, anon, authenticated;
grant execute on function public.alert_push_claim(jsonb) to service_role;

-- 「この便に乗る」で選ばれた便だけを毎分見る回の、最後に動いた時刻（id = 2）
alter table public.odpt_status_runs drop constraint if exists odpt_status_runs_id_check;
alter table public.odpt_status_runs add constraint odpt_status_runs_id_check check (id in (1, 2));
insert into public.odpt_status_runs (id) values (2) on conflict do nothing;

create or replace function ops.alert_watchdog() returns int
language plpgsql security definer set search_path = public, ops as $$
declare n int; by_kind text;
begin
  select coalesce(sum(c), 0)::int, string_agg(kind || ' ' || c, '、' order by c desc) into n, by_kind
    from (select kind, count(*) c from public.flight_alerts
           where created_at > now() - interval '1 hour' and (late is null or late >= 60) group by kind) k;
  if n >= 20
     and not exists (select 1 from ops.client_errors where kind = 'alert_surge' and created_at > now() - interval '3 hours') then
    insert into ops.client_errors (session, platform, version, kind, message, detail)
    values ('server', 'server', 'alert_watchdog', 'alert_surge',
            left('遅れ・ダイバートのお知らせが直近1時間に急に増えています（誤報の可能性。種類ごと：' || coalesce(by_kind, '') || '）', 300),
            jsonb_build_object('since', now() - interval '1 hour'));
    return 1;
  end if;
  return 0;
end $$;
revoke all on function ops.alert_watchdog() from public, anon, authenticated;

do $outer$
begin
  if not exists (select 1 from pg_available_extensions where name = 'pg_cron')
     or not exists (select 1 from pg_available_extensions where name = 'pg_net') then
    raise notice 'pg_cron / pg_net がないため、乗る便の毎分の確認と送った記録の掃除は設定しない';
    return;
  end if;
  execute 'create extension if not exists pg_net with schema extensions';
  execute 'create extension if not exists pg_cron';
  -- 「この便に乗る」で選ばれた便だけ、航空会社の運航情報を毎分見る（ODPT への問い合わせは1回に6件まで。選ばれた便がなければ問い合わせない）
  execute $q$
    select cron.schedule('odpt-status-fast', '* * * * *', $job$
      select net.http_get(
        url := 'https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/odpt-status?fast=1',
        headers := '{"User-Agent": "soramemo (odpt-status fast)"}'::jsonb,
        timeout_milliseconds := 50000)
    $job$)
  $q$;
  -- 送った記録は3日で消す（お知らせ（flight_alerts）は2日で消している。記録は便の照合に使わない）
  execute $q$
    select cron.schedule('alert-push-log-cleanup', '25 19 * * *', $job$
      set statement_timeout = '30s'; set lock_timeout = '5s';
      delete from public.alert_push_log where svc_date < (now() at time zone 'Asia/Tokyo')::date - 3;
    $job$)
  $q$;
end
$outer$;
