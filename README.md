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

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Project Docs

- [Context](./CONTEXT.md)
- [Solo Developer Workflow](./docs/WORKFLOW.md)
- [GitHub Project Setup](./docs/GITHUB_PROJECT_SETUP.md)
- [MVP Seed Issues](./docs/MVP_ISSUES.md)

## Safety Rule

Never trigger, click, or emulate final submit.
