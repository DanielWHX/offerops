# Agent Fallback Contract

Agent Fallback is a secondary review step. It receives only fields that the
deterministic adapter could not resolve or could not fill safely.

This slice defines the contract only. It does not call an LLM, drive a browser,
fill a form, or continue to final submit.

## Input Shape

Deterministic adapters should pass a `MissingFieldReviewPlan` with:

- `provider`: detected ATS provider.
- `adapter`: selected adapter name.
- `field_reviews`: fields that need Agent review.

Each `field_reviews` item contains:

- `field_name`: stable internal field id.
- `label`: visible form label when known.
- `issue`: `missing` or `deterministic_fill_failed`.
- `required`: whether the field blocks application progress.
- `attempted_value`: value the deterministic path tried, or `null`.
- `details`: short reason the deterministic path could not complete the field.

## Review Plan Fields

The same deterministic handoff plan records suggested review handling:

- `agent_review_action`: `infer_from_context`, `inspect_failed_fill`, or `ask_human`.
- `stop_for_human_review`: whether the workflow must stop for human review.
- `human_review_reasons`: stable stop reasons for reviewers and future UI.

The sample fixture is `tests/fixtures/missing_field_review_plan.json`.

## Required Review Stops

The workflow must stop for human review when:

- a required field is still missing after deterministic handling;
- deterministic fill failed for a field that affects the application payload;
- the application state is unknown or low-confidence;
- the workflow reaches any final-submit boundary.

Unknown or low-confidence state should use `unknown_application_state`.
Final-submit boundaries should use `final_submit_boundary`.
