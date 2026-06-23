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

Return a small normalized object from the parser.

Example:

```json
{
  "provider": "workday",
  "adapter": "workday_adapter",
  "job_title": "Software Engineer Intern",
  "company": "Example Corp",
  "location": "Remote"
}
```

Verification:

- Unit test each provider result.

Out of scope:

- Confidence scores.
- Complex schema validator.

## 4. Create adapter skeletons

Labels: `type:feature`, `area:adapter`, `priority:p1`

Goal:

Create empty adapter entrypoints for Workday, Greenhouse, Lever, Ashby, and Unknown.

Scope:

- Each adapter exposes the same minimal interface.
- Unknown adapter should stop and ask for manual review.

Verification:

- Parser can route to an adapter name without running real form filling.

Out of scope:

- Real Workday filling.
- Browser automation.

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
