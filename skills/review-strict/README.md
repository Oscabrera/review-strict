> 🌐 **English** · [Español](README.es.md)

# /review-strict — overview

A **strict, repo-adaptive PR/branch/diff reviewer**. A Claude Code skill: it adapts to the repo you run it in (reads that repo's real rules) and produces a rigorous, multi-agent, adversarially-verified review.

Part of the analysis family: **`/spec-strict`** (the plan) → **`/review-strict`** (the change) → **`/audit-strict`** (the repo).

## What it does

Reviews a diff at staff-engineer rigor and **reports errors only** (no "looks good"), with `file:line` evidence and a final decision of `approve` / `request-changes` / `comment`.

## How to use it

```
/review-strict                    # current branch vs base (pre-PR)
/review-strict 433                # PR #433 via gh
/review-strict --base main        # override the base
/review-strict 433 --repo-copy    # also copy to the repo's reviews path (.ai/pr-reviews)
/review-strict 433 --post         # publish to GitHub (asks first; always English)
/review-strict --fast             # single agent (cheaper, less rigorous)
/review-strict 433 --lang es      # report in Spanish for this run
/review-strict 433 --no-save      # don't archive (print only)
```

## Environment variables (per-developer config)

- **`REVIEW_STRICT_ARCHIVE_DIR`** — folder where reports are archived. If unset, the report lands **inside the reviewed repo** at `reviews/<project>-pr-<N>.md` (portable — everyone has it). If set, it uses `$REVIEW_STRICT_ARCHIVE_DIR/<repo>/<file>` (handy for a central notes folder).
- **`REVIEW_STRICT_LANG`** — report language: `en` (default) or `es`. The `--lang <en|es>` flag overrides it per run.
- **Hard rule:** anything published outward (a GitHub or ClickUp comment via `--post`) is **always in English**, regardless of the report language.

## How it works (6 phases)

0. **Profile the repo** — `AGENTS.md` + `CLAUDE.md` + `.claude/skills/*` (and `.aiassistant/rules/*` only if present). Local-wins precedence.
1. **Diff + toolchain** — pulls the diff, excludes noise (`specs/`, `vendor/`, `evidence/`, lockfiles), and captures Pint/PHPStan best-effort (uses evidence/CI if present; otherwise skips — never blocks).
2. **Fan-out of 5 lenses** (independent agents): correctness/#4, security, architecture & reuse, tests, migration. Detects no-op agents and retries.
3. **Adversarial verification** — a skeptic pass that kills false positives (default-refute).
4. **Synthesis** — severities in the repo's vocabulary (Blocker/Major/Minor), most-severe first.
5. **Deliver** — prints + archives (see `REVIEW_STRICT_ARCHIVE_DIR`); `--post` publishes to GitHub after confirmation.

The **#4** check verifies the PR's self-declarations (risks/ACs) against the diff: a real declared risk is still a finding, and a claimed mitigation/AC absent from the code is `claimed-but-not-done` / `ac-traceability-gap`.

## Two sources of truth

1. **The repo's rules** — win on format, severity and commands.
2. **The plugin's own staff baseline** (`references/baseline-criteria.md`) — always applies, even with no repo rules; it adds findings the repo's checklist forgot.

## Files

- `SKILL.md` — orchestrator (invocation, flags, phases)
- `references/repo-profile.md` — repo-adaptation logic
- `references/lenses.md` — the 5 review briefs
- `references/baseline-criteria.md` — the always-on staff bar
- `references/severity-output.md` — severity crosswalk, verification, output template

## Design origin

Built from the best of three systems: **Sentinel** (stratos-autopilot — multi-pass rigor), **AIWF** (standalone command + stack-packs), and **per-repo rules** (`.aiassistant/rules/`). Designed and validated on cp-shops-pcb PR #433.
