param(
    [Parameter(Mandatory=$true)][string]$InputJsonl,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [int]$Limit = 0
)
$ErrorActionPreference = "Stop"

$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Script = Join-Path $ProjectRoot "evaluate_execution_nbest.py"

$LocalDir = "C:\tmp\MIRAGE\exec_eval_nbest"
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$LocalInput = Join-Path $LocalDir "input.jsonl"
$LocalOutput = Join-Path $LocalDir "output.jsonl"
$LocalSummary = Join-Path $LocalDir "summary.json"

Copy-Item -LiteralPath $InputJsonl -Destination $LocalInput -Force

$extraArgs = "--input-jsonl `"$LocalInput`" --output-jsonl `"$LocalOutput`" --summary-json `"$LocalSummary`""
if ($Limit -gt 0) {
    $extraArgs = "$extraArgs --limit $Limit"
}
$env:MIRAGE_STEP_FEATURE_ARGS = $extraArgs
& $FllumaCli $Script
if ($LASTEXITCODE -ne 0) {
    throw "N-best execution evaluation failed"
}
Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Copy-Item -LiteralPath $LocalOutput -Destination (Join-Path $OutputDir "execution_nbest_rows.jsonl") -Force
Copy-Item -LiteralPath $LocalSummary -Destination (Join-Path $OutputDir "execution_nbest_summary.json") -Force

Get-Content (Join-Path $OutputDir "execution_nbest_summary.json")
