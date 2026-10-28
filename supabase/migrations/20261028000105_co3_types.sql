-- エアライン経営 co-v3：機種の表（仕様書「機体」の表。値段・維持費は 10/24 に 0.6倍にしたもの）
--   席は「全席普通にしたときの席」。貨物機は積める重さ（トン）、ビジネスジェットは VIP 席の数。
--   仕様書にない翼の幅の区分・最大の重さ（トン）・記号（ICAO の機種の記号と、時刻表の機種の記号）は、公表されている機体の数字の目安。
--   乗った機体の記号（ICAO か時刻表）から機種を引き、路線ごとの内わけの席・重さ・騒音に使う。引けない機体は大きさの区分の目安のまま。
--   貨物機と旅客機は ICAO の記号が同じ（B738・B763 など）なので、記号では貨物機を引かない（貨物機は会社の方針と機体の印で決める。次の段階）

create table if not exists public.co3_types (
  code       text primary key check (code ~ '^[A-Z0-9-]{2,12}$'),
  name       text not null,
  kind       text not null check (kind in ('pax', 'freighter', 'bizjet', 'small', 'heli')),
  seats      numeric not null,            -- 旅客機・小型機：全席普通の席、貨物機：積める重さ（t）、ビジネスジェット：VIP 席
  range_km   integer not null,
  runway_m   integer,                     -- ヘリは null
  gen        text not null check (gen in ('old', 'mid', 'new')),
  mult       numeric,                     -- 機体の倍率（小型機は null）
  price      integer not null,
  upkeep     integer not null,
  wing       text not null check (wing in ('B', 'C', 'D', 'E', 'F')),
  mtow       numeric not null,            -- 最大の重さ（t、着陸料の重さの額）
  noise      text not null check (noise in ('none', 'prop', 'jet', 'wide')),
  icao       text[] not null default '{}',
  iata       text[] not null default '{}'
);
alter table public.co3_types enable row level security;
revoke all on public.co3_types from public, anon, authenticated;
grant select on public.co3_types to anon, authenticated;
drop policy if exists "types are public" on public.co3_types;
create policy "types are public" on public.co3_types for select to anon, authenticated using (true);

