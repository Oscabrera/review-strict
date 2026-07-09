> 🌐 **English** · [Español](README.es.md)

# review-strict

A **strict, repo-adaptive PR / branch / diff reviewer** for Claude Code. It runs a
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

```
/plugin marketplace add Oscabrera/review-strict
/plugin install review-strict
```

Then invoke `/spec-strict`, `/review-strict` or `/audit-strict` in any repo.

## Updating

Installed plugins do **not** update on their own by default — you pull new versions explicitly:

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

Releases are **version-gated**: consumers only move when the `version` in
`.claude-plugin/marketplace.json` is bumped (see `CHANGELOG.md`) — intermediate commits to
`main` are not pushed to anyone. Bumping `version` + updating `CHANGELOG.md` on a merge to
`main` is what cuts a release.

## Usage

```
/spec-strict                    # review the spec dir on the current branch (pre-code)
/spec-strict IT-52986           # resolve specs/IT-52986-*/ on this branch
/spec-strict specs/IT-123-x/    # explicit spec dir
/spec-strict --fast             # single-agent mode (cheaper, less rigorous)
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
| `REVIEW_STRICT_ARCHIVE_DIR` | *(unset)* | When set, reports archive to `$REVIEW_STRICT_ARCHIVE_DIR/<repo>/<file>`. When unset, they archive **inside the reviewed repo** at `reviews/<project>-pr-<N>.md` (portable — everyone has it). |
| `REVIEW_STRICT_LANG` | `en` | Report language: `en` or `es`. The `--lang <en|es>` flag overrides it per run. |

External comments (GitHub / ClickUp via `--post`) are **always English**, regardless of report language.

Reports are review **output**, not source — the in-repo `reviews/` folder is a good
`.gitignore` candidate unless your team wants review history committed.

## How it works

1. **Profile the repo** — reads `AGENTS.md`, `CLAUDE.md`, `.claude/skills/*` (and legacy `.aiassistant/rules/*` only if present), local-wins.
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
gh repo create Oscabrera/review-strict --private --source=. --remote=origin --push
git push -u origin develop
```

Day-to-day: land changes on `develop`; merge to `main` to cut a release
(bump `CHANGELOG.md`). Consumers on the marketplace always get `main`.

## License

MIT
