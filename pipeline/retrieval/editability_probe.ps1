param(
    [Parameter(Mandatory=$true)][string]$InputJsonl,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$Deltas = "-0.25,-0.1,0.1,0.25",
    [int]$Limit = 0,
    [int]$FingerprintPoints = 512,
    [int]$TimeoutSec = 300,
    [string]$ProgramField = "prediction",
    [string]$Python = "python"
)
$ErrorActionPreference = "Stop"

# NOTE ON STRUCTURE, because it differs from the sibling wrappers.
#
# evaluate_execution_nbest.ps1 and evaluate_geometry_nbest.ps1 run their whole loop
# inside one FllumaCLI invocation. This one cannot: perturbing a declared parameter
# can push OpenCASCADE into a state that ABORTS THE PROCESS rather than raising, so a
# single invocation dies partway through and loses the run. Observed on row 2 of a
# two-row smoke test -- no traceback, no "Execution failed" banner, just a silent exit.
#
# So the loop lives in editability_driver.py (ordinary Windows Python -- it needs only
# json and subprocess) and each ROW gets its own FllumaCLI worker. A crash costs one
# row, is recorded as `hard_crash`, and the run continues.

$FllumaCli   = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Worker      = Join-Path $ProjectRoot "editability_worker.py"
$Driver      = Join-Path $ProjectRoot "editability_driver.py"

foreach ($p in @($FllumaCli, $Worker, $Driver)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "not found: $p  (copy src/ to WSL first)" }
}

$LocalDir = "C:\tmp\MIRAGE\editability"
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
$LocalInput   = Join-Path $LocalDir "input.jsonl"
$LocalOutput  = Join-Path $LocalDir "output.jsonl"
$LocalSummary = Join-Path $LocalDir "summary.json"

Copy-Item -LiteralPath $InputJsonl -Destination $LocalInput -Force
foreach ($f in @($LocalOutput, $LocalSummary)) {
    if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force }
}

# The driver is plain Python, so arguments can be passed normally here -- no
# MIRAGE_STEP_FEATURE_ARGS smuggling. The driver sets that itself for each worker.
# --deltas MUST use the `--opt=value` form. The default value starts with a minus
# sign ("-0.25,..."), and in the separate-argument form argparse treats a leading-dash
# token as an option rather than a value and dies with a usage error. This is exactly
# how the first real overnight run failed, while a smoke test using "0.25" passed --
# so it is a trap that only appears with the default arguments.
$argv = @(
    $Driver,
    "--input-jsonl",  $LocalInput,
    "--output-jsonl", $LocalOutput,
    "--summary-json", $LocalSummary,
    "--flluma-cli",   $FllumaCli,
    "--worker",       $Worker,
    "--deltas=$Deltas",
    "--fingerprint-points", $FingerprintPoints,
    "--program-field", $ProgramField,
    "--timeout",      $TimeoutSec
)
if ($Limit -gt 0) { $argv += @("--limit", $Limit) }

# Native stderr must not become a terminating error here: the driver and the workers
# print progress and OCC chatter to stderr, and with ErrorActionPreference=Stop
# PowerShell 5.1 converts that into a NativeCommandError. That masked the real
# argparse message on the first run.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Python @argv
$code = $LASTEXITCODE
$ErrorActionPreference = $prevEap

$produced = (Test-Path -LiteralPath $LocalOutput) -and (Test-Path -LiteralPath $LocalSummary)
if (-not $produced) {
    throw "editability probe produced no output (driver exit code $code)."
}
if ($code -ne 0) {
    Write-Output "note: driver exited with code $code but produced output; continuing."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Copy-Item -LiteralPath $LocalOutput  -Destination (Join-Path $OutputDir "editability_rows.jsonl") -Force
Copy-Item -LiteralPath $LocalSummary -Destination (Join-Path $OutputDir "editability_summary.json") -Force

Write-Output "--- $OutputDir\editability_summary.json ---"
Get-Content (Join-Path $OutputDir "editability_summary.json")
