> 🌐 [English](README.md) · **Español**

# review-strict

Un **revisor de PR / branch / diff estricto y adaptativo al repo** para Claude Code. Corre una
revisión de código multi-agente y verificada adversarialmente con rigor de staff engineer
(corrección, seguridad, arquitectura, tests, seguridad de migraciones), se adapta a las reglas
propias de cada repositorio y archiva un reporte con nombre de proyecto. Es independiente de
cualquier pipeline de spec/CI — apúntalo a un PR, una rama o un diff.

El plugin trae **tres skills hermanas** — la familia de análisis, en orden de flujo:

- **`/spec-strict`** — revisión pre-código de un spec dir de Stratos/Axiom (`spec.md`/`plan.json`/`pr.md`/`validation.md`), **antes** de que Forge escriba código; caza omisiones (entry-points no cubiertos, ACs no diff-checkables, comandos de verificación del stack equivocado, inventario de riesgos incompleto, mal encaje de capas, scope inestable). Ver `skills/spec-strict/README.md`.
- **`/review-strict`** — la revisión de diff/PR de arriba (corrección, seguridad, arquitectura + SOLID + complejidad, tests, seguridad de migraciones).
- **`/audit-strict`** — auditoría de arquitectura profunda de todo el repo (mapa de componentes, flujos, ciclo de vida, modelo de datos, auditoría de calidad + roadmap priorizado). Ver `skills/audit-strict/README.md`.

En conjunto: **`/spec-strict` revisa el plan → `/review-strict` revisa el cambio → `/audit-strict` revisa el repo.**

## Instalación

Es un repo **público y autocontenido** (es a la vez el plugin y su propio marketplace):

```
/plugin marketplace add Oscabrera/review-strict
/plugin install review-strict
```

Luego invoca `/spec-strict`, `/review-strict` o `/audit-strict` en cualquier repo.

## Actualización

Los plugins instalados **no** se actualizan solos por defecto — jalas versiones nuevas explícitamente:

```
/plugin marketplace update review-strict     # trae la última versión publicada
```

Para actualizar automáticamente al iniciar sesión, opta **por usuario** en `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "review-strict": {
      "source": { "source": "github", "repo": "Oscabrera/review-strict" },
      "autoUpdate": true
    }
  }
}
```

Los releases son **version-gated**: los consumidores solo se mueven cuando se sube el `version` en
`.claude-plugin/marketplace.json` (ver `CHANGELOG.md`) — los commits intermedios a `main` no se
empujan a nadie. Subir `version` + actualizar `CHANGELOG.md` al mergear a `main` es lo que corta un release.

## Uso

```
/spec-strict                    # revisa el spec dir en la rama actual (pre-código)
/spec-strict IT-52986           # resuelve specs/IT-52986-*/ en esta rama
/spec-strict specs/IT-123-x/    # spec dir explícito
/spec-strict --fast             # modo single-agent (más barato, menos riguroso)
/spec-strict --model opus       # fuerza todas las lentes a un modelo (default: híbrido)
/spec-strict --lang es          # revisión en español
```

Ver `skills/spec-strict/README.md` para la referencia completa de `/spec-strict`.

```
/review-strict                 # revisa la rama actual vs su base (pre-PR)
/review-strict 433             # revisa el PR #433 vía gh
/review-strict --base main     # override de la rama base
/review-strict 433 --repo-copy # además copia el reporte al path de reviews del repo
/review-strict 433 --post      # publica el review en GitHub (pide confirmación; siempre en inglés)
/review-strict --fast          # modo single-agent (más barato, menos riguroso)
/review-strict 433 --model opus # fuerza todas las lentes a un modelo (default: híbrido)
/review-strict 433 --lang es    # reporte en español para esta corrida
/review-strict 433 --no-save    # solo imprime, no archiva
```

```
/audit-strict                   # auditoría profunda de todo el repo (auto-detecta stack)
/audit-strict --stack vue       # fuerza los cartógrafos Vue/Nuxt
/audit-strict --out ~/notes     # escribe a ~/notes/audit-strict/<repo>/
/audit-strict --model opus      # cartógrafos en Opus (default sonnet)
/audit-strict --fast            # modo single-agent (más barato, menos riguroso)
```

