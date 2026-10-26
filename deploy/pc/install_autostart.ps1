# Makes the CCTV worker start by itself every time you log in to this PC (and restart if it ever stops).
# Usage (normal PowerShell, no admin needed):
#   .\deploy\pc\install_autostart.ps1 -CameraId 1              # real camera
#   .\deploy\pc\install_autostart.ps1 -CameraId 1 -TestStream  # also start the fake looped test camera
#   .\deploy\pc\install_autostart.ps1 -Remove                  # undo
# For a PC that should work after a power cut without anyone logging in: set Windows to log in automatically
# (netplwiz) and, in the BIOS, "Restore on AC power loss" = Power On.
param([int[]]$CameraId = @(1), [switch]$TestStream, [switch]$Remove)
$ErrorActionPreference = "Stop"

# remove every Helmet task from an earlier install (any number of cameras)
Get-ScheduledTask -TaskName "HelmetCCTV*" -ErrorAction SilentlyContinue | ForEach-Object {
    Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false -ErrorAction SilentlyContinue }
if ($Remove) { "Auto-start removed."; return }

function Register($name, $script, $arguments, $delay) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`" $arguments"
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $trigger.Delay = $delay   # give the network a moment
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -RunLevel Limited -Force | Out-Null
    Start-ScheduledTask -TaskName $name
    "Registered and started: $name"
}

foreach ($id in $CameraId) {   # one worker per camera: -CameraId 1,2,3
    $taskName = if ($id -eq $CameraId[0]) { "HelmetCCTVWorker" } else { "HelmetCCTVWorker$id" }
    Register $taskName (Join-Path $PSScriptRoot "run_worker.ps1") "-CameraId $id" "PT30S"
}
if ($TestStream) { Register "HelmetCCTVTestStream" (Join-Path $PSScriptRoot "start_test_stream.ps1") "" "PT5S" }
"Done. Logs: backend\storage\cctv\worker_cam<ID>.log"
