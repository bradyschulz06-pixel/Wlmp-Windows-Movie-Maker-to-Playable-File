@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python was not found on PATH.
  pause
  exit /b 1
)
python wlmp_gui.py
if errorlevel 1 (
  echo [ERROR] GUI failed to start.
  pause
  exit /b 1
)
endlocal
