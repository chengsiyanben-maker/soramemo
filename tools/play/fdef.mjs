// 試遊版のデータベースで、関数の今の中身（マイグレーションで直したあとの形）を出す：node tools/play/fdef.mjs 'public.co3_route_econ_calc(uuid)'
import { buildDb } from './seed.mjs';
const db = await buildDb();
for (const f of process.argv.slice(2)) { const r = await db.query(`select pg_get_functiondef('${f}'::regprocedure) d`); console.log(r.rows[0].d); }
