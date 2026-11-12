# review-strict — Instrucciones para Claude Code y Agentes

Consulta [AGENTS.md](AGENTS.md) para el protocolo y las reglas completas de este repositorio.

## Resumen de reglas clave:
1. **Una rama por cambio pequeño:** basada en `develop`. Nada de cambios masivos ni commits directos a `develop` o `main`.
2. **Nunca destruir cambios ni worktrees existentes:** respeta el trabajo local y las ramas de Oscar.
3. **Flujo de PRs hacia `develop`:** cada entrega se valida con `pytest tests/` y entra por Pull Request.
