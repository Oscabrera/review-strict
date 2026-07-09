# Phase 1 — Structural grounding & the verified inventory

The inventory is what makes `/audit-strict` **cite-accurate**. Cartographers cite ONLY from evidence that traces back to this inventory (or to files they Read themselves). Build it in Phase 1, before any cartographer runs. This is the layer that kills hallucinated `file:line` ranges and false "X is missing" claims.

## Step 1 — Graphify first (if available)

The project convention (root `CLAUDE.md`) mandates graphify when its graph exists. Check and use it:

```bash
test -f graphify-out/graph.json && echo "graphify: yes" || echo "graphify: no"
```

If present, seed the inventory with:
- `graphify query "<the audit question, e.g. principal services, jobs, controllers and how they connect>"` — scoped subgraph of the relevant nodes/edges.
- `graphify explain "<principal entity / domain concept>"` — focused concept map for the lifecycle & data-model cartographers.
- `graphify path "<A>" "<B>"` — to confirm a claimed relationship between two modules before a cartographer asserts it.

Graphify output is a **starting map**, not proof. Cartographers still Read the cited files to pin exact line numbers and snippets.

## Step 2 — Deterministic inventory (always; the fallback when graphify is absent)

Build a stack-appropriate inventory with `rg`/glob (read-only). Do not install anything.

**Backend (Laravel/PHP):**
```bash
rg -l --type php 'class .* Controller' app/ 2>/dev/null | head -100      # controllers
fd -e php . app/Services 2>/dev/null || find app/Services -name '*.php'    # services
find app/Repositories app/Jobs app/Models app/Enums app/Constants -name '*.php' 2>/dev/null
find database/migrations -name '*.php' 2>/dev/null                          # schema source
rg -n 'Route::|#\[Route|#\[Get|#\[Post' app/ routes/ 2>/dev/null | head    # routes (incl. Spatie attrs)
```

**Vue/Nuxt (frontend):**
```bash
find pages layouts components composables stores plugins middleware -type f 2>/dev/null
test -f nuxt.config.ts && echo "nuxt" ; test -f nuxt.config.js && echo "nuxt"
rg -n 'defineStore|definePageMeta|defineNuxtRouteMiddleware|useFetch|\$fetch|axios' . 2>/dev/null | head
```

Record, per entry: **path**, one-line role, and (for the hot ones) the entry method + its line range. This list is the *only* set of files a cartographer may cite without having Read them itself — and even then, the cartographer Reads to get the exact snippet.

## Step 2b — Dependency & CVE grounding (best-effort, non-blocking)

A security-flavored audit that never looks at dependencies is incomplete. Capture, read-only:
- **Manifest facts** (always): framework + language version and their support status (e.g. is the framework EOL / security-only?), lockfile presence and package count, and whether a dependency-update bot is configured (`.github/dependabot.yml`, `renovate.json`).
  ```bash
  grep -E '"(php|laravel/framework|next|nuxt|vue|react)"' composer.json package.json 2>/dev/null
  test -f composer.lock && echo "lock: $(grep -c '"name":' composer.lock) pkgs"
  ls .github/dependabot.yml renovate.json 2>/dev/null || echo "no dep-bot"
  ```
- **CVE scan** (best-effort, like review-strict's toolchain step): if `composer audit` / `npm audit --omit=dev` run without installing anything, run and summarize. **Do NOT install to make them run.** If they can't run, record "CVEs no escaneados — acción requerida" as an explicit gap — never imply "no CVEs".
- Feed a `dependencies` slice into synthesis so the deliverable scores a **Dependencias & CVEs** dimension (EOL framework, known CVEs, no update bot). "No se ejecutó" is an honest finding, not an omission.

## Step 3 — The verified-inventory contract (passed to every cartographer)

Pass this into each Phase-2 dispatch:
- `stack` = `backend | vue-nuxt | both`
- `inventory` = the categorized file list above (paths + roles; ranges where known)
- `repo_profile` slice = layering, red lines, declared observability/telemetry, in-progress migrations, testing conventions, base branch (from Phase 0 — **ground truth**)
- `graphify_available` = true/false (so a cartographer knows whether it can `graphify explain` for more)

## Rules

- **Read-only.** `rg`, `find`, `fd`, `test`, `graphify query/explain/path` only. No writes, no installs, no branch switches.
- **Absence claims need a negative search.** If the inventory step's Grep for a pattern (e.g. `CircuitBreaker`, `sentry`, `->retry(`) returns nothing, that negative result is what licenses a cartographer's "No evidenciado" — a cartographer must never assert absence the inventory didn't probe.
- **The repo profile wins.** If Phase 0 loaded a `CLAUDE.md` that names telemetry/Horizon/alerts, the inventory must reflect it; a cartographer claiming "no observability" against that is a verify-skeptic drop in Phase 3.
