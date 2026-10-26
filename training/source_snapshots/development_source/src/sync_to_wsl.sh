#!/bin/bash
# Sync source from the Windows checkout into the WSL working tree, safely.
#
# WHY THIS EXISTS. ~/workspace/MIRAGE is not a git checkout, so an edit made on the Windows
# side never reaches it and `git pull` cannot fetch it. Three steps in one round were run
# against stale scripts because of that, and one of them cost eight hours: the B1 one-epoch
# arm trained for 7 h 52 m and then skipped inference, because the WSL runner predated a
# configurable arm label and the hardcoded output path already held the three-epoch
# predictions at exactly the expected row count. The completeness check passed. Nothing in
# the log looked wrong.
#
# So the failure mode this guards against is not "the copy failed". It is "the script ran,
# reported success, and measured the wrong thing".
#
# IT RUNS FROM THE WINDOWS PATH, so it never needs syncing itself:
#
#     bash __DEV_ROOT__/src/sync_to_wsl.sh
#     bash __DEV_ROOT__/src/sync_to_wsl.sh --apply
#
# DRY RUN BY DEFAULT. The standing rule in this project is that the WSL copy is authoritative
# where the two genuinely diverge, so nothing is overwritten until you have seen the list and
# passed --apply. A file that differs AND is newer on the WSL side is reported as a possible
# WSL-side edit and is skipped unless --force is given, because losing work silently is the
# one outcome worse than being out of date.
#
# LINE ENDINGS ARE NORMALISED ON COPY. A .sh file carrying CRLF fails in bash with
# "bad interpreter: /bin/bash^M", which is at least loud. Comparison strips CR first so that
# a pure line-ending difference is never reported as a change.
#
# SOURCE ONLY. outputs/, data/, checkpoints and results are never touched: they are the
# products, they are large, and several are only ever written on one side.
set -uo pipefail

WIN=${WIN:-__DEV_ROOT__/src}
WSL=${WSL:-$HOME/workspace/MIRAGE/src}
APPLY=0
FORCE=0
INCLUDE_NEW=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --force) FORCE=1 ;;
    --include-new) INCLUDE_NEW=1 ;;
    -h|--help) sed -n '2,32p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

[ -d "$WIN" ] || { echo "source not found: $WIN" >&2; exit 1; }
[ -d "$WSL" ] || { echo "destination not found: $WSL" >&2; exit 1; }

# Which files are source. Anything not matched here is none of this script's business.
list_source() {
  ( cd "$1" && find . \
      \( -path ./outputs -o -path ./data -o -path ./.git -o -name __pycache__ \) -prune -o \
      \( -name '*.py' -o -name '*.sh' \) ! -name sync_to_wsl.sh -print     ) 2>/dev/null | sed 's|^\./||' | sort
  # .ps1 is excluded: PowerShell wrappers cannot run in WSL, and listing them buries the
  # files that matter. This script is excluded too -- it runs from the Windows path.
}

# Hash with carriage returns stripped, so CRLF versus LF is not a difference.
hash_nocr() { tr -d '\r' < "$1" 2>/dev/null | sha256sum | cut -d' ' -f1; }

NEW=(); CHANGED=(); WSL_NEWER=(); SAME=0

while IFS= read -r rel; do
  [ -n "$rel" ] || continue
  src="$WIN/$rel"; dst="$WSL/$rel"
  if [ ! -f "$dst" ]; then
    NEW+=("$rel"); continue
  fi
  if [ "$(hash_nocr "$src")" = "$(hash_nocr "$dst")" ]; then
    SAME=$((SAME+1)); continue
  fi
  # Content differs. mtime over the 9p mount is not fully trustworthy, so it is a hint only.
  if [ "$dst" -nt "$src" ]; then
    WSL_NEWER+=("$rel")
  else
    CHANGED+=("$rel")
  fi
done < <(list_source "$WIN")

echo "source: $WIN"
echo "target: $WSL"
echo
printf '  %-34s %s\n' "identical (ignoring line endings)" "$SAME"
printf '  %-34s %s\n' "absent from WSL (harmless)" "${#NEW[@]}"
printf '  %-34s %s\n' "STALE in WSL (dangerous)" "${#CHANGED[@]}"
printf '  %-34s %s\n' "differ but NEWER on the WSL side" "${#WSL_NEWER[@]}"
echo

