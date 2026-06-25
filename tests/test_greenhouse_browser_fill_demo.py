from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "scripts" / "greenhouse_browser_fill_demo.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("greenhouse_browser_fill_demo", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load greenhouse browser fill demo script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GreenhouseBrowserFillDemoTests(unittest.TestCase):
    def test_load_profile_splits_text_and_file_values(self) -> None:
        script = _load_script_module()

        profile = script.load_profile(FIXTURES / "browser_applicant_profile.json")

        self.assertEqual(profile["text"]["first_name"], "Ada")
        self.assertEqual(profile["text"]["email"], "ada@example.test")
        self.assertEqual(profile["text"]["location_city"], "San Francisco, CA")
        self.assertTrue(profile["files"]["resume"].endswith("fake_resume.txt"))
        self.assertTrue(profile["files"]["cover_letter"].endswith("fake_cover_letter.txt"))


if __name__ == "__main__":
    unittest.main()
