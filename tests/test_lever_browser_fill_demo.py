from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
SCRIPT = ROOT / "scripts" / "lever_browser_fill_demo.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("lever_browser_fill_demo", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load lever browser fill demo script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LeverBrowserFillDemoTests(unittest.TestCase):
    def test_load_profile_reuses_browser_profile_shape(self) -> None:
        script = _load_script_module()

        profile = script.load_profile(FIXTURES / "browser_applicant_profile.json")

        self.assertEqual(profile["text"]["first_name"], "Ada")
        self.assertEqual(profile["text"]["last_name"], "Lovelace")
        self.assertEqual(profile["text"]["email"], "ada@example.test")
        self.assertTrue(profile["files"]["resume"].endswith("fake_resume.pdf"))

    def test_final_report_groups_lever_outcomes(self) -> None:
        script = _load_script_module()

        report = script.build_final_report(
            [
                [
                    {
                        "field_key": "full_name",
                        "status": "filled",
                        "verified_value_matches": True,
                    },
                    {
                        "field_key": "linkedin_profile",
                        "status": "not_found",
                        "verified_value_matches": False,
                    },
                ],
                [
                    {
                        "field_key": "resume",
                        "status": "attached",
                        "verified_file_visible": True,
                    },
                    {"field_key": "cover_letter", "status": "missing_file"},
                ],
            ],
            {"final_submit": "blocked_not_clicked"},
        )

        self.assertEqual(report["filled"], ["full_name", "resume"])
        self.assertEqual(report["missing_profile"], ["cover_letter"])
        self.assertEqual(report["needs_review"], ["linkedin_profile"])
        self.assertTrue(report["final_submit_blocked"])

    def test_required_review_fields_ignore_handled_labels(self) -> None:
        script = _load_script_module()

        fields = script.required_review_fields_from_labels(
            [
                "Full name *",
                "Email *",
                "Phone *",
                "Are you legally authorized to work in the U.S.? *",
                "Are you legally authorized to work in the U.S.? *",
            ]
        )

        self.assertEqual(
            fields,
            [
                {
                    "field_key": "required:are_you_legally_authorized_to_work_in_the_u_s",
                    "label": "Are you legally authorized to work in the U.S.?",
                    "status": "needs_review",
                    "value_present": False,
                }
            ],
        )

    def test_final_report_includes_required_review_fields(self) -> None:
        script = _load_script_module()

        review_fields = script.required_review_fields_from_labels(
            ["I certify and agree *"]
        )
        report = script.build_final_report(
            [review_fields],
            {"final_submit": "blocked_not_clicked"},
        )

        self.assertEqual(report["needs_review"], ["required:i_certify_and_agree"])

    def test_final_report_keeps_unverified_filled_fields_in_review(self) -> None:
        script = _load_script_module()

        report = script.build_final_report(
            [
                [
                    {
                        "field_key": "location_city",
                        "status": "needs_review",
                        "verified_value_matches": False,
                    }
                ]
            ],
            {"final_submit": "blocked_not_clicked"},
        )

        self.assertEqual(report["filled"], [])
        self.assertEqual(report["needs_review"], ["location_city"])


if __name__ == "__main__":
    unittest.main()