# Stale first: these are the dangerous ones.
for rel in "${CHANGED[@]:-}"; do [ -n "$rel" ] && echo "  STALE in WSL  $rel"; done
if [ "${#NEW[@]}" -gt 0 ]; then
  echo
  echo "  absent from WSL (harmless -- these fail loudly if ever needed; --include-new to copy):"
  for rel in "${NEW[@]:-}"; do [ -n "$rel" ] && echo "    $rel"; done
fi
if [ "${#WSL_NEWER[@]}" -gt 0 ]; then
  echo
  echo "  These differ and the WSL copy has the newer timestamp. That is what a WSL-side edit"
  echo "  looks like, and this project treats the WSL copy as authoritative when the two"
  echo "  genuinely diverge. Inspect before overwriting:"
  for rel in "${WSL_NEWER[@]}"; do
    echo "    SKIP  $rel"
    echo "          diff --strip-trailing-cr '$WSL/$rel' '$WIN/$rel'"
  done
  [ "$FORCE" -eq 1 ] && echo "  --force given: these WILL be overwritten."
fi

# A MISSING file fails loudly -- "No such file or directory". A STALE file runs and reports
# success while measuring the wrong thing, which is what cost eight hours. So --apply syncs
# updates, and creating absent files needs --include-new said out loud.
TODO=${#CHANGED[@]}
[ "$INCLUDE_NEW" -eq 1 ] && TODO=$(( TODO + ${#NEW[@]} ))
[ "$FORCE" -eq 1 ] && TODO=$(( TODO + ${#WSL_NEWER[@]} ))

if [ "$TODO" -eq 0 ]; then
  echo
  echo "nothing to do."
  exit 0
fi

if [ "$APPLY" -eq 0 ]; then
  echo
  echo "dry run. re-run with --apply to copy $TODO file(s)."
  echo "  --apply syncs the stale ones; add --include-new for the absent ones."
  exit 0
fi

# ---------------------------------------------------------------------------
# Copy, stripping CR. Then verify -- a copy that silently did not land is the whole
# reason this script exists.
# ---------------------------------------------------------------------------
echo
COPIED=0; FAILED=0
copy_one() {
  local rel="$1" src="$WIN/$1" dst="$WSL/$1"
  mkdir -p "$(dirname "$dst")"
  if ! tr -d '\r' < "$src" > "$dst"; then
    echo "  FAIL   $rel  (write error)"; FAILED=$((FAILED+1)); return
  fi
  if [ "$(hash_nocr "$src")" != "$(hash_nocr "$dst")" ]; then
    echo "  FAIL   $rel  (content differs after copy)"; FAILED=$((FAILED+1)); return
  fi
  if grep -q $'\r' "$dst"; then
    echo "  FAIL   $rel  (carriage return survived)"; FAILED=$((FAILED+1)); return
  fi
  echo "  synced $rel"; COPIED=$((COPIED+1))
}

for rel in "${CHANGED[@]:-}"; do [ -n "$rel" ] && copy_one "$rel"; done
if [ "$INCLUDE_NEW" -eq 1 ]; then
  for rel in "${NEW[@]:-}"; do [ -n "$rel" ] && copy_one "$rel"; done
fi
if [ "$FORCE" -eq 1 ]; then
  for rel in "${WSL_NEWER[@]:-}"; do [ -n "$rel" ] && copy_one "$rel"; done
fi

# ---------------------------------------------------------------------------
# A synced file that does not parse is the same class of problem as a stale one:
# it will fail late, or worse, run partially. Check now.
# ---------------------------------------------------------------------------
echo
echo "syntax check on what was just synced:"
BAD=0
check_one() {
  local rel="$1" dst="$WSL/$1"
  case "$rel" in
    *.sh) bash -n "$dst" 2>/dev/null || { echo "  FAIL  $rel  (bash -n)"; BAD=$((BAD+1)); return; } ;;
    *.py) ( cd "$WSL" && python -c "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True)" "$rel" ) >/dev/null 2>&1 \
            || { echo "  FAIL  $rel  (py_compile)"; BAD=$((BAD+1)); return; } ;;
    *) return ;;
  esac
}
for rel in "${CHANGED[@]:-}"; do [ -n "$rel" ] && check_one "$rel"; done
[ "$INCLUDE_NEW" -eq 1 ] && for rel in "${NEW[@]:-}"; do [ -n "$rel" ] && check_one "$rel"; done
[ "$BAD" -eq 0 ] && echo "  all clean"

echo
echo "copied $COPIED, failed $FAILED, syntax problems $BAD"
[ "$FAILED" -eq 0 ] && [ "$BAD" -eq 0 ] || exit 1
