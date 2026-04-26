import unittest, tempfile, zipfile
from pathlib import Path
import wlmp_offline_tool as tool

class WlmpOfflineToolTests(unittest.TestCase):
    def test_validate_package_reports_missing(self):
        with tempfile.TemporaryDirectory() as t:
            z = Path(t) / "p.zip"
            with zipfile.ZipFile(z, "w") as f:
                f.writestr("project.wlmp", "<Project><Media path='missing.wmv'/></Project>")
            r = tool.validate_package(z)
            self.assertEqual(r.missing_paths, ["missing.wmv"])

if __name__ == "__main__":
    unittest.main()
