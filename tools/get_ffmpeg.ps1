# ffmpeg.exe'yi indirip ffmpeg\ klasörüne koyar (build.bat tarafından çağrılır).
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root "ffmpeg"
$zip = Join-Path $dest "ffmpeg.zip"
$tmp = Join-Path $dest "tmp"

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
Expand-Archive $zip -DestinationPath $tmp -Force
$exe = Get-ChildItem $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1
Copy-Item $exe.FullName (Join-Path $dest "ffmpeg.exe") -Force
Remove-Item $tmp -Recurse -Force
Remove-Item $zip -Force
Write-Host "ffmpeg.exe hazir."
