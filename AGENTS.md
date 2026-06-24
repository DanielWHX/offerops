# Agent Workflow

This repository is built through small, auditable GitHub slices.

## Communication

- Keep updates short and concrete.
- Use project vocabulary from `CONTEXT.md`.
- State the current issue, current branch, and verification loop before editing.
- Do not continue past the agreed issue scope.

## Required Loop

1. Read `CONTEXT.md`, `docs/WORKFLOW.md`, the active issue, and relevant source/tests.
2. Confirm the tightest verification path.
3. Create or use a feature branch for one issue.
4. Make the smallest targeted change.
5. Run the verification path from the issue.
6. Remove temporary artifacts.
7. Open a PR with scope, verification, risks, and safety notes.
8. Wait for review before merging unless the repo owner explicitly authorizes merge.

## Safety Rules

- Never trigger, click, or emulate final submit.
- Do not add browser automation unless the issue explicitly includes it.
- Do not add live LLM calls unless the issue explicitly includes it.
- Do not add network fetches to tests.
- Unknown or low-confidence application state must stop for human review.

## PR Review Checklist

Reviewers should check only the highest-signal items:

- The PR stays inside the linked issue scope.
- The public behavior is verified through tests, fixtures, or a repeatable command.
- Safety boundaries are preserved.
- The change uses existing project vocabulary and module boundaries.
- Any remaining risk is written in the PR.

## Current Module Boundaries

- `parser`: detects ATS provider from one URL.
- `metadata`: extracts minimal title, company, and location from saved HTML.
- `models`: keeps stable result objects.
- `adapters`: selects a provider-specific, non-executing adapter plan.

Agent fallback is not implemented yet. Current work should only define its input/output contract unless a future issue explicitly expands the scope.
