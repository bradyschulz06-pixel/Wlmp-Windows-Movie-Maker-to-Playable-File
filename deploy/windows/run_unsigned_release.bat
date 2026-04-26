@echo off
setlocal
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.2.0
powershell -ExecutionPolicy Bypass -File .\deploy\windows\prepare_unsigned_release.ps1 -Version %VERSION%
endlocal
