Param()
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
Set-Location ..\..
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python was not found on PATH."
    exit 1
}
python .\wlmp_gui.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] GUI failed to start."
    exit $LASTEXITCODE
}
