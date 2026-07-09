# Severity crosswalk, verification protocol, and output

## Severity crosswalk

Reason internally in P0/P1/P2; report in the **repo's vocabulary** (from the profile). Default crosswalk when the repo uses Blocker/Major/Minor:

| Internal | Repo term | Meaning | Blocks merge? |
|---|---|---|---|
| **P0** | **Blocker** | Data loss, security breach, production outage, red-line violation, load-bearing behavior broken/untested, false-coverage stub tests, hardcoded env paths in runtime code, unsafe migration | **Yes** |
| **P1** | **Major** | Should fix in this PR: architecture debt, recoverable error-handling gap, N+1 with real exposure, missing tests for real behavior, missing docblocks on new public API | Should |
| **P2** | **Minor** | Cosmetic, naming, small refactor — deferrable if justified | No |

If the repo defines different words or levels, map onto them and keep the "blocks merge" column semantics.

**Spec-review vocabulary (`/spec-strict`).** A spec review reports readiness, not merge-blocking, so it uses its own words that map 1:1 onto the internal levels:

| Internal | Spec term | Meaning |
|---|---|---|
| **P0** | **block** | Omission that will cause a runtime fatal / re-open / wrong-stack command / unauthorized red-line — fix the spec before Forge. |
| **P1** | **should-fix** | Will cost a fix commit or a reviewer round-trip. |
| **P2** | **nice-to-have** | Clarity / robustness. |

Any surviving **block** → the readiness verdict is `revise-before-Forge`; otherwise `ready` (with should-fix / nice-to-have listed).

## Verification protocol (Phase 3)

Every candidate finding must survive a **refute** pass before it reaches the report.

- **Default is refuted.** The skeptic assumes the finding is wrong until the exact `file:line` evidence in the actual diff/codebase proves it.
- For each finding, the skeptic re-reads the cited location and returns:
  - `real` — evidence confirms the defect exactly as stated → keep.
  - `not-real` — the cited code doesn't do what the finding claims, the case is already handled elsewhere, the repo explicitly allows it, or the "caller" doesn't exist → **drop**.
  - `uncertain` — plausible but not provable from available context → keep only as a demoted "Reviewer attention" note (never a Blocker), naming what a human should check.
- **Adjust severity down** if the impact is real but the reachability is limited (e.g. an internal-only path). Never inflate.
- Multi-agent mode dispatches this as a dedicated skeptic sub-agent over the deduped finding list; `--fast` mode does it inline with the same discipline.

The cost of a false Blocker is a wasted dev cycle chasing a non-bug; the cost of a missed real bug is an incident. Bias to P1+attention under real uncertainty, P0 only when you can name the exploit/failure.

## Default output template (used when the repo supplies none)

Author the report in the resolved language (**English by default**; Spanish when it resolves to `es` via `--lang es` / `REVIEW_STRICT_LANG=es`) — prose only; code, identifiers, paths, commands, `file:line`, severity keywords, and evidence hunks stay verbatim. **Hard rule:** anything posted outward — a GitHub PR comment/review or a ClickUp comment — is ALWAYS in English regardless of the report language. Match the repo's template if it defines one. Otherwise:

**Localize the section headers to the report language** (default **English**; Spanish when the language resolves to `es` via `--lang es` / `REVIEW_STRICT_LANG=es`). The decision keywords (`request-changes` / `comment` / `approve`) map to GitHub review events and, together with all code / paths / commands / `file:line`, stay verbatim in every language. Default English template:

```markdown
# Review — <repo> · <PR #N | branch <name>> vs <base>

- **Decision:** request-changes | comment | approve
- **Estimated effort to review:** <1–10>/10   <!-- include only if the repo's rules ask for it -->
- **Recommended focus areas:** <3–5 comma-separated areas>
- **Profile:** <repo rules loaded | generic staff baseline (no repo rules found)>

## Build checks
- Lint (<cmd>): <summary or "not run — reason (CI corroborates)">
- Static analysis (<cmd>): <summary or "not run — reason (CI corroborates)">

## Findings
<!-- most-severe first; omit a severity section if empty -->

### Blockers
- [ ] **<file>:<line>** — <what>
  - **Why:** <failure scenario — what breaks, when>
  - **Fix:** <actionable direction>
  - **Evidence:** `<diff hunk / snippet>`

### Major
- [ ] ...

### Minor
- [ ] ...

## Reviewer attention (uncertain — needs human eyes)
- <file>:<line> — <what to check and why>

## Notes
- <baseline findings the repo checklist didn't request, if any, labeled here>
```

Spanish header equivalents when the language is `es`: `# Revisión`, `Decisión`, `Esfuerzo estimado de revisión`, `Áreas de foco recomendadas`, `Perfil`, `Build checks`, `Hallazgos`, `Bloqueantes`, `Mayores`, `Menores`, `Atención del revisor (incierto — requiere ojos humanos)`, `Notas`.

Rules for the report:
- **Errors only.** No praise, no summary of what the PR does. If there are zero blocking findings, say so plainly and list any Major/Minor.
- **Every finding cites `file:line` + evidence.** Drop anything that can't.
- **Final decision is honest:** any surviving Blocker → `request-changes`.
- Keep it scannable: conclusion (decision) at the top, detail below.

## Save-path resolution (Phase 5)

**Primary (always, unless `--no-save`) — portable archive:**

- **Default (portable — works for any developer):** inside the reviewed repo → `<repo-root>/reviews/<file>`.
- **Override:** if `REVIEW_STRICT_ARCHIVE_DIR` is set → `$REVIEW_STRICT_ARCHIVE_DIR/<repo>/<file>`.
- **Filename carries project + review id:** PR → `<repo>-pr-<N>.md` (e.g. `cp-shops-pcb-pr-433.md`); branch → `<repo>-<branch-slug>.md`. Re-runs → append `-<n>` to the stem.
- `mkdir -p` the target dir; print the exact path after.
- **Write with a Bash quoted heredoc, not the Write/Edit tool** (see SKILL.md Phase 5) — literal `$`/backticks, and no cross-repo edit-guard when the override points outside the repo.
- The in-repo `reviews/` folder is output, not source — suggest adding it to `.gitignore` unless the team wants review history committed.

**Secondary (only with `--repo-copy`) — the repo's own declared path:**

- If the profile declares a reviews path (`.ai/pr-reviews/`, `.ai-abstracts/pr-reviews/`), also write a copy there; otherwise skip.
