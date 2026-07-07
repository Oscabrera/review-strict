# Changelog

## 1.0.0
- Initial release. Strict, repo-adaptive, multi-agent PR/branch/diff reviewer.
- Adapts to `AGENTS.md` / `CLAUDE.md` / `.claude/skills` (legacy `.aiassistant/rules` optional).
- Five adversarial lenses + skeptic verification pass; no-op agent detection + retry.
- Diff-noise exclusion (`specs/`, `vendor/`, lockfiles); best-effort non-blocking Pint/PHPStan.
- Verifies the PR's self-declared risks + AC traceability (`claimed-but-not-done` / `ac-traceability-gap`).
- Portable report archive: `reviews/<project>-pr-<N>.md` in-repo by default; `REVIEW_STRICT_ARCHIVE_DIR` override.
- Report language English by default; `REVIEW_STRICT_LANG` / `--lang` for Spanish. External comments always English.
