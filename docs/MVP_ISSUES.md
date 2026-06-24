# MVP Seed Issues

## 1. Detect ATS provider from one job URL

Labels: `type:feature`, `area:parser`, `priority:p0`, `good-first-slice`

Goal:

Detect whether a single job page belongs to Workday, Greenhouse, Lever, Ashby, or Unknown.

Scope:

- Input: one job URL.
- Output: provider name and adapter name.
- No batch URL list.

Verification:

- Add one fixture URL or saved HTML sample per provider.
- Run parser command and confirm expected provider.

Out of scope:

- Form filling.
- Agent fallback.
- Resume matching.

## 2. Extract minimal job metadata

Labels: `type:feature`, `area:parser`, `priority:p0`

Goal:

Extract title, company, and location from a detected job page using URL plus saved HTML input.

Scope:

- Input one job URL.
- Optionally pass `--html-file <path>` for deterministic metadata extraction.
- Return `job_title`, `company`, and `location`.
- Return null for missing values.

Verification:

- Add saved HTML fixtures for Workday, Greenhouse, Ashby, Oracle Cloud HCM, and Unknown.
- Add tests for provider, adapter, `job_title`, `company`, and `location`.

Out of scope:

- No live browser automation.
- No network fetch in tests.
- No full JD parsing.
- No salary extraction.
- No skill extraction.
- No Agent fallback.

## 3. Add parser result object

Labels: `type:feature`, `area:parser`, `priority:p1`

Goal:

Make the parser output model explicit and stable.

Scope:

- Add a dedicated `ParserResult` model for end-to-end parser output.
- Add a provider-only model for URL signature detection.
- Keep CLI JSON keys stable.

Example:

```json
{
  "provider": "workday",
  "adapter": "workday_adapter",
  "reason": "host:myworkdayjobs.com",
  "job_title": "Software Engineer Intern",
  "company": "Example Corp",
  "location": "Remote"
}
```

Verification:

- Unit test provider-only output.
- Unit test `ParserResult.to_dict()`.
- Keep existing provider detection and metadata extraction tests passing.

Out of scope:

- Confidence scores.
- Complex schema validator.
- New metadata fields.
- Live fetch/browser automation.

## 4. Create adapter skeletons

Labels: `type:feature`, `area:adapter`, `priority:p1`

Goal:

Create non-executing adapter skeletons for every provider currently detected by the parser.

Scope:

- Add a shared adapter interface.
- Add adapter entrypoints for Workday, Greenhouse, Lever, Ashby, Oracle Cloud HCM, and Unknown.
- Add an adapter registry that routes from `ParserResult.adapter`.
- Known provider adapters return `not_implemented`.
- Unknown adapter returns `manual_review_required`.

Verification:

- Add tests for adapter registry coverage.
- Add tests that each known provider routes to the expected adapter class.
- Add tests that unknown provider stops with manual review.
- Keep parser tests passing.

Out of scope:

- No real Workday filling.
- No browser automation.
- No network fetch.
- No Agent fallback.
- No form filling.
- No final submit behavior.

## 5. Add missing-field review plan

Labels: `type:feature`, `area:agent`, `priority:p2`

Goal:

Define how Agent fallback receives missing or failed fields after deterministic adapter execution.

Scope:

- Document input and output shape.
- No live LLM call yet.

Verification:

- Add a sample missing-field JSON fixture.

Out of scope:

- Actual LLM integration.
- Automatic final submit.
