-- 毎日の新規登録の数（読むだけ。SQL Editor に貼って Run。何も書きかえない）
--   移行 admin_signups_daily を流す前でも使える。日本時間の日ごと、直近30日。退会した人は数えられない
select d.day,
       count(u.id)                                              as 登録,
       count(p.agreed_at)                                       as 同意,
       count(*) filter (where p.persona = 'spot')               as 撮る,
       count(*) filter (where p.persona = 'shugyo')             as 修行,
       count(*) filter (where p.persona = 'casual')             as 気軽,
       count(u.id) - count(*) filter (where p.persona in ('spot', 'shugyo', 'casual')) as 未回答
  from generate_series((now() at time zone 'Asia/Tokyo')::date - 29, (now() at time zone 'Asia/Tokyo')::date, interval '1 day') g(day)
  cross join lateral (select g.day::date as day) d
  left join auth.users u on (u.created_at at time zone 'Asia/Tokyo')::date = d.day
  left join public.user_profiles p on p.user_id = u.id
 group by d.day
 order by d.day desc;
