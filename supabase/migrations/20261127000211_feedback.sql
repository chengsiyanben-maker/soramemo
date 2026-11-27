-- 不具合・意見の報告を受ける仕組み（11/27 本人の指示「ユーザーがバグや不具合を報告できるツールを作っておいて」）
--   表 public.feedback：種類（不具合／ほしい機能／空港データの直し）・本文（2000字まで）・自動の付けたし（アプリの版・開いていた画面・端末の種類・直前のエラーの種類）
--                       ・任意で空港コード・利用者 ID（ログインしていれば）・起動ごとの使い捨ての値（session）・状態・運営のメモ
--   保存しないもの：位置・メールアドレス・IP（列がない。Edge Function feedback-submit も IP を読まない）
--   入れ方：ログインした人は表に直接入れる（RLS で自分の分だけ。運営の列・状態は入れられない）。
--           ログインしていない人（ログイン案B）は Edge Function feedback-submit（サービスの鍵）から入れる。user_id は必ず空になる
--   送りすぎの制限（入れる前の trigger）：同じ利用者か同じ起動の値で、10分に3件まで。ログインしていない人の全体で10分に30件まで
--   読む：ログインした人は自分の分だけ（運営のメモ・利用者 ID・起動の値は列の権限で見せない。my_feedback() でも読める）
--   運営：admin_feedback_list（一覧と状態ごとの数）・admin_feedback_set（状態の切り替えと運営のメモ。admin_actions に残す）。中で is_admin
--   夜の知らせ（ops-alert）：前に届けたあとに来た報告の数（種類ごと）を足す。止まった処理がない日も、新しい報告があれば20時以降に1日1回知らせる
--   退会：auth.users を on delete cascade で参照（本人の記録は消す決まり）
--   影響：チェックイン・経営とも、今の画面とロジックは変わらない（送る画面はチェックイン担当・デザイン担当が作る。F1・F2 が手本）

create table if not exists public.feedback (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  kind        text not null check (kind in ('bug', 'request', 'airport_data')),
  body        text not null check (char_length(body) between 1 and 2000),
  app_version text check (app_version ~ '^[0-9A-Za-z._+-]{1,24}$'),
  screen      text check (screen ~ '^[a-z0-9_:.-]{1,40}$'),
  device      text check (device ~ '^[a-z0-9_.-]{1,24}$'),
  last_error  text check (last_error ~ '^[a-z_]{1,20}$'),          -- client_errors の kind と同じ形（中身の文は入れない）
  airport     text check (airport ~ '^[A-Z0-9]{3,4}$'),
  user_id     uuid references auth.users (id) on delete cascade,
  session     text check (session ~ '^[a-z0-9]{8,32}$'),
  status      text not null default 'open' check (status in ('open', 'checking', 'fixed', 'wontfix')),
  admin_note  text check (char_length(admin_note) <= 2000),
  updated_at  timestamptz,
  constraint feedback_who check (user_id is not null or session is not null)
);
comment on table public.feedback is '不具合・意見の報告。位置・メール・IP は持たない。status：open 受付・checking 確認中・fixed 直した・wontfix 対応しない';

create index if not exists feedback_user    on public.feedback (user_id, created_at);
create index if not exists feedback_session on public.feedback (session, created_at) where session is not null;
create index if not exists feedback_time    on public.feedback (created_at);

-- 入れる前：誰の分かを決め、運営の列を空にし、送りすぎを止める（RLS の中から他の人の行も数えるので security definer）
create or replace function public.feedback_before_insert() returns trigger
language plpgsql security definer set search_path = public, ops set statement_timeout = '5s' as $$
declare
  uid uuid := auth.uid();
  n integer;
