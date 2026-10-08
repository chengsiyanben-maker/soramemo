# Supabase のダッシュボードのエディタに貼るための、checkin 関数の1ファイル版を作る
# （自動で反映する仕組みを使うなら不要。手で貼るときだけ使う）
#   python3 tools/make_dashboard_checkin.py  → tools/dashboard/checkin.ts
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
j = open(os.path.join(ROOT, "supabase/functions/_shared/judge.ts"), encoding="utf-8").read().replace("export type", "type").replace("export const", "const").replace("export function", "function")
i = open(os.path.join(ROOT, "supabase/functions/checkin/index.ts"), encoding="utf-8").read().replace('import { type Airport, decide, type Terminal } from "../_shared/judge.ts";\n', "")
lines = i.split("\n", 2)
out = "// ダッシュボードのエディタに貼り付ける用の1ファイル版（checkin/index.ts と _shared/judge.ts を結合したもの）\n" + "\n".join(lines[0:2]) + "\n\n" + j + "\n" + lines[2]
open(os.path.join(ROOT, "tools/dashboard/checkin.ts"), "w", encoding="utf-8").write(out); print("tools/dashboard/checkin.ts")
