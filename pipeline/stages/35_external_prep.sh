#!/bin/bash
# C-EXT1-min, step 1: turn Fusion 360 Gallery into something the pipeline can query.
#
# This wrapper does the part that does not need a CAD kernel -- resolve the official split
# and check the files are there -- and then prints the Windows commands for the rest.
#
# WHY THE REST IS ON WINDOWS. Reference clouds now come from the .step through Flluma's own
# sampler (occt_file_to_pointcloud, added to BindCSG.cpp), so that reference and generated
# clouds go through one exporter with one set of options. Only FllumaCLI can import flluma,
# and FllumaCLI runs on Windows -- so sampling happens there and the manifest carries both
# a Windows and a /mnt/c path for every file.
#
# The equivalence that justifies this is measured, not assumed: probe_step_pointcloud.py
# sampled a corpus model.step and compared it with the point_cloud.npz released for the same
# sample, which was sampled from the program instead. Identical bounding boxes, median
# nearest-neighbour 0.78 and 0.80 against an 89.55 diagonal -- sampling noise at 2,048 points.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

ROOT="${EXT_ROOT:-/mnt/c/Workspace/Project/Dataset/Fusion360Gallery/r1.0.1}"
OUT=data/external/fusion360
N="${EXT_N:-400}"

[ -d "$ROOT" ] || { echo "FATAL: $ROOT not found. Extract r1.0.1.zip there." >&2; exit 1; }
mkdir -p "$OUT"

python training_25k/scripts/external_prep.py \
  --root "$ROOT" --output-dir "$OUT" --limit "$N" --mode inventory

cat <<'EOF'

=== counts only; nothing was written ===

The frame is the published test split of train_test.json. Its 8,625 names match exactly the
8,625 three-field stems on disk; the other 19,333 files are per-extrude intermediates, and
scoring one of those would treat a partial solid as a target.

Next, in Windows PowerShell. First the same phase again but with geometry, which adds the
unit comparison against the corpus on 24 models:

  $env:MIRAGE_EXTERNAL_PREP_ARGS = '--root "C:\Workspace\Project\Dataset\Fusion360Gallery\r1.0.1" --output-dir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\ext_inventory" --mode inventory'
  & "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe" "C:\Workspace\Project\Paper\MIRAGE-V2\src\training_25k\scripts\external_prep.py"

If the corpus/external bbox ratio is near 1, build 400 of them:

  $env:MIRAGE_EXTERNAL_PREP_ARGS = '--root "C:\Workspace\Project\Dataset\Fusion360Gallery\r1.0.1" --output-dir "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360" --mode build --limit 400'
  & "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe" "C:\Workspace\Project\Paper\MIRAGE-V2\src\training_25k\scripts\external_prep.py"
  Remove-Item Env:\MIRAGE_EXTERNAL_PREP_ARGS

Then STEP features, which also need FllumaCLI:

  $env:MIRAGE_STEP_FEATURE_ARGS = '--input-jsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360\queries.jsonl" --output-dir "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360\step_features" --index-jsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360\step_index.jsonl" --summary-json "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360\step_summary.json" --resume'
  & "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe" "C:\Workspace\Project\Paper\MIRAGE-V2\src\extract_step_features.py"
  Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS

The calibration numbers the build prints belong beside any external geometry figure. The
internal ceiling of 0.244 and floor of 1.963 mm^2 were measured at 1,024 points on FllumaOne
parts and transfer to neither the density nor the part sizes here.
EOF