begin
  new.user_id    := uid;          -- 自分の分だけ。サービスの鍵（feedback-submit）からは空＝ログインしていない人
  new.created_at := now();
  new.status     := 'open';
  new.admin_note := null;
  new.updated_at := null;
  new.body       := btrim(new.body);
  -- 非常停止：ops.flags の feedback_enabled を false にすると受け付けない（行がなければ受け付ける）
  if not coalesce((ops.flag('feedback_enabled'))::boolean, true) then raise exception 'feedback_closed' using errcode = '55000'; end if;
  if new.body = '' then raise exception 'feedback_empty' using errcode = '22023'; end if;
  if uid is null and new.session is null then raise exception 'feedback_session_required' using errcode = '22023'; end if;
  if uid is not null then
    select count(*) into n from public.feedback where user_id = uid and created_at > now() - interval '10 minutes';
    if n >= 3 then raise exception 'feedback_too_many' using errcode = '54000'; end if;
  end if;
  if new.session is not null then
    select count(*) into n from public.feedback where session = new.session and created_at > now() - interval '10 minutes';
    if n >= 3 then raise exception 'feedback_too_many' using errcode = '54000'; end if;
  end if;
  if uid is null then
    select count(*) into n from public.feedback where created_at > now() - interval '10 minutes' and user_id is null;
    if n >= 30 then raise exception 'feedback_too_many' using errcode = '54000'; end if;
  end if;
  return new;
end $$;
revoke all on function public.feedback_before_insert() from public, anon, authenticated;
drop trigger if exists feedback_before_insert on public.feedback;
create trigger feedback_before_insert before insert on public.feedback for each row execute function public.feedback_before_insert();

-- 書き換え・消すのは運営の関数だけ（表への update / delete の権限はだれにも渡さない）
alter table public.feedback enable row level security;
revoke all on public.feedback from public, anon, authenticated;
grant insert (kind, body, app_version, screen, device, last_error, airport, session) on public.feedback to authenticated;
grant select (id, created_at, kind, body, app_version, screen, device, last_error, airport, status, updated_at) on public.feedback to authenticated;
grant select, insert on public.feedback to service_role;

drop policy if exists feedback_insert_own on public.feedback;
create policy feedback_insert_own on public.feedback for insert to authenticated with check (user_id = (select auth.uid()));
drop policy if exists feedback_select_own on public.feedback;
create policy feedback_select_own on public.feedback for select to authenticated using (user_id = (select auth.uid()));

-- 自分の報告（新しい順に50件。運営のメモは返さない）。user_id の列は本人にも読ませないので、絞り込みは関数の中で行う（security definer）
create or replace function public.my_feedback() returns table (id bigint, created_at timestamptz, kind text, body text, airport text, status text, updated_at timestamptz)
language sql stable security definer set search_path = public set statement_timeout = '5s' as $$
  select f.id, f.created_at, f.kind, f.body, f.airport, f.status, f.updated_at
    from public.feedback f where f.user_id = (select auth.uid()) order by f.id desc limit 50
$$;
revoke all on function public.my_feedback() from public, anon;
grant execute on function public.my_feedback() to authenticated;

-- 運営：一覧（状態・種類で絞る。p_before より古い id を p_limit 件）と状態ごとの数
create or replace function public.admin_feedback_list(p_status text default null, p_kind text default null, p_limit integer default 100, p_before bigint default null)
returns jsonb language plpgsql stable security definer set search_path = public, ops set statement_timeout = '10s' as $$
declare lim integer := least(greatest(coalesce(p_limit, 100), 1), 500);
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return jsonb_build_object(
    'counts', (select coalesce(jsonb_object_agg(status, n), '{}'::jsonb) from (select status, count(*)::int n from public.feedback group by status) c),
    'items', (select coalesce(jsonb_agg(to_jsonb(x) order by x.id desc), '[]'::jsonb) from (
      select f.id, f.created_at, f.kind, f.body, f.app_version, f.screen, f.device, f.last_error, f.airport,
             f.user_id, (f.user_id is not null) as logged_in, f.status, f.admin_note, f.updated_at
        from public.feedback f
       where (p_status is null or f.status = p_status) and (p_kind is null or f.kind = p_kind) and (p_before is null or f.id < p_before)
       order by f.id desc limit lim) x));
end $$;
revoke all on function public.admin_feedback_list(text, text, integer, bigint) from public, anon;
grant execute on function public.admin_feedback_list(text, text, integer, bigint) to authenticated;

