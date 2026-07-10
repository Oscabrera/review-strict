> 🌐 [English](README.md) · **Español**

# spec-strict

Una **revisión estricta y adaptativa al repo de un spec de Stratos/Axiom — antes de escribir código.**
El hermano pre-código de `/review-strict`: en vez de revisar un diff, revisa el **spec dir**
(`spec.md`, `plan.json`, `pr.md`, `validation.md`) en la rama del feature y caza las omisiones que
los specs de Stratos dejan de forma recurrente, para que se arreglen en el plan en lugar de volverse
fix commits en el PR.

Completa la familia: **`/spec-strict`** (el plan) → **`/review-strict`** (el cambio) →
**`/audit-strict`** (el repo).

## Por qué existe

Correr `/review-strict` (un reviewer de *diff*) sobre un spec funciona off-label y ya reduce rework
— pero sus lentes son de código/diff, así que se pierde las omisiones nativas de spec. Ejemplo real
(`cp-shops-catalog`): el PR **#1279** tuvo su spec revisado antes del código y shipeó con **0 fix
commits**; el hermano **#1278** se lo saltó y quemó ~5 fix commits + un rescope + un close/reopen.
`/spec-strict` vuelve esa revisión pre-código un chequeo de primera clase, nativo de spec.

## Qué caza (las seis lentes)

1. **Cobertura de entry-points / callers** — el AC arregla el camino feliz y olvida los otros callers.
2. **AC diff-checkable** — ACs sin mapeo a archivos concretos + un test real; tablas de traceability de relleno.
3. **Sanidad de comandos de verificación** — comandos que no existen para el stack (p.ej. `vitest` en un repo PHP/Pest).
4. **Inventario de bloqueadores/riesgos (grounded)** — el caller/subclase/migración que el plan no previó y rompe en runtime.
5. **Encaje de arquitectura y capas** — lógica/queries planeadas en la clase en vez de la capa repositorio/servicio del repo.
6. **Scope y completitud** — scope sin acotar que invita a rescope en vuelo; trabajo que el ticket implica pero el spec omite.

Grounded en el codebase real y verificado adversarialmente — cada finding es una **edición concreta al spec**, no una preocupación vaga.

## Uso

```
/spec-strict                     # auto-detecta el spec dir en la rama actual
/spec-strict IT-52986            # resuelve specs/IT-52986-*/ en esta rama
/spec-strict specs/IT-123-x/     # spec dir explícito
/spec-strict --fast              # modo single-agent (más barato, menos riguroso)
/spec-strict --model opus        # corre las lentes en el modelo de sesión (máx profundidad)
/spec-strict --lang es           # revisión en español
/spec-strict --out docs/         # escribe la revisión en un dir elegido
```

Flujo típico: córrelo en la rama del ticket **después de `/create-task`, antes de `/execute-task`** —
aplica sus ediciones al spec, y deja que Forge implemente un spec ya endurecido.

## Salida

Un `spec-review.md` (junto al spec por defecto) con un **veredicto de readiness**
(`ready` / `revise-before-Forge`), findings agrupados por lente (severidad: **block** / **should-fix**
/ **nice-to-have**), cada uno redactado como la edición exacta a aplicar al spec, más una nota de cobertura.

## Reglas

- **Read-only.** Nunca edita `spec.md`/`plan.json`/`pr.md`/`validation.md` — el humano o Axiom aplica las ediciones. Nunca commitea, ni crea ramas o PRs.
- **Las convenciones del repo ganan** — nunca exige un patrón que el repo no usa.
- Comparte `REVIEW_STRICT_LANG` / `REVIEW_STRICT_ARCHIVE_DIR` con el resto del plugin.
- **Costo:** las 6 lentes corren en `SPEC_STRICT_MODEL` / `--model` (Sonnet por defecto), mientras el pase adversarial de verificación se queda en tu modelo de sesión — el gate de rigor no se toca. Cuando existe `graphify-out/`, el grounding de la Fase 1 consulta el grafo antes de grep, reduciendo lecturas. Usa `--model inherit`/`opus` para una revisión de máxima profundidad.

## Aún no (roadmap)

- Un **gate en el pipeline**: correr `/spec-strict` automáticamente tras Axiom, antes de Forge — el leverage real de shift-left (vive en `cyberpuerta/stratos-autopilot`).
- Alimentar el patrón de omisiones recurrentes al prompt de authoring de Axiom (fix de raíz).
