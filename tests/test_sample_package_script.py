import unittest, subprocess, sys
from pathlib import Path

class SamplePackageScriptTests(unittest.TestCase):
    def test_create_sample_package(self):
        p = subprocess.run([sys.executable, "scripts/create_sample_package.py"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(Path("samples/sample_school_project.zip").exists())

if __name__ == "__main__":
    unittest.main()
