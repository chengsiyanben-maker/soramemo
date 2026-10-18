-- 到着予想の当たり具合を確かめるため、到着の60・30・15分前ごろの予想（推定）を便ごとの実績に残す
alter table public.flight_history add column if not exists eta60 timestamptz, add column if not exists eta30 timestamptz, add column if not exists eta15 timestamptz;
