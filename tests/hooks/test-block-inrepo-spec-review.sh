#!/usr/bin/env bash
#
# Test suite for hooks/block-inrepo-spec-review.sh.
#
# Plain bash — no test framework to install. Run it directly:
#   ./tests/hooks/test-block-inrepo-spec-review.sh
# Exits 0 if every case passes, 1 on the first failure summary.
#
# Each case feeds a PreToolUse envelope on stdin and asserts the exit code:
#   0 = allow, 2 = deny.
# The suite deliberately covers the UNHAPPY paths that make this guard
# trustworthy: the portable default must stay allowed, deletions must stay
# allowed, reads must stay allowed, and a malformed envelope must fail OPEN.

set -uo pipefail

HOOK="$(cd "$(dirname "$0")/../.." && pwd)/hooks/block-inrepo-spec-review.sh"
ARCHIVE="/Users/example/brain/review-strict"
REPO="/Users/example/projects/cp-shops-catalog"

pass=0; fail=0

# Guard against a self-deceiving suite: `bash` also exits 2 on a SYNTAX ERROR,
# so asserting the exit code alone would let a broken hook report every deny
# case as a pass (this actually happened while writing it). A deny must
# therefore ALSO emit the BLOCK marker, and an allow must emit no BLOCK and no
# bash parse error. Assert on both signals, never on the exit code alone.
assert_syntax_ok() {
  if bash -n "$HOOK" 2>/dev/null; then
    printf 'PASS  el hook parsea (bash -n)\n'; pass=$((pass+1))
  else
    printf 'FAIL  el hook NO parsea — todo deny de abajo seria un falso positivo:\n%s\n' \
      "$(bash -n "$HOOK" 2>&1 | head -3)"; fail=$((fail+1))
  fi
}

# run_case <name> <expected_exit> <env_archive_dir> <payload-json>
# An empty <env_archive_dir> means REVIEW_STRICT_ARCHIVE_DIR is unset.
run_case() {
  local name="$1" expected="$2" archive="$3" payload="$4"
  local actual out why=""
  if [ -n "$archive" ]; then
    out=$(printf '%s' "$payload" | REVIEW_STRICT_ARCHIVE_DIR="$archive" "$HOOK" 2>&1); actual=$?
  else
    out=$(printf '%s' "$payload" | env -u REVIEW_STRICT_ARCHIVE_DIR "$HOOK" 2>&1); actual=$?
  fi

  [ "$actual" -eq "$expected" ] || why="exit=$actual (esperado $expected)"

  # A syntax/parse error must never be mistaken for a real decision.
  case "$out" in
    *"syntax error"*|*"unexpected EOF"*)
      why="${why:+$why; }bash no pudo parsear el hook" ;;
  esac

  if [ "$expected" -eq 2 ]; then
    case "$out" in
      *"BLOCK:"*) ;;
      *) why="${why:+$why; }deny sin el marcador BLOCK: en la salida" ;;
    esac
  else
    case "$out" in
      *"BLOCK:"*) why="${why:+$why; }allow pero emitio BLOCK:" ;;
    esac
  fi

  if [ -z "$why" ]; then
    printf 'PASS  %s\n' "$name"; pass=$((pass+1))
  else
    printf 'FAIL  %s\n        %s\n        salida: %s\n' \
      "$name" "$why" "$(printf '%s' "$out" | head -2)"; fail=$((fail+1))
  fi
}

write_payload()  { printf '{"tool_name":"Write","cwd":"%s","tool_input":{"file_path":"%s"}}' "$REPO" "$1"; }
edit_payload()   { printf '{"tool_name":"Edit","cwd":"%s","tool_input":{"file_path":"%s"}}' "$REPO" "$1"; }
bash_payload()   { printf '{"tool_name":"Bash","cwd":"%s","tool_input":{"command":%s}}' "$REPO" "$(printf '%s' "$1" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"; }
patch_payload()  { printf '{"tool_name":"apply_patch","cwd":"%s","tool_input":{"command":%s}}' "$REPO" "$(printf '%s' "$1" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"; }

