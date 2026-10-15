-- 特別塗装機の種類：special（キャラクター・記念塗装など）と alliance（スターアライアンス・ワンワールド塗装）。
-- アライアンス塗装は毎日飛んでいるので通知せず、画面ではたたんだ欄に分けて出す
alter table public.livery_sightings add column if not exists kind text not null default 'special' check (kind in ('special', 'alliance'));

create or replace function public.special_now() returns jsonb
language sql stable security definer set search_path = public as $$
  select coalesce(jsonb_agg(jsonb_build_object('reg', reg, 'name', name, 'airline', airline, 'callsign', callsign, 'kind', kind,
           'lat', round(lat::numeric, 3), 'lon', round(lon::numeric, 3), 'alt_ft', alt_ft, 'iata', iata, 'phase', phase, 'src', src, 'at', seen_at)
           order by (kind = 'alliance'), (iata is null), seen_at desc), '[]'::jsonb)
  from public.livery_sightings where seen_at > now() - interval '15 minutes'
$$;
revoke all on function public.special_now() from public;
grant execute on function public.special_now() to anon, authenticated;
