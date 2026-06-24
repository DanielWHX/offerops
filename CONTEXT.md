# OfferOps Context

## Project Vocabulary

- `OfferOps`: human-in-the-loop job application workflow assistant.
- `Job Page Parser`: module that receives one job URL, reads the current page, and identifies the ATS provider plus minimal job metadata.
- `ATS Provider`: application system such as Workday, Greenhouse, Lever, Ashby, Oracle Cloud HCM, or Unknown.
- `ProviderDetection`: provider-only result from URL signature detection.
- `ParserResult`: normalized end-to-end parser output for provider, adapter, reason, and minimal metadata.
- `Adapter`: deterministic script for one ATS provider.
- `AdapterResult`: non-browser adapter planning result for adapter status and next handling.
- `Agent Fallback`: AI step used only for missing fields, unclear labels, or failed deterministic fills.
- `Review Stop`: hard boundary before final submit. The system must stop for human review.
- `Contributor`: human or Agent owner for one GitHub issue at a time.
- `Reviewer`: person or Agent checking scope, verification, safety, and handoff quality.

## MVP Scope

The first MVP focuses on the smallest useful slice:

1. User provides one job URL.
2. Parser detects the ATS provider.
3. Parser extracts minimal metadata: title, company, location when available.
4. System selects the matching adapter skeleton.
5. Adapter reports whether deterministic steps exist or manual review is required.
6. Agent checks missing or failed fields.
7. Workflow stops before final submit.

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
