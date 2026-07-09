---
name: spec-strict
description: Strict, repo-adaptive review of a Stratos/Axiom SPEC before any code is written — the pre-code sibling of /review-strict. Reviews the spec dir (spec.md, plan.json, pr.md, validation.md) on the feature branch and hunts the omissions Stratos specs recurrently leave: uncovered entry-points/callers, non-diff-checkable acceptance criteria, wrong-stack verification commands, an incomplete blocker/risk inventory, architecture/layering misfit (logic in the class instead of a repository/service), and unstable scope. Grounded in the actual codebase and adversarially verified. Use when the user says "spec-strict", "revisa el spec", "review this spec/task before code", "revisa el spec de Stratos", "check the spec before Forge", or names a spec dir / IT ticket to review. It reviews the plan; it never edits the spec and it is NOT a diff/PR review (that is /review-strict).
---

# /spec-strict — strict, repo-adaptive pre-code spec review

You are running the `/spec-strict` skill. Your job: review a **spec/plan before code exists** and surface the omissions that would otherwise become fix commits, re-opens, or reviewer round-trips at PR time. This is **shift-left**: catch the gap in the spec, not in the fix. Every finding must be real, anchored to the spec **and** (where proof needs it) the codebase, and survive a skeptic pass. Output is a set of **concrete spec edits** + a readiness verdict — you never edit the spec yourself.

This is the constructive pre-code sibling of the family: **`/spec-strict`** (the plan) → **`/review-strict`** (the change) → **`/audit-strict`** (the repo). It reuses review-strict's spine (repo profile, verify-skeptic, severity/output).

Two sources of truth, in order (same as review-strict): (1) the **repo's own rules** (Phase 0) win on conventions/severity/format; (2) the always-on staff baseline applies on top. The spec is judged against the **codebase + the ticket**, never a diff.

## Invocation & flags

- `/spec-strict` → auto-detect the spec dir added on the current branch vs its base.
- `/spec-strict <path>` → review that explicit spec dir.
- `/spec-strict IT-XXXXX` → resolve `specs/IT-XXXXX-*/` on the current branch.

Flags: `--base <branch>` (override base for detection) · `--fast` (single-agent, you walk all six lenses yourself) · `--lang <en|es>` (report language; overrides `REVIEW_STRICT_LANG`, default `en`) · `--out <dir>` (where to write the review; default: next to the spec as `<spec-dir>/spec-review.md`).

**Resolve config first:**
```bash
printf 'lang=%s archive=%s\n' "${REVIEW_STRICT_LANG:-en}" "${REVIEW_STRICT_ARCHIVE_DIR:-<in-spec-dir>}"
```
Then announce the resolved mode in one line (e.g. "Revisando spec `specs/IT-52986-…/` en cp-shops-catalog, multi-agente + verify, es").

## Phase 0 — Repo profile + spec-dir detection

