# バックアップ（運営コンソールで書き出したJSON）から、データを戻すSQLを作る
#   python3 tools/restore_from_backup.py soramemo-backup-20261006.json > restore.sql
# できた restore.sql を Supabase の「SQL Editor」に貼って「Run」する。
# - すでにある行は上書きしない（同じ番号・同じ人の行は飛ばす）。消えた行だけが戻る
# - ログインのアカウント（auth.users）にいない人の行は戻さない（アカウントそのものは、このファイルからは作れない）
import json, sys

TABLES = [  # 戻す順番（参照される側が先）、重なりの判定に使う列、番号を自動で振る列があるか
    ("public.checkins",       "(id)",                      True),
    ("public.flights",        "(id)",                      True),
    ("public.manual_flights", "(id)",                      True),
    ("public.companies",      "(user_id)",                 False),
    ("public.route_levels",   "(user_id, route_key)",      False),
    ("public.aircraft",       "(id)",                      True),
    ("public.facilities",     "(user_id, airport_id)",     False),
    ("public.subscriptions",  "(user_id)",                 False),
    ("ops.admins",            "(user_id)",                 False),
]

def main():
    if len(sys.argv) < 2:
        print(__doc__ or "使い方: python3 tools/restore_from_backup.py <バックアップのJSON>", file=sys.stderr); sys.exit(1)
    b = json.load(open(sys.argv[1], encoding="utf-8"))
    if b.get("app") != "soramemo": sys.exit("そらメモのバックアップではありません")
    out = [f"-- そらメモ：バックアップ（{b.get('created_at')}）から戻す", "begin;"]
    for table, key, identity in TABLES:
        name = table.split(".")[1]
        rows = b.get(name) or []
        if not rows: continue
        data = json.dumps(rows, ensure_ascii=False)
        assert "$soramemo$" not in data
        over = " overriding system value" if identity else ""
        out.append(f"-- {table}：{len(rows)}行")
        out.append(f"insert into {table}{over} select * from jsonb_populate_recordset(null::{table}, $soramemo${data}$soramemo$::jsonb) r "
                   f"where exists (select 1 from auth.users u where u.id = r.user_id) on conflict {key} do nothing;")
        if identity:
            out.append(f"select setval(pg_get_serial_sequence('{table}', 'id'), greatest((select coalesce(max(id), 1) from {table}), 1));")
    flags = b.get("flags") or []
    if flags:
        out.append("-- 運営の切り替え（メンテナンス中・経営の公開など）も、バックアップの時点に戻す")
        out.append(f"insert into ops.flags select * from jsonb_populate_recordset(null::ops.flags, $soramemo${json.dumps(flags, ensure_ascii=False)}$soramemo$::jsonb) "
                   "on conflict (key) do update set value = excluded.value, updated_at = excluded.updated_at;")
    out.append("commit;")
    print("\n".join(out))

if __name__ == "__main__":
    main()
