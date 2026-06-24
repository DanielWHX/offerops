# Contributor Onboarding

This page is the fastest path for a new contributor to become productive.

## Project In One Minute

OfferOps is a human-in-the-loop job application workflow assistant.

The current MVP is intentionally small:

```text
One job URL
-> detect ATS provider
-> extract title/company/location from saved HTML when available
-> select a deterministic adapter skeleton
-> define what Agent fallback should review
-> stop before final submit
```

The core rule is deterministic first, AI fallback second.

## Read First

Read these files in order:

1. `CONTEXT.md`
2. `docs/WORKFLOW.md`
3. `AGENTS.md`
4. `README.md`
5. The active GitHub issue

Do not start from old chat logs. The repo and GitHub issues are the source of truth.

## Current Architecture

```text
src/offerops/parser.py
  URL -> ProviderDetection -> ParserResult

src/offerops/metadata.py
  saved HTML -> title/company/location

src/offerops/models.py
  stable data objects and JSON shape

src/offerops/adapters/
  ParserResult.adapter -> non-executing adapter plan

tests/
  fixture-based verification, no network dependency
```

## Safe First Tasks

Good first tasks are small and fixture-driven:

- Add one saved ATS HTML fixture.
- Add one metadata extraction regression test.
- Add one provider URL detection case.
- Improve docs for an existing module boundary.
- Extend an adapter skeleton only when the issue explicitly asks for it.

Avoid as first tasks:

- Browser automation.
- Live LLM integration.
- Auto-submit behavior.
- Large refactors.
- Batch application workflows.

## How To Take Work

1. Pick a GitHub issue in `Ready`.
2. Confirm the issue has Goal, Scope, Verification, and Out of Scope.
3. Move it to `Doing`.
4. Create a branch from `main`.
5. Keep the PR limited to that issue.
6. Ask for review before merge.

## Verification Commands

Run the full test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run parser smoke tests:

```bash
PYTHONPATH=src python3 -m offerops parse "https://job-boards.greenhouse.io/bugcrowd/jobs/8016582" --html-file tests/fixtures/greenhouse.html
```

Check formatting-sensitive whitespace:

```bash
git diff --check
```

## Handoff Format

Use this format in issue or PR comments:

```text
Status: ready for review
Changed: added Greenhouse fixture metadata coverage
Verified: PYTHONPATH=src python3 -m unittest discover -s tests -v
Next: reviewer checks scope and safety
Risk: none known
```

## Safety Boundary

Never trigger, click, or emulate final submit.

If a page state is unknown, ambiguous, or low-confidence, stop and require human review.
