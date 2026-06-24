from __future__ import annotations

import unittest

from offerops.models import ParserResult, ProviderDetection


class ParserModelTests(unittest.TestCase):
    def test_provider_detection_dict_is_provider_only(self) -> None:
        detection = ProviderDetection(
            provider="greenhouse",
            adapter="greenhouse_adapter",
            reason="host:greenhouse.io",
        )

        self.assertEqual(
            detection.to_dict(),
            {
                "provider": "greenhouse",
                "adapter": "greenhouse_adapter",
                "reason": "host:greenhouse.io",
            },
        )

    def test_provider_detection_converts_to_parser_result(self) -> None:
        detection = ProviderDetection(
            provider="greenhouse",
            adapter="greenhouse_adapter",
            reason="host:greenhouse.io",
        )

        result = detection.to_result(
            job_title="Security Engineering Intern",
            company="Bugcrowd",
            location="Remote, USA",
        )

        self.assertIsInstance(result, ParserResult)
        self.assertEqual(result.provider, "greenhouse")
        self.assertEqual(result.job_title, "Security Engineering Intern")

    def test_parser_result_dict_keeps_cli_json_shape(self) -> None:
        result = ParserResult(
            provider="workday",
            adapter="workday_adapter",
            reason="host:myworkdayjobs.com",
            job_title="Computer Engineering Intern",
            company="Generac",
            location="Pewaukee, WI, USA",
        )

        self.assertEqual(
            result.to_dict(),
            {
                "provider": "workday",
                "adapter": "workday_adapter",
                "reason": "host:myworkdayjobs.com",
                "job_title": "Computer Engineering Intern",
                "company": "Generac",
                "location": "Pewaukee, WI, USA",
            },
        )


if __name__ == "__main__":
    unittest.main()
