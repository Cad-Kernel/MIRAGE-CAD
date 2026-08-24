param(
    [Parameter(Mandatory=$true)][string]$InputJsonl,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$CodeField = "prediction",
    [int]$Limit = 0,
    # See the geometry wrapper: a candidate can crash the kernel, the scorer appends and
    # records the offender, so each attempt advances past at least one crash and retrying
    # terminates. Bounded anyway, and abandoned early if an attempt advances nothing.
    [int]$MaxAttempts = 12
)
$ErrorActionPreference = "Stop"

$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"

# A staging directory per ARM, not one shared path and not one per process. Shared meant two
# concurrent invocations overwrote each other's input, output and summary. Per process would
# defeat the resume: evaluate_execution.py appends results and keeps an in-flight marker so
# that a candidate crashing the kernel costs one row instead of the whole arm, and that state
# has to survive into the next attempt. Keyed on the output directory name it does, while two
# different arms still cannot collide.
$RunId = [System.IO.Path]::GetFileNameWithoutExtension($OutputDir)
$LocalDir = Join-Path "C:\tmp\MIRAGE\exec_eval" $RunId
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$LocalInput   = Join-Path $LocalDir "input.jsonl"
$LocalOutput  = Join-Path $LocalDir "output.jsonl"
$LocalSummary = Join-Path $LocalDir "summary.json"
$LocalLog     = Join-Path $LocalDir "cli.log"
$LocalScript  = Join-Path $LocalDir "evaluate_execution.py"

# Copy the script across too, rather than having FllumaCLI read it over the UNC share.
# Python processes reading \\wsl.localhost fail intermittently on this machine, and when the
# failure lands on the script itself the CLI simply exits non-zero with nothing to read.
Copy-Item -LiteralPath $InputJsonl -Destination $LocalInput -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "evaluate_execution.py") -Destination $LocalScript -Force

$extraArgs = "--input-jsonl `"$LocalInput`" --output-jsonl `"$LocalOutput`" --summary-json `"$LocalSummary`" --code-field $CodeField"
if ($Limit -gt 0) {
    $extraArgs = "$extraArgs --limit $Limit"
}
$env:MIRAGE_STEP_FEATURE_ARGS = $extraArgs

# Tee the CLI's output. The old version threw a bare "Execution evaluation failed", which
# discarded the traceback that says what actually went wrong -- and OCCT writes so much to
# stdout that the real message scrolls away even on success.
$expected = (Get-Content $LocalInput | Measure-Object -Line).Lines
$cliExit = 0
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $before = 0
    if (Test-Path -LiteralPath $LocalOutput) {
        $before = (Get-Content $LocalOutput | Measure-Object -Line).Lines
    }
    & $FllumaCli $LocalScript 2>&1 | Tee-Object -FilePath $LocalLog
    $cliExit = $LASTEXITCODE
    $after = 0
    if (Test-Path -LiteralPath $LocalOutput) {
        $after = (Get-Content $LocalOutput | Measure-Object -Line).Lines
    }
    if ($cliExit -eq 0 -and (Test-Path -LiteralPath $LocalSummary)) { break }
    if ($cliExit -eq -1073741819) {
        Write-Host ""
        Write-Host "attempt $attempt/$MaxAttempts : a candidate crashed the kernel (0xC0000005)."
        Write-Host "  scored $before -> $after of $expected; recorded as a crash and skipped next time."
        if ($after -le $before) {
            Write-Host "  ** no forward progress, so this is not simply a crashing candidate. Stopping. **"
            break
        }
        continue
    }
    break
}
Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS -ErrorAction SilentlyContinue

if ($cliExit -ne 0 -or -not (Test-Path -LiteralPath $LocalSummary)) {
    Write-Host ""
    Write-Host "=== execution evaluation FAILED (exit $cliExit) ==="
    Write-Host "full log: $LocalLog"
    Write-Host "--- last 40 lines that are not OCCT transfer noise ---"
    Get-Content $LocalLog |
        Where-Object { $_ -notmatch 'Transfer|WorkSession|Step File Name|^\*+$|^\s*$' } |
        Select-Object -Last 40 |
        ForEach-Object { Write-Host "  $_" }
    throw "Execution evaluation failed; see $LocalLog"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Copy-Item -LiteralPath $LocalOutput -Destination (Join-Path $OutputDir "execution_rows.jsonl") -Force
Copy-Item -LiteralPath $LocalSummary -Destination (Join-Path $OutputDir "execution_summary.json") -Force
Copy-Item -LiteralPath $LocalLog -Destination (Join-Path $OutputDir "cli.log") -Force

Get-Content (Join-Path $OutputDir "execution_summary.json")
