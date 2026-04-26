#!/usr/bin/env python3
import tempfile, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import wlmp_offline_tool as tool

def main():
    out = Path("samples")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        p = Path(t)
        wlmp = p / "sample_project.wlmp"
        media = p / "media"
        media.mkdir()
        (media / "sample_clip.wmv").write_text("demo", encoding="utf-8")
        wlmp.write_text("<Project><Media path='sample_clip.wmv' /></Project>", encoding="utf-8")
        tool.package_project(wlmp, media, out / "sample_school_project.zip")
    print("Created sample package: samples/sample_school_project.zip")

if __name__ == "__main__":
    main()
