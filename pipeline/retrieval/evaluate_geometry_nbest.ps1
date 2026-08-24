param(
    [Parameter(Mandatory=$true)][string]$InputJsonl,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [int]$Limit = 0,
    # A candidate program can crash the kernel outright (0xC0000005), and more than one in a
    # 400-row arm does. Because the scorer appends results and records the offending
    # sample_id, every attempt is guaranteed to advance past at least one crash, so retrying
    # terminates -- but it is bounded anyway, since an attempt that advances nothing means
    # something other than a crashing candidate is wrong.
    [int]$MaxAttempts = 12
)
$ErrorActionPreference = "Stop"

$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"

# Staging per ARM, not one shared directory. Shared was actively dangerous here: four arms run
# through this in sequence, so the previous arm's output.jsonl sits in place while the next one
# runs, and any path where the CLI exits zero without writing would copy the previous arm's
# results into this arm's output directory. Keyed on the output directory name that cannot
# happen, and the resume state below survives into the next attempt.
$RunId = [System.IO.Path]::GetFileNameWithoutExtension($OutputDir)
$LocalDir = Join-Path "C:\tmp\MIRAGE\geometry_nbest" $RunId
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$LocalInput  = Join-Path $LocalDir "input.jsonl"
$LocalOutput = Join-Path $LocalDir "output.jsonl"
$LocalLog    = Join-Path $LocalDir "cli.log"
$LocalScript = Join-Path $LocalDir "evaluate_geometry_nbest.py"

# Copy the script across rather than having FllumaCLI read it over the UNC share, which fails
# intermittently on this machine and, when it fails on the script, exits non-zero with nothing
# to read.
Copy-Item -LiteralPath $InputJsonl -Destination $LocalInput -Force
Copy-Item -LiteralPath (Join-Path $ProjectRoot "evaluate_geometry_nbest.py") -Destination $LocalScript -Force

$extraArgs = "--input-jsonl `"$LocalInput`" --output-jsonl `"$LocalOutput`""
if ($Limit -gt 0) {
    $extraArgs = "$extraArgs --limit $Limit"
}
$env:MIRAGE_STEP_FEATURE_ARGS = $extraArgs

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

    if ($cliExit -eq 0 -and $after -ge $expected) { break }

    if ($cliExit -eq -1073741819) {
        Write-Host ""
        Write-Host "attempt $attempt/$MaxAttempts : a candidate crashed the kernel (0xC0000005)."
        Write-Host "  scored $before -> $after of $expected; the offending candidate will be"
        Write-Host "  recorded as a crash and skipped on the next attempt."
        if ($after -le $before) {
            Write-Host "  ** no forward progress, so this is not simply a crashing candidate. Stopping. **"
            break
        }
        continue
    }
    break
}
Remove-Item Env:\MIRAGE_STEP_FEATURE_ARGS -ErrorAction SilentlyContinue

$rowsNow = 0
if (Test-Path -LiteralPath $LocalOutput) {
    $rowsNow = (Get-Content $LocalOutput | Measure-Object -Line).Lines
}
if ($rowsNow -lt $expected) {
    Write-Host ""
    Write-Host "=== geometry evaluation INCOMPLETE ($rowsNow of $expected rows, last exit $cliExit) ==="
    Write-Host "  full log: $LocalLog"
    Write-Host "  --- last 40 lines that are not OCCT transfer noise ---"
    Get-Content $LocalLog |
        Where-Object { $_ -notmatch 'Transfer|WorkSession|Step File Name|^\*+$|^\s*$' } |
        Select-Object -Last 40 |
        ForEach-Object { Write-Host "    $_" }
    throw "N-best geometry evaluation incomplete: $rowsNow of $expected; see $LocalLog"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Copy-Item -LiteralPath $LocalOutput -Destination (Join-Path $OutputDir "geometry_nbest_rows.jsonl") -Force
Copy-Item -LiteralPath $LocalLog -Destination (Join-Path $OutputDir "cli.log") -Force

$n = (Get-Content (Join-Path $OutputDir "geometry_nbest_rows.jsonl") | Measure-Object -Line).Lines
Write-Host "wrote $n rows -> $OutputDir"
