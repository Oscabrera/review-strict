# Repo Review Profile — how to adapt to the repository

The profile is what makes `/review-strict` repo-adaptive. Build it in Phase 0, before any lens runs. Load everything with **local-wins precedence**: a repo-local statement always overrides the generic baseline, and a more specific file (a `.claude/skills` convention) overrides a more general one (a top-level guideline) on the same point.

## Step 1 — Locate & detect

- `REPO_ROOT = git rev-parse --show-toplevel`.
- Stack: read `composer.json` (Laravel/PHP? `require.php`, `laravel/framework`), `package.json` (Vue/React/TS?), presence of `phpunit.xml`, `pint.json`, `phpstan.neon`.
- Base branch: `--base` flag → else a configured base in `AGENTS.md`/CLAUDE.md workflow block (`git.base_branch`) → else `development` if it exists on origin → else `main`.
- Docker: does the repo have a `docker-commands` skill or `docker-compose.yaml`? Capture the exec prefix (e.g. `docker compose exec -T app`) — most CP repos run pint/phpstan/pest **inside** the container.

## Step 2 — Load the rule sources

The durable sources below are present in every Cyberpuerta repo and are the PRIMARY input. Read them first; the skill's bundled baseline (Step 3 of the skill) always applies on top.

1. **`AGENTS.md` / `CLAUDE.md`** (repo root) — the primary review contract in every CP repo. Extract:
   - **Red lines** ("do not cross") and the **"Forbidden patterns"** list — these are hard P0/Blocker triggers.
   - Layering/architecture description (Controller → Service → Repository, DTOs, Contracts) — the placement oracle for the architecture lens.
   - **Code standards** (strict types, PER/PSR-12, no fat controllers, FormRequest validation, N+1, `DB::transaction`, etc.) and **testing** rules (runner, e.g. Pest not `phpunit`; `RefreshDatabase` vs a persistent DB — **use what the repo says**).
   - Exact build/lint/static/test commands, base branch, branch/commit conventions.

2. **`.claude/skills/*/SKILL.md`** — the most specific, machine-adjacent conventions:
   - `coding-conventions` → concrete style/pattern targets.
   - `migration-rules` → the migration lens's checklist.
   - `repo-conventions` → catch-all repo rules.
   - `docker-commands` → the exact exec prefix for Phase 1 toolchain runs.
   Treat each non-empty rule body as a **verification target**; skip files left as `TODO` stubs. On a same-point collision with a general guideline, the skill body wins.

3. **`.aiassistant/rules/*.md` — OPTIONAL / LEGACY, being phased out.** Do NOT depend on these; they are **not present in every repo** and are being removed. If any exist (e.g. an older `pr-review-rules*.md` / `pr-review-rules-<flavor>.md`, `Repository Engineering Rules.md`, `Commit Review Rules.md`, `guidelines.md`), load them as **extra** signal and let them win on conflict for *format / severity vocabulary / save path / project-specific checks* (e.g. an SEO Content AI section: `seo_texts` state orchestration, job idempotency keys, AI-integration timeouts). If none exist, ignore silently — the durable sources above plus the bundled baseline fully carry the review. Never emit "no rules found → can't review"; the baseline is always there.

## Step 3 — Assemble the profile object

Hold these fields (in memory) and inject the relevant slice into each lens/verify prompt:

- `stack`, `repo_root`, `base_branch`, `docker_exec_prefix`
- `severity_vocab` + crosswalk to P0/P1/P2 (see `severity-output.md`)
- `output_policy` (header fields, errors-only, evidence rule) and `output_template` (if the repo supplies one)
- `blocking_checks[]` — repo-declared blockers
- `red_lines[]` — from AGENTS.md/CLAUDE.md (always Blocker)
- `project_specific_checks[]` — e.g. SEO-AI orchestration/idempotency/AI-integration rules
- `commands` = { lint, static, test } with the docker prefix applied
- `migration_policy` (two-phase deploy checklist)
- `save_path_pattern` + re-run naming
- `anti_patterns[]`

## Step 4 — Degradation

If a repo is thin on context (only `AGENTS.md`/`CLAUDE.md`, `.claude/skills` are TODO stubs, and no `.aiassistant/rules`):
- Fall back to the profile defaults: severity = Blocker/Major/Minor, output = the default template in `severity-output.md`, checks = the always-on baseline in `baseline-criteria.md` (staff bar + durable Laravel/PHP & TS/Vue conventions).
- **Say so in the report header** (e.g. "Perfil: solo AGENTS.md/CLAUDE.md — sin reglas .aiassistant; se usa el baseline del skill") so the reader knows how repo-tuned the review was.
- Never refuse to review for lack of rule files — the baseline always applies.

## Conflict resolution (important)

When a generic pack and the repo disagree, **the repo wins on how to review** (severity words, output shape, which commands, test-DB trait), and the baseline still contributes **findings** (a real defect the repo's checklist didn't mention is still reported — labeled as a baseline finding, never dropped). Example: a generic pack says "always `DatabaseTransactions`" but the repo's guidelines say "use `RefreshDatabase` for Feature tests" — follow the repo; do **not** flag `RefreshDatabase` as a defect.
