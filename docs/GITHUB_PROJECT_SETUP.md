# GitHub Project Setup

## Project View

Use the existing GitHub Project:

```text
OfferOps MVP
```

Use a board view with these columns:

```text
Backlog
Ready
Doing
Review
Done
Parking Lot
```

## Recommended Fields

- `Workflow Status`: Backlog, Ready, Doing, Review, Done, Parking Lot
- `Area`: parser, adapter, agent, test, docs, infra
- `Priority`: p0, p1, p2
- `Slice Size`: small, medium, large

## Labels

Create labels from `.github/labels.yml` manually, or sync them later with a label sync tool.

## Board Operating Rules

- GitHub issues and PRs are the execution source of truth.
- Each issue must have goal, scope, out of scope, verification, safety, and handoff format.
- Each contributor owns at most one `Doing` issue.
- PRs move their issue to `Review`; merged PRs move issues to `Done`.
- Main Agent reconciles board state after merges.

## Milestones

The original milestone was:

```text
MVP 0: Job Page Parser
```

Definition of done:

- Detects Workday, Greenhouse, Lever, Ashby, and Unknown.
- Extracts title, company, and location when available.
- Selects the adapter name.
- Includes fixture-based tests.
- Documents deterministic-first, AI-fallback architecture.

Current roadmap milestones:

- MVP 0: Job Page Parser.
- MVP 1: Provider Demo Surface.
- MVP 2: Workday Read-only Planning Surface.
- MVP 3: Unified Planning Report.

## Seed Issues

Use `docs/MVP_ISSUES.md` to create the first set of issues.

Use `docs/SPRINT_ROADMAP.md` for the current sprint plan and next issue batch.
