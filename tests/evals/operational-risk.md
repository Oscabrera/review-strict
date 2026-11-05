# Operational-risk review regression exercise

This is a behavioral exercise for the skill, not a wording/regex test. The
expected decisions in `operational-risk-cases.json` are manually classified
before evaluation. Keep them away from the evaluating reviewer. The first two
cases read real ab-shop snapshots; the others are small controls for budgets,
defaults, caller multiplication, missing evidence, and authorized disposition.

## Prepare blind inputs

Use an ab-shop checkout containing the two full commits in the case file:

```bash
python3 tests/evals/prepare-operational-risk.py --ab-shop /path/to/ab-shop --out /tmp/operational-risk-inputs
```

The destination must be new. Preparation reads the pinned Git blobs without
switching branches or modifying the source repo. The supplied 60-second socket
default is a fixture assumption, not a measurement of production configuration.
Dependency facts refer to Guzzle 6.5.5's StreamHandler and exception hierarchy.

Give an independent reviewer only the prepared directory and the updated
`review-strict` instructions, its operational/baseline/integrity/severity
references, the correctness/architecture/tests briefs, and the skeptic brief.
Ask it to perform these checks sequentially, including the coverage challenge,
without posting or changing source. Do not provide the answer key, earlier PR
reviews, this exercise's results, or the suspected issue. Per case, request:

```json
{"id":"case-01","decision":"approve|comment|request-changes|incomplete","triggered":true,"findings":[],"evidence":[],"gaps":[]}
```

Compare the result with each preclassified expectation and reason, inspecting
the evidence rather than counting verdict matches alone. A safe control must
not pass because the reviewer skipped applicable work. An incomplete case must
not acquire invented production facts. The accepted-risk control must retain
the real consequence without converting its verified advisory disposition into
a blocker. Report disagreements and fixture defects before any aggregate score.
One fixture exercise does not establish production detection reliability.

## Reproduce the underlying production-method behavior

```bash
php tests/evals/retry-budget.php /path/to/ab-shop 121a9345ecf5ea27815f618b854d0e42cfd94ea5 8f6f094a1e2e8e6a186c7d4c43e1831e9cba37ff
```

The harness executes the exact retry method and delay constant extracted from
each pinned snapshot, with controlled transport and clock seams. It asserts
exhausted and partially consumed budgets at 3 and 60 seconds. It neither runs
Guzzle/PHP-FPM nor proves handler behavior, production pool exhaustion, or LLM
review quality. The 60-second input is an effective budget supplied directly to
the method, not a test of the runtime-default resolver.

Existing plugin checks remain:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
bash tests/hooks/test-block-inrepo-spec-review.sh
```