insert into public.co3_types (code, name, kind, seats, range_km, runway_m, gen, mult, price, upkeep, wing, mtow, noise, icao, iata) values
  -- 旅客機
  ('DHC6',  'DHC-6 ツインオッター', 'pax',  19,  1300,  800, 'old', 0.88,  1500,  2, 'B',   5.7, 'prop', '{DHC6}', '{DHT}'),
  ('D228',  'Do228',                'pax',  19,  1100,  800, 'mid', 0.88,  1800,  2, 'B',   6.4, 'prop', '{D228}', '{D28}'),
  ('SF34',  'サーブ340B',           'pax',  36,  1700, 1200, 'old', 0.94,  2700,  4, 'B',  13.2, 'prop', '{SF34}', '{SF3}'),
  ('AT46',  'ATR42-600',            'pax',  48,  1300, 1100, 'new', 0.99,  5100,  4, 'C',  18.6, 'prop', '{AT46,AT45,AT43}', '{AT4,AT5}'),
  ('AT76',  'ATR72-600',            'pax',  70,  1500, 1300, 'new', 1.08,  7500,  5, 'C',  23.0, 'prop', '{AT76,AT75,AT72}', '{AT7,ATR}'),
  ('DH8D',  'Q400（DHC-8-400）',    'pax',  74,  2000, 1400, 'mid', 1.10,  6600,  7, 'C',  29.3, 'prop', '{DH8D}', '{DH4}'),
  ('E170',  'E170',                 'pax',  76,  3900, 1600, 'mid', 1.10,  6900,  7, 'C',  38.6, 'jet',  '{E170}', '{E70}'),
  ('E175',  'E175',                 'pax',  84,  4000, 1700, 'mid', 1.14,  7500,  8, 'C',  40.4, 'jet',  '{E75L,E75S,E175}', '{E75}'),
  ('E190',  'E190',                 'pax',  95,  4500, 1700, 'mid', 1.18,  8400,  8, 'C',  51.8, 'jet',  '{E190,E290}', '{E90,E9X}'),
  ('B737',  'B737-700',             'pax', 144,  6000, 1800, 'old', 1.38, 10500, 15, 'C',  70.1, 'jet',  '{B737}', '{73G,73W,737}'),
  ('B738',  'B737-800',             'pax', 170,  5400, 1800, 'mid', 1.48, 15300, 15, 'C',  79.0, 'jet',  '{B738}', '{738,73H,73K}'),
  ('B38M',  'B737 MAX 8',           'pax', 170,  6500, 1800, 'new', 1.48, 18300, 13, 'C',  82.2, 'jet',  '{B38M}', '{7M8}'),
  ('A320',  'A320',                 'pax', 180,  6100, 1800, 'mid', 1.52, 16200, 16, 'C',  78.0, 'jet',  '{A320}', '{320}'),
  ('A20N',  'A320neo',              'pax', 180,  6300, 1800, 'new', 1.52, 19500, 14, 'C',  79.0, 'jet',  '{A20N}', '{32N}'),
  ('A321',  'A321',                 'pax', 194,  5900, 2000, 'mid', 1.58, 17400, 17, 'C',  93.5, 'jet',  '{A321}', '{321}'),
  ('A21N',  'A321neo',              'pax', 194,  7400, 2000, 'new', 1.58, 21000, 15, 'C',  97.0, 'jet',  '{A21N}', '{32Q,32Y}'),
  ('B763',  'B767-300ER',           'pax', 270, 11000, 2000, 'old', 1.88, 19500, 27, 'D', 186.9, 'wide', '{B763}', '{763,76W,767}'),
  ('B788',  'B787-8',               'pax', 335, 13500, 2000, 'new', 2.14, 36300, 25, 'E', 227.9, 'wide', '{B788}', '{788}'),
  ('B789',  'B787-9',               'pax', 395, 14000, 2500, 'new', 2.38, 42600, 30, 'E', 254.0, 'wide', '{B789}', '{789}'),
  ('B78X',  'B787-10',              'pax', 429, 11900, 2500, 'new', 2.52, 46200, 32, 'E', 254.0, 'wide', '{B78X}', '{781}'),
  ('A333',  'A330-300',             'pax', 290, 11700, 2500, 'mid', 1.96, 26100, 26, 'E', 242.0, 'wide', '{A333}', '{333}'),
  ('A359',  'A350-900',             'pax', 369, 15000, 2500, 'new', 2.28, 39900, 28, 'E', 280.0, 'wide', '{A359}', '{359}'),
  ('A35K',  'A350-1000',            'pax', 239, 16000, 2500, 'new', 1.76, 25800, 18, 'E', 319.0, 'wide', '{A35K}', '{351}'),
  ('B772',  'B777-200',             'pax', 405,  9700, 2500, 'old', 2.42, 29100, 41, 'E', 247.2, 'wide', '{B772}', '{772}'),
  ('B773',  'B777-300',             'pax', 514, 11100, 2500, 'old', 2.86, 36900, 52, 'E', 299.4, 'wide', '{B773}', '{773}'),
  ('B77W',  'B777-300ER',           'pax', 244, 13600, 2500, 'mid', 1.78, 21900, 22, 'E', 351.5, 'wide', '{B77W}', '{77W}'),
  ('B748',  'B747-8',               'pax', 364, 14300, 3000, 'mid', 2.26, 32700, 33, 'F', 447.7, 'wide', '{B748}', '{74H}'),
  ('A388',  'A380',                 'pax', 520, 15000, 3000, 'mid', 2.88, 46800, 47, 'F', 575.0, 'wide', '{A388}', '{388}'),
  -- 貨物機（積める重さ t）
  ('B738F', 'B737-800BCF',          'freighter',  23, 3700, 2000, 'mid', 1.28,  8400,  8, 'C',  79.0, 'jet',  '{}', '{}'),
  ('B752F', 'B757-200F',            'freighter',  39, 5800, 2000, 'old', 1.61, 11100, 16, 'D', 115.7, 'jet',  '{}', '{}'),
  ('B763F', 'B767-300F',            'freighter',  52, 6000, 2500, 'old', 1.88, 15000, 21, 'D', 186.9, 'wide', '{}', '{}'),
  ('A333F', 'A330-300P2F',          'freighter',  61, 6600, 2500, 'mid', 2.07, 21900, 22, 'E', 233.0, 'wide', '{}', '{}'),
  ('MD11F', 'MD-11F',               'freighter',  91, 7300, 3000, 'old', 2.70, 26100, 37, 'D', 286.0, 'wide', '{}', '{}'),
  ('B77F',  'B777F',                'freighter', 102, 9200, 3000, 'mid', 2.92, 36600, 37, 'E', 347.8, 'wide', '{B77L}', '{77X}'),
  ('B744F', 'B747-400F',            'freighter', 113, 8200, 3000, 'old', 3.15, 32400, 45, 'E', 396.9, 'wide', '{}', '{74Y}'),
  ('B748F', 'B747-8F',              'freighter', 134, 8100, 3000, 'mid', 3.59, 48300, 48, 'F', 447.7, 'wide', '{}', '{74N}'),
  -- ビジネスジェット（VIP 席）
  ('HDJT',  'ホンダジェット エリート',     'bizjet',  5,  2600, 1100, 'new', 1.04, 10800,  8, 'B',   4.9, 'jet', '{HDJT}', '{}'),
  ('C25C',  'サイテーション CJ4',          'bizjet',  8,  4000, 1000, 'mid', 1.18, 14400, 14, 'B',   7.8, 'jet', '{C25C}', '{}'),
  ('C68A',  'サイテーション ラティチュード', 'bizjet', 8,  5000, 1200, 'mid', 1.18, 14400, 14, 'B',  14.0, 'jet', '{C68A}', '{}'),
  ('CL35',  'チャレンジャー350',           'bizjet',  9,  5900, 1500, 'mid', 1.23, 16200, 16, 'B',  18.4, 'jet', '{CL35}', '{}'),
  ('G280',  'ガルフストリーム G280',       'bizjet',  9,  6700, 1500, 'mid', 1.23, 16200, 16, 'B',  17.9, 'jet', '{G280}', '{}'),
  ('FA8X',  'ファルコン 8X',               'bizjet', 12, 11900, 1800, 'mid', 1.38, 21600, 22, 'C',  33.0, 'jet', '{FA8X}', '{}'),
  ('GLF6',  'ガルフストリーム G650ER',     'bizjet', 14, 13900, 1800, 'mid', 1.47, 25200, 25, 'C',  47.6, 'jet', '{GLF6}', '{}'),
  ('GL7T',  'グローバル 7500',             'bizjet', 14, 14200, 1800, 'new', 1.47, 30300, 21, 'C',  52.2, 'jet', '{GL7T}', '{}'),
  ('BBJ',   'BBJ（B737のVIP仕様）',        'bizjet', 25, 11000, 2000, 'mid', 2.00, 45000, 45, 'C',  79.0, 'jet', '{}', '{}'),
  ('ACJ',   'ACJ320neo（A320neoのVIP仕様）', 'bizjet', 25, 11000, 2000, 'new', 2.00, 54000, 38, 'C', 79.0, 'jet', '{}', '{}'),
  -- 小型機・ヘリ（地域航空。見ていなくても買える6機種）
  ('C172',  'セスナ172',                   'small',   3,  1200,  500, 'mid', null,   500,  1, 'B',   1.1, 'none', '{C172}', '{}'),
  ('BN2P',  'ブリテン・ノーマン アイランダー', 'small', 9, 1400,  500, 'old', null,  1300,  2, 'B',   3.0, 'none', '{BN2P,BN2T}', '{}'),
  ('C208',  'セスナ208 キャラバン',        'small',   9,  1700,  700, 'mid', null,  1600,  2, 'B',   4.0, 'none', '{C208}', '{}'),
  ('PC12',  'ピラタス PC-12',              'small',   8,  3300,  800, 'new', null,  1700,  1, 'B',   4.7, 'none', '{PC12}', '{}'),
  ('R44',   'ロビンソン R44（ヘリ）',      'heli',    3,   500, null, 'mid', null,   500,  1, 'B',   1.1, 'none', '{R44}', '{}'),
  ('H125',  'エアバス H125（ヘリ）',       'heli',    5,   600, null, 'mid', null,   900,  1, 'B',   2.3, 'none', '{AS50,EC30}', '{}')
