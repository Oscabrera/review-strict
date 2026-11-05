# Checked delivery of a diff review

Use `scripts/review-delivery.py` with Python 3.9+ after synthesis in both modes,
including chat-only/no-save runs. It never writes to the repo or posts to GitHub.
Save the frozen `review-context.py diff` result unchanged as `context.json` in
a temporary run directory. Create `assessment.json` with:

```json
{
  "subject": {"base_sha":"...","head_sha":"...","merge_base":"...","changed_files":[]},
  "mode":"fast",
  "decision":"approve",
  "currency":"current",
  "blocking_findings":0,
  "completion":[{"id":"correctness","status":"completed","evidence":["pinned path:line and what was checked"]}],
  "claims":[],
  "patch_assertions":[]
}
```

`subject` is the parsed frozen context object, not transcribed strings. Include
completion entries for all five lens ids (`correctness`, `security`,
`architecture`, `tests`, `migration`), `skeptic`, `approval-claims`, and any
applicable canonical/operational/parity obligations. For N/A and not-completed
use `reason`, an explicit gap/applicability explanation. Evidence is a list of
facts actually checked; do not use a section heading as execution evidence.
`claims` uses `approval-claims.md`. Empty means there is no consequential factual
assertion beyond the review disposition, not that claims were never audited.
`mode` describes actual execution, including any inline fallback in evidence.

For branch-sync/deletion warnings record a `patch_assertions` entry with `path`,
`kind` (`deletion|conflict`) and pinned patch/merge `evidence`. Base-only paths
cannot be PR regressions. A deletion must actually be in the merge-base patch.
A conflict entry additionally needs an inspected three-way merge result: a file
being changed is not itself proof of conflict. The helper checks patch membership,
not the truth of free-text merge evidence; the skeptic verifies that evidence.

Write review prose to `body.md` without subject/decision header fields. The helper
generates them and records plugin version, mode, source identity, completion and
claims in an embedded JSON comment. Do not add a second hand-authored header.

```bash
python3 <plugin-root>/skills/review-strict/scripts/review-delivery.py prepare \
  --repo <repo> --base <current-base-ref-or-OID> --head <current-head-ref-or-OID> \
  --assessment <run>/assessment.json --body <run>/body.md > <run>/review.md
python3 <plugin-root>/skills/review-strict/scripts/review-delivery.py validate \
  --repo <repo> --base <current-base-ref-or-OID> --head <current-head-ref-or-OID> \
  --assessment <run>/assessment.json --body <run>/body.md --artifact <run>/review.md
```

On a failed preparation, discard its partial/empty output and resolve the error;
never deliver it as clean. Reread PR base/head from the provider at delivery;
passing only old literal OIDs does not establish remote currency. Both commands
compare the receiving context to the frozen assessment; validation also compares
the exact rendered artifact. Copy those exact bytes to the archive/repo copy.
If Python is unavailable, mark this required integrity check not-completed;
report an incomplete assessment with its gap, without a current approval claim.

For an already authorized outward review, `github-payload` takes the same inputs
as `validate` and emits `{commit_id,event,body}` only after validation. It never
posts; normal posting consent still applies. Check provider currency immediately
before submitting that payload. Retain the run's assessment with the archive.
