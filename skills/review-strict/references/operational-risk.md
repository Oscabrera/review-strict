# Operational consequences of retries, deadlines, and concurrency

Apply this check when the diff changes retries, timeouts/deadlines, blocking
waits, fan-out, or concurrency limits, or declares a related operational risk.
Otherwise record `not-applicable` with the reason in the completion ledger;
do not demand an operational exercise for unrelated changes.

## Evidence and ownership

Use the frozen subject from `review-integrity.md`. Read relevant unchanged
callers, configuration, and dependency implementation/documentation as well as
the diff. Pin dependency facts to the version and handler actually used; a
lockfile or vendor source needed for this check is relevant context, not noise.

- **Correctness:** distinguish fast connection failures, timeout exhaustion,
  partial responses, HTTP errors, and cancellation where relevant. Verify the
  actual exception hierarchy/handler semantics; “no response” does not prove a
  fast network failure, and idempotency does not prove a retry is affordable.
  Establish the budget before and after the change: per-attempt vs total,
  pauses, elapsed time, timeout zero/unset, and defaults inherited from the
  runtime. Check whether cancellation releases or leaves work running.
- **Architecture:** trace affected production callers to an entry point or
  work unit. Account for sequential loops, nested retries, and parallel fan-out.
  Calculate the reachable worst-case time and number of downstream attempts,
  and identify resources held while waiting (workers, connections, locks).
  For serial work, sum attempts and waits, then account for caller repetitions;
  parallel work needs a critical-path calculation, not a serial sum. Cite the
  source of each input and distinguish calculated bounds from measured latency.
  Describe overload feedback when the dependency slows down. Do not assert a
  pool will exhaust or invent traffic/pool sizes absent deployment evidence.
- **Tests:** identify behavior hidden by mocks: elapsed time, blocking,
  cancellation, or resource release. For a changed retry budget, seek coverage
  of an attempt consuming the whole budget and a fast failure receiving only
  the remainder after waits. Existing guards or a deterministic fake clock can
  suffice; real sleeps, a live outage, and a new test per case are not required.
  Name a concrete broken budget/guard that would leave the tests green, if any.

The orchestrator supplies these obligations to the three owners, in both fan-out
and `--fast` modes. When requested, each owner returns this envelope instead of
its usual bare findings array:

```json
{
  "findings": [],
  "operational_assessment": {
    "status": "completed|not-completed",
    "evidence": ["pinned path:line and the relevant fact"],
    "analysis": "failure classes/budget, caller impact, or test blind spots for this lens",
    "gaps": []
  }
}
```

Keep each lens's existing finding schema. `completed` means the assessment was
performed, not that the change is safe; findings may remain. Missing required
evidence means `not-completed`, with the missing fact and next check in `gaps`.
Unknown traffic does not prevent reporting a proven per-call regression or
completing a bounded assessment with that deployment limitation stated.

## Risk disposition and approval challenge

For each declared or discovered operational risk, keep one ledger entry:
claim/scenario, pinned evidence, caller-visible consequence, mitigation and its
verification (or its absence), and disposition with the governing policy.
“Accepted”, “out of scope”, and “monitor after release” are declarations, not
mitigations. A risk acceptance can affect blocking disposition only when the
review verifies its authority and that its scope covers the actual consequence;
retain a demonstrated risk as a finding with that rationale. A convention
exception with no demonstrated defect need not become a finding.

In Phase 3, send the skeptic the risk ledger and all three assessments, even
when `findings` is empty. Request `coverage_audit` using the skeptic's output
contract. It independently challenges the proposed clean conclusion: are the
failure classes, effective budgets/defaults, affected callers, and test blind
spots evidenced, and is each risk disposition justified? An empty or missing
assessment cannot pass because the candidate list is empty. The skeptic may
identify additional candidates; the orchestrator must refute those against
pinned evidence before retaining them, using the same finding discipline.

Missing applicable assessments or unresolved required evidence produce
`incomplete`, not a fictional defect or approval. Known blocking findings still
require changes. Unrelated optional build checks remain best-effort. Summarize
the operational assessment and any limitations in the report; keep the detailed
ledger with the archived review.
