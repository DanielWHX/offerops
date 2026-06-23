# OfferOps

Human-in-the-loop job application workflow assistant.

## MVP

The first milestone is the smallest useful Job Page Parser:

```text
Input one job URL
-> detect ATS provider
-> extract title/company/location when available
-> choose deterministic adapter
-> run adapter
-> let Agent fallback review missing or failed fields
-> stop before final submit
```

## Core Principle

Deterministic first, AI fallback.

AI should not be the main browser executor. It should only help with uncertain semantic tasks such as unclear labels, missing fields, and unknown page states.

## Project Docs

- [Context](./CONTEXT.md)
- [Solo Developer Workflow](./docs/WORKFLOW.md)
- [GitHub Project Setup](./docs/GITHUB_PROJECT_SETUP.md)
- [MVP Seed Issues](./docs/MVP_ISSUES.md)

## Safety Rule

Never trigger, click, or emulate final submit.
