# Deliverables — the audit output contract

`/audit-strict` writes a **multi-file, self-contained** analysis to the resolved output dir — in-repo `<repo-root>/audit-strict/` by default, or `<base>/audit-strict/<repo>/` when a base is configured (see SKILL.md "Folder precedence"). Each file stands on its own (no "see the other file" cross-reference as the only content). All diagrams are embedded Mermaid. The `analisis.json` block must be valid JSON.

## The ten files

| File | Owner (cartographer / synth) | Content |
|---|---|---|
| `README.md` | synth | Non-technical exec summary + a **per-dimension scorecard** + findings **grouped by dimension** + index linking every other file. See "Balanced summary" below — do NOT emit a single severity-ranked flat list. |
| `componentes.md` | cart-components | Component map, responsibilities, internal/external deps, coupling, SPOFs, hot paths. |
| `flujos.md` | cart-flows | Principal end-to-end flows, each with a `sequenceDiagram`. |
| `ciclo-vida.md` | cart-lifecycle | Principal entity states/transitions + `stateDiagram-v2`. |
| `datos.md` | cart-datamodel | Derived data model + `erDiagram`. |
| `auditoria.md` | cart-quality | Good/bad practices, security, performance, operational risk (verified findings only). |
| `recomendaciones.md` | synth | Prioritized recommendations table + phased roadmap (see below). |
| `pruebas.md` | synth (from cart-quality tests findings) | Test-case matrix per flow/state, fixtures needed, coverage gaps. |
| `preguntas.md` | synth | Open questions + assumptions with confidence (alto/medio/bajo). Any section that lacked an input lands here — NOT as a `{{placeholder}}`. |
| `analisis.json` | synth | Valid JSON technical summary (schema below). |

Naming is **generic** — do not hardcode a domain (the prior run used `suscripciones.md`, which only fits CSP). Use the repo's actual principal entity name in the *prose*, but keep the *filenames* as above.

## `README.md` — the balanced summary (avoid single-dimension tunnel vision)

A pure severity-ranked "top N risks" list makes whichever dimension holds the P0/P1s (almost always **security**) monopolize the reader's first impression and bury performance, data-model, consistency and architecture work of equal importance. The README MUST give **every dimension a seat**:

