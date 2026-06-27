# Workday Read-only Safety Boundaries

## Goal

Workday support is currently a read-only planning surface.

The system may inspect a saved Workday page, classify the current application
stage, and return a planning report for human review. It must not operate the
browser, mutate the page, upload files, click navigation controls, or reach final
submit.

## Current Supported Surface

The current Workday implementation supports:

- Provider detection for `myworkdayjobs.com` URLs.
- Metadata extraction from saved HTML when available.
- Read-only stage detection with `detect_workday_stage(saved_content)`.

`detect_workday_stage` returns:

```json
{
  "stage": "my_information",
  "confidence": 0.75,
  "reason": "matched:my_information:my_information,legal_name"
}
```

The detector uses visible saved page text. It ignores `script` and `style`
content and returns `unknown` when the page has no strong Workday stage signal.

Sprint 1 owns exposing this detector through public planning reports. Until that
work is merged, contributors should treat the detector function and its fixtures
as the source of truth for Workday stage behavior.

## Stages

Known Workday stages:

- `account_gate`: sign in, create account, or already-have-account entry.
- `my_information`: legal name, contact information, phone, address.
- `my_experience`: resume/CV, upload prompt, work experience, education.
- `application_questions`: sponsorship, authorization, custom questions.
- `voluntary_disclosures`: gender, race/ethnicity, veteran, disability.
- `review`: review application or submit-boundary screen.
- `unknown`: no reliable saved-page signal.

## Human Review Rules

Workday planning must stop for human review when:

- `stage` is `unknown`.
- confidence is low or not backed by fixture coverage.
- visible page text conflicts with the detected stage.
- the next action would require browser control, file upload, credential entry,
  clicking Next, or clicking Submit.
- the page is at `review` or any final submit boundary.

Known fixture-backed stages currently return confidence at or above `0.7`.
Contributors should not treat that value as permission to execute browser
actions; it is only confidence in the read-only stage classification.

## Allowed Current Actions

Allowed in the current MVP:

- Read a saved HTML or saved text file.
- Detect provider and metadata.
- Run `detect_workday_stage(saved_content)`.
- Emit `stage`, `confidence`, and `reason`.
- Return `manual_review` or review items for unknown or unsafe next steps.
- Add fixtures and tests for saved-page reports.

Not allowed in the current MVP:

- Browser automation for Workday.
- Clicking Sign In, Create Account, Next, Continue, Review, or Submit.
- Uploading resume or attachments.
- Entering credentials or personal profile values into a Workday page.
- Live LLM fallback.
- Network fetches in tests.
- Final submit, submit emulation, or any path that makes final submit easier to
  trigger accidentally.

## Planned Report Boundary

The Workday planning report should remain observable and conservative.

Minimum read-only fields:

- `provider`
- `adapter`
- `status`
- `stage`
- `confidence`
- `reason`
- human-review flag or review reason for unsafe or unknown states

`allowed_next_actions` is a separate Sprint 1 issue. Until that contract is
merged, docs and code must not imply that OfferOps can advance a Workday
application stage.

## Verification Loop

Use the issue verification loop before opening a PR:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

For code or fixture changes, also run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m compileall -q src tests scripts
```

## Contributor Checklist

Before changing Workday behavior, confirm:

- The active GitHub issue explicitly includes the behavior.
- The change is read-only unless a future issue explicitly expands scope.
- Unknown or low-confidence state stops for human review.
- Fixtures cover every new report shape or stage signal.
- No test depends on network access.
- No code path can trigger final submit.