on conflict (code) do update set name = excluded.name, kind = excluded.kind, seats = excluded.seats, range_km = excluded.range_km,
  runway_m = excluded.runway_m, gen = excluded.gen, mult = excluded.mult, price = excluded.price, upkeep = excluded.upkeep,
  wing = excluded.wing, mtow = excluded.mtow, noise = excluded.noise, icao = excluded.icao, iata = excluded.iata;

-- 記号（ICAO か時刻表）から機種を引く。貨物機は引かない（記号が旅客機と同じため）。777F（B77L）だけは記号で分かる
create or replace function public.co3_type_of(p_code text) returns text
language sql stable security definer set search_path = public as $$
  select code from co3_types
   where p_code is not null and btrim(p_code) <> ''
     and (upper(btrim(p_code)) = any (icao) or upper(btrim(p_code)) = any (iata))
   order by (upper(btrim(p_code)) = any (icao)) desc, code limit 1
$$;
revoke all on function public.co3_type_of(text) from public;
grant execute on function public.co3_type_of(text) to anon, authenticated;

-- 会社の機体の数字：機種が分かれば機種の表、分からなければ大きさの区分の目安
create or replace function public.co3_ac_spec(p_aircraft bigint, out code text, out seats numeric, out mtow numeric, out noise text, out wing text, out wide boolean)
language sql stable security definer set search_path = public as $$
  select t.code,
         coalesce(t.seats, (co3.ac_class_spec(a.type)).seats),
         coalesce(t.mtow, (co3.ac_class_spec(a.type)).mtow),
         coalesce(t.noise, (co3.ac_class_spec(a.type)).noise),
         coalesce(t.wing, (co3.ac_class_spec(a.type)).wing),
         coalesce(t.wing >= 'D', a.type in ('wb', 'lg'))
    from aircraft a left join co3_types t on t.code = co3_type_of(a.icao)
   where a.id = p_aircraft
