# Builds E:\helmet_detection\helmet_bundle.zip = backend code + model + deploy scripts, ready to upload to the server.
# Excluded on purpose: .env (secrets), storage/ (uploads/results), __pycache__, old model backups.
# Usage (PowerShell):  .\deploy\make_bundle.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$stage = Join-Path $env:TEMP ("helmet_bundle_" + [guid]::NewGuid().ToString("N"))
$zip = Join-Path $root "helmet_bundle.zip"

New-Item -ItemType Directory -Path "$stage\backend", "$stage\deploy" | Out-Null
robocopy "$root\backend" "$stage\backend" /E /XD __pycache__ storage /XF .env best_v1.pt *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
Copy-Item "$root\deploy\*" "$stage\deploy" -Exclude "make_bundle.ps1"

# Linux wants LF line endings in scripts and configs
Get-ChildItem "$stage\deploy" -File | Where-Object { $_.Extension -in ".sh", ".service", ".conf" } | ForEach-Object {
    $text = [IO.File]::ReadAllText($_.FullName) -replace "`r`n", "`n"
    [IO.File]::WriteAllText($_.FullName, $text, (New-Object Text.UTF8Encoding($false)))
}
if (-not (Test-Path "$stage\backend\models\best.pt")) { throw "backend\models\best.pt is missing" }

if (Test-Path $zip) { Remove-Item $zip -Force }
# Compress-Archive in Windows PowerShell 5.1 writes backslash paths; build the zip by hand with "/" so Linux unzip is happy.
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::Open($zip, [IO.Compression.ZipArchiveMode]::Create)
Push-Location $stage   # relative paths below are taken from here (TEMP may be an 8.3 short path, so don't slice strings)
try {
    Get-ChildItem -Recurse -File | ForEach-Object {
        $entry = (Resolve-Path -LiteralPath $_.FullName -Relative).Substring(2).Replace("\", "/")
        [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $_.FullName, $entry, [IO.Compression.CompressionLevel]::Optimal)
    }
} finally { Pop-Location; $archive.Dispose() }
Remove-Item $stage -Recurse -Force
"Bundle ready: $zip  ({0:N1} MB)" -f ((Get-Item $zip).Length / 1MB)
