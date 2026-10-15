-- 海外の航空会社の特別塗装機も記録できるよう、登録記号の形を広げる（JA で始まるものだけ → 9V-OJJ・B-18101・D-AIFA・HL8306・N12345 など）
alter table public.livery_sightings drop constraint if exists livery_sightings_reg_check;
alter table public.livery_sightings add constraint livery_sightings_reg_check check (reg ~ '^[A-Z0-9]{1,3}-?[A-Z0-9]{2,6}$' and length(reg) <= 10);
