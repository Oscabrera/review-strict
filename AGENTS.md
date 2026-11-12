# review-strict — Reglas del Repositorio y Flujo de Trabajo

Este repositorio contiene la suite de plugins y skills de revisión rigurosa: `review-strict`, `audit-strict` y `spec-strict`.

## Remotes y Ramas
- Remote: `origin` (`https://github.com/Oscabrera/review-strict.git`)
- Rama base de desarrollo: `develop`
- Rama de producción/releases: `main`

---

## Reglas Obligatorias de Desarrollo

1. **Una rama por cada cambio pequeño:**
   - Todo trabajo (feature, bugfix, mejora a un lens o documentación) se realiza en su propia rama aislada (`feat/...`, `fix/...`, `docs/...`) basada en `develop`.
   - Cada cambio pequeño debe poder revisarse y evaluarse de forma independiente.

2. **Prohibido hacer commits directos a `develop` o `main`:**
   - Toda modificación debe entrar exclusivamente a través de Pull Request hacia `develop`.
   - Jamás hacer `git commit` directamente en `develop` ni `main` (ni en local ni en remoto).

3. **Respeto total a cambios y worktrees existentes:**
   - Nunca descartar (`git restore`, `git reset --hard`), borrar o sobrescribir cambios previos o worktrees activos que Oscar tenga en el árbol de trabajo.

4. **Calidad y verificación:**
   - Todo cambio debe pasar las pruebas locales con `pytest tests/`.
   - Mantener consistencia entre las tres plataformas soportadas (Claude Code, Codex y Gemini / Antigravity).
