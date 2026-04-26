import unittest, tempfile
from pathlib import Path
import wlmp_offline_tool as tool

class EndToEndWorkflowTests(unittest.TestCase):
    def test_package_then_validate_success(self):
        with tempfile.TemporaryDirectory() as t:
            b = Path(t)
            wlmp = b / "p.wlmp"
            media = b / "media"
            media.mkdir()
            (media / "a.wmv").write_text("x")
            wlmp.write_text("<Project><Media path='a.wmv'/></Project>")
            z = b / "out.zip"
            tool.package_project(wlmp, media, z)
            r = tool.validate_package(z)
            self.assertEqual(len(r.missing_paths), 0)

if __name__ == "__main__":
    unittest.main()
