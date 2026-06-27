from __future__ import annotations

from pathlib import Path
import unittest

from offerops.adapters.workday import detect_workday_stage

FIXTURES = Path(__file__).parent / "fixtures"


class WorkdayStageDetectorTests(unittest.TestCase):
    def test_detects_saved_workday_stage_fixtures(self) -> None:
        cases = [
            ("workday_stage_account_gate.html", "account_gate", "sign_in"),
            ("workday_stage_my_information.html", "my_information", "my_information"),
            ("workday_stage_my_experience.html", "my_experience", "my_experience"),
            (
                "workday_stage_application_questions.html",
                "application_questions",
                "application_questions",
            ),
            (
                "workday_stage_voluntary_disclosures.html",
                "voluntary_disclosures",
                "voluntary_disclosures",
            ),
            ("workday_stage_review.html", "review", "review"),
        ]

        for fixture_name, expected_stage, expected_reason in cases:
            with self.subTest(fixture_name=fixture_name):
                result = detect_workday_stage(_fixture(fixture_name))

                self.assertEqual(result.stage, expected_stage)
                self.assertGreaterEqual(result.confidence, 0.7)
                self.assertIn(expected_reason, result.reason)
                self.assertEqual(
                    result.to_dict(),
                    {
                        "stage": expected_stage,
                        "confidence": result.confidence,
                        "reason": result.reason,
                    },
                )

    def test_detects_stage_from_saved_text_without_html(self) -> None:
        result = detect_workday_stage(
            """
            Application Questions
            Are you legally authorized to work in the United States?
            Will you now or in the future require sponsorship?
            """
        )

        self.assertEqual(result.stage, "application_questions")
        self.assertGreaterEqual(result.confidence, 0.7)

    def test_hidden_script_and_style_strings_do_not_override_visible_stage(self) -> None:
        result = detect_workday_stage(
            """
            <!doctype html>
            <html>
              <head>
                <script>Review Your Application Submit Application</script>
                <style>.hidden::before { content: "Review Your Application"; }</style>
              </head>
              <body>
                <main>
                  <h1>My Information</h1>
                  <label>Legal Name</label>
                  <label>Country Phone Code</label>
                </main>
              </body>
            </html>
            """
        )

        self.assertEqual(result.stage, "my_information")
        self.assertIn("my_information", result.reason)

    def test_low_signal_content_returns_unknown_for_human_review(self) -> None:
        result = detect_workday_stage(_fixture("workday_stage_unknown.html"))

        self.assertEqual(result.stage, "unknown")
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.reason, "no_workday_stage_signal")


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
