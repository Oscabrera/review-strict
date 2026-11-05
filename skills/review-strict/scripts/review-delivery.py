#!/usr/bin/env python3
"""Prepare/check a review from frozen Git context; never post or write to the repo."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

_spec = importlib.util.spec_from_file_location("review_context", Path(__file__).with_name("review-context.py"))
ctx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ctx)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_context(repo, base, head, assessment):
    require(isinstance(assessment, dict), "assessment must be an object")
    actual = ctx.context(repo, base, head)
    require(assessment.get("subject") == actual, "assessment subject differs from resolved base/head/merge-base/patch")
    require(assessment.get("mode") in ("fast", "fan-out"), "record the actual review mode")
    require(assessment.get("decision") in ("approve", "request-changes", "comment", "incomplete"), "invalid decision")
    require(assessment.get("currency") == "current", "subject currency is not current")
    checks = assessment.get("completion")
    require(isinstance(checks, list) and checks, "completion ledger is required")
    seen = set()
    for check in checks:
        require(isinstance(check, dict), "invalid completion entry")
        key = check.get("id")
        require(isinstance(key, str) and key and key not in seen, "completion ids must be unique")
        seen.add(key)
        require(check.get("status") in ("completed", "not-applicable", "not-completed"), "invalid completion status")
        require(isinstance(check.get("evidence"), list) and all(isinstance(s, str) and s.strip() for s in check["evidence"]), "completion evidence must be a string list")
        require(check["status"] != "completed" or check["evidence"], "completed work needs evidence")
        require(check["status"] == "completed" or check.get("reason"), "incomplete/N/A work needs a reason")
    require({"correctness", "security", "architecture", "tests", "migration", "skeptic", "approval-claims"} <= seen, "missing required lens/skeptic/approval completion entries")
    claims = assessment.get("claims")
    require(isinstance(claims, list), "final claim ledger is required, even if empty")
    claim_ids = set()
    for claim in claims:
        require(isinstance(claim, dict) and claim.get("id") and claim.get("text"), "invalid claim")
        require(isinstance(claim["id"], str) and claim["id"] not in claim_ids, "claim ids must be unique strings")
        claim_ids.add(claim["id"])
        require(type(claim.get("required")) is bool, "claim.required must be boolean")
        require(claim.get("verdict") in ("verified", "unsupported", "contradicted"), "invalid claim verdict")
        evidence = claim.get("evidence")
        require(isinstance(evidence, list) and all(isinstance(s, str) and s.strip() for s in evidence), "claim evidence must be a string list")
        require(claim["verdict"] != "verified" or evidence, "verified claim needs evidence")
        require(claim["verdict"] != "contradicted", "correct contradicted approval claims before delivery")
    gaps = any(c["status"] == "not-completed" for c in checks) or any(c["required"] and c["verdict"] != "verified" for c in claims)
    require(not gaps or assessment["decision"] in ("incomplete", "request-changes"), "missing required evidence cannot yield approval/comment")
    blockers = assessment.get("blocking_findings")
    require(type(blockers) is int and blockers >= 0, "blocking_findings must be a nonnegative integer")
    require(not blockers or assessment["decision"] == "request-changes", "known blockers require changes")
    require(assessment["decision"] != "request-changes" or blockers > 0, "request-changes requires a verified blocker")
    deleted = set(ctx.paths(ctx.git(repo, "diff", "--diff-filter=D", "--name-only", "-z", actual["merge_base"], actual["head_sha"], "--")))
    require(isinstance(assessment.get("patch_assertions", []), list), "patch_assertions must be an array")
    for assertion in assessment.get("patch_assertions", []):
        require(isinstance(assertion, dict), "invalid patch assertion")
        path, kind = assertion.get("path"), assertion.get("kind")
        require(path in actual["changed_files"], "patch assertion concerns a base-only or unchanged path: " + str(path))
        require(kind in ("deletion", "conflict"), "unknown patch assertion kind")
        require(kind != "deletion" or path in deleted, "claimed deletion is absent from the PR patch: " + path)
        require(bool(assertion.get("evidence")), "patch assertion requires pinned patch/merge evidence")
    return actual


def prepare(repo, base, head, assessment, body):
    subject = checked_context(repo, base, head, assessment)
    # Subject/provenance fields belong to the generated header, never copied prose.
    require(not re.search(r"(?im)^\s*[-*]?\s*(?:\*\*)?(?:subject|base(?:_sha)?|head(?:_sha)?|merge[-_]base|decision|currency)\s*(?:\*\*)?\s*:", body), "remove hand-authored subject/decision fields from the body")
    for claim in assessment["claims"]:
        if claim["verdict"] != "verified":
            require(claim["text"] not in body, "omit unsupported claims from the final body")
    version = json.loads((Path(__file__).resolve().parents[3] / ".claude-plugin/plugin.json").read_text())["version"]
    metadata = {"subject": subject, "skill_version": version, "assessment": assessment,
                "body_sha256": hashlib.sha256(body.encode()).hexdigest()}
    encoded = json.dumps(metadata, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e")
    return ("<!-- review-strict-delivery " + encoded + " -->\n"
            + "Decision: " + assessment["decision"] + "\n"
            + "Base: " + subject["base_sha"] + "\nHead: " + subject["head_sha"]
            + "\nMerge-base: " + subject["merge_base"]
            + "\nProvenance: review-strict " + version + "; " + assessment["mode"]
            + "; currency=current\n\n" + body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "validate", "github-payload"))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base", required=True, help="current receiving ref/OID, rechecked at delivery")
    parser.add_argument("--head", required=True, help="current subject ref/OID, rechecked at delivery")
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--body", required=True, help="review prose without identity/decision header")
    parser.add_argument("--artifact", help="prepared report to compare byte for byte")
    args = parser.parse_args()
    try:
        assessment = json.loads(Path(args.assessment).read_text())
        body = Path(args.body).read_bytes().decode("utf-8")
        artifact = prepare(args.repo, args.base, args.head, assessment, body)
        if args.command == "prepare":
            sys.stdout.buffer.write(artifact.encode("utf-8"))
        else:
            require(args.artifact, "--artifact is required")
            require(Path(args.artifact).read_bytes() == artifact.encode("utf-8"), "artifact differs from its checked subject, assessment or body")
            if args.command == "github-payload":
                event = {"approve": "APPROVE", "request-changes": "REQUEST_CHANGES"}.get(assessment["decision"], "COMMENT")
                print(json.dumps({"commit_id": assessment["subject"]["head_sha"], "event": event, "body": artifact}))
            else:
                print(json.dumps({"valid": True, "subject": assessment["subject"], "decision": assessment["decision"]}))
    except (OSError, ValueError, TypeError, KeyError, ctx.ContextError) as error:
        print("review-delivery: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
