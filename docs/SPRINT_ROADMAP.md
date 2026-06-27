# OfferOps Sprint Roadmap

## Project Goal

OfferOps is a human-in-the-loop job application workflow assistant.

Given one job URL, the system should detect the ATS provider, understand the job
page, generate a safe application plan, and assist only inside explicit provider
boundaries. It must always stop at `Review Stop`, `manual_review`, or
`unsupported`; it must never trigger, click, or emulate final submit.

## Product Direction

- Deterministic first: parser, adapter, fixture, and provider-specific logic own
  behavior that can be tested directly.
- AI fallback later: AI only handles missing fields, unclear labels, failed
  deterministic fills, or unknown state reasoning.
- Human-in-the-loop: low-confidence or unknown states stop for review.
- Provider-by-provider: Greenhouse and Lever demos first, then Workday staged
  planning; no generic browser agent in the current MVP.

## Completed Milestones

### MVP 0: Job Page Parser

- Detect ATS provider from one URL.
- Extract minimal metadata: title, company, and location.
- Normalize parser output through `ProviderDetection` and `ParserResult`.
- Route providers to deterministic adapter skeletons.
- Define `MissingFieldReviewPlan` as the Agent fallback contract.
- Add fixture coverage and minimal Python CI.

### MVP 1: Provider Demo Surface

- Add Greenhouse application preflight and fill plan preview.
- Add Greenhouse browser demo with final submit guard.
- Add Lever browser demo with final submit guard.
- Add unified browser demo router for Greenhouse and Lever.
- Return `manual_review` or `unsupported` for providers without safe browser demos.

### MVP 2 Start: Workday Read-only Surface

- Add read-only Workday saved-page stage detector.
- Cover `account_gate`, `my_information`, `my_experience`,
  `application_questions`, `voluntary_disclosures`, `review`, and `unknown`.
- Keep detector heuristic and conservative; low-signal content returns `unknown`.

## Sprint 0: Project Control Reset

Goal: make the GitHub Project, docs, and local checkout trustworthy again.

Tracking issue:

- #41 `Reset OfferOps project control surface`

Tasks:

1. Reconcile `OfferOps MVP` board after browser and Workday slices.
2. Refresh project docs for MVP 1 completion and Workday read-only start.
3. Create Sprint 1 Workday planning issues.
4. Sync local main and preserve existing docs edits.

Done criteria:

- The `OfferOps MVP` Project board includes the recent completed slices:
  #31, #33, #34, #35, #37, #39 and PR #32, #36, #38, #40.
- All merged or closed slices are in `Workflow Status=Done`.
- README, CONTEXT, and project docs reflect the post-PR #40 state.
- Sprint 1 issues are created and placed in `Ready`.

## Sprint 1: Workday Read-only Planning Surface

Goal: make the Workday detector visible through public planning reports.

Ready issues:

1. #42 `Expose Workday stage detection in adapter plan`
2. #43 `Add Workday allowed_next_actions contract`
3. #44 `Add Workday stage report JSON fixtures`
4. #45 `Document Workday read-only safety boundaries`

Safety reference:

- `docs/WORKDAY_READ_ONLY_SAFETY.md`

Done criteria:

- `offerops plan <workday-url> --html-file saved.html` can report
  `stage`, `confidence`, and `reason`.
- `unknown` and low-confidence states stop for human review.
- No browser automation, clicking, upload, live LLM call, or final submit path.

## Sprint 2: Workday Deterministic Preview

Goal: add preview-only Workday stage behavior, one stage per issue.

Backlog issues:

1. #46 `Add Workday account_gate plan preview`
2. #47 `Add Workday my_information fill plan preview`
3. #48 `Add Workday my_experience upload validation contract`
4. #49 `Add Workday application_questions review item extraction`

Done criteria:

- Each stage returns a plan or review items only.
- No Next click, upload execution, browser control, or final submit.
- Each stage is verified through fixtures and public report output.

## Sprint 3: Unified Planning Report

Goal: make one product-facing report shape for supported and unsupported paths.

Backlog issues:

1. #50 `Unify parser metadata adapter route and Workday stage report`
2. #51 `Standardize safety block across CLI reports`
3. #52 `Add report examples for Greenhouse Lever Workday Unknown`
4. #53 `Document MVP-2 user flow`

Done criteria:

- One command returns provider, metadata, adapter plan, browser route or Workday
  stage report, and safety block.
- Greenhouse and Lever can route to demos.
- Workday returns a read-only stage report.
- Unknown, Ashby, and Oracle Cloud HCM remain conservative.

## Operating Model

GitHub Project `OfferOps MVP` is the execution source of truth.

Main Agent responsibilities:

- Keep issue scope, architecture boundaries, verification, and safety clear.
- Assign one `Ready` issue to a Contributor Agent at a time.
- Review PRs and merge only after owner authorization.
- Reconcile Project board state after merges.

Contributor Agent responsibilities:

- Work on one issue, one branch, one verification loop, and one PR.
- Do not merge.
- Report with `Status`, `Changed`, `Verified`, `Risk`, and `Next`.

Standard issue shape:

- `Goal`
- `Scope`
- `Out of scope`
- `Verification`
- `Safety`
- `Handoff format`
