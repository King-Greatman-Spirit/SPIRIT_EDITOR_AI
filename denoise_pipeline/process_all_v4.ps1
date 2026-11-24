$ErrorActionPreference = "Continue"
$base = "C:\Users\greatman.u\Music\INTERNS INTERVIEW_denoised"
$audioDir = Join-Path $base "audio"
$finalDir = Join-Path $base "Final_v4"
New-Item -ItemType Directory -Force -Path $audioDir, $finalDir | Out-Null

Get-ChildItem (Join-Path $base "*.mp4") | ForEach-Object {
    $name = $_.BaseName
    $out = Join-Path $finalDir "$name.mp4"
    if (Test-Path $out) { Write-Host "SKIP (already done): $name"; return }

    Write-Host "`n========== $name =========="
    $wav = Join-Path $audioDir "$name.v4.01.raw.wav"
    $d1  = Join-Path $audioDir "$name.v4.02.deepfilter.wav"
    $d2  = Join-Path $audioDir "$name.v4.03.nr.wav"
    $d3  = Join-Path $audioDir "$name.v4.04.norm.wav"
    $d4  = Join-Path $audioDir "$name.v4.05.final.wav"

    Write-Host "[1/5] extract audio"
    ffmpeg -y -hide_banner -loglevel error -i $_.FullName -vn -ac 1 -ar 48000 -c:a pcm_s16le $wav

    Write-Host "[2/5] DeepFilterNet neural denoise"
    python (Join-Path $base "df_pass.py") $wav $d1 2>$null
    if (-not (Test-Path $d1)) { Write-Host "FAILED deepfilter: $name"; return }

    Write-Host "[3/5] noisereduce with noise profile from this clip"
    python (Join-Path $base "strong_pass.py") $d1 $d2 $d1 2>$null
    if (-not (Test-Path $d2)) { Write-Host "FAILED noisereduce: $name"; return }

    Write-Host "[4/5] loudness + silence gate"
    ffmpeg -y -hide_banner -loglevel error -i $d2 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a pcm_s16le $d3
    python (Join-Path $base "clean_pipeline.py") gate-silence $d3 $d4 2>$null
    if (-not (Test-Path $d4)) { Write-Host "FAILED vad: $name"; return }

    Write-Host "[5/5] remux video with clean audio"
    ffmpeg -y -hide_banner -loglevel error -i $_.FullName -i $d4 -c:v copy -map 0:v:0 -map 1:a:0 -c:a aac -b:a 192k -shortest $out
    if (Test-Path $out) {
        Write-Host "DONE: $out"
        python (Join-Path $base "clean_pipeline.py") verify $wav $d4
    } else { Write-Host "FAILED remux: $name" }
}
Write-Host "`nAll finished."
