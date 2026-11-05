# Service repoints and caller-visible parity

Trigger when a change repoints a service/dependency and claims compatible behavior,
even without retry/timeout changes. Migration owns the parity assessment; correctness
traces consumers, and tests assesses the scope of existing evidence.

Trace consumed fields, null/empty/error semantics, status mapping and side effects
from the real caller. Compare equivalent inputs against compatible data snapshots.
Request-path/options mocks returning `{}` prove routing only. Look for captured
response fixtures, existing contract tests, or an explicitly owned rollout check
when the repo permits it. Live production calls and a new test are not mandatory.

An observed difference in a consumed business field is a candidate defect only
when the compatibility contract requires equivalence. An intentional authorized
change is judged against the new consumer contract. Distinguish an executed
mismatch, a QA report, and missing evidence. Missing load-bearing parity proof
means not-completed/incomplete absent known blockers; optional unknowns do not.

Return a finding using the migration schema for a demonstrated defect. Regardless
of findings, send a compact completion entry to the orchestrator with the required
contract, consumed fields, evidence and limitations; include consequential parity
assertions in the approval ledger. No extra default agent is needed.
