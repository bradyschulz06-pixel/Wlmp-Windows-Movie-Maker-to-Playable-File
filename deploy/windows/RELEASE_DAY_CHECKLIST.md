Run:
python deploy/windows/preflight_check.py
powershell -ExecutionPolicy Bypass -File .\deploy\windows\prepare_unsigned_release.ps1 -Version 1.2.0
