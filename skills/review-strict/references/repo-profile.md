# Repo Review Profile — how to adapt to the repository

The profile is what makes `/review-strict` repo-adaptive. Build it in Phase 0, before any lens runs. Follow the repo's declared rule ownership and path scopes. An explicitly canonical contract wins over its summaries; scoped conventions refine it without overriding mandatory requirements. The plugin baseline is a fallback, not a competing policy.

## Step 1 — Locate & detect

- `REPO_ROOT = git rev-parse --show-toplevel`.
- Stack: read `composer.json` (Laravel/PHP? `require.php`, `laravel/framework`), `package.json` (Vue/React/TS?), presence of `phpunit.xml`, `pint.json`, `phpstan.neon`.
- **Complexity/quality config:** look for `phpmd.xml`(`.dist`), `phpinsights.php`, and any PHPStan cognitive/cyclomatic-complexity rules. If present, extract the repo's configured thresholds (cyclomatic complexity, method/class length, parameter/method/field counts, coupling) — these become the architecture lens's `complexity_thresholds` and **override** the baseline defaults. Most repos do NOT run PHPMD/PHP Insights — if one does, note it so Phase 1 can read the evidence; otherwise the architecture lens estimates complexity from the diff (it does not depend on the tools being installed).
- Base branch: `--base` flag → else a configured base in `AGENTS.md`/CLAUDE.md workflow block (`git.base_branch`) → else `development` if it exists on origin → else `main`.
- Docker: does the repo have a `docker-commands` skill or `docker-compose.yaml`? Capture the exec prefix (e.g. `docker compose exec -T app`) — most CP repos run pint/phpstan/pest **inside** the container.

## Step 2 — Load the rule sources

The durable sources below are present in every Cyberpuerta repo and are the PRIMARY input. Read them first; the skill's bundled baseline (Step 3 of the skill) always applies on top.

1. **`AGENTS.md` / `CLAUDE.md`** (repo root) — the primary review contract in every CP repo. Extract:
   - **Red lines** ("do not cross") and the **"Forbidden patterns"** list — these are hard P0/Blocker triggers.
   - Layering/architecture description (Controller → Service → Repository, DTOs, Contracts) — the placement oracle for the architecture lens.
   - **Code standards** (strict types, PER/PSR-12, no fat controllers, FormRequest validation, N+1, `DB::transaction`, etc.) and **testing** rules (runner, e.g. Pest not `phpunit`; `RefreshDatabase` vs a persistent DB — **use what the repo says**).
   - Exact build/lint/static/test commands, base branch, branch/commit conventions.

2. **`.claude/rules/*.md` and `.codex/rules/*.md`**, when present — read rules whose declared scopes match the reviewed files or planned changes. Include applicable nested `AGENTS.md` files. Pass the actual rule text and scope to the relevant lenses.

3. **`.codex/skills/*/SKILL.md` and `.claude/skills/*/SKILL.md`** — relevant machine-adjacent conventions:
   - `coding-conventions` → concrete style/pattern targets.
   - `migration-rules` → the migration lens's checklist.
   - `repo-conventions` → catch-all repo rules.
   - `docker-commands` → the exact exec prefix for Phase 1 toolchain runs.
   Treat each non-empty rule body as a **verification target**; skip files left as `TODO` stubs. Respect the governing contract's declared precedence.

4. **Canonical review contracts.** Follow pointers in the repo's rules. When present, load `contract/review-rubric.md` for severity/disposition and `contract/spec-review-rubric.md` for spec obligations. Load applicable test-quality/Test Intent rules. For Stratos, follow [stratos-contracts.md](stratos-contracts.md). Missing required contracts make a review incomplete; a generic repo need not install Stratos to be reviewed.

5. **`.aiassistant/rules/*.md` — OPTIONAL / LEGACY, being phased out.** Do NOT depend on these; they are **not present in every repo** and are being removed. If any exist (e.g. an older `pr-review-rules*.md` / `pr-review-rules-<flavor>.md`, `Repository Engineering Rules.md`, `Commit Review Rules.md`, `guidelines.md`), load them as **extra** signal as *format / severity vocabulary / save path / project-specific checks*, without overriding a current canonical contract (e.g. an SEO Content AI section: `seo_texts` state orchestration, job idempotency keys, AI-integration timeouts). If none exist, ignore silently — the durable sources above plus the bundled baseline fully carry the review. Never emit "no rules found → can't review"; the baseline is always there.


Legacy rules do not override an explicitly canonical current contract.

## Step 3 — Assemble the profile object

Hold these fields (in memory) and inject the relevant slice into each lens/verify prompt:

- `stack`, `repo_root`, `base_branch`, `docker_exec_prefix`
- `severity_vocab` + crosswalk to P0/P1/P2 (see `severity-output.md`)
- `output_policy` (header fields, errors-only, evidence rule) and `output_template` (if the repo supplies one)
- `blocking_checks[]` — repo-declared blockers
- `contracts[]`, `scoped_rules[]`, `review_obligations[]` — loaded sources and applicable work to discharge
- `disposition_policy` — what requires a fix, filing, or an advisory reply, separate from severity
- `test_intent_policy` — frozen per-ticket version and applicable reuse/new-test rules, or not applicable
- `red_lines[]` — from AGENTS.md/CLAUDE.md (always Blocker)
- `project_specific_checks[]` — e.g. SEO-AI orchestration/idempotency/AI-integration rules
- `commands` = { lint, static, test } with the docker prefix applied
- `complexity_thresholds` — from `phpmd.xml`/`phpinsights.php`/PHPStan if declared; else null (architecture lens falls back to its PHPMD-derived baseline budget)
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
