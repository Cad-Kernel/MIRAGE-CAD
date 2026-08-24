"""Shared path roots for the analysis scripts, resolved for whichever side they run on.

Every analysis in this directory reads from two places that live in different
filesystems:

  OUTPUTS  model outputs -- WSL, at ~/workspace/MIRAGE/src/outputs
  SCRATCH  execution results -- the Windows repo, at <repo>/scratch (committed to git)

Hardcoding one side's spelling meant `python src/scratch/x.py` worked from Windows and
died on the first path in WSL, which cost two round-trips. Each root is now discovered
from a short candidate list, so the same command works from either side.

    from _roots import OUTPUTS, SCRATCH
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()


def _first_dir(*candidates: Path) -> Path:
    for c in candidates:
        try:
            if c.is_dir():
                return c
        except OSError:          # UNC share asleep, unreadable mount
            continue
    return candidates[0]         # let the caller fail with a real path in the message


# <repo>/src/scratch/_roots.py -> <repo>
_REPO = _HERE.parents[2]

SCRATCH = _first_dir(
    _REPO / "scratch",                                            # running from the repo
    Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch"),        # Windows, elsewhere
    Path("/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch"),     # WSL, via the C: mount
)

OUTPUTS = _first_dir(
    Path.home() / "workspace/MIRAGE/src/outputs",                 # WSL, native
    Path(r"\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs"),  # Windows
    _REPO / "src" / "outputs",                                    # if ever colocated
)


def require(root: Path, what: str) -> Path:
    if not root.is_dir():
        sys.exit(f"cannot find {what} at {root}\n"
                 f"  (running on {sys.platform}; if this is WSL, the Windows repo must "
                 f"be mounted at /mnt/c, and if this is Windows the WSL share must be awake)")
    return root
