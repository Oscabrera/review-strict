#!/usr/bin/env bash
#
# block-inrepo-spec-review.sh — PreToolUse hook for Claude/Codex edits and shell calls.
#
# Blocks writing a `/spec-strict` review INTO the reviewed repo when the
# developer has configured a central archive via REVIEW_STRICT_ARCHIVE_DIR.
#
# WHY THIS EXISTS
# ---------------
# /spec-strict once resolved its save path in PROSE rather than in code, so it
# silently ignored REVIEW_STRICT_ARCHIVE_DIR and fell through to its in-repo
# fallback `<spec-dir>/spec-review.md`. 21 review reports were committed onto
# the base branches of 5 repos before anyone noticed. v1.2.1 fixed the skill's
# instructions (Phase 0 binds $OUT_DIR, Phase 5 consumes it, both announce the
# resolved path) — but an instruction is not an enforcement. This hook is the
# mechanical guard: if the fallback ever fires again while an archive dir is
# configured, the write is DENIED instead of silently landing in the repo.
#
# THE RULE
# --------
# Deny a WRITE whose target basename matches `spec-review*.md` when ALL hold:
#   1. REVIEW_STRICT_ARCHIVE_DIR is set and non-empty. When it is UNSET the
#      in-repo path is the skill's documented portable default, so the write
#      is legitimate and this hook is a no-op. This is what keeps the guard
#      correct for every other user of the plugin, not just one machine.
#   2. The target is not inside REVIEW_STRICT_ARCHIVE_DIR itself.
#   3. The target is not an ephemeral scratch path (/tmp, /var/tmp,
#      /private/tmp, $TMPDIR) — drafting a report there is fine.
#
# WHY MATCHING THE BASENAME IS SUFFICIENT
# ---------------------------------------
# The two precedence branches use DIFFERENT filenames: the archive writes
# `<spec-slug>.md` (e.g. `IT-52986-chore-make-feature-suite-runnable.md`),
# and only the in-repo fallback writes `spec-review.md`. So the basename alone
# identifies the branch — which is what lets this hook work even when the
# directory part is an unresolvable shell variable, e.g.
# `cat > "$OUT_DIR/spec-review.md" <<'EOF'`. A literal `spec-review.md`
# basename plus a configured archive dir means the fallback fired.
#
# WHY THE Bash MATCHER IS NOT OPTIONAL
# ------------------------------------
# The skill is instructed to write the report with a Bash quoted heredoc (so
# the report's own `$`/backticks land literally), NOT with the Write tool. A
# Write|Edit-only matcher would therefore catch nothing in the normal path.
#
# DELETIONS ARE ALLOWED ON PURPOSE
# --------------------------------
# Only write verbs are inspected (`>`/`>>`, tee, cp, mv, install, rsync,
# ditto). `rm` / `git rm` on a spec-review.md must keep working — that is
# exactly how the already-committed residue gets cleaned up.
#
# FAIL-OPEN POSTURE
# -----------------
# Any internal error (missing jq, unparseable envelope, python failure) exits
# 0 with a WARN. A buggy hook must never break a session; a false negative
# here is a tolerable regression to the status quo, a false positive that
# blocks unrelated writes is not.

set -uo pipefail

fail_open() {
  echo "WARN: block-inrepo-spec-review.sh internal error at line ${1:-?} (${2:-?}); failing open" >&2
  exit 0
}
trap 'fail_open "$LINENO" "$BASH_COMMAND"' ERR

# Test-only force-error knob, so the fail-open contract itself is testable.
if [ "${REVIEW_STRICT_HOOK_FORCE_ERROR:-0}" = "1" ]; then
  echo "WARN: block-inrepo-spec-review.sh forced error; failing open" >&2
  exit 0
fi

# Per-call escape valve for a deliberate one-off (incident recovery, or a
# developer who genuinely wants the report in the repo despite the env var).
if [ "${REVIEW_STRICT_HOOK_BYPASS:-0}" = "1" ]; then
  exit 0
fi

# Rule 1 — no configured archive means the in-repo path IS the intended
# default. Nothing to enforce; exit before touching stdin's payload.
ARCHIVE_DIR="${REVIEW_STRICT_ARCHIVE_DIR:-}"
if [ -z "$ARCHIVE_DIR" ]; then
  exit 0
fi

command -v jq >/dev/null 2>&1 || fail_open "$LINENO" "jq not found"

payload=$(cat)
tool=$(printf '%s' "$payload" | jq -r '.tool_name // ""' 2>/dev/null || echo "")
[ -n "$tool" ] || exit 0

