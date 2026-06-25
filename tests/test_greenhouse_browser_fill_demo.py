from __future__ import annotations

import importlib.util
import json
import os
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
        self.assertTrue(profile["files"]["resume"].endswith("fake_resume.pdf"))
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
                        "education": {
                            "current_school": "Example University",
                            "current_degree": "Master of Science",
                        },
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
        self.assertEqual(profile["education"]["school"], "Example University")
        self.assertEqual(profile["education"]["degree"], "Master of Science")
        self.assertTrue(profile["files"]["resume"].endswith("resume.pdf"))

    def test_load_profile_accepts_runtime_gpa_override(self) -> None:
        script = _load_script_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile_path = root / "profile.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "identity": {
                            "first_name": "Grace",
                            "last_name": "Hopper",
                        },
                    }
                ),
                encoding="utf-8",
            )
            previous = os.environ.get("OFFEROPS_GPA")
            os.environ["OFFEROPS_GPA"] = "3.68"
            try:
                profile = script.load_profile(profile_path)
            finally:
                if previous is None:
                    os.environ.pop("OFFEROPS_GPA", None)
                else:
                    os.environ["OFFEROPS_GPA"] = previous

        self.assertEqual(profile["custom_text"]["current_gpa"], "3.68")

    def test_final_report_groups_observable_outcomes(self) -> None:
        script = _load_script_module()

        report = script.build_final_report(
            [
                [
                    {
                        "field_key": "first_name",
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
                [
                    {
                        "field_key": "school",
                        "status": "needs_review",
                        "verified_value_matches": False,
                    },
                    {
                        "field_key": "degree",
                        "status": "filled",
                        "verified_value_matches": True,
                    },
                    {"field_key": "optional_field", "status": "not_present"},
                ],
            ],
            {"final_submit": "blocked_not_clicked"},
        )

        self.assertEqual(report["filled"], ["first_name", "resume", "degree"])
        self.assertEqual(report["missing_profile"], ["cover_letter"])
        self.assertEqual(report["needs_review"], ["linkedin_profile", "school"])
        self.assertTrue(report["final_submit_blocked"])

    def test_final_report_requires_verification_for_filled_status(self) -> None:
        script = _load_script_module()

        report = script.build_final_report(
            [
                [
                    {
                        "field_key": "location_city",
                        "status": "filled",
                        "verified_value_matches": False,
                    }
                ]
            ],
            {"final_submit": "not_blocked"},
        )

        self.assertEqual(report["filled"], [])
        self.assertEqual(report["needs_review"], ["location_city"])
        self.assertFalse(report["final_submit_blocked"])

    def test_location_search_terms_try_city_before_full_location(self) -> None:
        script = _load_script_module()

        self.assertEqual(
            script.location_search_terms("Champaign, Illinois, United States"),
            ["Champaign", "Champaign, Illinois, United States"],
        )

    def test_education_degree_search_uses_small_degree_token(self) -> None:
        script = _load_script_module()

        self.assertEqual(
            script.education_search_terms("degree", "Master of Science"),
            ["Master", "Master of Science"],
        )

    def test_education_school_search_adds_greenhouse_variant(self) -> None:
        script = _load_script_module()

        self.assertIn(
            "University of Illinois at Urbana-Champaign",
            script.education_search_terms(
                "school", "University of Illinois Urbana-Champaign"
            ),
        )
        self.assertIn(
            "university of illinois at urbana-champaign",
            script.education_match_tokens(
                "school", "University of Illinois Urbana-Champaign"
            ),
        )

    def test_fill_education_fields_reports_absent_and_missing_values(self) -> None:
        script = _load_script_module()
        original_visible = script.element_id_is_visible

        try:
            script.element_id_is_visible = (
                lambda page, field_id: field_id == "school--0"
            )

            result = script.fill_education_fields(object(), {})
        finally:
            script.element_id_is_visible = original_visible

        self.assertEqual(
            result,
            [
                {
                    "field_key": "school",
                    "status": "missing_profile_value",
                    "value_present": False,
                },
                {
                    "field_key": "degree",
                    "status": "not_present",
                    "value_present": False,
                },
            ],
        )

    def test_digits_only_normalizes_phone_formatting(self) -> None:
        script = _load_script_module()

        self.assertEqual(script.digits_only("+1 (415) 555-0100"), "14155550100")


if __name__ == "__main__":
    unittest.main()