$$;
revoke all on function public.co3_ac_spec(bigint) from public, anon, authenticated;

-- 本物の便の平均の座席も、機種が分かれば機種の表で数える
create or replace function public.co3_seats_of(p_type text, p_aircraft text) returns numeric
language sql stable security definer set search_path = public as $$
  select coalesce((select seats from co3_types where kind = 'pax' and code = co3_type_of(coalesce(nullif(p_type, ''), p_aircraft))),
                  (co3.ac_class_spec(ac_class(coalesce(nullif(p_type, ''), p_aircraft)))).seats, 170)
$$;
revoke all on function public.co3_seats_of(text, text) from public, anon, authenticated;

-- 路線ごとの内わけと本物の便の数え方を、機種の表を使う形に直す
do $do$
declare src text; n0 integer;
begin
  select pg_get_functiondef('public.co3_route_econ(uuid)'::regprocedure) into src;
  n0 := length(src);
  src := replace(src, 'coalesce((co3.ac_class_spec(r.ac_type)).seats, 0) as raw_seats,', 'coalesce((co3_ac_spec(r.ac_id)).seats, 0) as raw_seats,');
  src := replace(src, 'r.ac_type in (''wb'', ''lg'') as wide,', 'coalesce((co3_ac_spec(r.ac_id)).wide, false) as wide,');
  src := replace(src, '(co3.ac_class_spec(r.ac_type)).mtow as mtow, (co3.ac_class_spec(r.ac_type)).noise as noise,',
                      '(co3_ac_spec(r.ac_id)).mtow as mtow, (co3_ac_spec(r.ac_id)).noise as noise,');
  if position('co3.ac_class_spec(r.ac_type)' in src) > 0 or position('co3_ac_spec(r.ac_id)).wide' in src) = 0 then
    raise exception 'co3_route_econ の形が変わっていて、機種の表を入れられない';
  end if;
  execute src;

  select pg_get_functiondef('public.co3_route_real_refresh()'::regprocedure) into src;
  src := replace(src, 'coalesce((co3.ac_class_spec(ac_class(coalesce(nullif(type, ''''), aircraft)))).seats, 170) as seats',
                      'co3_seats_of(type, aircraft) as seats');
  if position('co3_seats_of' in src) = 0 then raise exception 'co3_route_real_refresh の形が変わっていて、機種の表を入れられない'; end if;
  execute src;
end
$do$;
