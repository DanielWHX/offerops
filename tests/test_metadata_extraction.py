from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from offerops.metadata import extract_job_metadata
from offerops.parser import parse_job_page

FIXTURES = Path(__file__).parent / "fixtures"


class MetadataExtractionTests(unittest.TestCase):
    def test_extracts_workday_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://generac.wd5.myworkdayjobs.com/en-US/external/job/example",
            _fixture("workday.html"),
        )

        self.assertEqual(result.provider, "workday")
        self.assertEqual(result.adapter, "workday_adapter")
        self.assertEqual(result.job_title, "Computer Engineering Intern")
        self.assertEqual(result.company, "Generac")
        self.assertEqual(result.location, "Pewaukee, WI, USA")

    def test_extracts_greenhouse_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
            _fixture("greenhouse.html"),
        )

        self.assertEqual(result.provider, "greenhouse")
        self.assertEqual(result.adapter, "greenhouse_adapter")
        self.assertEqual(result.job_title, "Security Engineering Intern")
        self.assertEqual(result.company, "Bugcrowd")
        self.assertEqual(result.location, "Remote, USA")

    def test_extracts_lever_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://jobs.lever.co/example-ai/platform-engineering-intern",
            _fixture("lever.html"),
        )

        self.assertEqual(result.provider, "lever")
        self.assertEqual(result.adapter, "lever_adapter")
        self.assertEqual(result.job_title, "Platform Engineering Intern")
        self.assertEqual(result.company, "Example AI")
        self.assertEqual(result.location, "New York, NY")

    def test_extracts_ashby_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://jobs.ashbyhq.com/gen-digital/example/application",
            _fixture("ashby.html"),
        )

        self.assertEqual(result.provider, "ashby")
        self.assertEqual(result.adapter, "ashby_adapter")
        self.assertEqual(result.job_title, "Software Engineering Intern")
        self.assertEqual(result.company, "Gen Digital")
        self.assertEqual(result.location, "Tempe, AZ")

    def test_extracts_oracle_cloud_hcm_metadata_from_saved_html(self) -> None:
        result = parse_job_page(
            "https://ebwg.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/19501",
            _fixture("oracle_cloud_hcm.html"),
        )

        self.assertEqual(result.provider, "oracle_cloud_hcm")
        self.assertEqual(result.adapter, "oracle_cloud_hcm_adapter")
        self.assertEqual(result.job_title, "Software Engineer Intern")
        self.assertEqual(result.company, "Oracle")
        self.assertEqual(result.location, "Austin, TX")

    def test_unknown_returns_null_metadata_even_with_saved_html(self) -> None:
        result = parse_job_page("https://example.com/jobs/123", _fixture("unknown.html"))

        self.assertEqual(result.provider, "unknown")
        self.assertEqual(result.adapter, "unknown_adapter")
        self.assertIsNone(result.job_title)
        self.assertIsNone(result.company)
        self.assertIsNone(result.location)

    def test_cli_accepts_html_file(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "offerops",
                "parse",
                "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582",
                "--html-file",
                str(FIXTURES / "greenhouse.html"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["provider"], "greenhouse")
        self.assertEqual(payload["job_title"], "Security Engineering Intern")
        self.assertEqual(payload["company"], "Bugcrowd")
        self.assertEqual(payload["location"], "Remote, USA")

    def test_json_ld_graph_extracts_job_posting(self) -> None:
        metadata = extract_job_metadata(
            """
            <script type="application/ld+json">
              {
                "@graph": [
                  {"@type": "Organization", "name": "Example"},
                  {
                    "@type": "JobPosting",
                    "title": "Data Engineering Intern",
                    "hiringOrganization": {"name": "Graph Corp"},
                    "jobLocation": {
                      "address": {
                        "addressLocality": "Boston",
                        "addressRegion": "MA",
                        "addressCountry": "USA"
                      }
                    }
                  }
                ]
              }
            </script>
            """
        )

        self.assertEqual(metadata.job_title, "Data Engineering Intern")
        self.assertEqual(metadata.company, "Graph Corp")
        self.assertEqual(metadata.location, "Boston, MA, USA")

    def test_json_ld_list_extracts_job_posting_with_string_organization(self) -> None:
        metadata = extract_job_metadata(
            """
            <script type="application/ld+json">
              [
                {"@type": "BreadcrumbList"},
                {
                  "@type": ["Thing", "JobPosting"],
                  "title": "Platform Intern",
                  "hiringOrganization": "List Labs",
                  "jobLocation": "Remote"
                }
              ]
            </script>
            """
        )

        self.assertEqual(metadata.job_title, "Platform Intern")
        self.assertEqual(metadata.company, "List Labs")
        self.assertEqual(metadata.location, "Remote")

    def test_json_ld_multiple_locations_are_joined(self) -> None:
        metadata = extract_job_metadata(
            """
            <script type="application/ld+json">
              {
                "@type": "JobPosting",
                "title": "Backend Intern",
                "hiringOrganization": {"name": "Multi City Co"},
                "jobLocation": [
                  {
                    "address": {
                      "addressLocality": "Austin",
                      "addressRegion": "TX"
                    }
                  },
                  {
                    "address": {
                      "addressLocality": "Denver",
                      "addressRegion": "CO"
                    }
                  }
                ]
              }
            </script>
            """
        )

        self.assertEqual(metadata.job_title, "Backend Intern")
        self.assertEqual(metadata.company, "Multi City Co")
        self.assertEqual(metadata.location, "Austin, TX; Denver, CO")

    def test_missing_json_ld_optional_fields_return_null(self) -> None:
        metadata = extract_job_metadata(
            """
            <script type="application/ld+json">
              {
                "@type": "JobPosting",
                "title": "Frontend Intern"
              }
            </script>
            """
        )

        self.assertEqual(metadata.job_title, "Frontend Intern")
        self.assertIsNone(metadata.company)
        self.assertIsNone(metadata.location)

    def test_meta_fallback_uses_open_graph_and_job_location(self) -> None:
        metadata = extract_job_metadata(
            """
            <meta property="og:title" content="Design Intern at Pixel Works Careers">
            <meta name="job:location" content="New York, NY">
            """
        )

        self.assertEqual(metadata.job_title, "Design Intern")
        self.assertEqual(metadata.company, "Pixel Works")
        self.assertEqual(metadata.location, "New York, NY")

    def test_meta_fallback_uses_twitter_title_and_company(self) -> None:
        metadata = extract_job_metadata(
            """
            <meta name="twitter:title" content="QA Intern">
            <meta name="company" content="Quality Co">
            <meta name="location" content="Remote, Canada">
            """
        )

        self.assertEqual(metadata.job_title, "QA Intern")
        self.assertEqual(metadata.company, "Quality Co")
        self.assertEqual(metadata.location, "Remote, Canada")

    def test_document_title_fallback_splits_company(self) -> None:
        metadata = extract_job_metadata(
            "<title>Product Intern - Roadmap Inc Jobs</title>"
        )

        self.assertEqual(metadata.job_title, "Product Intern")
        self.assertEqual(metadata.company, "Roadmap Inc")
        self.assertIsNone(metadata.location)

    def test_body_visible_title_and_location_fallback(self) -> None:
        metadata = extract_job_metadata(
            """
            <main>
              <h1>Machine Learning Intern</h1>
              <p class="job-location">San Francisco, CA</p>
            </main>
            """
        )

        self.assertEqual(metadata.job_title, "Machine Learning Intern")
        self.assertIsNone(metadata.company)
        self.assertEqual(metadata.location, "San Francisco, CA")


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
