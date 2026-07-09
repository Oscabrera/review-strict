# Cartographers — the deep-analysis sub-agent briefs

> **Note:** when installed as a plugin, each cartographer runs as a dedicated read-only agent under `agents/` (`review-strict:cart-*`), whose body carries the same checklist. This file is the canonical, human-readable spec **and** the fallback source the SKILL inlines when dispatching `general-purpose` (skill running loose, not installed). Keep the two in sync — same rule as `lenses.md`.

Each cartographer is dispatched independently (Phase 2). Give each: the **verified inventory** (Phase 1), the relevant **Repo Review Profile** slice, the detected **stack**, and — for cart-quality — the **baseline slice** (`../../review-strict/references/baseline-criteria.md`). Each is language-agnostic in structure but must apply the **repo's own conventions** as ground truth.

## Shared claim contract (all cartographers return this, after their markdown section)

```json
{"cartographer":"components|flows|lifecycle|datamodel|quality",
 "kind":"citation|relationship|finding",
 "file":"relative/path.ext","line":"42 or 120-240 (start<=end)",
 "claim":"one-sentence assertion tied to this exact location",
 "evidence":"the exact snippet READ at that location",
 "severity":"P0|P1|P2"}
```
`severity` only on `kind":"finding"`. This is the list Phase 3 (verify-skeptic) refutes.

## Shared anti-defect discipline (every cartographer, non-negotiable)

These four rules are the entire reason `/audit-strict` exists — they are the fixes for the four defects observed in the prior "codex" run:

1. **Cite only what you read this session.** Every `file:line` comes from a real Read/Grep. A range has `start <= end`. (Fix for the impossible `718-716` citation.)
2. **Never assert absence without a negative Grep**, and never contradict the repo profile. If unproven → **"No evidenciado"**. (Fix for "no observability" when telemetry exists, and for recommending an already-in-progress migration.)
3. **No placeholders** — never emit `{{...}}` or a templated blank; missing inputs go to `preguntas.md`. (Fix for the leaked `{{DESCRIBE_NEW_LOGIC}}`.)
4. **Even depth** — every subsection gets real treatment; no front-loaded richness followed by thin bullet stubs. (Fix for the 191-line vs 17-line imbalance — the fan-out itself enforces this: each cartographer owns one deliverable and has budget for it.)

---

## cart-components — Components & interconnections

- **Backend:** controllers, services, repositories, models, jobs/queues, traits, contracts, providers, console/cron. External: distributor/ERP/payment SDKs, Horizon/Redis queues, webhooks, sibling microservices, cache. Responsibility per module; internal vs external deps; strong coupling (orchestration+integration+persistence in one class); SPOFs; hot paths (cite entry method).
- **Vue/Nuxt:** pages, layouts, components, composables, stores (Pinia/Vuex), plugins, middleware, route guards, HTTP/API clients. SSR/CSR/ISR boundaries; nav guards; the central store/plugin every route funnels through (SPOF); heaviest screens (hot paths).

## cart-flows — End-to-end flows (+ `sequenceDiagram`)

- 3–6 principal flows. **Coverage rule:** must include the repo's primary user-facing/product flow (builder/compatibility engine, checkout, search, …), not only event-driven/webhook/async/cron flows — cross-check the inventory's controller groups; every group with real business endpoints gets a traced flow or an explicit out-of-scope note. Who starts, inputs/outputs. Sequential steps with `file:line`: event → entry → service/composable/store → external call → state change → response/render. Errors/timeouts/retries (Grep-prove absence before claiming it). One `sequenceDiagram` per flow with real participant names.
- **Vue/Nuxt flows:** user event → component → composable/store → API call → state update → re-render; how loading/error/empty states are shown.

## cart-lifecycle — States & transitions (+ `stateDiagram-v2`)

- States from the repo's real enums/constants (backend `app/Enums`/`app/Constants`; frontend store status + `loading`/`error`/`empty`). Transitions: event → from → to + gating rule + side effects, each cited. Persistence & third-party sync (if evidenced). Use the repo's real state names verbatim.

## cart-datamodel — Derived data model (+ `erDiagram`)

- **Backend:** from `database/migrations/**` + models — tables, columns+types, PK/FK/UK, indexes, constraints, relations (cite migration + model method). Flag finance/audit-critical fields (amounts, currency, timestamps, idempotency keys, event logs).
- **Vue/Nuxt:** from stores + TS types/DTOs — store shapes, fields+types, ids, normalized vs nested, API DTOs, adapters/mappers. Describe backend shape only if evidenced by shared types — never invent SQL from a frontend guess.

## cart-quality — Quality audit (reuses the review-strict lens oracles + baseline)

Apply the **architecture**, **security**, and **tests** lens checklists from `../../review-strict/references/lenses.md` and the six baseline dimensions from `../../review-strict/references/baseline-criteria.md`, but repo-wide (not diff-scoped):
- Good practices (specific, no vague praise) · Bad practices/smells (quote duplication copies) · Security/privacy · Performance/cost · Operational risk.
- **Per-resource ownership (IDOR):** for every state-changing/detail endpoint on a user-owned resource (config, quote, cart, build, user, order…), verify the handler checks the caller *owns this record* (compares the record's `user_id`/tenant to the authenticated identity), not just that a token exists — and that ownership is NOT decided from client-supplied unverified input (body `userId`, an id header). Report missing-auth and missing-ownership as separate findings.
- **Vue/Nuxt specifics:** reactivity anti-patterns (side-effects in `computed`, excessive `watch`), God components, scattered API calls with no client layer, token/secret handling in the client, XSS via `v-html`, bundle/lazy-load gaps.
- Findings feed `recomendaciones.md` — every recommendation must trace back to a verified finding here.
