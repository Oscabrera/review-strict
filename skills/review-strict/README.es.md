> 🌐 [English](README.md) · **Español**

# /review-strict — resumen

Revisor de PR/branch/diff **estricto y adaptativo al repo**. Skill de Claude Code: se adapta al repo donde lo corras (lee sus reglas reales) y produce un review riguroso, multi-agente y verificado adversarialmente.

Parte de la familia de análisis: **`/spec-strict`** (el plan) → **`/review-strict`** (el cambio) → **`/audit-strict`** (el repo).

## Qué hace

Revisa un diff con rigor de staff engineer y **solo reporta errores** (nada de "looks good"), con evidencia `file:línea` y decisión final `approve` / `request-changes` / `comment`.

## Cómo usarlo

```
/review-strict                    # rama actual vs base (pre-PR)
/review-strict 433                # PR #433 vía gh
/review-strict --base main        # override de base
/review-strict 433 --repo-copy    # además copia al path de reviews del repo (.ai/pr-reviews)
/review-strict 433 --post         # publica en GitHub (pide confirmación; siempre en inglés)
/review-strict --fast             # 1 solo agente (más barato, menos riguroso)
/review-strict 433 --lang es      # reporte en español para esta corrida
/review-strict 433 --no-save      # no archivar (solo imprimir)
```

## Variables de entorno (config por persona)

- **`REVIEW_STRICT_ARCHIVE_DIR`** — carpeta donde se archivan los reportes. Si NO está definida, el reporte cae **dentro del repo revisado** en `reviews/<proyecto>-pr-<N>.md` (portable, todos lo tienen). Si la defines, se usa `$REVIEW_STRICT_ARCHIVE_DIR/<repo>/<archivo>` (útil para una carpeta central de notas).
- **`REVIEW_STRICT_LANG`** — idioma del reporte: `en` (por defecto) o `es`. El flag `--lang <en|es>` lo sobreescribe por corrida.
- **Regla firme:** lo publicado hacia afuera (comentario en GitHub o ClickUp con `--post`) va **siempre en inglés**, sin importar el idioma del reporte.

## Cómo funciona (6 fases)

0. **Perfila el repo** — `AGENTS.md` + `CLAUDE.md` + `.claude/skills/*` (y `.aiassistant/rules/*` solo si existen). Precedencia local-gana.
1. **Diff + toolchain** — saca el diff, excluye ruido (`specs/`, `vendor/`, `evidence/`, lockfiles) y captura Pint/PHPStan best-effort (usa evidencia/CI si existe; si no, lo omite — nunca bloquea).
2. **Fan-out de 5 lentes** (agentes independientes): corrección/#4, seguridad, arquitectura/reuso, tests, migración. Detecta agentes no-op y reintenta.
3. **Verificación adversarial** — pase escéptico que mata falsos positivos (default-refute).
4. **Síntesis** — severidad en vocab del repo (Blocker/Major/Minor), más severo primero.
5. **Entrega** — imprime + archiva (ver `REVIEW_STRICT_ARCHIVE_DIR`); `--post` publica en GitHub con confirmación.

El check **#4** verifica lo que el PR se auto-declara (riesgos/ACs) contra el diff: un riesgo real declarado sigue siendo finding, y una mitigación/AC reclamada pero ausente del código es `claimed-but-not-done` / `ac-traceability-gap`.

## Dos fuentes de verdad

1. **Reglas del repo** — mandan en formato, severidad y comandos.
2. **Baseline staff propio** (`references/baseline-criteria.md`) — se aplica siempre, aun sin reglas de repo; agrega hallazgos que el checklist del repo olvidó.

## Archivos

- `SKILL.md` — orquestador (invocación, flags, fases)
- `references/repo-profile.md` — lógica de adaptación al repo
- `references/lenses.md` — los 5 briefs de revisión
- `references/baseline-criteria.md` — la vara staff siempre-activa
- `references/severity-output.md` — crosswalk de severidad, verificación, plantilla de salida

## Origen del diseño

Construido tomando lo mejor de tres sistemas: **Sentinel** (stratos-autopilot — rigor multi-pass), **AIWF** (comando standalone + stack-packs), y las **reglas por repo** (`.aiassistant/rules/`). Diseñado y validado en cp-shops-pcb PR #433.
