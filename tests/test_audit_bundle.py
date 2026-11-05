"""Validate whole bundles, including relocation, partial output and bad contracts."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/audit-strict/scripts/validate-bundle.py"
spec = importlib.util.spec_from_file_location("bundle", SCRIPT)
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "bundle"
        self.root.mkdir()
        self.source = "a" * 40
        self.data = {"schema_version": 1, "repo": "fixture", "stack": "plugin-tooling", "generated_for": "2026-11-05", "entities": [], "relationships": [], "flows": [], "lifecycle": {"states": [], "transitions": []}, "confidence": {"verified_meaning": "citation accuracy", "security_severities_conditional_on": "reach", "exposure_signal": "not checked", "blast_radius": "unknown"}, "coverage": {"traced": [], "shallow": [], "not_audited": ["runtime"]}, "scorecard": [], "risks": [], "recommendations": [], "roadmap": [], "open_questions": [], "sections": {name: {"status": "completed", "source_id": self.source, "verification": "fixture.py:1 reread at pinned source", "limitations": []} for name in bundle.FILES}}
        for name in bundle.FILES:
            (self.root / name).write_text("# " + name + "\n\nConcrete, verified fixture analysis.\n")
        self.save()

    def save(self):
        (self.root / "analisis.json").write_text(json.dumps(self.data))
        table = "| Section | Status | Source |\n|---|---|---|\n"
        table += "\n".join("| " + name + " | " + row["status"] + " | " + row["source_id"] + " |" for name, row in self.data.get("sections", {}).items())
        (self.root / "README.md").write_text("# Audit\n\nConcrete fixture summary. [Flows](flujos.md)\n\n" + table + "\n")

    def check(self, code=0, root=None):
        r = subprocess.run([sys.executable, str(SCRIPT), str(root or self.root)], cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def test_valid_bundle_remains_valid_after_move(self):
        self.check()
        dest = Path(self.temp.name) / "moved"
        shutil.move(self.root, dest)
        self.check(root=dest)

    def test_broken_link_with_existing_sibling(self):
        p = self.root / "README.md"
        p.write_text(p.read_text().replace("](flujos.md)", "](audit-strict/fixture/flujos.md)"))
        result = self.check(2)
        self.assertTrue(any("broken local link" in e for e in result["structural"]))

    def test_reference_links_and_spaces(self):
        (self.root / "two words.md").write_text("An attachment.")
        p = self.root / "flujos.md"
        p.write_text("# Flow\n\n[Attachment](<two words.md>) and [reference][x].\n[x]: two%20words.md\n")
        self.check()
        p.write_text(p.read_text().replace("two%20words.md", "missing.md"))
        self.check(2)

    def test_balanced_and_escaped_parentheses_are_valid_destinations(self):
        (self.root / "diagram(v2).svg").write_text("<svg/>")
        (self.root / "flujos.md").write_text('# Flow\n\n[Attachment](diagram(v2).svg)\n[Escaped](diagram\\(v2\\).svg "title")\n')
        self.check()
        (self.root / "diagram(v2).svg").unlink()
        self.assertTrue(any("diagram(v2).svg" in e for e in self.check(2)["structural"]))

    def test_code_examples_are_not_links(self):
        (self.root / "flujos.md").write_text('# Flow\n\nA syntax example: `[Example](missing.md)` and `` `[Second](also-missing.md)` ``.\n\n````markdown\n[Third](absent.md)\n```\n````\n\n[Actual](datos.md)\n')
        self.check()
        (self.root / "flujos.md").write_text('[Actual](really-missing.md)\n')
        self.check(2)

    def test_escaped_brackets_preserve_active_links_after_literal_backslashes(self):
        page = self.root / "flujos.md"
        for count, status in [(0, 2), (1, 0), (2, 2), (3, 0), (4, 2)]:
            with self.subTest(backslashes=count):
                page.write_text("An example: " + chr(92) * count + "[Actual](missing.md)\n")
                self.check(status)
        page.write_text(chr(92) + "![Actual](missing.md)\n")
        self.check(2)  # Escaped ! leaves an ordinary active link.
        page.write_text(chr(92) + "`[Actual](missing.md)`\n")
        self.check(2)  # An escaped opening backtick does not create a code span.

    def test_missing_files_and_valid_json_missing_required_fields(self):
        (self.root / "datos.md").unlink()
        self.check(2)
        (self.root / "datos.md").write_text("Explicit data analysis.")
        del self.data["lifecycle"]
        self.save()
        self.assertTrue(any("lifecycle" in e for e in self.check(2)["structural"]))

    def test_nested_schema_values_and_unknown_version(self):
        self.data["scorecard"] = [{"dimension": "Architecture", "score": True, "top_finding": "none", "detail": "auditoria.md"}]
        self.save()
        self.check(2)
        self.data["scorecard"] = []
        self.data["schema_version"] = 99
        self.save()
        self.assertTrue(self.check(3)["unsupported_schema"])

    def test_historical_schema_is_explicitly_legacy(self):
        del self.data["schema_version"]
        del self.data["sections"]
        self.save()
        self.assertTrue(self.check()["legacy"])
        del self.data["repo"]
        self.save()
        self.check(2)

    def test_honest_partial_and_na_preserve_provenance(self):
        self.data["sections"]["flujos.md"].update(status="not-completed", verification="runtime unavailable", limitations=["only notes available"])
        self.data["sections"]["datos.md"].update(status="not-applicable", limitations=["no entities/tables in scoped module"])
        self.save()
        self.assertEqual(self.check()["partial_sections"], ["flujos.md"])
        del self.data["sections"]["datos.md"]["source_id"]
        (self.root / "analisis.json").write_text(json.dumps(self.data))
        self.check(2)

    def test_completion_and_source_mismatch(self):
        self.data["sections"]["flujos.md"].update(status="not-completed", limitations=["not retraced"])
        (self.root / "analisis.json").write_text(json.dumps(self.data))
        self.assertTrue(self.check(2)["semantic_coverage"])
        self.save()
        self.check()
        p = self.root / "README.md"
        p.write_text(p.read_text().replace(self.source, "b" * 40, 1))
        self.check(2)

    def test_placeholders_empty_content_and_partial_reason(self):
        p = self.root / "datos.md"
        p.write_text("# Data\n\n{{unfinished}}\n")
        self.check(2)
        p.write_text("# Data\n")
        self.check(2)
        self.data["sections"]["datos.md"].update(status="not-completed", verification="not checked", limitations=[])
        self.save()
        self.check(2)


if __name__ == "__main__":
    unittest.main()
