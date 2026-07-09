> 🌐 [English](README.md) · **Español**

# audit-strict

Una **auditoría de arquitectura profunda, adaptativa al repo, de todo el repositorio** para Claude Code — el
hermano constructivo de `/review-strict`. Donde `review-strict` revisa un diff/PR (solo errores),
`audit-strict` hace ingeniería inversa del **repo completo** en un análisis multi-archivo, preciso en
citas, y un roadmap priorizado por fases que el equipo puede accionar.

Va en el mismo plugin y reusa la espina de review-strict: el repo profile, el pase adversarial
`verify-skeptic`, el crosswalk de severidad y el baseline staff.

Parte de la familia de análisis: **`/spec-strict`** (el plan) → **`/review-strict`** (el cambio) → **`/audit-strict`** (el repo).

## Qué produce

Un entregable autocontenido en `audit-strict/` (in-repo por defecto; `<base>/audit-strict/<repo>/` cuando se configura una base):

| Archivo | Contenido |
|---|---|
| `README.md` | Resumen ejecutivo, top-10 riesgos, 10 recomendaciones clave, índice, limitaciones |
| `componentes.md` | Mapa de componentes, dependencias, acoplamiento, SPOFs, hot paths |
| `flujos.md` | Flujos end-to-end principales + `sequenceDiagram` Mermaid |
| `ciclo-vida.md` | Estados/transiciones de la entidad + `stateDiagram-v2` Mermaid |
| `datos.md` | Modelo de datos derivado + `erDiagram` Mermaid |
| `auditoria.md` | Buenas/malas prácticas, seguridad, rendimiento, riesgo operacional |
| `recomendaciones.md` | Tabla impacto/esfuerzo/prioridad + roadmap Fase 0–5 |
| `pruebas.md` | Matriz de casos de prueba + gaps de cobertura |
| `preguntas.md` | Preguntas abiertas + supuestos (con nivel de confianza) |
| `analisis.json` | Resumen técnico en JSON válido |

## Uso

```
/audit-strict                    # audita todo el repo actual (auto-detecta stack)
/audit-strict --stack vue        # fuerza los cartógrafos Vue/Nuxt
/audit-strict src/Domain         # acota la auditoría a un subárbol
/audit-strict --lang es          # prosa del entregable en español
/audit-strict --model opus       # corre los cartógrafos en Opus (default sonnet)
/audit-strict --fast             # modo single-agent (más barato, menos riguroso)
/audit-strict --no-save          # solo imprime README + resumen, no escribe nada
/audit-strict --out ~/projects/brain  # escribe a brain/audit-strict/<repo>/
```

## Cómo funciona

1. **Perfila el repo** (reusado de review-strict) — `AGENTS.md`, `CLAUDE.md`, `.claude/skills/*`; local-gana. Es **la verdad de base** — lo que el repo ya tiene y ya hace.
2. **Grounding** — graphify-first (si existe `graphify-out/`), si no, un inventario determinista `rg`/glob. Los cartógrafos solo citan de ese conjunto verificado.
3. **Cinco cartógrafos en paralelo** — componentes, flujos, ciclo de vida, modelo de datos, auditoría de calidad. Uno por entregable → profundidad pareja. Variantes backend y Vue/Nuxt, auto-seleccionadas. Corren en **sonnet por default** (lectores más baratos; `--model` para cambiar).
4. **Verificación adversarial** (reusa `verify-skeptic`, en el modelo de sesión) — refuta cada cita y claim contra el código real y el repo profile. Rangos imposibles, rutas que no resuelven y claims "falta X" que contradicen el repo se descartan.
5. **Síntesis** — los nueve archivos + un roadmap priorizado; cada ítem traza a un finding que sobrevivió; cero placeholders.
6. **Entrega** — escribe el entregable `audit-strict/` (heredoc, Mermaid/código literales), imprime el resumen.

## Por qué es más estricto que un análisis de una sola pasada

Se construyó para arreglar cuatro defectos observados en una corrida previa "codex" de una sola pasada:
placeholders `{{...}}` filtrados, rangos de línea imposibles (`718-716`), findings que contradecían
el propio `CLAUDE.md` del repo (afirmar "no hay observabilidad" cuando existe un job de telemetría), y
profundidad de secciones muy dispareja. El fan-out + el pase de verificación adversarial son los fixes.

## Configuración (carpeta + idioma, ambos configurables)

Paridad con `/review-strict`: la carpeta de salida y el idioma de la prosa son configurables por-developer
(env var) o por-corrida (flag). Las env vars propias de audit tienen precedencia, luego las `REVIEW_STRICT_*`
compartidas como fallback.

**Carpeta de salida** — precedencia de mayor a menor. Una **base** configurada se agrupa por herramienta y luego por repo (`<base>/audit-strict/<repo>/`), así el output de audit nunca choca con los reportes de `/review-strict` (que una base compartida guarda en `<base>/<repo>/`):

| Fuente | Resultado |
|---|---|
| `--out <base>` (flag) | `<base>/audit-strict/<repo>/` |
| `AUDIT_STRICT_OUT_DIR` (env) | `$AUDIT_STRICT_OUT_DIR/audit-strict/<repo>/` |
| `REVIEW_STRICT_ARCHIVE_DIR` (env, compartida) | `$REVIEW_STRICT_ARCHIVE_DIR/audit-strict/<repo>/` |
| *(ninguna)* | in-repo `<repo-root>/audit-strict/` |

Ejemplo — mandar las auditorías de hoy a `brain/`: `--out ~/projects/brain` → `~/projects/brain/audit-strict/cp-shops-csp/`.

**Idioma** — precedencia de mayor a menor:

| Fuente | Resultado |
|---|---|
| `--lang <en\|es>` (flag) | ese idioma, esta corrida |
| `AUDIT_STRICT_LANG` (env) | `en` o `es` |
| `REVIEW_STRICT_LANG` (env, compartida) | `en` o `es` |
| *(ninguna)* | `en` |

El código, rutas, identificadores, `file:línea` y palabras clave de Mermaid quedan literales en cualquier idioma.

**Modelo de cartógrafos (control de costo)** — los cinco cartógrafos son lectura-intensivos y corren en **sonnet por default**; el pase de verificación y la síntesis siempre usan tu modelo de sesión, así que el rigor no se afecta. Precedencia de mayor a menor:

| Fuente | Resultado |
|---|---|
| `--model <sonnet\|opus\|haiku\|inherit>` (flag) | ese modelo para los cartógrafos, esta corrida |
| `AUDIT_STRICT_MODEL` (env) | default por-developer |
| *(ninguna)* | `sonnet` |

`inherit` significa "usa mi modelo de sesión" (sin override). Las auditorías de repo completo leen muchos archivos — correr los lectores en un tier más barato es la mayor palanca de costo. Si existe `graphify-out/`, la Fase 1 consulta el grafo en vez de leer a fuerza bruta, recortando tokens aún más.

Solo lee; solo escribe el dir del entregable. Nunca edita código fuente, ni commitea, ni crea ramas o PRs.
