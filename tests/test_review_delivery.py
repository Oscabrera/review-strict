"""Exercise prepared artifacts through delivery against real divergent Git history."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/review-strict/scripts"


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name)
        self.repo = self.run_dir / "repo"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.write("source.txt", "base\n")
        self.write("remove.txt", "remove me\n")
        self.commit("base")
        self.git("checkout", "-b", "feature")
        self.write("source.txt", "feature\n")
        self.commit("feature")
        self.git("checkout", "main")
        self.write(".github/workflows/check.yml", "name: receiving-base-only\n")
        self.commit("base adds workflow")
        self.assessment = self.make_assessment()
        (self.run_dir / "body.md").write_text("# Findings\n\nNo blocking findings.\n")

    def git(self, *args, ok=True):
        r = subprocess.run(["git", "-C", str(self.repo), *args], text=True, capture_output=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def write(self, name, text):
        p = self.repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)

    def make_assessment(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "review-context.py"), "--repo", str(self.repo), "diff", "--base", "main", "--head", "feature"], text=True, capture_output=True, check=True)
        return {"subject": json.loads(result.stdout), "mode": "fast", "decision": "approve", "currency": "current", "blocking_findings": 0, "completion": [{"id": k, "status": "completed", "evidence": ["source.txt:1 inspected " + k]} for k in ["correctness", "security", "architecture", "tests", "migration", "skeptic", "approval-claims"]], "claims": [], "patch_assertions": []}

    def run_delivery(self, command="prepare", assessment=None, ok=True, head="feature"):
        (self.run_dir / "assessment.json").write_text(json.dumps(assessment or self.assessment))
        args = [sys.executable, str(SCRIPTS / "review-delivery.py"), command, "--repo", str(self.repo), "--base", "main", "--head", head, "--assessment", str(self.run_dir / "assessment.json"), "--body", str(self.run_dir / "body.md")]
        if command != "prepare":
            args += ["--artifact", str(self.run_dir / "review.md")]
        r = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0 if ok else 2, r.stderr)
        return r

    def prepare(self, assessment=None):
        result = self.run_delivery(assessment=assessment)
        (self.run_dir / "review.md").write_text(result.stdout)
        return result.stdout

    def test_base_only_workflow_is_not_a_deletion_and_merge_preserves_it(self):
        self.assertIn(".github/workflows/check.yml", self.git("diff", "--name-only", "main", "feature"))
        self.assertNotIn(".github/workflows/check.yml", self.assessment["subject"]["changed_files"])
        tree = self.git("merge-tree", "--write-tree", "main", "feature").strip()
        self.assertEqual(self.git("show", tree + ":.github/workflows/check.yml"), "name: receiving-base-only\n")
        body = self.prepare()
        self.assertIn("Head: " + self.assessment["subject"]["head_sha"], body)
        self.run_delivery("validate")
        bad = copy.deepcopy(self.assessment)
        bad["patch_assertions"] = [{"kind": "deletion", "path": ".github/workflows/check.yml", "evidence": "two-tip diff"}]
        self.assertIn("base-only", self.run_delivery(assessment=bad, ok=False).stderr)

    def test_invalid_or_different_subject_cannot_be_delivered(self):
        self.run_delivery(head="not-a-commit", ok=False)
        bad = copy.deepcopy(self.assessment)
        bad["subject"]["head_sha"] = self.git("rev-parse", "main").strip()
        self.run_delivery(assessment=bad, ok=False)
        self.prepare()
        p = self.run_dir / "review.md"
        p.write_text(p.read_text().replace(self.assessment["subject"]["head_sha"], "0" * 40))
        self.run_delivery("validate", ok=False)

    def test_real_feature_deletion_and_conflict_remain_reportable(self):
        self.git("checkout", "feature")
        self.git("rm", "remove.txt")
        self.commit("actual deletion")
        self.git("checkout", "main")
        self.write("source.txt", "receiving change\n")
        self.commit("conflicting base")
        merge = self.git("merge-tree", "--write-tree", "main", "feature", ok=False)
        self.assertIn("CONFLICT", merge)
        a = self.make_assessment()
        a["patch_assertions"] = [{"path": "remove.txt", "kind": "deletion", "evidence": "pinned PR deletion"}, {"path": "source.txt", "kind": "conflict", "evidence": merge}]
        self.prepare(a)
        self.run_delivery("validate", assessment=a)

    def test_currency_and_dirty_tree(self):
        self.prepare()
        self.write("source.txt", "dirty ignored\n")
        self.run_delivery("validate")
        self.assertEqual((self.repo / "source.txt").read_text(), "dirty ignored\n")
        self.git("restore", "source.txt")
        self.write("later.txt", "new base\n")
        self.commit("base moves")
        self.run_delivery("validate", ok=False)

    def test_missing_checks_or_required_claim_proof_prevent_approval(self):
        a = copy.deepcopy(self.assessment)
        a["completion"].pop()
        self.run_delivery(assessment=a, ok=False)
        a = copy.deepcopy(self.assessment)
        a["claims"] = [{"id": "rollout", "text": "Rollout safe", "required": True, "verdict": "unsupported", "evidence": []}]
        self.run_delivery(assessment=a, ok=False)
        a["decision"] = "incomplete"
        self.prepare(a)
        payload = json.loads(self.run_delivery("github-payload", assessment=a).stdout)
        self.assertEqual(payload["event"], "COMMENT")
        self.assertEqual(payload["commit_id"], a["subject"]["head_sha"])

    def test_unsupported_or_contradicted_review_claims_are_not_source_defects(self):
        a = copy.deepcopy(self.assessment)
        a["claims"] = [{"id": "status", "text": "Returns HTTP 422", "required": False, "verdict": "contradicted", "evidence": ["request.py:4 returns 404"]}]
        self.run_delivery(assessment=a, ok=False)
        a["claims"][0].update(text="Returns HTTP 404", verdict="verified")
        a["mode"] = "fan-out"
        self.prepare(a)
        payload = json.loads(self.run_delivery("github-payload", assessment=a).stdout)
        self.assertEqual(payload["event"], "APPROVE")
        self.assertIn("fan-out", payload["body"])
        a["claims"][0].update(text="Fallback is available", verdict="unsupported", evidence=[])
        (self.run_dir / "body.md").write_text("Fallback is available\n")
        self.run_delivery(assessment=a, ok=False)

    def test_blocker_disposition_and_artifact_tampering(self):
        a = copy.deepcopy(self.assessment)
        a["blocking_findings"] = 1
        self.run_delivery(assessment=a, ok=False)
        a["decision"] = "request-changes"
        a["completion"][0].update(status="not-completed", reason="caller missing", evidence=[])
        self.prepare(a)
        self.assertEqual(json.loads(self.run_delivery("github-payload", assessment=a).stdout)["event"], "REQUEST_CHANGES")
        (self.run_dir / "review.md").write_text("An unrelated report\n")
        self.run_delivery("validate", assessment=a, ok=False)

    def test_hand_transcribed_subject_header_rejected(self):
        (self.run_dir / "body.md").write_text("Head: " + "f" * 40 + "\n")
        self.run_delivery(ok=False)

    def test_artifact_comparison_preserves_exact_newline_bytes(self):
        self.prepare()
        path = self.run_dir / "review.md"
        original = path.read_bytes()
        path.write_bytes(original.replace(b"\n", b"\r\n"))
        self.run_delivery("validate", ok=False)
        path.write_bytes(original)
        self.run_delivery("validate")


if __name__ == "__main__":
    unittest.main()
