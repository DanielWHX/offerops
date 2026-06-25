from __future__ import annotations

import importlib.util
import json
import tempfile
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

    def test_load_profile_accepts_nested_real_profile_shape(self) -> None:
        script = _load_script_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resume = root / "resume.pdf"
            resume.write_text("fake pdf placeholder", encoding="utf-8")
            profile_path = root / "profile.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "identity": {
                            "first_name": "Grace",
                            "last_name": "Hopper",
                            "email": "grace@example.test",
                            "phone": "2125550100",
                            "location": "New York, NY",
                            "linkedin": "https://linkedin.example/grace",
                        },
                        "resume": {"resume_path": str(resume)},
                        "work_authorization": {
                            "future_sponsorship_required": "No sponsorship needed"
                        },
                        "application_answers": {
                            "current_location": "New York, NY",
                            "compensation": {"default_answer": "Market rate"},
                            "certification": {"initials": "GH"},
                            "self_identification": {
                                "hispanic_latino": "No, I am not Hispanic or Latino"
                            },
                        },
                        "default_answers": {
                            "gender": "I don't wish to answer",
                            "veteran_status": "I don't wish to answer",
                            "disability_status": "I don't wish to answer",
                            "race": "I don't wish to answer",
                        },
                    }
                ),
                encoding="utf-8",
            )

            profile = script.load_profile(profile_path)

        self.assertEqual(profile["text"]["first_name"], "Grace")
        self.assertEqual(profile["text"]["location_city"], "New York, NY")
        self.assertEqual(profile["custom_text"]["linkedin_profile"], "https://linkedin.example/grace")
        self.assertEqual(profile["custom_text"]["desired_salary"], "Market rate")
        self.assertEqual(profile["dropdowns"]["phone_country"], "United States")
        self.assertEqual(profile["dropdowns"]["visa_sponsorship"], "No")
        self.assertEqual(profile["dropdowns"]["acknowledgement"], "Yes")
        self.assertEqual(profile["dropdowns"]["gender"], "Decline To Self Identify")
        self.assertEqual(profile["dropdowns"]["race"], "I don't wish to answer")
        self.assertEqual(profile["dropdowns"]["disability_status"], "I do not want to answer")
        self.assertTrue(profile["files"]["resume"].endswith("resume.pdf"))


if __name__ == "__main__":
    unittest.main()
