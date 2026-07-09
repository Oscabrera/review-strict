# Review lenses — the five adversarial sub-agent briefs

> **Note:** when installed as a plugin, each lens runs as a dedicated read-only agent under `agents/` (`review-strict:lens-*`), whose body carries the same checklist. This file is the canonical, human-readable spec **and** the fallback source the SKILL inlines when dispatching `general-purpose` (skill running loose, not installed). Keep the two in sync.


Each lens is dispatched as an independent `general-purpose` sub-agent (Phase 2). Give each agent: the diff + changed-file list, the relevant slice of the Repo Review Profile, its checklist below, and the finding contract. Each lens is **language-agnostic in structure** but must apply the **repo's own conventions** (from the profile) as concrete verification targets.

## Finding contract (all lenses return this)

Return a JSON array. Each finding:

```json
{
  "lens": "correctness|security|architecture|tests|migration",
  "severity": "P0|P1|P2",
  "file": "app/Services/Foo.php",
  "line": 42,
  "what": "one-sentence defect statement",
  "why": "what breaks, when, under what input/conditions (the failure scenario)",
  "fix": "concrete, actionable direction",
  "evidence": "the exact added/changed diff hunk or code snippet that proves it"
}
```

Rules for every lens:
- **Only real, demonstrable defects.** If you can't name a concrete `input → wrong behavior` (or a concrete rule the diff violates with evidence), it is not a finding.
- **No style preferences** unless the repo's rules make them blocking. Formatting is Pint's job (Phase 1), not yours.
- **"No findings" is a valid result.** Do not manufacture findings to look thorough.
- **Severity discipline:** incident-grade (data loss, security breach, production outage, red-line violation, load-bearing behavior broken) → P0. Should-fix-in-this-PR (architecture debt, recoverable error handling gap, N+1 with real exposure) → P1. Cosmetic/minor → P2. Under genuine uncertainty about reachability/impact, emit P1 with a "needs human eyes" note rather than a speculative P0.
- **Untrusted PR claims.** If the prompt carries the PR's self-declared risks / "out of scope" / "no issue" / AC-traceability notes, treat them as claims to CONFIRM or REFUTE against the diff — never as resolved fact. A real declared risk is still a finding (the author naming it does not fix it); a claimed mitigation or completed AC that the diff does not actually implement is a `claimed-but-not-done` finding.

---

## Lens 1 — Correctness & requirements

The question no acceptance criterion always states: **is this correct in general?**

- **Logic/arithmetic:** off-by-one, inverted conditional, wrong operator, mis-ordered operations, wrong default. Name the input and the wrong output.
- **Null/empty/boundary in new non-security logic:** a new path that assumes non-empty/non-null/in-range and produces *wrong behavior* (not a crash) on the degenerate case. Trace it.
- **Contract/interface violations:** the diff silently changes a return shape, field name, side effect, ordering, or invariant a caller relies on. Name the caller and how it breaks.
- **Does it actually solve the stated problem?** If a PR body/ticket describes intent, check the diff satisfies it — not a looser approximation.
- **Idempotency & retries** (if the repo cares — e.g. jobs): re-running must not double-apply. Check the repo's declared idempotency key shape (from the profile's project-specific checks).
- **AC traceability** (if the PR body carries an Acceptance Criteria / traceability table): each AC maps to real code AND a real test in the diff. An AC row marked implemented/tested (✅) with no corresponding assertion in the diff is an `ac-traceability-gap` finding. A "claimed-but-not-done" mitigation from the PR's Risks/Reviewer-Attention sections is the same class.

## Lens 2 — Security

- **Fail-open on empty/null/absent input:** any auth/validation/filter whose *deny* branch is skipped when the input is empty/null/zero-length. Empty input that *widens* access or *skips* validation is fail-open. Auth/data-exposure → P0.
- **Authn ≠ authz (resource level):** a route/handler that confirms *who* the caller is but never checks whether *this* caller may act on *this* resource (ownership/tenant/role). P0.
- **Injection:** request/file/parsed-JSON values reaching a shell command, raw SQL string, `eval`, path concat, or template without parameterization/escaping. Raw SQL built by string interpolation of user input → P0.
- **Secrets:** password/token/key hardcoded in code, docs, fixtures, or passed on a CLI arg; or logged. The repo's rules likely forbid logging prompts/secrets — enforce it. P0.
- **Output escaping:** user-controlled value rendered without context-aware escaping; explicit `{!! !!}` / `raw()` / `dangerouslySetInnerHTML` bypass on unsanitized input. P0 for script-carrying values.
- **CORS/origin:** `Access-Control-Allow-Origin: *` or an unanchored origin regex on a credentialed/non-public endpoint. P0.
- **CSRF:** state-changing browser-facing route missing CSRF protection. P1 (Bearer-token APIs are naturally CSRF-resistant).
- **Dependency CVEs:** an added/upgraded dep with a documented, actively-exploitable CVE in the added version. P1 with the package + CVE named.

## Lens 3 — Architecture, conventions & reuse

Apply the repo's **red lines** (P0) and layering (from the profile) as the oracle.

