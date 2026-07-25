> 🌐 **English** · [Español](README.es.md)

# review-strict

A **strict, repo-adaptive PR / branch / diff reviewer** for Claude Code **and Codex**. It runs a
multi-agent, adversarially-verified code review at staff-engineer rigor
(correctness, security, architecture, tests, migration safety), adapts to each
repository's own rules, and archives a project-named report. It is independent of
any spec/CI pipeline — point it at a PR, a branch, or a diff.

The plugin ships **three sibling skills** — the analysis family, in workflow order:

- **`/spec-strict`** — pre-code review of a Stratos/Axiom spec dir (`spec.md`/`plan.json`/`pr.md`/`validation.md`), **before** Forge writes code; hunts omissions (uncovered entry-points, non-diff-checkable ACs, wrong-stack verification commands, incomplete risk inventory, layering misfit, unstable scope). See `skills/spec-strict/README.md`.
- **`/review-strict`** — the diff/PR review above (correctness, security, architecture + SOLID + complexity, tests, migration safety).
- **`/audit-strict`** — deep whole-repo architecture audit (component map, flows, lifecycle, data model, quality audit + prioritized roadmap). See `skills/audit-strict/README.md`.

Together: **`/spec-strict` reviews the plan → `/review-strict` reviews the change → `/audit-strict` reviews the repo.**

## Install

This is a **public, self-contained** repo (it is both the plugin and its own marketplace):

### Claude Code

```
/plugin marketplace add Oscabrera/review-strict
/plugin install review-strict
```

Then invoke `/spec-strict`, `/review-strict` or `/audit-strict` in any repo.

### Codex

```bash
codex plugin marketplace add Oscabrera/review-strict --ref main
codex plugin add review-strict@review-strict
```

Start a new thread, then invoke `$spec-strict`, `$review-strict`, or `$audit-strict` (plain-language requests using those names work too). The bundled archive guard is a lifecycle hook; review and trust it with `/hooks` before expecting enforcement.

The same `skills/` directory is shared by both hosts. Codex uses the portable host adapter to run the bundled agent briefs through its own sub-agent mechanism and inherits the session model when a Claude-only model selector is not available.

## Updating

Installed plugins do **not** update on their own by default — you pull new versions explicitly.

Claude Code:

```
/plugin marketplace update review-strict     # fetch the latest published version
```

