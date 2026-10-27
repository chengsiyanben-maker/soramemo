-- 米軍が管理する飛行場（横田基地・嘉手納基地・普天間飛行場）を、番外編の「基地」から「一般の人が行けない飛行場」（secret）へ移す。
--   基地の枠（mil）は自衛隊の飛行場だけになる。厚木基地は海上自衛隊が管理しているので基地のまま。
--   押した記録（checkins）はそのまま残り、枠の数え方だけが変わる。表の作りは変えないので RLS は今のまま。
--   category も secret にして、前の移行（category = 'military' を mil にする）を流し直しても戻らないようにする。何度流しても同じ。
update public.airports set extra_kind = 'secret', category = 'secret' where id in (1015, 1029, 1030);
