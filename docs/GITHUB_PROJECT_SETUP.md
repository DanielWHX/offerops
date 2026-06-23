# GitHub Project Setup

## Project View

Create one GitHub Project named:

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

- `Status`: Backlog, Ready, Doing, Review, Done, Parking Lot
- `Area`: parser, adapter, agent, test, docs, infra
- `Priority`: p0, p1, p2
- `Slice Size`: small, medium, large

## Labels

Create labels from `.github/labels.yml` manually, or sync them later with a label sync tool.

## Milestones

Start with one milestone:

```text
MVP 0: Job Page Parser
```

Definition of done:

- Detects Workday, Greenhouse, Lever, Ashby, and Unknown.
- Extracts title, company, and location when available.
- Selects the adapter name.
- Includes fixture-based tests.
- Documents deterministic-first, AI-fallback architecture.

## Seed Issues

Use `docs/MVP_ISSUES.md` to create the first set of issues.