To update automatically at session start, opt in **per user** in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "review-strict": {
      "source": { "source": "github", "repo": "Oscabrera/review-strict" },
      "autoUpdate": true
    }
  }
}
```

Codex:

```bash
codex plugin marketplace upgrade review-strict
codex plugin add review-strict@review-strict
```

Start a new thread after reinstalling so Codex loads the updated skills and hooks.

Releases are **version-gated**: consumers only move when the `version` in
`.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json` is bumped (see `CHANGELOG.md`) — intermediate commits to `main` are not pushed to anyone. Bumping both versions + updating `CHANGELOG.md` on a merge to `main` is what cuts a release.

## Usage

```
/spec-strict                    # review the spec dir on the current branch (pre-code)
/spec-strict IT-52986           # resolve specs/IT-52986-*/ on this branch
/spec-strict specs/IT-123-x/    # explicit spec dir
/spec-strict --fast             # single-agent mode (cheaper, less rigorous)
/spec-strict --model opus       # force all lenses on one model (default: hybrid)
/spec-strict --lang es          # review in Spanish
```

See `skills/spec-strict/README.md` for the full `/spec-strict` reference.

```
/review-strict                 # review the current branch vs its base (pre-PR)
/review-strict 433             # review PR #433 via gh
/review-strict --base main     # override the base branch
/review-strict 433 --repo-copy # also copy the report to the repo's reviews path
/review-strict 433 --post      # post the review to GitHub (asks first; always English)
/review-strict --fast          # single-agent mode (cheaper, less rigorous)
/review-strict 433 --model opus # force all lenses on one model (default: hybrid)
/review-strict 433 --lang es    # report in Spanish for this run
/review-strict 433 --no-save    # print only, don't archive
```

```
/audit-strict                   # deep whole-repo audit (auto-detect stack)
/audit-strict --stack vue       # force the Vue/Nuxt cartographers
/audit-strict --out ~/notes     # write to ~/notes/audit-strict/<repo>/
/audit-strict --model opus      # cartographers on Opus (default sonnet)
/audit-strict --fast            # single-agent mode (cheaper, less rigorous)
```

See `skills/audit-strict/README.md` for the full `/audit-strict` reference.

## Configuration (per developer, via env vars)

| Variable | Default | Effect |
|---|---|---|
| `REVIEW_STRICT_ARCHIVE_DIR` | *(unset)* | Shared archive base for all three skills. When set: `/review-strict` → `$DIR/<repo>/<file>`, `/spec-strict` → `$DIR/<repo>/spec-reviews/<spec-slug>.md`, `/audit-strict` → `$DIR/audit-strict/<repo>/`. When unset, each archives **inside the reviewed repo** (`reviews/<project>-pr-<N>.md`, `<spec-dir>/spec-review.md`, `audit-strict/`) — portable, everyone has it. |
| `REVIEW_STRICT_LANG` | `en` | Report language: `en` or `es`. The `--lang <en|es>` flag overrides it per run. |
| `REVIEW_STRICT_MODEL` | *(hybrid)* | Forces `/review-strict`'s 5 lenses to one uniform model (`sonnet`/`opus`/`haiku`/`inherit`); `--model` overrides it. **Unset = hybrid** (the default): deep lenses (correctness, security, architecture) on the session model, mechanical (tests, migration) on Sonnet. **The main cost lever.** |
| `SPEC_STRICT_MODEL` | *(hybrid)* | Same for `/spec-strict`'s 6 lenses — hybrid: coverage/risk/architecture/scope on the session model, ac-quality/verification on Sonnet. |
| `AUDIT_STRICT_MODEL` | `sonnet` | Model for `/audit-strict`'s 5 cartographers (Phase 2 only). |
| `REVIEW_STRICT_HOOK_BYPASS` | `0` | Set to `1` on a single call to bypass the archive-guard hook below (a deliberate one-off). |

## Enforcement: the archive guard

Setting `REVIEW_STRICT_ARCHIVE_DIR` used to be advisory — `/spec-strict` once ignored
it and wrote its review into the reviewed repo instead, and 21 reports were committed
into 5 repos before anyone noticed. A `PreToolUse` hook now makes it mechanical:

- **What it blocks:** any write whose target basename matches `spec-review*.md` — the
  in-repo fallback filename — **while `REVIEW_STRICT_ARCHIVE_DIR` is set**. The archive
  branch writes `<spec-slug>.md`, so the basename alone identifies the wrong branch,
  even when the directory is an unresolved shell variable.
- **When it does nothing:** whenever `REVIEW_STRICT_ARCHIVE_DIR` is unset or empty. The
  in-repo default is then the documented behavior, and the hook is a no-op — it corrects
  a misconfiguration, it never imposes the archive on you.
- **What stays allowed:** reading and **deleting** a `spec-review.md` (that is how
  already-committed residue gets cleaned up), writes under the archive dir itself, and
  drafts under `/tmp`, `/var/tmp`, `/private/tmp`, `$TMPDIR`.
- **Fail-open:** any internal error allows the call with a `WARN` — a guard must never
  break your session. `REVIEW_STRICT_HOOK_BYPASS=1` covers the deliberate one-off.

Run its suite with `./tests/hooks/test-block-inrepo-spec-review.sh` (plain bash, 30 cases).

The model knobs only touch the read-heavy fan-out; the adversarial verify pass always runs on your session model, so the rigor gate is never lowered. External comments (GitHub / ClickUp via `--post`) are **always English**, regardless of report language.

Reports are review **output**, not source — the in-repo `reviews/` folder is a good
`.gitignore` candidate unless your team wants review history committed.

## How it works

1. **Profile the repo** — reads `AGENTS.md`, `CLAUDE.md`, `.codex/skills/*`, `.claude/skills/*` (and legacy `.aiassistant/rules/*` only if present), local-wins.
2. **Diff + toolchain** — pulls the diff, excludes noise (`specs/`, `vendor/`, lockfiles), captures lint/static-analysis best-effort (evidence/CI if available; never blocks).
3. **Five adversarial lenses** in parallel — correctness/requirements, security, architecture & reuse, tests, migration safety. No-op agents are retried.
4. **Adversarial verification** — a skeptic pass refutes each finding against the diff; only evidenced findings survive.
5. **Synthesize** — severities mapped to the repo's vocabulary (Blocker/Major/Minor), most-severe first.
6. **Deliver** — prints + archives the report; `--post` publishes to GitHub after confirmation.

It also cross-checks the PR's own self-declared risks and AC-traceability table as
**untrusted claims** — a real declared risk is still a finding, and a claimed
mitigation absent from the diff is flagged `claimed-but-not-done`.

## Publishing

Branching: **`main`** is the stable/default branch the marketplace installs from
(`ref: main`); **`develop`** is the integration branch for ongoing work.

```
git init && git add -A && git commit -m "feat: review-strict plugin v1.0.0"
git branch -M main
git branch develop
gh repo create Oscabrera/review-strict --public --source=. --remote=origin --push
git push -u origin develop
```

Day-to-day: land changes on `develop`; merge to `main` to cut a release
(bump `CHANGELOG.md`). Consumers on the marketplace always get `main`.

## License

MIT
