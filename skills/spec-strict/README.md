> 🌐 **English** · [Español](README.es.md)

# spec-strict

A **strict, repo-adaptive review of a Stratos/Axiom spec — before any code is written.**
The pre-code sibling of `/review-strict`: instead of reviewing a diff, it reviews the **spec
dir** (`spec.md`, `plan.json`, `pr.md`, `validation.md`) on the feature branch and hunts the
omissions that Stratos specs recurrently leave, so they get fixed in the plan instead of
becoming fix commits at PR time.

Completes the family: **`/spec-strict`** (the plan) → **`/review-strict`** (the change) →
**`/audit-strict`** (the repo).

## Why it exists

Running `/review-strict` (a *diff* reviewer) against a spec works off-label and already reduces
rework — but its lenses are code/diff lenses, so it misses spec-native omissions. Real example
(`cp-shops-catalog`): PR **#1279** had its spec reviewed before code and shipped with **0 fix
commits**; sibling **#1278** skipped it and burned ~5 fix commits + a rescope + a close/reopen.
`/spec-strict` makes that pre-code review a first-class, spec-native check.

## What it catches (the six lenses)

1. **Entry-point / caller coverage** — the AC fixes the happy path and forgets the other callers.
2. **AC diff-checkability** — ACs not mapped to concrete files + a real test; template-fill traceability tables.
3. **Verification-command sanity** — commands that don't exist for the stack (e.g. `vitest` in a PHP/Pest repo).
4. **Blocker/risk inventory (grounded)** — the caller/subclass/migration the plan didn't foresee that breaks at runtime.
5. **Architecture & layering fit** — logic/queries planned in the class instead of the repo's repository/service layer.
6. **Scope & completeness** — unbounded scope that invites in-flight rescope; work the ticket implies but the spec omits.

Grounded in the actual codebase and adversarially verified — every finding is a **concrete spec edit**, not a vague concern.

## Usage

```
/spec-strict                     # auto-detect the spec dir on the current branch
/spec-strict IT-52986            # resolve specs/IT-52986-*/ on this branch
/spec-strict specs/IT-123-x/     # explicit spec dir
/spec-strict --fast              # single-agent mode (cheaper, less rigorous)
/spec-strict --model opus        # run the lenses on the session model (max depth)
/spec-strict --lang es           # review in Spanish
/spec-strict --out docs/         # write the review to a chosen dir
```

Typical flow: run it on the ticket's branch **after `/create-task`, before `/execute-task`** —
apply its spec edits, then let Forge implement a hardened spec.

## Output

A `spec-review.md` (written next to the spec by default) with a **readiness verdict**
(`ready` / `revise-before-Forge`), findings grouped by lens (severity: **block** / **should-fix**
/ **nice-to-have**), each phrased as the exact edit to apply to the spec, plus a coverage note.

## Rules

- **Read-only.** Never edits `spec.md`/`plan.json`/`pr.md`/`validation.md` — the human or Axiom applies the edits. Never commits, branches, or opens PRs.
- **Repo conventions win** — never demands a pattern the repo doesn't use.
- Shares `REVIEW_STRICT_LANG` / `REVIEW_STRICT_ARCHIVE_DIR` with the rest of the plugin.
- **Cost:** the 6 lens agents run on `SPEC_STRICT_MODEL` / `--model` (default **Sonnet**), while the adversarial verify pass stays on your session model — the rigor gate is untouched. When `graphify-out/` exists, Phase-1 grounding queries the graph before grep, cutting reads. Use `--model inherit`/`opus` for a maximum-depth review.

## Not yet (roadmap)

- A **pipeline gate**: run `/spec-strict` automatically after Axiom authors the spec, before Forge — the real shift-left leverage (lives in `cyberpuerta/stratos-autopilot`).
- Feeding the recurring omission pattern back into Axiom's spec-authoring prompt (root-cause fix).
