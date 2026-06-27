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
- `Lever Browser Demo`: narrow Playwright demo that fills one Lever application with fake profile data and stops before final submit.
- `Browser Demo Router`: URL-based command that routes supported providers to their provider-specific browser demo and returns manual review or unsupported for the rest.
- `WorkdayStageDetection`: read-only Workday saved-page classifier that returns stage, confidence, and reason.
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

## Current State

The current active slice is Sprint 0 project control reset.

- MVP 0: Job Page Parser is complete.
- MVP 1: Greenhouse and Lever browser demos plus the unified browser demo router are complete.
- MVP 2 has started with the Workday read-only stage detector.
- Issue #41: `Reset OfferOps project control surface`.
- Open Ready issues for Sprint 1: #42, #43, #44, #45.
- Backlog issues for later Workday preview and unified report work: #46 through #53.
- Project board: `OfferOps MVP`.

Current implementation surfaces:

- Parser CLI: `python -m offerops parse <url> [--html-file saved.html]`.
- Adapter plan CLI: `python -m offerops plan <url> [--html-file saved.html] [--profile-file fake_profile.json]`.
- Live planning demo: `python -m offerops demo <url>` uses one HTTP GET and does not control a browser.
- Browser demo router: `scripts/run_browser_demo.sh <url> [--dry-run]`.
- Greenhouse demo runner: `scripts/run_greenhouse_demo.sh`.
- Lever demo runner: `scripts/run_lever_demo.sh`.
- Workday read-only detector: `detect_workday_stage(saved_content)`.

Standard verification loop:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m compileall -q src tests scripts
git diff --check
```

Known handoff notes for browser demos:

- The demo must never click, trigger, or emulate final submit.
- If Codex escalated execution fails with a transport error, treat it as a tooling approval/runtime issue, not as a script failure.

## Overall Product Direction

OfferOps is a human-in-the-loop job application workflow assistant.

The long-term flow:

```text
one job URL -> provider detection -> metadata extraction -> deterministic plan
-> provider-specific demo or stage report -> human review -> no final submit
```

Product layers:

1. Planning Surface: URL, provider, metadata, adapter plan, manual review.
2. Provider Demo Surface: Greenhouse and Lever safe browser demos plus router.
3. Workday Staged Surface: read-only stage detection, stage reports, allowed next actions, then deterministic previews.
4. Unified Product Surface: one stable JSON report for provider, metadata, route, Workday stage, and safety.

## Next Recommended Slice

After Sprint 0 merges, Sprint 1 should expose Workday read-only planning through public reports.

Immediate work:

- #42: expose Workday stage detection in adapter plan.
- #43: add Workday `allowed_next_actions` contract.
- #44: add Workday stage report JSON fixtures.
- #45: document Workday read-only safety boundaries.
- Keep all Workday work read-only until a future issue explicitly expands scope.

## Non-Goals For MVP

- No batch application workflow.
- No automatic final submit.
- No full resume tailoring pipeline.
- No complex scoring dashboard.
- No generic browser agent as the primary executor.

## Engineering Principle

Deterministic first, AI fallback.

## Future Workday Direction

This is an initial direction, not a frozen final architecture. Future agents may
revise it when real Workday testing exposes better boundaries or failure modes.
Changes should stay evidence-driven and be recorded through GitHub issues or PRs.

Workday should be implemented as a staged adapter, not as a generic free-form
browser agent.

Workday remains one ATS provider. Its browser automation should be split into
stage handlers:

1. `account_gate`: login, create account, already signed in.
2. `my_information`: name, address, phone, email.
3. `my_experience`: resume upload, work experience, education.
4. `application_questions`: sponsorship, location, availability, custom questions.
5. `voluntary_disclosures`: gender, race, veteran, disability.
6. `review`: summarize filled, missing, and needs-review fields.
7. `final_submit_boundary`: always stop.

The intended control flow:

```text
detect current stage -> run deterministic stage handler -> validate page state
-> emit final_report and allowed_next_actions -> human/Agent coordinator may
choose Continue/Next only when allowed -> stop at Review or final submit boundary
```

The AI/Agent role is coordination and unknown-field reasoning. It should call
deterministic handlers and inspect reports; it should not freely click around or
trigger final submit.

## Collaboration Principle

Repo docs and GitHub issues are the source of truth.

Every contributor and Agent follows the same loop:

```text
Issue -> Branch -> Verification -> PR -> Review -> Merge
```
