-- 運営コンソール：毎日の新規登録の数（読むだけ。広告の担当からの依頼）
--   admin_signups_daily(日数) … 日本時間の日ごとに、その日に登録した人の数と、そのうち規約に同意した人・使い方の答え（撮る・修行・気軽・未回答）の内訳
--   ・運営者（is_admin：登録と2段階認証）だけが呼べる。数だけを返し、メールや名前は返さない
--   ・登録日は auth.users の作成日（日本時間）。退会した人はもう数えられない（その日の数が後から減ることがある）
--   ・日数は 1〜365（既定 30）。登録が 0 の日も 0 で返す
--   ・表は変えない（関数だけ）。RLS はいまのまま
--   影響：チェックイン・経営のどちらの表・関数も変えない
create or replace function public.admin_signups_daily(p_days integer default 30) returns jsonb
language plpgsql stable security definer set search_path = public, auth as $$
declare
  n int := least(greatest(coalesce(p_days, 30), 1), 365);
  today date := (now() at time zone 'Asia/Tokyo')::date;
begin
  if not is_admin() then raise exception 'admin only'; end if;
  return (
    with d as (select (today - g)::date as day from generate_series(0, n - 1) g),
    u as (
      select (au.created_at at time zone 'Asia/Tokyo')::date as day, p.agreed_at, coalesce(p.persona, 'unanswered') as persona
        from auth.users au left join public.user_profiles p on p.user_id = au.id
       where au.created_at >= ((today - (n - 1))::timestamp at time zone 'Asia/Tokyo')
    )
    select jsonb_build_object(
      'days', n,
      'total', (select count(*) from u),
      'all_users', (select count(*) from auth.users),
      'rows', coalesce(jsonb_agg(jsonb_build_object(
        'day', d.day,
        'signups', (select count(*) from u where u.day = d.day),
        'agreed', (select count(*) from u where u.day = d.day and u.agreed_at is not null),
        'spot', (select count(*) from u where u.day = d.day and u.persona = 'spot'),
        'shugyo', (select count(*) from u where u.day = d.day and u.persona = 'shugyo'),
        'casual', (select count(*) from u where u.day = d.day and u.persona = 'casual'),
        'unanswered', (select count(*) from u where u.day = d.day and u.persona = 'unanswered')
      ) order by d.day desc), '[]'::jsonb))
    from d);
end;
$$;
revoke all on function public.admin_signups_daily(integer) from public, anon;
grant execute on function public.admin_signups_daily(integer) to authenticated;
