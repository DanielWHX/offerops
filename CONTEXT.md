# OfferOps Context

## Project Vocabulary

- `OfferOps`: human-in-the-loop job application workflow assistant.
- `Job Page Parser`: module that receives one job URL, reads the current page, and identifies the ATS provider plus minimal job metadata.
- `ATS Provider`: application system such as Workday, Greenhouse, Lever, Ashby, Oracle Cloud HCM, or Unknown.
- `ProviderDetection`: provider-only result from URL signature detection.
- `ParserResult`: normalized end-to-end parser output for provider, adapter, reason, and minimal metadata.
- `Adapter`: deterministic script for one ATS provider.
- `AdapterResult`: non-browser adapter planning result for adapter status and next handling.
- `planned`: AdapterResult status for a deterministic, non-executing provider preflight.
- `Fill Plan Preview`: non-executing adapter detail that maps detected fields to profile keys without printing values.
- `Greenhouse Browser Demo`: narrow Playwright demo that fills one Greenhouse application with fake profile data and stops before final submit.
- `Agent Fallback`: AI step used only for missing fields, unclear labels, or failed deterministic fills.
- `MissingFieldReviewPlan`: Agent Fallback contract for fields that are missing, failed deterministic fill, or require a human Review Stop.
- `Review Stop`: hard boundary before final submit. The system must stop for human review.
- `Contributor`: human or Agent owner for one GitHub issue at a time.
- `Reviewer`: person or Agent checking scope, verification, safety, and handoff quality.

## MVP Scope

The first MVP focuses on the smallest useful slice:

1. User provides one job URL.
2. Parser detects the ATS provider.
3. Parser extracts minimal metadata: title, company, location when available.
4. System selects the matching adapter.
5. Adapter reports whether deterministic preflight exists or manual review is required.
6. Agent checks missing or failed fields.
7. Workflow stops before final submit.

## Current Active Slice

The current browser-work slice is Greenhouse-only.

- Branch: `codex/greenhouse-browser-fill-demo`.
- Goal: run one real Greenhouse application page with fake applicant data, fill supported fields, attach fake files, capture a screenshot, and stop before final submit.
- Runner: `scripts/run_greenhouse_demo.sh`.
- Browser runtime: Playwright launching local Google Chrome with a dedicated profile directory.
- Environment: `.venv` already exists; `scripts/run_greenhouse_demo.sh` creates it if missing and installs `requirements-dev.txt`.
- Dependency file: `requirements-dev.txt` currently pins `playwright==1.60.0`.
- Demo script: `scripts/greenhouse_browser_fill_demo.py`.
- Fake profile: `tests/fixtures/browser_applicant_profile.json`.
- Fake files: `tests/fixtures/fake_resume.txt`, `tests/fixtures/fake_cover_letter.txt`.
- Screenshot output: `artifacts/greenhouse_fill_demo.png`.

Run command:

```bash
scripts/run_greenhouse_demo.sh
```

Verification loop:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m compileall -q src tests scripts
git diff --check
```

Known handoff notes:

- The demo must never click, trigger, or emulate final submit.
- The current target URL is `https://job-boards.greenhouse.io/bugcrowd/jobs/8016582`.
- A fresh live rerun filled basic text fields, attached resume, and filled cover letter through `Enter manually`.
- Greenhouse's current `Location (City)` autocomplete does not reliably accept scripted input; the demo reports `needs_review` instead of pretending it filled.
- If Codex escalated execution fails with a transport error, treat it as a tooling approval/runtime issue, not as a Greenhouse script failure.

## Non-Goals For MVP

- No batch application workflow.
- No automatic final submit.
- No full resume tailoring pipeline.
- No complex scoring dashboard.
- No generic browser agent as the primary executor.

## Engineering Principle

Deterministic first, AI fallback.

## Collaboration Principle

Repo docs and GitHub issues are the source of truth.

Every contributor and Agent follows the same loop:

```text
Issue -> Branch -> Verification -> PR -> Review -> Merge
```