# Collect the write targets this tool call would touch, one per line.
targets=""
case "$tool" in
  Write|Edit)
    targets=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // ""' 2>/dev/null || echo "")
    ;;
  apply_patch)
    patch=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
    [ -n "$patch" ] || exit 0
    # Codex reports patch edits with canonical tool_name=apply_patch. Block
    # Add/Update/Move destinations, while deliberately leaving Delete allowed.
    targets=$(printf '%s' "$patch" | sed -nE \
      -e 's/^\*\*\* (Add|Update) File: (.*spec-review[^/]*\.md)$/\2/p' \
      -e 's/^\*\*\* Move to: (.*spec-review[^/]*\.md)$/\1/p')
    ;;
  Bash)
    cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
    [ -n "$cmd" ] || exit 0
    # Extract only tokens that a WRITE verb targets. Deliberately narrow: a
    # read (cat/grep/git show) or a delete (rm/git rm) of the same path is
    # allowed, so this must not match them.
    # NOTE: this python source is embedded in a single-quoted shell string, so
    # it must contain NO literal apostrophe. Shell quote characters that need
    # to appear in the regexes are written as \x27 (') and \x22 (") escapes.
    targets=$(printf '%s' "$cmd" | python3 -c '
import re, sys
cmd = sys.stdin.read()
# A path token ending in a spec-review*.md basename. It stops at shell
# metacharacters and at either quote, so a redirection like
# > "$OUT_DIR/spec-review.md" yields the inner path with the quote dropped.
PATH_TOKEN = r"[^\s\x27\x22|;&<>()]*spec-review[^\s\x27\x22|;&<>()]*\.md"
WRITE_VERBS = {"tee", "cp", "mv", "install", "rsync", "ditto"}
found = []

# Work per shell segment. A write verb is only a write verb in COMMAND
# position: matching it anywhere in the segment would fire on a path that
# merely contains the word — e.g. `\bcp\b` matches the "cp" inside a repo
# named cp-shops-catalog, which would wrongly block `rm`/`cat`/`grep` on any
# path under it. Splitting first, then reading the command word, is what
# keeps deletions and reads allowed.
for segment in re.split(r"[;&|\n]+", cmd):
    if not segment.strip():
        continue

    # Shape A — an output redirection is a write regardless of the verb.
    found += re.findall(r">>?\s*[\x27\x22]?(" + PATH_TOKEN + r")", segment)

    # Shape B — the segment command word is a copying/writing verb. Skip any
    # leading KEY=VALUE env assignments the way the shell itself does.
    tokens = segment.split()
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    if i < len(tokens):
        verb = tokens[i].split("/")[-1]  # /usr/bin/cp -> cp
        if verb in WRITE_VERBS:
            found += re.findall(r"[\x27\x22]?(" + PATH_TOKEN + r")", segment)

seen = set()
for t in found:
    if t and t not in seen:
        seen.add(t)
        print(t)
' 2>/dev/null || echo "")
    ;;
  *)
    exit 0
    ;;
esac

[ -n "$targets" ] || exit 0

# Normalize a prefix for containment tests: absolute, no trailing slash,
# `~` expanded. Purely lexical — the target may not exist yet.
norm_prefix() {
  local p="${1:-}"
  [ -n "$p" ] || { printf '%s' ""; return; }
  case "$p" in
    "~") p="$HOME" ;;
    "~/"*) p="$HOME/${p#\~/}" ;;
  esac
  printf '%s' "${p%/}"
}

archive_norm=$(norm_prefix "$ARCHIVE_DIR")
tmpdir_norm=$(norm_prefix "${TMPDIR:-/tmp}")

deny() {
  cat >&2 <<EOF
BLOCK: refusing to write a /spec-strict review into the reviewed repo.

  target : $1
  reason : its basename matches spec-review*.md — the in-repo FALLBACK path —
           but REVIEW_STRICT_ARCHIVE_DIR is configured, so the review belongs
           in the central archive. Only the fallback uses this filename; the
           archive writes <spec-slug>.md.

This is the regression that put 21 review reports into 5 repos' base branches
(ClickUp IT-55173). The review is OUTPUT, not spec source — it must not be
committed to a product repo.

Write it here instead:
  ${archive_norm}/<repo>/spec-reviews/<spec-slug>.md

Resolve the path the way /spec-strict Phase 0 mandates, then reuse it:
  REPO="\$(basename "\$(git rev-parse --show-toplevel)")"
  OUT_DIR="\${REVIEW_STRICT_ARCHIVE_DIR}/\${REPO}/spec-reviews"

Deleting or reading a spec-review.md is NOT blocked — only writing one.
For a deliberate one-off, prefix the call with REVIEW_STRICT_HOOK_BYPASS=1.
EOF
  exit 2
}

while IFS= read -r target || [ -n "$target" ]; do
  [ -n "$target" ] || continue

  base="${target##*/}"
  # Only the fallback filename shape is in scope.
  case "$base" in
    spec-review*.md) ;;
    *) continue ;;
  esac

  # Resolve relative targets against the envelope cwd so containment tests
  # below see an absolute path. Unresolvable shell variables are left as-is;
  # the basename check above already established intent.
  abs="$target"
  case "$abs" in
    /*) ;;
    "~/"*) abs="$HOME/${abs#\~/}" ;;
    *)
      cwd=$(printf '%s' "$payload" | jq -r '.cwd // ""' 2>/dev/null || echo "")
      [ -n "$cwd" ] && abs="${cwd%/}/$abs"
      ;;
  esac

  # Rule 2 — already inside the archive: allowed (belt-and-braces; the
  # archive never uses this basename).
  case "$abs" in
    "$archive_norm"|"$archive_norm"/*) continue ;;
  esac

  # Rule 3 — ephemeral scratch paths: allowed.
  case "$abs" in
    /tmp/*|/var/tmp/*|/private/tmp/*) continue ;;
    "$tmpdir_norm"/*) continue ;;
  esac

  deny "$target"
done <<EOF
$targets
EOF

exit 0
