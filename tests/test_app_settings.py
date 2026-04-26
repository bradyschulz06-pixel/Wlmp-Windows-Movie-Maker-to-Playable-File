import unittest
from app_settings import load_settings, AppSettings
from pathlib import Path
import tempfile

class AppSettingsTests(unittest.TestCase):
    def test_load_settings_defaults_when_missing(self):
        with tempfile.TemporaryDirectory() as t:
            s = load_settings(Path(t) / "missing.json")
            self.assertIsInstance(s, AppSettings)

if __name__ == "__main__":
    unittest.main()
