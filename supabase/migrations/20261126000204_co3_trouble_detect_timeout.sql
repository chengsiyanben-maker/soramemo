-- 経営の毎日の仕事 co3-trouble-detect に時間の上限（statement_timeout 3分・lock_timeout 5秒）を付ける
--   データ担当からの依頼（11/16 の見回りの 5、11/26 の見回りでも残ったまま）
--   この仕事は 20261028000119 で止めた（便ごとのトラブル co3-legs-check に置きかえ）ので、リポジトリの移行どおりなら本番にはもうない
--   それでも本番に残っている（119 の取り消しが効かなかった）場合に備え、残っているときだけ同じ時刻・同じ中身のまま上限を付けて付け直す
--   ないときは何もしない（新しく作らない。止めた決定は変えない。消す作業もしない）
--   pg_cron の有無は cron.job の表があるかで見る（ない環境では何もしない）
--   表・関数・RLS・権限は変えない。画面は変わらない

do $outer$
declare
  j record;
  body text;
begin
  if to_regclass('cron.job') is null then return; end if;
  for j in execute $q$ select jobname, schedule, command from cron.job where jobname = 'co3-trouble-detect' $q$ loop
    body := regexp_replace(j.command, '^\s*(set\s+statement_timeout\s*=\s*''[^'']*''\s*;\s*)?(set\s+lock_timeout\s*=\s*''[^'']*''\s*;\s*)?', '', 'i');
    execute format('select cron.schedule(%L, %L, %L)', j.jobname, j.schedule,
      'set statement_timeout = ''3min''; set lock_timeout = ''5s''; ' || body);
  end loop;
end
$outer$;
