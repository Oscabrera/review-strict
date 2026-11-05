# Review lessons: validation record for unreleased 1.4.1

The spec evaluations returned the frozen reference outcome for every supplied
case in both execution modes. They were evaluated independently without the key.
Diff-review examples also preserved the distinction between a wrong review claim,
a source defect, an authorized trade-off and missing required evidence. This is
a targeted regression exercise, not a production detection-rate estimate.
Reference labels were manually classified by the implementation session before
evaluation; no independent human adjudication is claimed.

## Spec readiness

| Case | Reference | Fast evaluator | Normal evaluator |
|---|---|---|---|
| 01 | revise-before-Forge | revise-before-Forge | revise-before-Forge |
| 02 | ready | ready | ready |
| 03 | revise-before-Forge | revise-before-Forge | revise-before-Forge |
| 04 | ready | ready | ready |
| 05 | revise-before-Forge | revise-before-Forge | revise-before-Forge |
| 06 | ready | ready | ready |
| 07 | revise-before-Forge | revise-before-Forge | revise-before-Forge |
| 08 | ready | ready | ready |
| 09 | revise-before-Forge | revise-before-Forge | revise-before-Forge |
| 10 | ready | ready | ready |
| 11 | incomplete | incomplete | incomplete |
| 12 | ready | ready | ready |

Fast evaluation applied all six briefs and the skeptic inline. Normal evaluation
used six independent lens agents and a separate skeptic, dispatching sequentially
at available host capacity. A dispatch that inherited earlier context was
discarded and replaced before any result was accepted. Evaluators read all raw
spec/source inputs and checked their hashes at completion; required external
runtime semantics remained unavailable in case 11 rather than being invented.

## Diff review, fast mode

- 01/02: correct false approval claims; no source defect invented.
- 03/08/09: verified clean assertions, equivalent responses, and an intentional
  response change with a compatible consumer.
- 04/05/07: cached degraded value survives recovery, host-shared breaker violates
  endpoint isolation, and a consumed response field differs under required parity.
- 06: retain authorized host-wide coupling as a nonblocking trade-off.
- 10: required parity proof unavailable; incomplete, no reproduced mismatch claimed.

These are scoped fixture decisions, not full PR approvals: no live provider,
Git identity, CI, deployment or traffic assumptions were supplied. Normal
multi-agent diff review was not evaluated in this new corpus. Its instructions
share the same criteria; delivery tests exercise both mode labels without
claiming those tests perform a model review.

## Reproduction

```bash
python3 tests/evals/prepare-spec-verification.py --out /tmp/spec-lessons-new
python3 tests/evals/prepare-spec-verification.py --kind review --out /tmp/review-lessons-new
python3 tests/evals/exercise-review-lessons.py
python3 -m unittest discover -s tests -p 'test_*.py'
bash tests/hooks/test-block-inrepo-spec-review.sh
```

Use the blind evaluation protocol in `spec-verification.md` to repeat reviewer
execution. `review-lessons-results.json` records observed outcomes and actual
mode/limitations; it is not another evaluator input. To rederive spec comparisons:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('tests/evals')
key = {c['id']: c['expected'] for c in json.loads((p/'spec-verification-cases.json').read_text())['cases']}
results = json.loads((p/'review-lessons-results.json').read_text())['spec']
for c in results:
    assert c['fast'] == c['normal'] == key[c['id']], c
    print(c['id'], c['fast'], c['normal'])
PY
```

The executable review examples demonstrate flag-independent routing, actual 404,
cached 150 remaining after recovery to 210 until TTL expiry, host coupling through
mixed successes/failures, and caller-visible parity or mismatch. Synthetic state
and clocks do not establish production impact.

## Helper review

A separate narrow read-only implementation review reproduced valid Markdown
parentheses/code-span rejection and newline normalization in claimed byte-exact
artifact validation. Fixes add balanced/escaped-target scanning, code exclusion,
and raw UTF-8 artifact comparison. Focused regressions protect those mechanisms;
structural checks still do not establish factual claims or exploitability.

The focused recheck confirmed the original three fixes and found an escape-parity
regression in the new scanner. Prefix counting now distinguishes literal paired
backslashes from an escaped bracket, with explicit odd/even, escaped-image and
escaped-backtick controls. That final correction was verified by local regressions;
no additional whole-corpus model run is claimed.