echo "== the hook itself must parse before any assertion means anything =="
assert_syntax_ok

echo
echo "== the guard fires only when an archive dir is configured =="
run_case "sin env var: el fallback in-repo es el default documentado -> allow" \
  0 "" "$(write_payload "$REPO/specs/IT-1-foo/spec-review.md")"
run_case "con env var: el fallback in-repo es una regresion -> deny" \
  2 "$ARCHIVE" "$(write_payload "$REPO/specs/IT-1-foo/spec-review.md")"
run_case "env var definida pero VACIA: se trata como no definida -> allow" \
  0 "" "$(write_payload "$REPO/specs/IT-1-foo/spec-review.md")"

echo
echo "== the archive itself and scratch paths stay writable =="
run_case "escribir en el archivo central -> allow" \
  0 "$ARCHIVE" "$(write_payload "$ARCHIVE/cp-shops-catalog/spec-reviews/IT-1-foo.md")"
run_case "nombre de fallback PERO dentro del archivo -> allow" \
  0 "$ARCHIVE" "$(write_payload "$ARCHIVE/cp-shops-catalog/spec-reviews/spec-review.md")"
run_case "borrador en /tmp -> allow" \
  0 "$ARCHIVE" "$(write_payload "/tmp/draft/spec-review.md")"
run_case "borrador en /private/tmp -> allow" \
  0 "$ARCHIVE" "$(write_payload "/private/tmp/scratch/spec-review.md")"

echo
echo "== the Bash heredoc path — the one the skill actually uses =="
run_case "heredoc a ruta in-repo literal -> deny" \
  2 "$ARCHIVE" "$(bash_payload "mkdir -p d && cat > $REPO/specs/IT-1-foo/spec-review.md <<'EOF'
cuerpo
EOF")"
run_case "heredoc con \$OUT_DIR sin resolver, basename delata el fallback -> deny" \
  2 "$ARCHIVE" "$(bash_payload 'cat > "$OUT_DIR/spec-review.md" <<'"'"'SPEC_STRICT_EOF'"'"'
cuerpo
SPEC_STRICT_EOF')"
run_case "heredoc a nombre de archivo central (<spec-slug>.md) -> allow" \
  0 "$ARCHIVE" "$(bash_payload 'cat > "$OUT_DIR/IT-52986-chore-make-suite-runnable.md" <<'"'"'EOF'"'"'
cuerpo
EOF')"
run_case "re-run con sufijo -2 tambien se bloquea in-repo -> deny" \
  2 "$ARCHIVE" "$(bash_payload "cat > $REPO/specs/IT-1-foo/spec-review-2.md <<'EOF'
cuerpo
EOF")"
run_case "append (>>) in-repo -> deny" \
  2 "$ARCHIVE" "$(bash_payload "echo x >> $REPO/specs/IT-1-foo/spec-review.md")"
run_case "tee in-repo -> deny" \
  2 "$ARCHIVE" "$(bash_payload "echo x | tee $REPO/specs/IT-1-foo/spec-review.md")"
run_case "cp hacia ruta in-repo -> deny" \
  2 "$ARCHIVE" "$(bash_payload "cp /tmp/a.md $REPO/specs/IT-1-foo/spec-review.md")"

echo
echo "== Codex apply_patch envelope =="
run_case "Codex Add File in-repo -> deny" \
  2 "$ARCHIVE" "$(patch_payload '*** Begin Patch
*** Add File: specs/IT-1-foo/spec-review.md
+body
*** End Patch')"
run_case "Codex Update File in-repo -> deny" \
  2 "$ARCHIVE" "$(patch_payload '*** Begin Patch
*** Update File: specs/IT-1-foo/spec-review-2.md
@@
-old
+new
*** End Patch')"
run_case "Codex Delete File stays allowed" \
  0 "$ARCHIVE" "$(patch_payload '*** Begin Patch
