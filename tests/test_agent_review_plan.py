from __future__ import annotations

import json
import unittest
from pathlib import Path

from offerops.models import MissingFieldReviewItem, MissingFieldReviewPlan

FIXTURES = Path(__file__).parent / "fixtures"


class MissingFieldReviewPlanTests(unittest.TestCase):
    def test_review_item_dict_describes_one_missing_or_failed_field(self) -> None:
        item = MissingFieldReviewItem(
            field_name="phone_country_code",
            label="Country Phone Code",
            issue="missing",
            required=True,
            attempted_value=None,
            agent_review_action="infer_from_context",
            details="No deterministic profile value matched the field.",
        )

        self.assertEqual(
            item.to_dict(),
            {
                "field_name": "phone_country_code",
                "label": "Country Phone Code",
                "issue": "missing",
                "required": True,
                "attempted_value": None,
                "agent_review_action": "infer_from_context",
                "details": "No deterministic profile value matched the field.",
            },
        )

    def test_review_plan_matches_sample_json_fixture(self) -> None:
        fixture = json.loads(
            (FIXTURES / "missing_field_review_plan.json").read_text(encoding="utf-8")
        )

        plan = MissingFieldReviewPlan(
            provider="workday",
            adapter="workday_adapter",
            field_reviews=(
                MissingFieldReviewItem(
                    field_name="phone_country_code",
                    label="Country Phone Code",
                    issue="missing",
                    required=True,
                    attempted_value=None,
                    agent_review_action="infer_from_context",
                    details=(
                        "No deterministic profile value matched the Country Phone "
                        "Code field."
                    ),
                ),
                MissingFieldReviewItem(
                    field_name="resume_upload",
                    label="Resume",
                    issue="deterministic_fill_failed",
                    required=True,
                    attempted_value="resume.pdf",
                    agent_review_action="inspect_failed_fill",
                    details=(
                        "Deterministic upload did not confirm that the resume field "
                        "accepted the file."
                    ),
                ),
            ),
            stop_for_human_review=True,
            human_review_reasons=(
                "required_field_missing",
                "deterministic_fill_failed",
            ),
        )

        self.assertEqual(plan.to_dict(), fixture)

    def test_review_plan_makes_missing_and_failed_fields_observable(self) -> None:
        fixture = json.loads(
            (FIXTURES / "missing_field_review_plan.json").read_text(encoding="utf-8")
        )

        missing_fields = [
            field["field_name"]
            for field in fixture["field_reviews"]
            if field["issue"] == "missing"
        ]
        failed_fields = [
            field["field_name"]
            for field in fixture["field_reviews"]
            if field["issue"] == "deterministic_fill_failed"
        ]

        self.assertEqual(missing_fields, ["phone_country_code"])
        self.assertEqual(failed_fields, ["resume_upload"])
        self.assertTrue(fixture["stop_for_human_review"])
        self.assertIn("required_field_missing", fixture["human_review_reasons"])


if __name__ == "__main__":
    unittest.main()