1. **⚠️ Confianza y condicionalidad (box, right after the title)** — three short points the reader must see BEFORE the findings, because they reframe everything: (a) what "verified" means — the skeptic confirmed **citation accuracy (the code says what the finding says), NOT exploitability or measured impact**; (b) **security severities are conditional on reach** — if the audit couldn't confirm the perimeter (internet vs internal-only / VPC / service mesh), say so and make the #0 action "confirm exposure"; cite any exposure signal found (ingress/gateway/LB config); (c) **blast radius unknown** without business data (row counts) — severities are gravity-if-reachable, not probability.
2. **Exec summary** — what the system does + one honest "salud general" sentence that names the *spread* of weaknesses across dimensions, not just the scariest one.
3. **Scorecard por dimensión** — a table scoring each dimension **1–5** (5 ejemplar · 4 sólido · 3 aceptable con brechas · 2 débil · 1 crítico), with the dimension's single top finding + which file has the detail. Use these seven dimensions (adapt names to the stack): Seguridad & autorización · Correctitud & consistencia · Rendimiento · Modelo de datos & migraciones · **Dependencias & CVEs** · Arquitectura, estándares & reuso · Observabilidad & operación. For a dimension whose score depends on an unresolved condition (e.g. security-if-exposed), show the conditional (`score_if_...`). Give a simple average and name the highest-leverage fix — but explicitly note the other dimensions that weigh equally.
4. **Hallazgos por dimensión** — findings **grouped under each dimension heading**, most-severe first *within* each group. This guarantees a P0-heavy security section cannot push a P1 performance/consistency/dependency finding out of view. Never collapse this into one global severity-sorted list. **Separate active harm from latent/aspirational debt** — a repo that violates its own *declared-but-unadopted* standard (e.g. a strict-typing mandate that isn't enforced and whose static analysis already passes) is latent debt (P2/P3), not an active bug (do not inflate to P1).
5. **Cobertura del análisis** — a short table of what was **traced / shallow / not audited** (modules, flows, dependencies, tests, runtime). The reader must know where to trust the report and where work remains — silent gaps read as "covered everything".
6. **Index + limitations.**

Severity is not lost: it stays as a tag on every finding and orders items *within* each dimension. `recomendaciones.md` (below) is the place for the global priority ordering — that is an action list, so severity-first is correct there; the README is the map, so dimension-first is correct here.

## `recomendaciones.md` — the actionable roadmap (the point of this tool)

Two parts, both required:

1. **Recommendations table** — one row per recommendation, most-impactful first:
   `| Item | Justificación | Impacto (H/M/L) | Esfuerzo (H/M/L) | Prioridad (1..n) | Quick win? |`
   Each Item must trace to a **verified** finding from `auditoria.md` or a cartographer claim that survived Phase 3 — no recommendation without evidence behind it. At least 10 items when the repo warrants it.

2. **Phased roadmap** — Fase 0 (higiene) → Fase 5 (seguridad). For **each phase**: `objetivo`, `tareas`, `owner/rol`, `riesgos`, `rollback`, `criterio de aceptación`, `estimación relativa`. Tasks must be grounded in the real repo (reference real modules), not generic advice. Do **not** recommend work the repo profile shows is already done or in progress.

## `analisis.json` schema (must be valid JSON)

```json
{
  "repo": "<name>", "stack": "backend|vue-nuxt|both", "generated_for": "<YYYY-MM-DD>",
  "entities": [{"name":"...","fields":[{"name":"...","type":"...","pk":false,"fk":false,"nullable":true}]}],
  "relationships": [{"from":"...","to":"...","type":"1-N","via":"..."}],
  "flows": [{"name":"...","steps":[{"ref":"file:line","desc":"..."}]}],
  "lifecycle": {"states":["..."],"transitions":[{"from":"...","to":"...","on":"event","rules":"..."}]},
  "confidence": {"verified_meaning":"citation accuracy, not exploitability","security_severities_conditional_on":"reach/perimeter","exposure_signal":"...","blast_radius":"unknown — no business data"},
  "coverage": {"traced":["..."],"shallow":["..."],"not_audited":["dependencies/CVEs if not scanned","tests suite","runtime"]},
  "scorecard": [{"dimension":"Seguridad & autorización","score":2,"score_if_...":3,"top_finding":"...","detail":"auditoria.md §3"}],
  "risks": [{"item":"...","severity":"P0|P1|P2"}],
  "recommendations": [{"item":"...","impact":"H|M|L","effort":"H|M|L","priority":1,"quick_win":true}],
  "roadmap": [{"phase":"Fase 0","objetivo":"...","tareas":["..."],"riesgo":"...","rollback":"...","aceptacion":"..."}],
  "open_questions": ["...?"]
}
```
Every `flows[].steps[].ref` must be a `file:line` that survived Phase-3 verification. Validate with `jq . analisis.json` before finishing.

## Mermaid & style rules

- `sequenceDiagram` (flows), `stateDiagram-v2` (lifecycle), `erDiagram` (data model) — real participant/entity names from the code.
- Mark anything not proven in code as **"No evidenciado"** — never invent.
- State the analysis **LIMITATIONS** in `README.md` (e.g. "static analysis not run", "no prod logs").
- **Trazabilidad:** **every** finding carries a `file:line` **in every file it appears in — including the README scorecard/summary bullets**, not only in the detail file. A summary that names a defect ("N+1 al crear builds") without its location forces the reader to hunt; anchor it inline (the scorecard's `detail` column may point to the file for the long form, but the finding bullet still needs its `file:line`). For in-loop/N+1/perf findings, cite the loop line AND the per-iteration query line, not just the method. A claim that can't be anchored was dropped in Phase 3.
- Prose language follows the resolved language precedence (`--lang` → `AUDIT_STRICT_LANG` → `REVIEW_STRICT_LANG` → `en`). Code/paths/identifiers/`file:line`/Mermaid keywords stay verbatim.