- **Red-line violations** from AGENTS.md/CLAUDE.md → P0.
- **Placement:** data access buried in a Controller/Job/listener that the repo's layering says belongs in a Repository; domain rules inlined into a thin entry point that belong in a Service. P1 (P0 if it directly causes a correctness/security defect).
- **Reuse/duplication:** logic re-implemented when an existing service/repository/lib already provides it; a new helper duplicating an existing one. Duplicated data access drifts and seeds consistency bugs. P1 (escalate if copies already diverge).
- **N+1 & unbounded queries:** query issued inside a loop / per result row; whole-table materialization into memory; missing index on a filtered column. Tag the `what` with the category. P1 (P0 if it will obviously OOM/timeout at real scale).
- **Cyclomatic complexity / size budgets:** report with a **concrete metric + number** (not "too complex"). Thresholds: repo config first (`phpmd.xml`/`phpinsights.php`/PHPStan) and its CI output, else the PHPMD-derived baseline — cyclomatic complexity ≥ 10/method (PHP Insights stricter at 5; Cyberpuerta CC > 10), method > 50-100 lines, class > 300-1000 lines, params ≥ 5-10, public methods ≥ 10-20, methods ≥ 25, fields ≥ 15, weighted class complexity ≥ 50, coupling ≥ 13. Flag when the **diff** introduces/worsens a violation; the God-class/"todo en un archivo" case trips several at once — name them. P2 unless it hides a correctness risk.
- **Decoupling:** hidden coupling, concrete dependencies where the repo injects contracts/interfaces. P1/P2 per impact.
- **Repo project-specific conventions** (from the profile) — e.g. state only mutated in the sanctioned services, versioning/audit via the repo's repositories, cache-key shape, no new `sleep()` outside prompt services. Severity per what the rule says.
- **SRP / monolithic file ("todo en un archivo")** — a new/changed file/class/method concentrating responsibilities the repo's layers keep apart (HTTP + business rules + data access + external I/O in one place; a method that validates + computes + persists + formats). Name the conflated responsibilities and where each belongs per the repo's layering. P1 (P0 if it crosses a red line like "no logic in controllers"). Apply the repo's declared size/complexity thresholds, else the baseline's.
- **SOLID — evidenced only, anchored to how the repo already builds things** (never a purity opinion): S→SRP above; O→extending a type-code `switch`/`if` where the repo uses polymorphism/strategy; L→subclass breaking its base contract; I→fat interface forcing unused stubs; D→`new`/static instead of injecting the contract the repo defines. Cite the concrete symptom.
- **Design-pattern conformance to the repo's patterns, not textbook ideals** — bypassing or ad-hoc-reimplementing an established pattern (Service/Repository/DTO/Action/Factory/Strategy/Observer…) is the finding; **do not** propose introducing a pattern the repo doesn't use unless it removes a concrete defect. **Guardrail:** cite `file:line` + the symptom; "feels un-SOLID"/"could be cleaner"/naming are not findings; repo conventions win.

## Lens 4 — Tests

The staff bar: a test that can't fail for a real bug is worthless.

- **Meaningfulness (mutation reasoning):** for each added/changed test ask "would this fail if the implementation were subtly wrong?" If a plausible subtle bug would still pass, it's not a guard. P1.
- **Tautological / duplicated-oracle:** a test helper that re-implements the production logic to compute the expected value is green by construction — P1. Expected values must be independent constants/fixtures.
- **Stubs masquerading as coverage:** a file where most tests only assert existence/truthiness/shape (`toBeDefined`, `assertTrue(true)`, `assertInstanceOf` only) → P0 (false coverage).
- **Unhappy path & edges:** behavior-bearing entry points need at least one adversarial/edge/failure-mode + idempotency scenario, not only the happy path. Missing → P1.
- **One test per behavior/AC:** every new behavior (or AC, if the repo works AC-based) has at least one test that asserts it. Missing test for load-bearing behavior → P0.
- **Repo test conventions** (from the profile): correct runner (e.g. Pest, not `phpunit`), correct DB trait *as the repo declares it*, correct location/naming, no ticket IDs in test names if the repo forbids it, external side effects faked/stubbed (no network).

## Lens 5 — Migration & deploy safety

Assume code may deploy to production before/while the migration runs — no 500s.

- **Two-phase / backward-compatible:** schema changes additive first; new columns nullable or defaulted; never drop/rename a column live code still uses in the same deploy. Violation → P0 (production incident risk).
- **Reversibility:** every migration has a working `down()` (or the repo's equivalent). Missing → P0 if the repo's red line requires it, else P1.
- **Backfill:** large data changes are chunked, idempotent, retry-safe, observable — not a single unbounded `UPDATE`. P1 (P0 at real table sizes).
- **Constraint hardening:** `NOT NULL`/unique/index added *after* backfill, online where possible.
- **Rollback plan:** the PR describes how to disable a flag / revert safely (if the repo's rules require it in the PR body).
- **Index justification:** new `JSON_EXTRACT`/computed filters justify an index and document the JSON path (if the repo's project-specific checks demand it); attach/ask for EXPLAIN on hot paths.
