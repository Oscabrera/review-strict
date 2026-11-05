# Portable audit bundle validation

Run before delivery after the ten files are assembled:

```bash
python3 <plugin-root>/skills/audit-strict/scripts/validate-bundle.py <OUT_DIR>
```

Requires Python 3.9+. It reads only: checks files, placeholders, relative Markdown
file targets (including reference links, not heading anchors), versioned JSON structure, and declared section
coverage consistency. It never fetches external links. Local links must stay
inside the bundle so moving it keeps it self-contained. Use sibling filenames,
not a second `audit-strict/<repo>/` prefix. Exit 0 = valid, 2 = invalid, 3 =
unsupported schema; JSON output separates structural and semantic diagnostics.
Syntax validation alone (`jq .`) is not the completion check.

For new bundles set `schema_version: 1`. Preserve the documented summary fields
and add a `sections` object, one entry for each of the nine Markdown files:

```json
"sections": {
  "componentes.md": {
    "status":"completed",
    "source_id":"<full reviewed Git SHA or snapshot SHA-256>",
    "verification":"<what was actually reread/executed, with evidence anchors>",
    "limitations":[]
  }
}
```

Use `completed`, `not-completed`, or `not-applicable`. Partial/N/A entries need
a limitation/applicability reason and still identify the source they refer to.
An unverified section may name the intended source but its verification text must
state what was unavailable. A partial refresh retains each section's actual
source and verification; do not relabel inherited sections as newly checked.

README includes one matching row per section (the first three columns are stable;
headings/prose can use the report language):

```markdown
| Section | Status | Source | Limitation |
|---|---|---|---|
| componentes.md | completed | <same source_id> | <actual limitation, if any> |
```

This ledger complements the module/flow coverage map. The validator reconciles
explicit status/source rows, not arbitrary natural-language assertions. The final
completeness pass must still check substantive content, stale completion claims,
missing core flows and actual evidence, including source provenance. A placeholder
or a cross-reference alone is not substantive analysis. No claim of exploitability
or citation truth follows from validator success. Honest partial output may be
structurally valid and reports `partial_sections` rather than inventing content.

Unversioned files validate as legacy v0 under their original documented shape;
the result explicitly says per-section provenance was not assessed. Missing v0
fields fail that contract. Unknown versions fail as unsupported. Do not silently
upgrade historical notes or fabricate identities to satisfy v1.
