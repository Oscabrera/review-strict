# Load-bearing verification ledger

AC-quality and verification share a compact ledger per load-bearing invariant:
`id`, `spec_anchor`, relevant `runtime_assumptions`, `activation_evidence`,
`expected_observable`, `safe_control`, `sibling_claims`, `evidence`, `status`
(completed/not-completed) and `gap`. Reuse existing checks; N/A needs a reason.
The orchestrator deduplicates the entries and supplies them to the skeptic along
with findings. Include the ledger with the archived report, not just a lens count.

Challenge the actual oracle: would the proposed assertion fail on the faulty base,
or does it assert the faulty result? Does the failure/mode activate in each isolated
invocation? Does the runtime version produce the semantic difference, rather than
merely report that a mode is on? Is a negative/safe control required by the claimed
invariant missing? After a correction, trace its dependent claims through decisions,
design, traceability and handoff; a resolved sentence does not correct its siblings.

Exercise representative commands when the claim depends on their semantics and
this is permitted with existing tools. Separate executed evidence, historical
reports and reasoning. Lack of an essential runtime fact gives not-completed;
without a known blocker use incomplete. Never demand implementation before spec
readiness, a live production experiment, optional sidecars, duplicate tests or a
wider scope than the authorized contract. A sound portable oracle is clean.

Regression protocol and blind input preparation: `tests/evals/spec-verification.md`
in the plugin source. The semantic checks apply in both normal and fast modes;
record the mode and lens/skeptic work actually performed, not an assumed fan-out.
