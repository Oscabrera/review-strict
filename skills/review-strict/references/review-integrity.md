# Freeze the subject; distinguish clean from incomplete

Apply this reference to `/review-strict` and `/spec-strict`. It supplements the
repo profile; it does not create a Stratos gate or replace Sentinel evidence.

## Immutable diff and source context

1. Resolve the base using the repo profile. In PR mode, first capture
   `gh pr view <N> --json number,title,body,headRefOid,baseRefOid,headRefName,baseRefName`.
   Freeze those full `headRefOid` and `baseRefOid` values. Fetch missing objects
   from the PR's repository using its existing remote (for example,
   `git fetch --no-tags <remote> pull/<N>/head` for the head), then verify they
   resolve to the captured SHAs. Never substitute the current checkout, a stale
   remote-tracking ref, or a newer PR head. If the objects are unavailable,
   report `incomplete` with the failed command.
2. Run the bundled helper (Python 3 + Git, no extra packages):

   ```bash
   python3 <plugin-root>/skills/review-strict/scripts/review-context.py diff --base <base-ref-or-sha> --head <head-ref-or-sha>
   ```

   It returns full `base_sha`, `head_sha`, `merge_base`, and `changed_files`.
   Generate the patch with `git diff <merge_base> <head_sha> --`, using those
   literal SHAs. Branch mode defaults the head to `HEAD`; an explicit range
   supplies both endpoints. Never combine `--merge-base` with `A...B`.
3. All repo rules, source, spec files, and CI results must belong to that head.
   If the change edits governing rules, compare them with the receiving base:
   the author's proposed waiver is itself under review, not permission to
   disregard a still-governing requirement.
   Read blobs with `git show <head_sha>:<path>` or the helper's
   `show --head <head_sha> <path>`. The orchestrator supplies these pinned
   excerpts, with repo-relative paths, to read-only lens/skeptic agents. They
   must request more pinned context from the orchestrator when needed; they
   must not silently Read a different checkout. Record deleted-file evidence
   against the merge base, labeling the side.
4. Branch/path reviews are committed comparisons by default. Check
   `git status --short` and disclose staged, unstaged, and untracked files as
   excluded; do not call an empty committed diff a review of local edits. If
   the user requests working-tree changes, snapshot the relevant bytes outside
   the repo, record SHA-256 digests, and recheck them at delivery. The base must
   still be pinned. Never commit, stash, or switch branches to obtain context.
5. At delivery, re-read the PR head **and base** OIDs (or the branch/range refs).
   If either moved or cannot be checked, mark currency `stale` or `unknown`,
   withhold approval/readiness, and preserve historical findings with their
   reviewed SHAs. Apply the completion rules below (known blockers still require
   changes; otherwise `incomplete`). Do not automatically loop over moving heads. In `--post` mode repeat
   the check immediately before posting and bind the review with
   `gh api --method POST repos/<owner>/<repo>/pulls/<N>/reviews` using JSON
   `commit_id=<head_sha>`, `body`, and `event`. Do not post if currency is not
   current. Existing authorization and English-only posting rules still apply.

If Python is unavailable, run the equivalent Git commands explicitly: resolve
both commits, compute their merge base, then diff that merge base against the
head. A failed base resolution is an error, never “no diff” or “no spec”.

## Spec context

For an explicit spec path, inventory the directory first. Read **every sibling
Markdown design/contract/decision file present**, including `design.md`,
`contracts.md`, `decisions.md`, `data-model.md`, `brief.md`, and referenced
subdocuments needed to judge the plan, plus `spec.md`, `plan.json`, `pr.md`, and
`validation.md` when present. Read `.test-intent-contract-version` when present.
Generated evidence is supporting data, not a substitute for these sources.

Pin the codebase head used for grounding. An uncommitted/untracked spec may be
reviewed without committing it: snapshot its source files outside the repo and
record their SHA-256 digests. Verify the inventory and bytes have not changed at
delivery. A missing sibling is a finding only when the governing contract
requires it; do not demand `validation.md`, a new test, or a traceability format
merely because an older template had one.

## Completion and disposition

Keep a small coverage ledger: each applicable lens/rubric obligation is
`completed` (findings or clean, with what was checked), `not-applicable` (a reason),
or `not-completed` (the missing evidence/work). An empty findings array is valid
after real work. It is not proof that a missing lens ran. The same applies to
the skeptic, including an explicitly completed inline fallback.

- A surviving blocking defect yields `request-changes` / `revise-before-Forge`,
  even if some coverage is incomplete; state the coverage gap too.
- Without a known blocker, any `not-completed` obligation, missing required
  contract, or stale/unknown subject yields **`incomplete`**, never `approve` or
  `ready`. On GitHub this is a `COMMENT`, not an approval.
- Only a current subject with completed/applicably discharged obligations can
  yield `approve` / `ready`. Best-effort build checks remain optional unless the
  repo explicitly makes them a review prerequisite; “not run” is not CI evidence.

Use the repo's severity **and disposition** rules, not only its severity words.
For Stratos, read `contract/review-rubric.md`: impact, `blocking`, introduced
status, evidence, and FIX/FILE/REPLY are separate judgments. A style preference
or hypothetical hardening is not a blocker; an observable, declared degraded
state is not automatically a swallowed failure. Verify claimed defects with a
realistic input and caller-visible consequence or an explicit contract breach.
Do not create tickets, send messages, or write Stratos review receipts as a side
effect of these review-only skills.
