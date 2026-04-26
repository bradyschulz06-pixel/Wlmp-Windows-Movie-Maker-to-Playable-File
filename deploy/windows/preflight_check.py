#!/usr/bin/env python3
from pathlib import Path
import shutil, subprocess, sys

REQUIRED = [
    Path("wlmp_gui.py"),
    Path("wlmp_offline_tool.py"),
    Path("config/app_config.json"),
    Path("deploy/windows/prepare_unsigned_release.ps1"),
]
def main():
    print("== Preflight ==")
    for p in REQUIRED:
        if not p.exists():
            print(f"[FAIL] Missing: {p}")
            return 1
        print(f"[OK] {p}")
    print("[OK] ffmpeg found" if shutil.which("ffmpeg") else "[WARN] ffmpeg missing (can still continue)")
    rc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]).returncode
    return rc
if __name__ == "__main__":
    raise SystemExit(main())
