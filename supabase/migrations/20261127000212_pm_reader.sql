-- PM が本番のデータを読むだけで見るための役割 pm_reader（11/27 本人の指示・data/pm-reader）
--   ・ログインできない形で作る。パスワードとログインは本人が SQL Editor で付ける（docs/pm/report-pm-reader.md の手順）。
--     パスワードはこのファイル・チャット・プルリクエストに書かない。
--   ・読めるのは、便・航跡・機体・空港・運用・天気・特別塗装機・運用予想の「公開に近い表」だけ（下の一覧）。
--     利用者のデータ（印・乗った便・プロフィール・ピン・報告・使われ方・auth・経営の会社 など）は一覧に入れないので読めない。
--   ・書く権限は一切付けない。加えて、つないだ時の既定を読むだけの取引にし、1文60秒・取引の途中で止まったら2分で切る。
--     （既定は本人の側で変えられるので、GitHub の流す仕組み tools/pm_query.mjs でも毎回 read only の取引の中で流す）
--   ・RLS が有効な表には pm_reader 用の「読むだけ」のポリシーを、一覧の表にだけ足す。
--   影響：チェックイン・経営とも画面とロジックは変わらない（新しい役割に読む権限を足すだけ。今の役割の権限・ポリシーはそのまま）。

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'pm_reader') then
    create role pm_reader nologin noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
  end if;
end $$;

-- 既に誰かが作っていても、強い力は付けない形にそろえる（ログインの有無は本人が決めるので触らない）
alter role pm_reader noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
alter role pm_reader set default_transaction_read_only = on;
alter role pm_reader set statement_timeout = '60s';
alter role pm_reader set idle_in_transaction_session_timeout = '120s';
alter role pm_reader set idle_session_timeout = '600s';
alter role pm_reader set search_path = public;

grant usage on schema public to pm_reader;

-- 読める表の一覧（名前は今の表に合わせた。足すときはこの一覧と t151 の一覧を一緒に直す）
do $$
declare
  t text;
  allow text[] := array[
    -- 便と航跡と機体（全機の記録）
    'flight_history', 'flight_tracks', 'track_points', 'reg_legs', 'flight_schedule', 'flight_changes', 'timetable',
    'foreign_legs', 'foreign_usual', 'airport_daily',
    -- 空港・航空会社
    'airports', 'terminals', 'airline_codes', 'airport_facts', 'airport_yomi', 'world_airport_status',
    -- 運用（滑走路・地上の動き・着陸の向き）と天気（METAR・TAF）
    'ops_log', 'rwy_samples', 'rwy_learned_days', 'ground_moves', 'arr_watch', 'wx_obs', 'wx_taf', 'wx_taf_hours',
    -- 特別塗装機
    'livery_extra', 'livery_sightings', 'livery_plans',
    -- 運用予想
    'rot_pairs', 'rot_eval', 'rotation_obs'
  ];
begin
  foreach t in array allow loop
    if to_regclass('public.' || t) is null then
      raise notice 'pm_reader: 表 public.% がないので飛ばす', t;
      continue;
    end if;
    execute format('grant select on public.%I to pm_reader', t);
    if (select relrowsecurity from pg_class where oid = ('public.' || t)::regclass) then
      execute format('drop policy if exists pm_reader_read on public.%I', t);
      execute format('create policy pm_reader_read on public.%I for select to pm_reader using (true)', t);
    end if;
  end loop;
end $$;
