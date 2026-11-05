# Verify the proposed approval, including empty findings

Before synthesis, draft a compact ledger of consequential assertions the review
itself will make: guards/flags, fallback behavior, response codes, coverage,
semantic parity and required rollout readiness. Give each claim an id, its text,
whether approval requires it, and pinned source/test/deployment evidence.
An HTTP status follows the actual adapter/request contract, not a framework's
generic default. A flag in an older revision is not evidence it still exists.

Send this ledger and the proposed conclusion to the existing skeptic with
`coverage_audit`, even with no findings or operational trigger. The skeptic
returns one coverage check per claim, plus `claim_checks` entries containing
`id`, `verdict` (`verified|contradicted|unsupported`) and an evidence-based `note`.
It rereads the anchor, not merely its presence. In fast mode do this inline.
Correct contradicted assertions; omit unsupported optional assertions. Missing
required proof uses the completion rules (`incomplete` without a known blocker),
not a manufactured source defect. Recheck consequential assertions added after
the skeptic pass; no second agent is required by default.

The delivery assessment records the final claims as `claims` entries with
`id`, `text`, `required`, `verdict` and `evidence` (list). Only verified claims
belong in the final report. A contradicted review sentence does not by itself
establish a code bug. This is distinct from verifying the author's PR claims.
