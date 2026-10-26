# TEST ONLY: plays the Myanmar sample video in a loop as a fake CCTV camera at rtsp://127.0.0.1:8554/cam1.
# Not needed (and should not be installed) once a real camera is connected.
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$mtx = Join-Path $root "tools\mediamtx\mediamtx.exe"
$ffmpeg = Join-Path $root "tools\ffmpeg\ffmpeg.exe"
$video = Join-Path $root "data_helmet_myanmar\video\test_loop.mp4"
foreach ($f in $mtx, $ffmpeg, $video) { if (-not (Test-Path $f)) { throw "Missing $f" } }

if (-not (Get-Process mediamtx -ErrorAction SilentlyContinue)) {
    Start-Process $mtx -ArgumentList (Join-Path $root "tools\mediamtx\helmet.yml") -WindowStyle Hidden
    Start-Sleep 3
}
while ($true) {
    & $ffmpeg -loglevel error -re -stream_loop -1 -i $video -c copy -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/cam1
    Start-Sleep 5
}
