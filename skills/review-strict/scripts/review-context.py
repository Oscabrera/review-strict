#!/usr/bin/env python3
"""Resolve immutable review inputs without switching branches or writing files."""

import argparse
import json
from pathlib import PurePosixPath
import re
import subprocess
import sys


class ContextError(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", repo, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise ContextError(detail or "git command failed: " + " ".join(args))
    return result.stdout


def commit(repo, ref):
    return git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()


def paths(raw):
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def context(repo, base, head):
    base_sha = commit(repo, base)
    head_sha = commit(repo, head)
    merge_base = git(repo, "merge-base", base_sha, head_sha).decode().strip()
    changed = paths(git(repo, "diff", "--name-only", "-z", merge_base, head_sha, "--"))
    return {
        "base_sha": base_sha,
        "head_sha": head_sha,
        "merge_base": merge_base,
        "changed_files": changed,
    }


def spec_context(repo, data, ticket):
    present = set(paths(git(repo, "ls-tree", "-r", "--name-only", "-z", data["head_sha"], "--", "specs/")))
    candidates = present if ticket else data["changed_files"]
    directories = sorted({
        p.rsplit("/", 1)[0] for p in candidates
        if re.fullmatch(r"specs/[^/]+/spec\.md", p) and p in present
        and (not ticket or p.startswith("specs/" + ticket + "-"))
    })
    if len(directories) != 1:
        raise ContextError(
            "expected one spec directory; found " + str(len(directories))
            + (": " + ", ".join(directories) if directories else "")
            + ". Pass an explicit spec path to the skill."
        )
    directory = directories[0]
    siblings = sorted(p for p in present if str(PurePosixPath(p).parent) == directory)
    data["spec_dir"] = directory
    data["spec_files"] = [p for p in siblings if p.endswith((".md", ".json")) or PurePosixPath(p).name == ".test-intent-contract-version"]
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("diff", "spec"):
        sub = commands.add_parser(name)
        sub.add_argument("--base", required=True)
        sub.add_argument("--head", default="HEAD")
        if name == "spec":
            sub.add_argument("--ticket", type=valid_ticket)
    show = commands.add_parser("show")
    show.add_argument("--head", required=True)
    show.add_argument("path")
    args = parser.parse_args()
    try:
        if args.command == "show":
            path = PurePosixPath(args.path)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ContextError("expected a repository-relative file path")
            sha = commit(args.repo, args.head)
            sys.stdout.buffer.write(git(args.repo, "show", sha + ":" + str(path)))
        else:
            data = context(args.repo, args.base, args.head)
            if args.command == "spec":
                data = spec_context(args.repo, data, args.ticket)
            print(json.dumps(data, indent=2, ensure_ascii=True))
    except ContextError as error:
        print("review-context: " + str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print("review-context: " + str(error), file=sys.stderr)
        return 2
    return 0


def valid_ticket(value):
    if not re.fullmatch(r"IT-\d+", value):
        raise argparse.ArgumentTypeError("expected IT-<digits>")
    return value


if __name__ == "__main__":
    sys.exit(main())
