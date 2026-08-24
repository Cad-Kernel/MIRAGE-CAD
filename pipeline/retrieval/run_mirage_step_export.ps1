# Re-export MIRAGE's predicted STEP for the external Fusion 360 set, keeping the files.
#
# Modelled on evaluate_geometry_nbest.ps1 deliberately: that wrapper already survived this exact
# arm, including the candidate that raises an access violation inside the kernel, so its shape
# (append, resume, bounded retry, forward-progress check) is proven on this input rather than
# guessed. Two things are added and one is removed.
#
# ADDED, A TIMEOUT. The published wrapper retries on a crash but waits forever on a hang. A
# generated program that spins does not crash, so no retry ever fires and the run simply stops
# making progress with no signal. Start-Process plus WaitForExit(ms) bounds each attempt; because
# rows are appended and fsynced per sample, a killed attempt resumes exactly where it stopped.
#
# ADDED, PER-SAMPLE GATE VERIFICATION, done inside the Python script: every re-exported part is
# checked against its own published gate outcome, not against the arm totals. Landing 232 exports
# that are a different 232 would be a silent unpairing of the comparison.
#
# REMOVED, THE STAGING COPY-BACK. The published wrapper stages output through C:\tmp because its
# results are one small jsonl. Here the output is hundreds of STEP files, and they are written
# straight to their final home on the local C: volume -- which the WSL scorer reads as /mnt/c.
# What still gets copied into C:\tmp is only what is read over the UNC share: the two Python
# files and the input jsonl, because reading those over \\wsl.localhost fails intermittently on
# this machine and, when it fails, FllumaCLI exits non-zero with nothing to read.
#
# ONE ARM PER INVOCATION, never two at once: FllumaCLI stages through process-wide kernel state.

param(
    [Parameter(Mandatory=$true)][ValidateSet("point_genplan","point_nnir")][string]$Arm,
    [int]$Limit = 0,
    [int]$MaxAttempts = 12,
    [int]$TimeoutSec = 3600
)
$ErrorActionPreference = "Stop"

$FllumaCli   = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$WslSrc      = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$WinSrc      = "C:\Workspace\Project\Paper\MIRAGE-V2\src"
$ScratchRoot = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch"

$InputJsonl    = Join-Path $WslSrc "outputs\external_geometry\geom_input_$Arm.jsonl"
$PublishedRows = Join-Path $ScratchRoot "geom_ext_$Arm\geometry_nbest_rows.jsonl"
$StepRoot      = Join-Path $ScratchRoot "mirage_runs"
$OutputJsonl   = Join-Path $StepRoot "$Arm\export_rows.jsonl"

foreach ($p in @($FllumaCli, $InputJsonl, $PublishedRows)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "missing required input: $p" }
}

# Local staging for the UNC-hosted files only.
$LocalDir = Join-Path "C:\tmp\MIRAGE\mirage_step_export" $Arm
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $OutputJsonl) | Out-Null

$LocalInput  = Join-Path $LocalDir "input.jsonl"
$LocalScript = Join-Path $LocalDir "mirage_step_export.py"
$LocalOut    = Join-Path $LocalDir "cli.out.log"
$LocalErr    = Join-Path $LocalDir "cli.err.log"

Copy-Item -LiteralPath $InputJsonl -Destination $LocalInput -Force
Copy-Item -LiteralPath (Join-Path $WinSrc "scratch\mirage_step_export.py") -Destination $LocalScript -Force
# The gate implementation this script calls. Same directory, so `import evaluate_geometry_nbest`
# resolves to the copy that ran, not to whatever an older sys.path might reach.
Copy-Item -LiteralPath (Join-Path $WslSrc "evaluate_geometry_nbest.py") `
          -Destination (Join-Path $LocalDir "evaluate_geometry_nbest.py") -Force

$argLine = "--input-jsonl `"$LocalInput`" --published-rows `"$PublishedRows`" " +
           "--step-root `"$StepRoot`" --output-jsonl `"$OutputJsonl`" --arm $Arm"
if ($Limit -gt 0) { $argLine = "$argLine --limit $Limit" }
$env:MIRAGE_STEP_FEATURE_ARGS = $argLine

$expected = (Get-Content $LocalInput | Measure-Object -Line).Lines
if ($Limit -gt 0 -and $Limit -lt $expected) { $expected = $Limit }
Write-Host "=== $Arm : $expected rows, STEP -> $StepRoot\$Arm ==="

