# Phase 1b: extract STEP/B-Rep features for the 25K split via FllumaCLI.
# Must run in Windows PowerShell (not WSL -- WSL cannot `import flluma`).
# Run per split: .\02_extract_step_features.ps1 -Split train
#                .\02_extract_step_features.ps1 -Split val
#                .\02_extract_step_features.ps1 -Split test
# Safe to re-run: always passes --resume, so an interrupted run just picks up
# where it left off (see docs/Todo.md's WSL-tmpfs-log-loss lesson -- this
# script stages I/O on local C:\tmp, not WSL /tmp, for the same reason).
param(
    [Parameter(Mandatory=$true)][ValidateSet("train","val","test")][string]$Split,
    [int]$Limit = 0
)
$ErrorActionPreference = "Stop"

$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Script = Join-Path $ProjectRoot "extract_step_features.py"

$LocalDir = "C:\tmp\MIRAGE\25k\step_features_$Split"
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$LocalInputJsonl = Join-Path $LocalDir "input.jsonl"
$LocalFeatureDir = Join-Path $LocalDir "features"
$LocalIndexJsonl = Join-Path $LocalDir "index.jsonl"
$LocalSummaryJson = Join-Path $LocalDir "summary.json"

Copy-Item -LiteralPath (Join-Path $ProjectRoot "data\25k\$Split.jsonl") -Destination $LocalInputJsonl -Force

$extraArgs = "--input-jsonl `"$LocalInputJsonl`" --output-dir `"$LocalFeatureDir`" --index-jsonl `"$LocalIndexJsonl`" --summary-json `"$LocalSummaryJson`" --resume"
if ($Limit -gt 0) {
    $extraArgs = "$extraArgs --limit $Limit"
}
$env:MIRAGE_STEP_FEATURE_ARGS = $extraArgs
& $FllumaCli $Script
$cliExit = $LASTEXITCODE
Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS -ErrorAction SilentlyContinue
if ($cliExit -ne 0) {
    throw "STEP feature extraction failed for split=$Split (exit $cliExit)"
}

# Copy results back to the WSL mirror. IMPORTANT: this is a single FLAT shared
# directory across train/val/test (data/25k/step_features/{sample_id}.json,
# no per-split subfolder) -- this matches prepare_manifest.py's own
# step_feature_path convention exactly (verified against data/smoke5k's
# existing rows, e.g. "step_feature_path": "data/smoke5k/step_features/
# flluma_0090357.json"). Do NOT nest this under a $Split subfolder or every
# row's step_feature_path will fail to resolve.
$RemoteFeatureDir = Join-Path $ProjectRoot "data\25k\step_features"
New-Item -ItemType Directory -Force -Path $RemoteFeatureDir | Out-Null
Copy-Item -Path (Join-Path $LocalFeatureDir "*") -Destination $RemoteFeatureDir -Recurse -Force
Copy-Item -LiteralPath $LocalIndexJsonl -Destination (Join-Path $ProjectRoot "data\25k\step_features_$Split.jsonl") -Force
Copy-Item -LiteralPath $LocalSummaryJson -Destination (Join-Path $ProjectRoot "data\25k\step_features_${Split}_summary.json") -Force

Write-Host "=== Wrote data/25k/step_features/ (flat, shared), data/25k/step_features_$Split.jsonl, data/25k/step_features_${Split}_summary.json (WSL paths) ==="
Get-Content (Join-Path $ProjectRoot "data\25k\step_features_${Split}_summary.json")