1. Read `../review-strict/references/repo-profile.md` and assemble the **Repo Review Profile** (layering, red lines, established patterns, the real build/lint/test commands, base branch) — this is the oracle the spec is judged against.
2. Read `references/spec-detection.md` and resolve the **spec dir** (path arg → `IT-XXXXX` → auto-detect on branch → fallback). Load `spec.md`, `plan.json`, `pr.md`, `validation.md` (whatever exists; note what's missing). Optionally load the ticket text read-only if reachable.
3. If no spec dir is found, say so and stop — there is nothing to review. Never review arbitrary markdown.

## Phase 1 — Ground the spec in the codebase

This is what lets you **prove** omissions instead of guessing. For each file/class/behavior the plan will touch, read the real repo (read-only: Read/Grep/Glob/`git`):
- **Callers & entry-points** of the thing being changed (`rg`) — so Lens 1 can show an uncovered path.
- **The real test runner** (from `composer.json` scripts / `AGENTS.md` / `package.json`) — so Lens 3 can flag wrong-stack commands.
- **Existing repositories/services/patterns** the plan should use, and the repo's layering — so Lens 5 can show a bypass.
- **Subclasses / implementers / contracts** that a planned signature change would break — so Lens 4 can show a foreseeable fatal.
Produce a short **grounding slice** (paths + facts) passed into every lens.

## Phase 2 — Six spec lenses (fan-out)

Dispatch **one sub-agent per lens, in parallel** (single message, multiple `Agent` calls; `subagent_type: general-purpose`, inheriting the session model/effort — no override). Each gets: the spec files, the relevant **Repo Review Profile** slice, the **Phase-1 grounding**, and its brief inlined from `references/spec-lenses.md`. The six lenses: **coverage** (entry-points), **ac-quality** (diff-checkability), **verification** (command sanity vs the real stack), **risk** (grounded blocker inventory), **architecture** (layering/pattern fit), **scope** (bounded & complete).

Each returns the finding contract from `spec-lenses.md` (with `spec_quote` + `codebase_evidence` + `spec_edit`). Apply the family's **no-op detection + one retry**: a dispatch that returns nothing / echoes instructions / reports 0 tool uses is re-dispatched once with *"Do real work now — your FIRST action must Read the spec files and grep the repo; return the findings JSON."*; mark a lens "not completed" if it no-ops twice.

In `--fast` mode, skip the fan-out and walk all six lens briefs yourself.

## Phase 3 — Adversarial verification

Collect all findings, dedup by `spec_file + omission`. Dispatch this plugin's **`review-strict:verify-skeptic`** agent (read-only; no model override) with a spec-review reframing: for each candidate, **default-refute** — is the spec *really* missing/wrong on this (re-read the cited spec line), and is the `codebase_evidence` real (the uncovered caller / existing repository / breaking subclass / wrong runner actually exists in the repo)? Drop `not-real`; keep `uncertain` only as a demoted "needs human eyes" note. A finding survives only if the skeptic can point at both the spec text and (where claimed) the code. (Fallback: `general-purpose` with the refute brief inlined. Same no-op + one-retry; else refute inline.) `--fast`: refute inline yourself.

Verification here confirms the **omission is real & grounded** — not that it is exploitable.

## Phase 4 — Synthesize the review

Map internal P0/P1/P2 to the spec-native vocabulary **block / should-fix / nice-to-have** (see `../review-strict/references/severity-output.md` crosswalk). Then:
1. A one-line **readiness verdict**: `revise-before-Forge` if any surviving **block**; else `ready` (with should-fix/nice listed).
2. **Findings grouped by lens**, most-severe first within each — each phrased as **the concrete spec edit to apply** (the #1279 pattern: "broaden AC-1 to require durable xdebug-off across ALL entry-points incl. `./vendor/bin/pest`; add a pest-direct test scenario; note the residual in Security & Risk Notes"), with the spec quote and the codebase evidence.
3. A short **coverage note**: which spec files existed, which lenses ran, what you could not assess.
Errors only — no praise, no restating the spec. A clean spec yields an honest "ready — no blocking omissions" with any should-fix listed.

## Phase 5 — Deliver

- Print the review in chat.
- Write it (unless `--no-save`) to `--out` → else `$REVIEW_STRICT_ARCHIVE_DIR/<repo>/spec-reviews/<spec-slug>.md` if that env var is set → else **next to the spec**: `<spec-dir>/spec-review.md`. Use a Bash quoted heredoc (literal `$`/backticks). `mkdir -p` as needed; print the path.
- **NEVER edit `spec.md` / `plan.json` / `pr.md` / `validation.md`.** This skill reviews only; the human or Axiom applies the edits. It does not commit, branch, or open PRs.

## Operating rules (always)

- **Prove, don't suspect.** Every finding anchors to the spec text and, where the proof needs it, a real `file:line` in the repo. Drop anything the skeptic can't confirm.
- **Repo conventions win.** Never demand a pattern the repo doesn't use; never invent a layering it didn't adopt. The baseline adds omissions the repo forgot to guard, labeled as such.
- **Spec-native, actionable output.** Every finding is a ready-to-apply spec edit, not a vague concern.
- **Read-only on the spec and the repo.** No edits, no installs, no branch switches.
- **Bounded cost.** Six lens agents + one verify pass is the default shape.