$cliExit = 0
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $before = 0
    if (Test-Path -LiteralPath $OutputJsonl) {
        $before = (Get-Content $OutputJsonl | Measure-Object -Line).Lines
    }
    # The inflight file names candidates that were STARTED. It is the second progress signal and
    # the one that matters on resume: an attempt that begins at the crashing candidate dies having
    # written no result row, so rows alone read as "no progress" and would stop the loop one
    # attempt too early. A grown inflight list means a new candidate was attempted and killed the
    # process, which the next attempt converts into a recorded crash -- so that IS progress.
    $inflightPath = [System.IO.Path]::ChangeExtension($OutputJsonl, ".inflight")
    $inflightBefore = 0
    if (Test-Path -LiteralPath $inflightPath) {
        $inflightBefore = (Get-Content $inflightPath | Measure-Object -Line).Lines
    }

    $proc = Start-Process -FilePath $FllumaCli -ArgumentList "`"$LocalScript`"" -PassThru `
                          -NoNewWindow -RedirectStandardOutput $LocalOut -RedirectStandardError $LocalErr
    # Touch .Handle before the process exits. Without this, -PassThru hands back an object whose
    # ExitCode reads as EMPTY once it has gone, which is exactly what happened on the first run:
    # the crash was never classified, every comparison against an exit code was false, and the
    # loop fell through to its final break with 235 of 400 rows written.
    $null = $proc.Handle
    if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
        Write-Host "attempt $attempt/$MaxAttempts : no exit within $TimeoutSec s, killing it."
        try { $proc.Kill() } catch {}
        $proc.WaitForExit()
        $cliExit = "killed-on-timeout"
    } else {
        $cliExit = $proc.ExitCode
        if ($null -eq $cliExit) { $cliExit = "unavailable" }
    }

    $after = 0
    if (Test-Path -LiteralPath $OutputJsonl) {
        $after = (Get-Content $OutputJsonl | Measure-Object -Line).Lines
    }
    Write-Host "attempt $attempt : exit $cliExit, rows $before -> $after of $expected"

    # The decision is made on PROGRESS, not on the exit code. The exit code is a diagnostic that
    # this environment has already failed to supply once, and the semantics that matter do not
    # need it: a complete run stops, an advancing run retries, and a run that advanced nothing is
    # not a crashing candidate and must not be retried forever. Because the Python side records a
    # crashed sample_id and refuses to retry it, every attempt advances past at least one crash,
    # so this loop terminates.
    $inflightAfter = 0
    if (Test-Path -LiteralPath $inflightPath) {
        $inflightAfter = (Get-Content $inflightPath | Measure-Object -Line).Lines
    }

    if ($after -ge $expected) { break }
    if ($after -gt $before) {
        Write-Host "  advanced $before -> $after rows but short of $expected; resuming."
        continue
    }
    if ($inflightAfter -gt $inflightBefore) {
        Write-Host "  no new rows, but $($inflightAfter - $inflightBefore) candidate(s) were"
        Write-Host "  started and killed the process. The next attempt records them and moves on."
        continue
    }
    Write-Host "  ** no rows written and no candidate started: this is not a crashing candidate."
    Write-Host "     Stopping rather than looping. **"
    break
}
Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS -ErrorAction SilentlyContinue

$rowsNow = 0
if (Test-Path -LiteralPath $OutputJsonl) {
    $rowsNow = (Get-Content $OutputJsonl | Measure-Object -Line).Lines
}
Write-Host ""
if ($rowsNow -lt $expected) {
    Write-Host "=== INCOMPLETE: $rowsNow of $expected rows, last exit $cliExit ==="
    Write-Host "  --- last 40 log lines that are not OCCT transfer noise ---"
    Get-Content $LocalOut, $LocalErr -ErrorAction SilentlyContinue |
        Where-Object { $_ -notmatch 'Transfer|WorkSession|Step File Name|^\*+$|^\s*$' } |
        Select-Object -Last 40 | ForEach-Object { Write-Host "    $_" }
    throw "STEP export incomplete for $Arm : $rowsNow of $expected"
}

$report = [System.IO.Path]::ChangeExtension($OutputJsonl, ".report.txt")
if (Test-Path -LiteralPath $report) {
    Write-Host "--- report tail ---"
    Get-Content $report | Select-Object -Last 14 | ForEach-Object { Write-Host "  $_" }
}
Write-Host "$rowsNow rows -> $OutputJsonl"
