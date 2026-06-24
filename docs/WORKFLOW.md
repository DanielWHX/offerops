# Team Development Workflow

## Operating Rule

Keep GitHub as the source of truth for engineering progress.

Notion can store long-term ideas, but daily execution should leave traces in GitHub:

```text
Issue -> Branch -> Commit -> Test/Demo -> PR -> Merge
```

## Roles

- `Tech Lead`: owns MVP scope, module boundaries, and final architecture calls.
- `Contributor`: owns one issue at a time and delivers a verified vertical slice.
- `Reviewer`: checks scope, verification, safety, and risk before merge.
- `Agent`: follows `AGENTS.md` and works only inside the active issue scope.

The same person can play multiple roles, but every PR must have an author and a reviewer.

## Kanban Columns

- `Backlog`: good ideas, not scheduled.
- `Ready`: small enough to start this week.
- `Doing`: currently active. Each contributor should own at most one issue.
- `Review`: implementation done, waiting for review or cleanup.
- `Done`: merged.
- `Parking Lot`: intentionally paused.

## Contributor Loop

1. Pick one `Ready` issue.
2. Comment on the issue if ownership is not obvious.
3. Create a branch from the issue.
4. Build one vertical slice.
5. Run the verification path from the issue.
6. Open a PR.
7. Request review.
8. Merge only after review approval or explicit owner authorization.

## Agent Loop

Agents must follow the same loop as contributors:

```text
Read context -> state scope -> edit -> verify -> PR -> review
```

Before editing, an agent should read:

- `AGENTS.md`
- `CONTEXT.md`
- this workflow
- the active GitHub issue
- relevant source files and tests

## Issue Standard

Every issue should answer:

- What user-visible behavior changes?
- What is explicitly in scope?
- How will it be verified?
- What is out of scope?
- Which module boundary owns the change?
- What should reviewers pay special attention to?

## PR Standard

Every PR should include:

- What changed.
- How it was verified.
- Any remaining risk.
- Linked issue.
- Safety statement.
- Reviewer checklist.

## Branch Naming

Use short names:

```text
codex/provider-detect
codex/workday-adapter-skeleton
codex/lever-title-parser
codex/mvp-scope
codex/job-page-fixtures
```

## Commit Style

Prefer small commits with clear verbs:

```text
feat: detect greenhouse job pages
test: add workday job page fixture
docs: define mvp workflow
fix: avoid treating unknown pages as workday
```

## Review Standard

Reviewers should focus on:

- Scope: the PR only does what the issue says.
- Verification: tests, fixtures, or commands prove the behavior.
- Safety: no final submit, no unintended browser automation, no live LLM call.
- Boundaries: parser, metadata, models, adapters, and agent contracts stay separate.
- Handoff: future contributors can understand what changed from the PR alone.

## Daily Handoff

When stopping work, leave one short issue or PR comment:

```text
Status: in progress / blocked / ready for review
Changed: ...
Verified: ...
Next: ...
Risk: ...
```

## Weekly Review

Once per week:

1. Close stale ideas or move them to `Parking Lot`.
2. Pick 3 to 5 issues for the next week.
3. Update README or project status.
4. Make sure the demo still runs.
