# Keeps the CCTV worker running on this PC: restarts it a few seconds after it stops or crashes.
# Started automatically at logon by install_autostart.ps1. Logs go to backend\storage\cctv\worker.log.
param([int]$CameraId = 1)
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backend = Join-Path $root "backend"
$python = Join-Path $root ".venv\Scripts\python.exe"
$log = Join-Path $backend "storage\cctv\worker_cam$CameraId.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null
Set-Location $backend
while ($true) {
    if ((Test-Path $log) -and (Get-Item $log).Length -gt 5MB) { Move-Item $log "$log.old" -Force }   # keep the log small
    "[$(Get-Date -Format 's')] worker starting" | Add-Content $log
    & $python -m services.cctv_worker --camera-id $CameraId 2>&1 | ForEach-Object { "$_" } | Out-File -Append -Encoding utf8 $log
    "[$(Get-Date -Format 's')] worker stopped (exit $LASTEXITCODE), restarting in 10 s" | Add-Content $log
    Start-Sleep 10
}