Ver `skills/audit-strict/README.md` para la referencia completa de `/audit-strict`.

## Configuración (por desarrollador, vía env vars)

| Variable | Default | Efecto |
|---|---|---|
| `REVIEW_STRICT_ARCHIVE_DIR` | *(sin definir)* | Si se define, los reportes se archivan en `$REVIEW_STRICT_ARCHIVE_DIR/<repo>/<archivo>`. Si no, se archivan **dentro del repo revisado** en `reviews/<proyecto>-pr-<N>.md` (portable — todos lo tienen). |
| `REVIEW_STRICT_LANG` | `en` | Idioma del reporte: `en` o `es`. El flag `--lang <en|es>` lo sobreescribe por corrida. |
| `REVIEW_STRICT_MODEL` | *(híbrido)* | Fuerza las 5 lentes de `/review-strict` a un modelo uniforme (`sonnet`/`opus`/`haiku`/`inherit`); `--model` lo sobreescribe. **Sin definir = híbrido** (el default): lentes profundas (corrección, seguridad, arquitectura) en el modelo de sesión, mecánicas (tests, migración) en Sonnet. **La palanca principal de costo.** |
| `SPEC_STRICT_MODEL` | *(híbrido)* | Igual para las 6 lentes de `/spec-strict` — híbrido: coverage/risk/architecture/scope en el modelo de sesión, ac-quality/verification en Sonnet. |
| `AUDIT_STRICT_MODEL` | `sonnet` | Modelo de los 5 cartógrafos de `/audit-strict` (solo Fase 2). |

Las perillas de modelo solo tocan el fan-out de lectura pesada; el pase adversarial de verificación siempre corre en tu modelo de sesión, así el gate de rigor nunca baja. Los comentarios externos (GitHub / ClickUp vía `--post`) van **siempre en inglés**, sin importar el idioma del reporte.

Los reportes son **salida** de review, no código fuente — la carpeta in-repo `reviews/` es buena candidata para `.gitignore` a menos que tu equipo quiera commitear el historial de reviews.

## Cómo funciona

1. **Perfila el repo** — lee `AGENTS.md`, `CLAUDE.md`, `.claude/skills/*` (y los legacy `.aiassistant/rules/*` solo si existen), local-gana.
2. **Diff + toolchain** — saca el diff, excluye ruido (`specs/`, `vendor/`, lockfiles), captura lint/static-analysis best-effort (evidencia/CI si está disponible; nunca bloquea).
3. **Cinco lentes adversariales** en paralelo — corrección/requisitos, seguridad, arquitectura & reuso, tests, seguridad de migraciones. Los agentes no-op se reintentan.
4. **Verificación adversarial** — un pase escéptico refuta cada finding contra el diff; solo sobreviven los evidenciados.
5. **Síntesis** — severidades mapeadas al vocabulario del repo (Blocker/Major/Minor), más severo primero.
6. **Entrega** — imprime + archiva el reporte; `--post` publica en GitHub tras confirmación.

También verifica los riesgos auto-declarados del PR y su tabla de AC-traceability como
**claims no confiables** — un riesgo real declarado sigue siendo un finding, y una mitigación
reclamada pero ausente del diff se marca `claimed-but-not-done`.

## Publicación

Ramas: **`main`** es la rama estable/default desde la que instala el marketplace (`ref: main`);
**`develop`** es la rama de integración para trabajo en curso.

```
git init && git add -A && git commit -m "feat: review-strict plugin v1.0.0"
git branch -M main
git branch develop
gh repo create Oscabrera/review-strict --public --source=. --remote=origin --push
git push -u origin develop
```

Día a día: aterriza cambios en `develop`; mergea a `main` para cortar un release
(sube `CHANGELOG.md`). Los consumidores del marketplace siempre reciben `main`.

## Licencia

MIT
