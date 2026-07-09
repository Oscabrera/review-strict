# Always-on staff baseline — the reviewer's own criterion

This is the independent standard `/review-strict` applies **on top of** whatever the repo declares — the "separate criterion" that keeps the review rigorous even when a repo's rules are thin or missing. These dimensions are review-blocking when violated in the current diff; they are never deferred as "later". Findings raised here are labeled as baseline findings and reported even if the repo's own checklist didn't ask for them.

## The six baseline dimensions

1. **Meaningful tests.** Tests assert real behavior, edge cases, failure modes, and idempotency — including the unhappy path. No tautological tests that mirror the implementation to go green; a test that can't fail for a real bug is worthless. New/changed behavior without a test that would catch its regression is a finding.

2. **Architecture, SOLID & reuse.** Respect the project's layering, established patterns and conventions; reuse existing code before adding new. **No logic dumped into one monolithic file, class or method** — a change concentrating responsibilities the repo's layers keep apart (HTTP + business rules + data access + I/O in one place) is a Single-Responsibility violation and a finding, escalated if it crosses a repo red line. Check SOLID and design-pattern **conformance to how the repo already builds things** — but only on an *evidenced symptom* (a conflated responsibility, a bypassed established pattern, a broken contract, a concretion where the repo injects an interface), never as a purity opinion, and never by proposing a pattern the repo doesn't use. (The architecture lens owns the deep check.)

3. **Defensive programming.** Validate inputs; handle null/empty/boundary cases; fail safe; never assume the happy path or trust callers. Fail-safe includes **config/env boolean coercion**: a flag or kill-switch read from `env()` and consumed by truthiness fails OPEN for any off-synonym `env()` does not map (`off`/`no`/`disabled` stay truthy strings and *arm* the guarded behavior) — require `filter_var(FILTER_VALIDATE_BOOLEAN)` (or an explicit cast) at the boundary, and expect tests to cover the off-synonyms, not just `false`/`null`. (Security lens owns the deep check.)

4. **Performance hygiene.** No read or write N+1; no unbounded materialization of a table into memory (prefer anti-joins + bounded `whereIn` over chunks); bounded worker memory; real indexes on the columns actually filtered.

5. **Low cyclomatic complexity.** Small, single-responsibility methods; flatten nesting with early returns/guard clauses. Report complexity with a **concrete metric and number**, not "too complex" — cyclomatic complexity is the headline; also weighted class complexity (Σ of method CC), method/class length, parameter count, public-method count and coupling. Since PHPMD/PHP Insights usually aren't wired into these repos, **count it from the changed code yourself** (exact where countable; CC as an estimate from decision points). Repo-configured limits (`phpmd.xml`/`phpinsights.php`/PHPStan) win on thresholds; the architecture lens carries the PHPMD-derived default budget when the repo is silent.

6. **Decoupling.** Depend on contracts/interfaces; inject dependencies; avoid hidden coupling.

## How the baseline interacts with the repo profile

- The baseline **adds coverage**, it does not override the repo. If the repo defines severities as Blocker/Major/Minor, report baseline findings in those words too.
- If the repo's rules and the baseline point at the same defect, report it once (dedup in Phase 3), attributing to the repo rule (more specific).
- If the baseline flags something the repo explicitly allows (e.g. a documented exception), **defer to the repo** and do not flag it. The repo is authoritative about its own trade-offs.

## Generic stack defaults (used only when the repo declares nothing)

- **Laravel/PHP** (durable Cyberpuerta conventions — kept here so the review stays rigorous even where per-repo rule files were removed):
  - **Layering:** thin controllers (coordination/validation/response only); business logic in `app/Services/**` (or Actions); complex/reused queries in `app/Repositories/**`; DTOs in `app/DataObjects/**` with no business logic; DI over `new`.
  - **Validation & auth:** FormRequest classes for input (no raw request reads for validated fields); Policies/Gates before acting on models; no mass-assignment of raw input (use `$fillable` / DTO mapping).
  - **Types & style:** `declare(strict_types=1);` at the top of PHP files under `app/`/`src/`/`packages/`; native type hints on params/returns/properties, avoid `mixed`; PER Coding Style 3.0 + PSR-12; short array syntax.
  - **Data:** avoid N+1 (`with()`/`loadMissing()`); `DB::transaction()` for multi-step state changes; safe/reversible/two-phase migrations; pagination/chunking for heavy queries.
  - **Errors & hygiene:** domain-specific exceptions over generic `Exception`; never silence exceptions (no `@`, no empty `catch`); no `dd()`/`var_dump()`/debug leftovers; structured logs without secrets/PII; English-only code & comments.
  - **Complexity thresholds (refactor triggers)** — Cyberpuerta's stated bar, stricter than PHPMD's defaults: cyclomatic complexity > 10; method > 50 lines or > 5 params; class > 300 lines or > 20 public methods; weighted class complexity (Σ method CC) high (PHPMD flags ≥ 50); high coupling between objects (PHPMD ≥ 13); logic duplicated across 3+ locations; no deep nesting (> 3 levels — use early returns). No fat controllers, no God classes. A repo's own `phpmd.xml`/`phpinsights.php` numbers override these.
- **TypeScript/Vue/React:** explicit types on public contracts; guard external-boundary values (fetch/parsed JSON/file reads) before deref; handle the clear/empty path (`[] !== null` truthy-empty-array trap); binding type match (array-emitting component into single-value state); validation checks format, not just non-empty; no `console.log` in production paths.

Keep the baseline language-agnostic in spirit: the six dimensions apply to any stack; the stack defaults are only a fallback when the repo is silent.
