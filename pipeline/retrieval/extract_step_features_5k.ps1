param(
    [int]$Limit = 0
)
$ErrorActionPreference = "Stop"

$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Script = Join-Path $ProjectRoot "extract_step_features.py"
$DataDir = Join-Path $ProjectRoot "data\smoke5k"
$FeatureDir = Join-Path $DataDir "step_features"
$LocalDataDir = "C:\tmp\MIRAGE\smoke5k"
$LocalFeatureDir = Join-Path $LocalDataDir "step_features"

New-Item -ItemType Directory -Force -Path $LocalDataDir | Out-Null
New-Item -ItemType Directory -Force -Path $LocalFeatureDir | Out-Null

if (Test-Path -LiteralPath $FeatureDir) {
    Copy-Item -Path (Join-Path $FeatureDir "*") -Destination $LocalFeatureDir -Recurse -Force -ErrorAction SilentlyContinue
}

$splits = @("train", "val", "test")
foreach ($split in $splits) {
    $InputJsonl = Join-Path $DataDir "$split.jsonl"
    $LocalInputJsonl = Join-Path $LocalDataDir "$split.jsonl"
    $LocalIndexJsonl = Join-Path $LocalDataDir "step_features_$split.jsonl"
    $LocalSummaryJson = Join-Path $LocalDataDir "step_features_$split.summary.json"
    if (!(Test-Path -LiteralPath $InputJsonl)) {
        throw "Missing $InputJsonl. Run this first in WSL: cd ~/workspace/MIRAGE/src && bash scripts/prepare_5k.sh"
    }
    Copy-Item -LiteralPath $InputJsonl -Destination $LocalInputJsonl -Force
    $extraArgs = "--input-jsonl `"$LocalInputJsonl`" --output-dir `"$LocalFeatureDir`" --index-jsonl `"$LocalIndexJsonl`" --summary-json `"$LocalSummaryJson`" --resume"
    if ($Limit -gt 0) {
        $extraArgs = "$extraArgs --limit $Limit"
    }
    $env:MIRAGE_STEP_FEATURE_ARGS = $extraArgs
    & $FllumaCli $Script
    if ($LASTEXITCODE -ne 0) {
        throw "STEP feature extraction failed for split: $split"
    }
    Copy-Item -LiteralPath $LocalIndexJsonl -Destination (Join-Path $DataDir "step_features_$split.jsonl") -Force
    Copy-Item -LiteralPath $LocalSummaryJson -Destination (Join-Path $DataDir "step_features_$split.summary.json") -Force
}

New-Item -ItemType Directory -Force -Path $FeatureDir | Out-Null
Copy-Item -Path (Join-Path $LocalFeatureDir "*") -Destination $FeatureDir -Recurse -Force
Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS -ErrorAction SilentlyContinue
