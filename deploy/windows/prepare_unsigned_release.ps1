Param([string]$Version = "")
$ErrorActionPreference = "Stop"
if ($Version -eq "") {
  $config = Get-Content "config/app_config.json" | ConvertFrom-Json
  $Version = $config.release_version
}
python deploy/windows/preflight_check.py
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --name JonesboroWLMPConverter --windowed --add-data "assets;assets" --add-data "config;config" wlmp_gui.py
$releaseRoot = "release/JonesboroWLMPConverter-$Version"
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
Copy-Item -Recurse -Force "dist/JonesboroWLMPConverter/*" "$releaseRoot/"
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
  Copy-Item -Force (Get-Command ffmpeg).Source "$releaseRoot/ffmpeg.exe"
}
Get-ChildItem -Path "release" -Recurse -File | ForEach-Object {
  $h = Get-FileHash -Algorithm SHA256 $_.FullName
  "$($h.Hash)  $($_.FullName)" | Out-File -FilePath "release/SHA256SUMS.txt" -Append -Encoding utf8
}
Write-Host "Unsigned release complete: $releaseRoot"
