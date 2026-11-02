// 試遊版のデータベースで、アプリから呼べる経営の関数（authenticated に許した co_・co3_）と引数を一覧にする：node tools/play/listfn.mjs
import { buildDb } from './seed.mjs';
const db = await buildDb();
const r = await db.query(`select p.proname, pg_get_function_identity_arguments(p.oid) args from pg_proc p join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public' and (p.proname like 'co3_%' or p.proname like 'co_%') and has_function_privilege('authenticated', p.oid, 'execute') order by 1`);
for (const x of r.rows) console.log(x.proname + '(' + x.args + ')');
