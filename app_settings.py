from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("config/app_config.json")

@dataclass
class AppSettings:
    app_title: str = "Jonesboro ISD WLMP to MP4 File Conversion System"
    logo_path: str = "assets/jonesboro_isd_logo.png"
    organization: str = "Jonesboro ISD"
    release_version: str = "1.2.0"

def load_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> AppSettings:
    if not config_path.exists():
        return AppSettings()
    data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    return AppSettings(
        app_title=data.get("app_title", AppSettings.app_title),
        logo_path=data.get("logo_path", AppSettings.logo_path),
        organization=data.get("organization", AppSettings.organization),
        release_version=data.get("release_version", AppSettings.release_version),
    )
