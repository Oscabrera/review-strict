#!/usr/bin/env python3
"""Prepare blind review inputs; keep expected judgments out of the output."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ab-shop", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    cases = json.loads(Path(__file__).with_name("operational-risk-cases.json").read_text())

    def blob(sha, path):
        return subprocess.run(["git", "-C", str(args.ab_shop), "show", f"{sha}:{path}"],
                              check=True, text=True, capture_output=True).stdout

    # Read all snapshots before creating output: unavailable Git objects fail visibly.
    prepared = []
    for case in cases:
        files = dict(case.get("files", {}))
        if "snapshot" in case:
            sha = case["snapshot"]
            paths = ["modules/cp/lib/Base.php", "modules/cp/lib/structs/ApiOptions.php",
                     "tests/unit/modules/cp/lib/BaseTransportRetryTest.php"]
            for path in paths:
                files[path] = blob(sha, path)
            for path, start, end in [
                ("modules/cp/cpsaldo/models/cpsaldo_oxuser.php", 35, 90),
                ("modules/cp/cpdeliveryset/models/cpdeliveryset_oxdeliveryset.php", 235, 280),
            ]:
                lines = blob(sha, path).splitlines()
                files[path + ".excerpt"] = "\n".join(
                    f"{n}: {lines[n-1]}" for n in range(start, min(end, len(lines)) + 1)) + "\n"
            files["context.txt"] = (
                f"Frozen ab-shop source: {sha}. Review the retry change only. "
                "Before the PR, sendThroughGuzzle made one client request with the same options. "
                "Relevant dependency facts: composer.lock pins Guzzle 6.5.5. "
                "StreamHandler is selected with stream=true and the default client handler. "
                "Its fopen errors become no-response RequestException, including read timeouts; "
                "ConnectException also extends RequestException in 6.5.5. "
                "timeout=0 omits the stream timeout override, inheriting default_socket_timeout. "
                "Use 60 s as the fixture runtime default, not a verified production setting. "
                "No deployment pool size or traffic is supplied. PR originally declared 3x latency "
                "accepted, with no total cap, but supplied no acceptance authority. "
                "Judge the supplied source, not that declaration. Do not assume an observed outage. "
                "Dependency reference: https://github.com/guzzle/guzzle/blob/6.5.5/src/Handler/StreamHandler.php\n"
            )
        prepared.append((case["id"], files))
    args.out.mkdir(parents=True, exist_ok=False)
    for case_id, files in prepared:
        for name, content in files.items():
            path = args.out / case_id / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print(f"Prepared {len(prepared)} blind cases in {args.out}")


if __name__ == "__main__":
    main()
