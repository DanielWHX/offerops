# OfferOps Report Examples

These checked-in examples show current public report shapes for common OfferOps
paths. They are generated from local fixtures only and contain no real applicant
profile values or secrets.

## Examples

- `docs/examples/reports/greenhouse_plan_report.json`
  - Command: `python -m offerops plan https://job-boards.greenhouse.io/bugcrowd/jobs/8016582 --html-file tests/fixtures/greenhouse_application.html --profile-file tests/fixtures/applicant_profile.json`
  - Shows Greenhouse deterministic field preflight, fake-profile value sources,
    missing resume review, and final submit boundary.
- `docs/examples/reports/lever_plan_report.json`
  - Command: `python -m offerops plan https://jobs.lever.co/example-company/example-role --html-file tests/fixtures/lever.html`
  - Shows the current Lever adapter skeleton report. Lever browser demo routing
    is separate from this non-browser adapter plan.
- `docs/examples/reports/workday_stage_plan_report.json`
  - Command: `python -m offerops plan https://example.wd5.myworkdayjobs.com/job/example --html-file tests/fixtures/workday_stage_my_information.html`
  - Shows Workday read-only stage detection and descriptive
    `allowed_next_actions`.
- `docs/examples/reports/unknown_plan_report.json`
  - Command: `python -m offerops plan https://example.com/jobs/123 --html-file tests/fixtures/unknown.html`
  - Shows conservative manual review for unsupported or unknown providers.

## Safety

- Examples are report-only.
- They do not launch a browser.
- They do not upload files.
- They do not call a live LLM.
- They do not trigger, click, emulate, or approach final submit.

## Verification

`tests/test_report_examples.py` compares each example against current local CLI
output from the command above.
