#!/usr/bin/env python3
"""Read-only audit bundle checks. Exit 0 valid, 2 invalid, 3 unsupported schema."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

FILES = ("README.md", "componentes.md", "flujos.md", "ciclo-vida.md", "datos.md",
         "auditoria.md", "recomendaciones.md", "pruebas.md", "preguntas.md")


def schema_errors(value, schema, path="$"):
    """Evaluate the small JSON Schema subset used by the bundled versioned schemas.

    Supports type, required, properties, additionalProperties, items, enum,
    minLength, pattern, minimum, maximum and the bundled local $ref. This is not a general JSON Schema engine.
    """
    errors = []
    if "$ref" in schema:
        reference = Path(__file__).resolve().parents[1] / "references/schemas" / schema["$ref"]
        errors.extend(schema_errors(value, json.loads(reference.read_text()), path))
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
    kind = schema.get("type")
    if kind and type(value) is not types[kind]:
        return [path + ": expected " + kind]
    if "enum" in schema and not any(type(value) is type(v) and value == v for v in schema["enum"]):
        errors.append(path + ": value outside enum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(path + "." + key + ": missing required field")
        props = schema.get("properties", {})
        for key, item in value.items():
            rule = props.get(key, schema.get("additionalProperties"))
            if isinstance(rule, dict):
                errors.extend(schema_errors(item, rule, path + "." + key))
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(schema_errors(item, schema["items"], path + "[" + str(i) + "]"))
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        errors.append(path + ": invalid source identity format")
    if isinstance(value, str) and len(value.strip()) < schema.get("minLength", 0):
        errors.append(path + ": empty required text")
    if type(value) is int:
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(path + ": below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(path + ": above maximum")
    return errors


def escaped(text, pos):
    start = pos
    while start > 0 and text[start - 1] == "\\":
        start -= 1
    return (pos - start) % 2 == 1


def without_code(text):
    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        match = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
        elif match:
            fence = match[1]
        else:
            lines.append(line)
    text, result, pos = "".join(lines), [], 0
    while pos < len(text):
        start = text.find("`", pos)
        if start < 0:
            result.append(text[pos:])
            break
        end = start
        while end < len(text) and text[end] == "`":
            end += 1
        if escaped(text, start):
            result.append(text[pos:end])
            pos = end
            continue
        delimiter = text[start:end]
        close = re.search(r"(?<!`)" + re.escape(delimiter) + r"(?!`)", text[end:])
        result.append(text[pos:start])
        if close:
            stop = end + close.end()
            result.append(re.sub(r"[^\n]", " ", text[start:stop]))
            pos = stop
        else:
            result.append(delimiter)
            pos = end
    return "".join(result)


def destination(text, start):
    """Read a link target without truncating balanced or escaped parentheses."""
    if start >= len(text):
        return None
    if text[start] == "<":
        end = text.find(">", start + 1)
        return text[start + 1:end] if end >= 0 else None
    pos, depth = start, 0
    while pos < len(text):
        char = text[pos]
        if char == "\\" and pos + 1 < len(text):
            pos += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        elif char.isspace():
            break
        pos += 1
    return text[start:pos] if depth == 0 else None


def local_links(text):
    text = without_code(text)
    links = []
    for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*", text):
        opening = match.start() + int(text[match.start()] == "!")
        if escaped(text, opening):
            continue
        target = destination(text, match.end())
        if target:
            links.append(target)
    for match in re.finditer(r"(?m)^ {0,3}\[[^\]]+\]:\s*", text):
        target = destination(text, match.end())
        if target:
            links.append(target)
    return [re.sub(r"\\([^\w\s])", r"\1", link) for link in links]


def check_bundle(root):
    structural, semantic = [], []
    texts = {}
    for name in (*FILES, "analisis.json"):
        path = root / name
        if not path.is_file():
            structural.append(name + ": missing required file")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            structural.append(name + ": " + str(error))
            continue
        texts[name] = text
        if re.search(r"\{\{[^{}]*\}\}", text):
            structural.append(name + ": unresolved placeholder")
        if name.endswith(".md"):
            for link in local_links(text):
                target = urlsplit(link)
                if target.scheme or target.netloc or not target.path:
                    continue
                dest = (path.parent / unquote(target.path)).resolve()
                if not dest.is_relative_to(root):
                    structural.append(name + ": local link leaves bundle: " + link)
                elif not dest.exists():
                    structural.append(name + ": broken local link: " + link)
    try:
        data = json.loads(texts.get("analisis.json", ""))
        if not isinstance(data, dict):
            raise ValueError("expected object")
    except ValueError as error:
        structural.append("analisis.json: " + str(error))
        return 2, {"structural": structural, "semantic_coverage": ["not checked: invalid JSON"], "schema_version": None}
    version = data.get("schema_version", 0)
    if type(version) is not int or version not in (0, 1):
        return 3, {"structural": structural, "semantic_coverage": ["not checked: unsupported schema"], "schema_version": version, "unsupported_schema": True}
    schema = json.loads((Path(__file__).resolve().parents[1] / "references/schemas" / ("audit-v" + str(version) + ".json")).read_text())
    structural.extend(schema_errors(data, schema, "$"))
    if structural:
        return 2, {"structural": structural, "semantic_coverage": ["not checked: structural errors"], "schema_version": version}
    if version == 0:
        return 0, {"structural": [], "semantic_coverage": ["not assessed: legacy v0 has no per-section provenance contract"], "schema_version": 0, "legacy": True}
    rows = {}
    for line in texts["README.md"].splitlines():
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in FILES:
            if cells[0] in rows:
                semantic.append("README.md: duplicate coverage row: " + cells[0])
            rows[cells[0]] = cells[1:3]
    partial = []
    for name in FILES:
        section = data["sections"][name]
        if rows.get(name) != [section["status"], section["source_id"]]:
            semantic.append(name + ": README coverage row differs from JSON status/source or is missing")
        if section["status"] == "not-completed":
            partial.append(name)
        if section["status"] != "completed" and not section["limitations"]:
            semantic.append(name + ": partial/N/A section needs a limitation or applicability reason")
        content = re.sub(r"<!--.*?-->", "", texts[name], flags=re.S)
        content = "\n".join(line for line in content.splitlines() if not line.lstrip().startswith("#")).strip()
        if section["status"] == "completed" and not content:
            semantic.append(name + ": completed section contains no content beyond headings")
    return (2 if semantic else 0), {"structural": [], "semantic_coverage": semantic,
        "schema_version": 1, "partial_sections": partial,
        "limitations": "Checks reconcile declared structure/status/provenance; substance, citation truth and exploitability require review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        code, result = check_bundle(args.bundle.resolve())
    except (OSError, ValueError, TypeError) as error:
        code, result = 2, {"structural": [str(error)], "semantic_coverage": ["not checked"]}
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
