# Solo Developer Workflow

## Operating Rule

Keep GitHub as the source of truth for daily engineering progress.

Notion can store long-term ideas, but daily execution should leave traces in GitHub:

```text
Issue -> Branch -> Commit -> Test/Demo -> PR -> Merge
```

## Kanban Columns

- `Backlog`: good ideas, not scheduled.
- `Ready`: small enough to start this week.
- `Doing`: currently active. Limit to 1 or 2.
- `Review`: implementation done, waiting for self-review or cleanup.
- `Done`: merged.
- `Parking Lot`: intentionally paused.

## Daily Loop

1. Pick one `Ready` issue.
2. Create a branch from the issue.
3. Build one vertical slice.
4. Run the verification path from the issue.
5. Open a PR, even for solo work.
6. Self-review the diff.
7. Merge and close the issue.

## Issue Standard

Every issue should answer:

- What user-visible behavior changes?
- What is explicitly in scope?
- How will it be verified?
- What is out of scope?

## PR Standard

Every PR should include:

- What changed.
- How it was verified.
- Any remaining risk.

## Branch Naming

Use short names:

```text
feat/provider-detect
feat/workday-adapter-skeleton
fix/lever-title-parser
docs/mvp-scope
test/job-page-fixtures
```

## Commit Style

Prefer small commits with clear verbs:

```text
feat: detect greenhouse job pages
test: add workday job page fixture
docs: define mvp workflow
fix: avoid treating unknown pages as workday
```

## Weekly Review

Once per week:

1. Close stale ideas or move them to `Parking Lot`.
2. Pick 3 to 5 issues for the next week.
3. Update README or project status.
4. Make sure the demo still runs.
