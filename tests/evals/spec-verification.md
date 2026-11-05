# Spec verification regressions

`spec-verification-cases.json` freezes synthetic inputs and expected outcomes
manually classified by the implementation session before reviewer execution.
These are reference labels, not an independently human-adjudicated benchmark. It includes valid oracles,
authorized narrowed scope, existing-test reuse, missing required evidence and
an unrelated change as controls. It is a targeted corpus, not production recall.

Prepare blind inputs in a new temporary directory:

```bash
python3 tests/evals/prepare-spec-verification.py --out /tmp/spec-verification-blind
```

Do not give an evaluator the corpus file, expected outcomes or retrospective.
Give it only the prepared directory and the installed spec-strict skill/lenses.
For each case it must read the raw spec/source and return readiness, findings,
invariant ledger and work actually performed. Treat each fixture as the entire
supplied contract; no optional documents are required by default. `source.py`
is pinned synthetic codebase evidence, not the implementation to write.

Run once with the inline `--fast` path, and once with the six independently
scoped lens briefs plus skeptical verification under the host's concurrency
limit. Use actual available inherited models; do not claim a fan-out when only
one reader ran. No production calls or source edits are needed. Evaluators may
execute the tiny source snippets in an isolated scratchpad when helpful.

Compare per-case outcomes against the frozen key after evaluation. Record the
commands, runtime, coverage gaps and differences; do not turn agreement on this
hand-built corpus into a reliability percentage. Missing essential runtime
proof is incomplete, while a proven blocker remains revise-before-Forge.

For the related diff-review changes, `review-lessons-cases.json` freezes a separate
synthetic key for approval claims, shared state and caller parity. Prepare inputs with `python3 tests/evals/prepare-spec-verification.py --kind review
--out /tmp/review-lessons-blind`; folders contain only `request.md` and
`source.py` (never `expected`). Apply
correctness/architecture/tests/migration and skeptical claim checks, including
clean and accepted-risk controls. Keep these outcomes separate from spec readiness.

Execute the trusted synthetic review examples without external services:

```bash
python3 tests/evals/exercise-review-lessons.py
```

The output separates observations from the expected review dispositions. It does
not run a model or grade reviewer quality.
