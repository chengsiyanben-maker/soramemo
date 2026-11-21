// 運用予想担当：特別塗装機（_shared/liveries.ts の kind が special のもの）ごとに、今の予想の部品で予想が出せるかを見る
// 読むだけの SQL（docs/pm/yosoku-livery-coverage.sql）を作る。登録記号の一覧はデータベースにないので、SQL の中に書き込む。
// 使い方：node tools/yosoku_livery_sql.mjs（Node 22.18 以上。liveries.ts をそのまま読む）
//   一覧が変わったら流し直す。tests/sql/t97_yosoku_livery_coverage.mjs が「SQL が一覧と合っているか」を確かめる
import fs from 'fs';

const root = new URL('../', import.meta.url).pathname;
const tplPath = root + 'docs/pm/yosoku-livery-coverage.tpl.sql';
const outPath = root + 'docs/pm/yosoku-livery-coverage.sql';

export async function specialLiveries() {
  const { LIVERIES } = await import(root + 'supabase/functions/_shared/liveries.ts');
  return LIVERIES.filter(l => (l.kind || 'special') === 'special');
}

const lit = s => s == null ? 'null' : `'${String(s).replace(/'/g, "''")}'`;

export async function buildSql() {
  const list = await specialLiveries();
  const values = list.map(l => `    (${lit(l.reg)}, ${lit(l.name)}, ${lit(l.airline)}, ${l.from ? `date ${lit(l.from)}` : 'null::date'}, ${l.until ? `date ${lit(l.until)}` : 'null::date'})`).join(',\n');
  const tpl = fs.readFileSync(tplPath, 'utf8');
  return tpl.replaceAll('/*LIVERIES*/', `values\n${values}`).replace('/*COUNT*/', String(list.length));
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const sql = await buildSql();
  fs.writeFileSync(outPath, sql);
  console.log(`書いた：docs/pm/yosoku-livery-coverage.sql（特別塗装機 ${(await specialLiveries()).length} 件）`);
}
