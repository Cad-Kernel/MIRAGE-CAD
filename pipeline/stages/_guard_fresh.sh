#!/bin/bash
# Refuse to run a stale script. Source this at the top of any long runner:
#
#     source training_25k/_guard_fresh.sh training_25k/scripts/gen_predicted_ir.py train_program_lora.py
#
# WHY IT IS A GUARD AND NOT A CHECKLIST. ~/workspace/MIRAGE is not a git checkout, so a
# Windows-side edit does not reach it and `git pull` cannot fetch it. Three steps in one round
# ran against stale scripts, and one cost 7 h 52 m: the B1 one-epoch arm trained, then skipped
# inference, because the WSL runner predated a configurable arm label and the hardcoded output
# path already held the three-epoch predictions at exactly the expected row count. The
# completeness check passed. Nothing in the log looked wrong.
#
# A tool you have to remember to run cannot prevent that, because forgetting is the failure.
# This runs whether or not anyone remembers, and it runs before the GPU is touched.
#
# IT CHECKS ITS CALLER AND EVERY PATH IT IS GIVEN. The runner being current is not sufficient:
# a stale generation or training script is exactly as expensive, and harder to notice, because
# the runner's own log looks correct. Pass every script the runner invokes.
#
# CR IS IGNORED. The Windows checkout may hold CRLF; that is not a difference in meaning, and
# treating it as one would make the guard fire constantly and be disabled within a day.
#
# AN UNVERIFIABLE TREE IS A FAILURE, NOT A PASS. If the Windows checkout is not mounted there
# is no source of truth to compare against, which is precisely the state that cost the eight
# hours. Set ALLOW_UNVERIFIED=1 to proceed anyway; it prints what it could not check.

_GUARD_WIN=${GUARD_WIN:-/mnt/c/Workspace/Project/Paper/MIRAGE-V2/src}
_GUARD_WSL=${GUARD_WSL:-$HOME/workspace/MIRAGE/src}

_guard_hash() { tr -d '\r' < "$1" 2>/dev/null | sha256sum | cut -d' ' -f1; }

_guard_run() {
  local caller="${BASH_SOURCE[2]:-${BASH_SOURCE[1]:-$0}}"
  local -a targets=("$caller" "$@")
  local stale=0 missing=0 checked=0

  if [ ! -d "$_GUARD_WIN" ]; then
    echo "GUARD: the Windows checkout is not mounted at $_GUARD_WIN, so freshness cannot be" >&2
    echo "       verified. That is the exact state in which a stale runner burned 7 h 52 m." >&2
    if [ "${ALLOW_UNVERIFIED:-0}" = "1" ]; then
      echo "       ALLOW_UNVERIFIED=1 -- proceeding unverified." >&2
      return 0
    fi
    echo "       Set ALLOW_UNVERIFIED=1 to override." >&2
    exit 1
  fi

  for t in "${targets[@]}"; do
    [ -n "$t" ] || continue
    # Resolve to a path relative to the WSL source root, whatever form the caller used.
    local abs rel
    abs=$(cd "$(dirname "$t")" 2>/dev/null && pwd)/$(basename "$t") || abs="$t"
    rel=${abs#"$_GUARD_WSL"/}
    if [ "$rel" = "$abs" ]; then
      echo "GUARD: skip  $t  (outside $_GUARD_WSL)" >&2
      continue
    fi
    local win="$_GUARD_WIN/$rel"
    if [ ! -f "$win" ]; then
      echo "GUARD: NO SOURCE  $rel" >&2
      echo "         exists here but not in the Windows checkout. Either it was deleted there," >&2
      echo "         or this file only ever existed in WSL and is not under version control." >&2
      missing=$((missing + 1))
      continue
    fi
    if [ "$(_guard_hash "$abs")" != "$(_guard_hash "$win")" ]; then
      echo "GUARD: STALE  $rel" >&2
      stale=$((stale + 1))
    fi
    checked=$((checked + 1))
  done

  if [ "$stale" -gt 0 ] || [ "$missing" -gt 0 ]; then
    echo >&2
    echo "Refusing to start: $stale stale, $missing without a source, of $checked checked." >&2
    echo "A stale script does not fail loudly. It runs, reports success, and measures the" >&2
    echo "wrong thing -- which is why this exits instead of warning." >&2
    echo >&2
    echo "  bash $_GUARD_WIN/sync_to_wsl.sh                      # see what differs" >&2
    echo "  bash $_GUARD_WIN/sync_to_wsl.sh --apply --include-new # then re-run this" >&2
    echo >&2
    echo "If the WSL copy is the one you meant to keep, copy it to Windows and commit it" >&2
    echo "first -- do not sync over it." >&2
    exit 1
  fi

  echo "guard: $checked script(s) match the Windows checkout"
}

_guard_run "$@"
