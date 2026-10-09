#!/usr/bin/env bash
# 非常停止を呼ぶ（メンテナンスをオンにする。戻すのは運営画面から）。
# 合言葉は環境変数 EMERGENCY_STOP_TOKEN から読む。ファイルやこの履歴には書かない。
#   使い方: EMERGENCY_STOP_TOKEN=... tools/emergency_stop.sh "点検中です"
set -euo pipefail
: "${EMERGENCY_STOP_TOKEN:?EMERGENCY_STOP_TOKEN が未設定です}"
MSG="${1:-}"
BODY="$(python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1]}, ensure_ascii=False))' "$MSG")"
curl -sS -X POST "https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/emergency-stop" \
  -H "x-stop-token: ${EMERGENCY_STOP_TOKEN}" -H "content-type: application/json" -d "$BODY"
echo