-- 運営：状態を切り替える。p_note は null なら今のまま、'' なら空にする
create or replace function public.admin_feedback_set(p_id bigint, p_status text, p_note text default null) returns void
language plpgsql security definer set search_path = public, ops set statement_timeout = '10s' as $$
begin
  if not is_admin() then raise exception 'admin only'; end if;
  if p_status not in ('open', 'checking', 'fixed', 'wontfix') then raise exception 'bad status'; end if;
  if p_note is not null and char_length(p_note) > 2000 then raise exception 'bad note'; end if;
  update public.feedback
     set status = p_status, admin_note = case when p_note is null then admin_note else nullif(btrim(p_note), '') end, updated_at = now()
   where id = p_id;
  if not found then raise exception 'not found'; end if;
  insert into ops.admin_actions (admin_id, action, target, detail) values (auth.uid(), 'feedback_set', p_id::text, jsonb_build_object('status', p_status));
end $$;
revoke all on function public.admin_feedback_set(bigint, text, text) from public, anon;
grant execute on function public.admin_feedback_set(bigint, text, text) to authenticated;

-- ---------- 夜の知らせ（ops-alert）に「新しい報告 ○件」を足す ----------
--   数えるのは、前に届けた知らせ（ok）が数えた時刻 fb_until のあとに来た報告。届かなければ次の回にまた数える
--   止まった処理（ng）があれば今までどおりいつでも送り、報告の数も載せる。ng がなく報告だけなら、日本時間20時以降に送る（1日1回は今までどおり）
--   20時は ops.flags の feedback_alert_hour（行がなければ 20）で変えられる。報告だけの知らせが届いた日は、そのあとに止まった処理は次の日の0時41分の知らせになる
alter table ops.ops_alert_log add column if not exists fb_new   integer not null default 0;
alter table ops.ops_alert_log add column if not exists fb_kinds jsonb not null default '{}'::jsonb;
alter table ops.ops_alert_log add column if not exists fb_until timestamptz;

create or replace function public.ops_alert_claim() returns jsonb
language plpgsql security definer set search_path = ops, public set statement_timeout = '30s' as $$
declare
  today date := (now() at time zone 'Asia/Tokyo')::date;
  hour  integer := extract(hour from (now() at time zone 'Asia/Tokyo'))::int;
  upto  timestamptz := now();
  since timestamptz;
  bad jsonb;
  fb integer;
  fbk jsonb;
  claimed date;
begin
  select coalesce(jsonb_agg(jsonb_build_object('key', x->>'key', 'label', x->>'label', 'last', x->'last', 'limit_min', x->'limit_min') order by x->>'key'), '[]'::jsonb)
    into bad from jsonb_array_elements(ops.data_health()) x where not coalesce((x->>'ok')::boolean, true);
  since := coalesce((select max(fb_until) from ops.ops_alert_log where ok), '-infinity'::timestamptz);
  select coalesce(sum(n), 0)::int, coalesce(jsonb_object_agg(kind, n), '{}'::jsonb) into fb, fbk
    from (select kind, count(*)::int n from public.feedback where created_at > since and created_at <= upto group by kind) k;
  if jsonb_array_length(bad) = 0 and fb = 0 then return jsonb_build_object('send', false, 'reason', 'ok'); end if;
  if jsonb_array_length(bad) = 0 and hour < coalesce((ops.flag('feedback_alert_hour') #>> '{}')::int, 20) then return jsonb_build_object('send', false, 'reason', 'wait', 'feedback_new', fb); end if;
  insert into ops.ops_alert_log as l (day, items, fb_new, fb_kinds, fb_until) values (today, bad, fb, fbk, upto)
  on conflict (day) do update set attempts = l.attempts + 1, made_at = now(), items = excluded.items,
                                  fb_new = excluded.fb_new, fb_kinds = excluded.fb_kinds, fb_until = excluded.fb_until
   where not l.ok and l.attempts < 6
  returning day into claimed;
  if claimed is null then return jsonb_build_object('send', false, 'reason', 'already'); end if;
  return jsonb_build_object('send', true, 'day', today, 'items', bad, 'feedback_new', fb, 'feedback_kinds', fbk);
end $$;
revoke all on function public.ops_alert_claim() from public, anon, authenticated;
grant execute on function public.ops_alert_claim() to service_role;
