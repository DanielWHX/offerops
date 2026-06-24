# OfferOps

Human-in-the-loop job application workflow assistant.

## MVP

The first milestone is the smallest useful Job Page Parser:

```text
Input one job URL
-> detect ATS provider
-> extract title/company/location when available
-> choose deterministic adapter
-> run adapter
-> let Agent fallback review missing or failed fields
-> stop before final submit
```

## Core Principle

Deterministic first, AI fallback.

AI should not be the main browser executor. It should only help with uncertain semantic tasks such as unclear labels, missing fields, and unknown page states.

## Current Slice

The parser now has two explicit model layers:

```text
ProviderDetection: URL -> provider/adapter/reason
ParserResult: provider/adapter/reason + job_title/company/location
```

The adapter layer is registered and non-executing:

```text
Greenhouse application HTML -> status=planned
Other known provider adapter -> status=not_implemented
Unknown adapter -> status=manual_review_required
```

The Agent Fallback contract is defined but not executed:

```text
MissingFieldReviewPlan -> field_reviews + stop_for_human_review
```

See `docs/AGENT_FALLBACK.md` and `tests/fixtures/missing_field_review_plan.json`.

## Parser Coverage

Current deterministic coverage:

| ATS Provider | URL Detection | Metadata Fixture | Adapter Registry |
| --- | --- | --- | --- |
| Workday | Real URL, shard subdomain, no-scheme URL | `tests/fixtures/workday.html` | `workday_adapter` |
| Greenhouse | `boards.greenhouse.io`, `job-boards.greenhouse.io` | `tests/fixtures/greenhouse.html` | `greenhouse_adapter` |
| Lever | `jobs.lever.co`, `/apply`, custom jobs subdomain | `tests/fixtures/lever.html` | `lever_adapter` |
| Ashby | `jobs.ashbyhq.com`, `/application` | `tests/fixtures/ashby.html` | `ashby_adapter` |
| Oracle Cloud HCM | `oraclecloud.com` Candidate Experience path | `tests/fixtures/oracle_cloud_hcm.html` | `oracle_cloud_hcm_adapter` |
| Unknown | Generic jobs URL, missing host | `tests/fixtures/unknown.html` | `unknown_adapter` |

Fixture standards:

- Use saved HTML only; tests must not fetch live network pages.
- Keep fixtures small, curated, and checked into `tests/fixtures/`.
- Assert public behavior through parser or CLI outputs.
- Unknown or low-confidence state must stop for human review.
- Do not add browser automation, form filling, or final submit behavior.

Detect the ATS provider from one job URL:

```bash
PYTHONPATH=src python3 -m offerops parse "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582"
```

Extract minimal metadata from a saved HTML fixture:

```bash
PYTHONPATH=src python3 -m offerops parse "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582" --html-file tests/fixtures/greenhouse.html
```

Example output:

```json
{
  "adapter": "greenhouse_adapter",
  "company": "Bugcrowd",
  "job_title": "Security Engineering Intern",
  "location": "Remote, USA",
  "provider": "greenhouse",
  "reason": "host:greenhouse.io"
}
```

Inspect adapter routing from Python:

```bash
PYTHONPATH=src python3 - <<'PY'
from offerops.adapters import plan_adapter
from offerops.parser import parse_job_page

result = parse_job_page("https://job-boards.greenhouse.io/bugcrowd/jobs/8016582")
print(plan_adapter(result).to_dict())
PY
```

Preview a Greenhouse fill plan from saved HTML and a fake profile:

```bash
PYTHONPATH=src python3 -m offerops plan "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582" --html-file tests/fixtures/greenhouse_application.html --profile-file tests/fixtures/applicant_profile.json
```

The preview reports value sources and missing required values, but never prints
profile values or fills the form.

Run a live planning demo against one real job page:

```bash
PYTHONPATH=src python3 -m offerops demo "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582"
```

The demo uses one HTTP GET, prints parser and adapter JSON, and never runs
browser automation, form filling, account creation, LLM calls, or final submit.

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Project Docs

- [Context](./CONTEXT.md)
- [Team Development Workflow](./docs/WORKFLOW.md)
- [Agent Workflow](./AGENTS.md)
- [GitHub Project Setup](./docs/GITHUB_PROJECT_SETUP.md)
- [MVP Seed Issues](./docs/MVP_ISSUES.md)

## Safety Rule

Never trigger, click, or emulate final submit.
