> 🌐 **English** · [Español](README.es.md)

# audit-strict

A **deep, repo-adaptive whole-repository architecture audit** for Claude Code — the
constructive sibling of `/review-strict`. Where `review-strict` reviews a diff/PR
(errors-only), `audit-strict` reverse-engineers the **whole repo** into a multi-file,
cite-accurate analysis and a prioritized, phased roadmap the team can act on.

It ships in the same plugin and reuses review-strict's spine: the repo profile,
the adversarial `verify-skeptic` pass, the severity crosswalk, and the staff baseline.

## What it produces

A self-contained deliverable in `audit-strict/` (in-repo by default; `<base>/audit-strict/<repo>/` when a base is configured):

| File | Content |
|---|---|
| `README.md` | Exec summary, top-10 risks, 10 key recommendations, index, limitations |
| `componentes.md` | Component map, dependencies, coupling, SPOFs, hot paths |
| `flujos.md` | Principal end-to-end flows + Mermaid `sequenceDiagram` |
| `ciclo-vida.md` | Entity states/transitions + Mermaid `stateDiagram-v2` |
| `datos.md` | Derived data model + Mermaid `erDiagram` |
| `auditoria.md` | Good/bad practices, security, performance, operational risk |
| `recomendaciones.md` | Impact/effort/priority table + Fase 0–5 roadmap |
| `pruebas.md` | Test-case matrix + coverage gaps |
| `preguntas.md` | Open questions + assumptions (confidence-rated) |
| `analisis.json` | Valid JSON technical summary |

## Usage

```
/audit-strict                    # audit the whole current repo (auto-detect stack)
/audit-strict --stack vue        # force the Vue/Nuxt cartographers
/audit-strict src/Domain         # scope the audit to a subtree
/audit-strict --lang es          # deliverable prose in Spanish
/audit-strict --model opus       # run the cartographers on Opus (default is sonnet)
/audit-strict --fast             # single-agent mode (cheaper, less rigorous)
/audit-strict --no-save          # print README + summary only, write nothing
/audit-strict --out ~/projects/brain  # write to brain/audit-strict/<repo>/
```

## How it works

1. **Profile the repo** (reused from review-strict) — `AGENTS.md`, `CLAUDE.md`, `.claude/skills/*`; local-wins. This is **ground truth** — what the repo already has and is already doing.
2. **Ground it** — graphify-first (if `graphify-out/` exists), else a deterministic `rg`/glob inventory. Cartographers cite only from this verified set.
3. **Five cartographers in parallel** — components, flows, lifecycle, data model, quality audit. One per deliverable → even depth. Backend and Vue/Nuxt variants, auto-selected. Run on **sonnet by default** (cheaper readers; `--model` to change).
4. **Adversarial verification** (reused `verify-skeptic`, on the session model) — refutes every citation and claim against the real code and the repo profile. Impossible ranges, unresolved paths, and "X is missing" claims that contradict the repo are dropped.
5. **Synthesize** — the nine files + a prioritized roadmap; every item traces to a surviving finding; zero placeholders.
6. **Deliver** — writes the `audit-strict/` deliverable (heredoc, literal Mermaid/code), prints the summary.

## Why it's stricter than a single-pass analysis

It was built to fix four defects observed in a prior single-pass "codex" run:
leaked `{{placeholders}}`, impossible line ranges (`718-716`), findings that
contradicted the repo's own `CLAUDE.md` (claiming "no observability" when a
telemetry job exists), and wildly uneven section depth. The fan-out + the
adversarial verify pass are the fixes.

## Configuration (folder + language, both configurable)

Parity with `/review-strict`: the output folder and the prose language are each
configurable per-developer (env var) or per-run (flag). Audit-specific env vars take
precedence, then the shared `REVIEW_STRICT_*` vars as a fallback.

**Output folder** — precedence high → low. A configured **base** is grouped by tool then repo (`<base>/audit-strict/<repo>/`), so audit output never collides with `/review-strict` reports (which a shared base holds at `<base>/<repo>/`):

| Source | Result |
|---|---|
| `--out <base>` (flag) | `<base>/audit-strict/<repo>/` |
| `AUDIT_STRICT_OUT_DIR` (env) | `$AUDIT_STRICT_OUT_DIR/audit-strict/<repo>/` |
| `REVIEW_STRICT_ARCHIVE_DIR` (env, shared) | `$REVIEW_STRICT_ARCHIVE_DIR/audit-strict/<repo>/` |
| *(none)* | in-repo `<repo-root>/audit-strict/` |

Example — send today's audits to `brain/`: `--out ~/projects/brain` → `~/projects/brain/audit-strict/cp-shops-csp/`.

**Language** — precedence high → low:

| Source | Result |
|---|---|
| `--lang <en\|es>` (flag) | that language, this run |
| `AUDIT_STRICT_LANG` (env) | `en` or `es` |
| `REVIEW_STRICT_LANG` (env, shared) | `en` or `es` |
| *(none)* | `en` |

Code, paths, identifiers, `file:line`, and Mermaid keywords stay verbatim in every language.

**Cartographer model (cost control)** — the five cartographers are read/mapping-heavy and run on **sonnet by default**; the verify pass and synthesis always use your session model, so rigor is unaffected. Precedence high → low:

| Source | Result |
|---|---|
| `--model <sonnet\|opus\|haiku\|inherit>` (flag) | that model for the cartographers, this run |
| `AUDIT_STRICT_MODEL` (env) | per-developer default |
| *(none)* | `sonnet` |

`inherit` means "use my session model" (no override). Whole-repo audits read a lot of files — running the readers on a cheaper tier is the single biggest lever on cost. If `graphify-out/` exists, Phase 1 queries the graph instead of brute-force reading, cutting tokens further.

Reads only; writes only the deliverable dir. Never edits source, commits, branches, or opens PRs.
