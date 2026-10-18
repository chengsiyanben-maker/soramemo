# そらメモ：毎日の記録をこのパソコンに保存する（Windows）
#   はじめに一度だけ:  powershell -ExecutionPolicy Bypass -File .\soramemo-archive.ps1 -Setup
#   毎朝の自動実行に登録: powershell -ExecutionPolicy Bypass -File .\soramemo-archive.ps1 -Install
#   手で今すぐ保存:      powershell -ExecutionPolicy Bypass -File .\soramemo-archive.ps1
# 保存先: このファイルと同じフォルダの data\年\年-月-日.json.gz（ODPT のデータを含むので、公開しないこと）
param([switch]$Setup, [switch]$Install, [int]$Days = 10)
$ErrorActionPreference = "Stop"
$Here  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Token = Join-Path $Here "token.txt"
$Data  = Join-Path $Here "data"
$Log   = Join-Path $Here "archive.log"
$Url   = "https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/archive-export"
function Say($m) { $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m; Write-Host $line; Add-Content -Path $Log -Value $line -Encoding UTF8 }

if ($Setup) {
  # 合言葉を作って、このパソコンだけに保存する（チャットには貼らない）
  $bytes = New-Object byte[] 30; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $t = ([Convert]::ToBase64String($bytes)).Replace("+", "A").Replace("/", "B").Replace("=", "")
  Set-Content -Path $Token -Value $t -NoNewline -Encoding ASCII
  icacls $Token /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
  Set-Clipboard -Value $t
  Write-Host ""
  Write-Host "合言葉を作って token.txt に保存し、クリップボードにも写しました。"
  Write-Host "開いた Supabase の画面（Edge Functions の Secrets）で、次の名前で追加してください:"
  Write-Host "    名前: ARCHIVE_EXPORT_TOKEN"
  Write-Host "    値  : (Ctrl+V で貼り付け)"
  Write-Host "貼り付けたら、クリップボードは別の文字をコピーして消しておくと安心です。"
  Start-Process "https://supabase.com/dashboard/project/bygwdoypfrccgfjjrorc/settings/functions"
  exit 0
}

if ($Install) {
  # 毎朝6時に実行。パソコンが切れていたら、次に起動したときに実行する
  $action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"{0}`"" -f $MyInvocation.MyCommand.Path) -WorkingDirectory $Here
  $trigger = New-ScheduledTaskTrigger -Daily -At 6:00am
  $set     = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
  Register-ScheduledTask -TaskName "soramemo-archive" -Action $action -Trigger $trigger -Settings $set -Description "そらメモの毎日の記録をこのパソコンに保存する" -Force | Out-Null
  Write-Host "毎朝6時に保存するよう登録しました（タスク スケジューラの「soramemo-archive」）。"
  exit 0
}

if (-not (Test-Path $Token)) { Say "token.txt がありません。先に -Setup を実行してください。"; exit 1 }
$t = (Get-Content -Path $Token -Raw).Trim()
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$saved = 0; $missing = 0
for ($i = 1; $i -le $Days; $i++) {
  $d = (Get-Date).ToUniversalTime().AddHours(9).AddDays(-$i).ToString("yyyy-MM-dd")
  $dir = Join-Path $Data $d.Substring(0, 4); $file = Join-Path $dir "$d.json.gz"
  if (Test-Path $file) { continue }
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  try {
    Invoke-WebRequest -Uri "$($Url)?day=$d" -Headers @{ "x-export-token" = $t } -OutFile "$file.part" -UseBasicParsing -TimeoutSec 120
    Move-Item -Force "$file.part" $file; $saved++
    Say ("保存しました: {0} ({1:N0} KB)" -f $d, ((Get-Item $file).Length / 1KB))
  } catch {
    if (Test-Path "$file.part") { Remove-Item "$file.part" -Force }
    $code = $null; try { $code = [int]$_.Exception.Response.StatusCode } catch {}
    if ($code -eq 404) { $missing++ } elseif ($code -eq 403) { Say "合言葉が合いません（Supabase の ARCHIVE_EXPORT_TOKEN と token.txt を確かめてください）"; exit 1 }
    else { Say ("{0} を保存できませんでした: {1}" -f $d, $_.Exception.Message) }
  }
}
Say ("おわり: 新しく {0} 日ぶん保存（まだ作られていない日 {1}）" -f $saved, $missing)
