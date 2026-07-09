# Locating & parsing a Stratos spec dir

`/spec-strict` reviews the spec **before** code exists. The spec is a directory Stratos/Axiom
authored on the feature branch. This file is how Phase 0 finds and reads it.

## The Stratos spec dir layout

A spec dir lives at `specs/IT-XXXXX-<type>-<slug>/` on the ticket's feature branch
(`<type>/IT-XXXXX-<slug>`). Typical contents:

| File | What it is | What spec-strict reads it for |
|---|---|---|
| `spec.md` | The spec: Goals, Out of Scope, Acceptance Criteria, Security & Risk Notes, plan | the primary review target — coverage, ACs, risk, architecture, scope |
| `plan.json` | Machine-readable task/phase breakdown (bundled/epic) | scope completeness, task boundaries |
| `pr.md` | Pre-authored PR body incl. the **AC-traceability table** | AC diff-checkability, verification commands |
| `validation.md` | Manual test runbook / commands to run | verification-command sanity vs the real stack |

Not every ticket has all four (a single task may have only `spec.md` + `pr.md`). Read whatever exists; note what's missing (a missing `validation.md` on a behavior-changing task is itself a finding).

## Resolution order (Phase 0)

1. **Explicit path arg** — `/spec-strict specs/IT-52986-.../` → use it verbatim.
2. **Ticket arg** — `/spec-strict IT-52986` → glob `specs/IT-52986-*/` (on the current branch); if >1, list and pick the one on this branch.
3. **Auto-detect from the current branch** (default) — the spec dir added on this branch vs its base:
   ```bash
   BASE="${SPEC_BASE:-$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null | sed 's#origin/##')}"; BASE="${BASE:-development}"
   git diff --name-only --merge-base "$BASE"...HEAD 2>/dev/null | rg 'specs/.+/spec\.md$'
   ```
   If the branch name carries an IT number (`<type>/IT-XXXXX-...`), prefer the `specs/IT-XXXXX-*/` that matches it.
4. **Fallback** — if no spec dir is found: say so plainly and stop (there is nothing to review). Do NOT review arbitrary markdown. Suggest the user pass a path or run from the ticket's branch.

## Ground truth for the review

- The **repo** (its code + `AGENTS.md`/`CLAUDE.md` layering/conventions + real test runner) is the oracle — the spec is judged against it, not against a template.
- The **ticket** text, if reachable read-only (`gh`, or the `autopilot nexus` CLI if present), sharpens "does the spec cover the ticket's implied work?" — optional; never block on it.
- **Read-only always.** `/spec-strict` never edits `spec.md`/`plan.json`/`pr.md` — it emits a review the human or Axiom applies.