*** Delete File: specs/IT-1-foo/spec-review.md
*** End Patch')"
run_case "Codex unrelated patch stays allowed" \
  0 "$ARCHIVE" "$(patch_payload '*** Begin Patch
*** Update File: app/Services/FooService.php
@@
-old
+new
*** End Patch')"

echo
echo "== deletions and reads MUST keep working (the cleanup depends on it) =="
run_case "git rm del residuo ya commiteado -> allow" \
  0 "$ARCHIVE" "$(bash_payload "git rm specs/IT-1-foo/spec-review.md")"
run_case "rm -f del residuo -> allow" \
  0 "$ARCHIVE" "$(bash_payload "rm -f $REPO/specs/IT-1-foo/spec-review.md")"
run_case "leer el archivo con cat -> allow" \
  0 "$ARCHIVE" "$(bash_payload "cat $REPO/specs/IT-1-foo/spec-review.md")"
run_case "grep sobre el archivo -> allow" \
  0 "$ARCHIVE" "$(bash_payload "grep -n verdict $REPO/specs/IT-1-foo/spec-review.md")"
run_case "git show del blob -> allow" \
  0 "$ARCHIVE" "$(bash_payload "git show origin/development:specs/IT-1-foo/spec-review.md > /tmp/out.md")"

echo
echo "== unrelated work is never touched =="
run_case "Write a codigo de producto -> allow" \
  0 "$ARCHIVE" "$(write_payload "$REPO/app/Services/FooService.php")"
run_case "Edit al spec.md mismo -> allow" \
  0 "$ARCHIVE" "$(edit_payload "$REPO/specs/IT-1-foo/spec.md")"
run_case "Bash sin ninguna ruta de review -> allow" \
  0 "$ARCHIVE" "$(bash_payload "composer test")"
run_case "reporte de review-strict (reviews/, otro basename) -> allow" \
  0 "$ARCHIVE" "$(write_payload "$REPO/reviews/cp-shops-catalog-pr-1.md")"

echo
echo "== fail-open and the escape valve =="
run_case "envelope malformado -> allow (fail-open)" \
  0 "$ARCHIVE" 'no soy json {{{'
run_case "envelope vacio -> allow (fail-open)" \
  0 "$ARCHIVE" ''
run_case "tool sin file_path -> allow" \
  0 "$ARCHIVE" '{"tool_name":"Write","cwd":"/x","tool_input":{}}'
run_case "tool fuera del matcher -> allow" \
  0 "$ARCHIVE" '{"tool_name":"Read","cwd":"/x","tool_input":{"file_path":"/x/specs/a/spec-review.md"}}'

# The bypass and forced-error knobs need their own env, so they bypass run_case.
if printf '%s' "$(write_payload "$REPO/specs/IT-1-foo/spec-review.md")" \
    | REVIEW_STRICT_ARCHIVE_DIR="$ARCHIVE" REVIEW_STRICT_HOOK_BYPASS=1 "$HOOK" >/dev/null 2>&1; then
  echo "PASS  REVIEW_STRICT_HOOK_BYPASS=1 permite el one-off -> allow"; pass=$((pass+1))
else
  echo "FAIL  REVIEW_STRICT_HOOK_BYPASS=1 deberia permitir"; fail=$((fail+1))
fi
if printf '%s' "$(write_payload "$REPO/specs/IT-1-foo/spec-review.md")" \
    | REVIEW_STRICT_ARCHIVE_DIR="$ARCHIVE" REVIEW_STRICT_HOOK_FORCE_ERROR=1 "$HOOK" >/dev/null 2>&1; then
  echo "PASS  error interno forzado -> falla abierto (allow)"; pass=$((pass+1))
else
  echo "FAIL  un error interno debe fallar abierto, no bloquear"; fail=$((fail+1))
fi

echo
echo "-------------------------------------------"
printf 'total: %s pass, %s fail\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
