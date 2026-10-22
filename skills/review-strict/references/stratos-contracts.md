# When the reviewed repository uses Stratos

Read the repository's own contract files at the pinned review head. If rules
declare an external contract directory, resolve it by the repo's supported
mechanism and record its provenance/version; do not silently read a different
installed release. These are pointers, not copies of evolving Stratos policy:

- `contract/review-rubric.md`: review dimensions, severity, disposition, and
  applicable adjudication obligations. Discharge the applicable dimensions within
  the existing lenses; do not require another agent per dimension.
- `contract/spec-review-rubric.md`, for spec review: discharge every applicable
  obligation in the coverage ledger, including assertion strength, consumer
  tracing, claim refutation, citation content, and existing-test reuse. Use the
  current file's complete set, not this orientation list as a frozen checklist.
- `contract/rubric.md` and `contract/test-quality-rules.md`, when present:
  test value and quality, together with applicable scoped testing rules.
- The ticket's `.test-intent-contract-version` and the governing Test Intent
  policy pointed to by the repo: distinguish shadow from governing obligations.
  A current opt-in does not reinterpret tickets minted under an older version.
  Trace each applicable matrix row to the failure it protects and its existing
  or proposed assertion. Check that a plausible broken implementation would fail
  it. Do not require a new test per AC when existing coverage or an authorized
  non-test disposition satisfies the governing contract.

For assertions on predicates, expressions, or guards, work through concrete
green-but-broken mutations and name the stronger assertion or existing test.
Follow the rubric's required exercise size and valid clean/vacuous discharges;
do not invent mutations merely to fill a quota. For process/environment probes,
prove the failure injection or mode was activated: a healthy and sabotaged arm
that take the same path cannot demonstrate the promised failure behavior.

The review report is advisory input to the normal Stratos lifecycle. It does not
mint a Sentinel PASS, review receipt, merge authority, or an automatic pre-Forge
gate. Run these skills when requested; do not insert a new mandatory review into
`/create-task`, `/execute-task`, or `/orchestrate`.
