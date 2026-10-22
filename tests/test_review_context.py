"""Exercise review inputs against real Git histories, without network access."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/review-strict/scripts/review-context.py"


class ReviewContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="review-context-test-")
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write("source.txt", "base\n")
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.git("checkout", "-b", "feature")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout

    def write(self, name, value):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def run_context(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *args], capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, "")
        return result

    def test_diverged_base_excludes_changes_only_on_main(self):
        self.write("feature.txt", "feature\n")
        head = self.commit("feature")
        self.git("checkout", "main")
        self.write("main-only.txt", "main\n")
        base_tip = self.commit("main advances")
        data = json.loads(self.run_context("diff", "--base", "main", "--head", head).stdout)
        self.assertEqual(data, {"base_sha": base_tip, "head_sha": head, "merge_base": self.base, "changed_files": ["feature.txt"]})

    def test_missing_base_is_an_error_not_an_empty_diff(self):
        result = self.run_context("diff", "--base", "missing", ok=False)
        self.assertIn("review-context:", result.stderr)

    def test_pinned_reads_ignore_dirty_checkout_and_moving_branch(self):
        self.write("source.txt", "reviewed\n")
        head = self.commit("reviewed")
        data = json.loads(self.run_context("diff", "--base", "main").stdout)
        self.write("source.txt", "later\n")
        self.commit("later")
        self.write("source.txt", "dirty\n")
        self.assertEqual(data["head_sha"], head)
        self.assertEqual(self.run_context("show", "--head", data["head_sha"], "source.txt").stdout, "reviewed\n")
        self.assertEqual((self.repo / "source.txt").read_text(), "dirty\n")

    def test_filenames_with_spaces_and_newlines_are_not_split(self):
        names = ["two words.txt", "two\nlines.txt"]
        for name in names:
            self.write(name, "value\n")
        self.commit("unusual names")
        data = json.loads(self.run_context("diff", "--base", "main").stdout)
        self.assertEqual(set(data["changed_files"]), set(names))

    def test_spec_inventory_includes_design_decisions_and_contract_version(self):
        directory = "specs/IT-123-fix-example"
        names = ["spec.md", "design.md", "contracts.md", "decisions.md", ".test-intent-contract-version"]
        for name in names:
            self.write(directory + "/" + name, "fixture\n")
        self.write(directory + "/evidence/large.patch", "evidence\n")
        self.commit("spec")
        data = json.loads(self.run_context("spec", "--base", "main").stdout)
        self.assertEqual(data["spec_dir"], directory)
        self.assertEqual(set(data["spec_files"]), {directory + "/" + name for name in names})

    def test_ambiguous_and_absent_specs_fail_visibly(self):
        self.run_context("spec", "--base", "main", ok=False)
        for ticket in ("IT-123", "IT-124"):
            self.write("specs/" + ticket + "-fix-example/spec.md", "spec\n")
        self.commit("two specs")
        result = self.run_context("spec", "--base", "main", ok=False)
        self.assertIn("found 2", result.stderr)
        data = json.loads(self.run_context("spec", "--base", "main", "--ticket", "IT-124").stdout)
        self.assertEqual(data["spec_dir"], "specs/IT-124-fix-example")

    def test_ticket_lookup_can_find_spec_already_on_base(self):
        self.write("specs/IT-123-fix-example/spec.md", "spec\n")
        self.commit("spec")
        self.git("branch", "new-base")
        data = json.loads(self.run_context("spec", "--base", "new-base", "--ticket", "IT-123").stdout)
        self.assertEqual(data["changed_files"], [])
        self.assertEqual(data["spec_dir"], "specs/IT-123-fix-example")

    def test_deleted_spec_is_not_selected(self):
        self.write("specs/IT-123-fix-example/spec.md", "spec\n")
        self.commit("spec")
        self.git("branch", "with-spec")
        self.git("rm", "specs/IT-123-fix-example/spec.md")
        self.commit("remove spec")
        self.run_context("spec", "--base", "with-spec", ok=False)

    def test_show_rejects_escape_and_missing_blob(self):
        for name in ("../source.txt", "/source.txt", "missing.txt"):
            self.run_context("show", "--head", "HEAD", name, ok=False)


if __name__ == "__main__":
    unittest.main()
