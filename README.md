# review-strict

A **strict, repo-adaptive PR / branch / diff reviewer** for Claude Code. It runs a
multi-agent, adversarially-verified code review at staff-engineer rigor
(correctness, security, architecture, tests, migration safety), adapts to each
repository's own rules, and archives a project-named report. It is independent of
any spec/CI pipeline — point it at a PR, a branch, or a diff.

## Install

This repo is self-contained (it is both the plugin and its own marketplace):

```
/plugin marketplace add Oscabrera/review-strict
/plugin install review-strict
```

Then invoke `/review-strict` in any repo. (Private repo? Installers need `gh`
access to it. Public is easiest for sharing.)

## Usage

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

The manifests are already filled for `Oscabrera`. The repo follows **gitflow**:
`master` is the stable branch the marketplace installs from (`ref: master`), and
`develop` is the integration branch for ongoing work.

```
git init && git add -A && git commit -m "feat: review-strict plugin v1.0.0"
git branch -M master
git branch develop
gh repo create Oscabrera/review-strict --public --source=. --remote=origin --push
git push -u origin develop
```

Day-to-day: land changes on `develop`; merge to `master` to cut a release
(bump `CHANGELOG.md`). Consumers on the marketplace always get `master`.

## License

MIT
