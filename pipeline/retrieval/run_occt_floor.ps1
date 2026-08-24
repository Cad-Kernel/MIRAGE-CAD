# Sample Fusion360 STEP models twice per point count through the frozen OCCT sampler.
#
# WHY THIS EXISTS. The CD sampling floor measured so far was calibrated on trimesh surface
# sampling, which is what CAD-Recode's released demo uses. The external MIRAGE pathway samples
# through OCCT surface_uv instead, and two different samplers have no reason to share a floor
# constant. Until this is measured, the observation that CAD-Recode's published Fusion360 median
# sits near the 8192-point floor belongs to THEIR implementation and cannot be restated as a
# property of our external evaluation.
#
# NO CHECKPOINT, NO MODEL, NO GPU. This only samples geometry that already exists on disk.
#
#   & .\src\scripts\run_occt_floor.ps1                    # 20 stratified shapes, 4 point counts
#   & .\src\scripts\run_occt_floor.ps1 -Shapes 40
#
# The shapes are chosen stratified by bbox_diag so the set spans small and large parts rather
# than whatever happens to sit at the top of the file. Selection is deterministic.
[CmdletBinding()]
param(
    [int]$Shapes = 20,
    [string]$PointCounts = "1024,2048,4096,8192",
    [string]$Seeds = "20260810,20260811",
    [string]$OutDir = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\occt_floor",
    [int]$MaxAttempts = 3
)

$ErrorActionPreference = "Stop"
$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectSrc = "C:\Workspace\Project\Paper\MIRAGE-V2\src"
$Queries = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360\queries.jsonl"

if (-not (Test-Path -LiteralPath $FllumaCli)) { throw "FllumaCLI not found: $FllumaCli" }
if (-not (Test-Path -LiteralPath $Queries))   { throw "queries.jsonl not found: $Queries" }

# FllumaCLI reads its script and inputs from local disk; the UNC share fails for it, which is
# why evaluate_geometry_nbest.ps1 stages everything the same way.
$RunId = "occt_floor"
$LocalDir = Join-Path "C:\tmp\MIRAGE" $RunId
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutDir  | Out-Null

$LocalScript = Join-Path $LocalDir "occt_floor_sample.py"
$LocalInput  = Join-Path $LocalDir "shapes.jsonl"
$LocalLog    = Join-Path $LocalDir "cli.log"
Copy-Item -LiteralPath (Join-Path $ProjectSrc "occt_floor_sample.py") -Destination $LocalScript -Force

# ---------------------------------------------------------------------------
# Stratified selection by bbox_diag. Deterministic: sort by diagonal, take evenly spaced
# indices. Taking the first N would sample one region of the size distribution, and the floor
# is expected to vary with size, which is the thing being measured.
# ---------------------------------------------------------------------------
$rows = Get-Content -LiteralPath $Queries | Where-Object { $_.Trim() } | ForEach-Object {
    $o = $_ | ConvertFrom-Json
    [pscustomobject]@{
        sample_id = $o.sample_id
        step_path = $o.step_path
        bbox_diag = [double]$o.bbox_diag
    }
} | Where-Object { $_.step_path -and (Test-Path -LiteralPath $_.step_path) }

if ($rows.Count -eq 0) { throw "no readable STEP files among the queries rows" }

# One Fusion360 model reports a bbox diagonal of 4,004,345 mm - four kilometres - where the next
# largest is 5,264 and the median is 95.65. A 760x jump from the second largest is a defect in that
# model, not a large part, and it matters twice: it would anchor the top of the strata, and
# linear_deflection is ABSOLUTE, so tessellating a four-kilometre solid at 0.05 mm is pathological.
# Excluded by a gap rule rather than a threshold picked to fit: p99 is 2,598, the second-largest is
# 2x p99, and the outlier is 1,541x p99, so this removes exactly one shape.
$allDiag = ($rows | Sort-Object bbox_diag | ForEach-Object { $_.bbox_diag })
$p99 = $allDiag[[int][Math]::Floor(0.99 * ($allDiag.Count - 1))]
$cut = 100.0 * $p99
$excluded = $rows | Where-Object { $_.bbox_diag -gt $cut }
if ($excluded) {
    Write-Host "=== excluded $(@($excluded).Count) shape(s) with an implausible bbox diagonal ==="
    foreach ($e in $excluded) {
        Write-Host ("    {0}  diag {1:N2} mm  = {2:N0}x the 99th percentile ({3:N2})" -f `
            $e.sample_id, $e.bbox_diag, ($e.bbox_diag / $p99), $p99)
    }
    Write-Host "    A defect in the source model, not a size. Recorded, not silently dropped."
}
$rows = $rows | Where-Object { $_.bbox_diag -le $cut }

# Strata on a LOG axis: the surviving range is 1.59 to 5,264 mm, a factor of 3,300, and even
# strata on a linear axis would put almost every shape in the first bin.
$sorted = $rows | Sort-Object bbox_diag
$take = [Math]::Min($Shapes, $sorted.Count)
$logLo = [Math]::Log($sorted[0].bbox_diag)
$logHi = [Math]::Log($sorted[-1].bbox_diag)
$picked = @()
for ($i = 0; $i -lt $take; $i++) {
    $target = $logLo + ($logHi - $logLo) * $i / [Math]::Max($take - 1, 1)
    $best = $sorted | Sort-Object { [Math]::Abs([Math]::Log($_.bbox_diag) - $target) } |
        Where-Object { $picked -notcontains $_ } | Select-Object -First 1
    if ($best) { $picked += $best }
}
# WriteAllLines with UTF8Encoding($false), not Set-Content -Encoding utf8: in PowerShell 5.1 the
# latter emits a BOM, and json.loads rejects a BOM outright. The sampler now reads utf-8-sig as
# well, but a file other tools may read should not carry one in the first place.
$jsonLines = $picked | ForEach-Object {
    [pscustomobject]@{ sample_id = $_.sample_id; step_path = $_.step_path } | ConvertTo-Json -Compress
}
[System.IO.File]::WriteAllLines($LocalInput, [string[]]$jsonLines, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "=== selected $($picked.Count) of $($sorted.Count) shapes, stratified on log(bbox_diag) ==="
Write-Host ("    diagonal range {0:N2} .. {1:N2}" -f $picked[0].bbox_diag, $picked[-1].bbox_diag)
Write-Host "=== tessellation left at library defaults (linear 0.05, angular 0.3) on purpose ==="
Write-Host "    those are the values external_prep.py used for all 400 clouds; passing them"
Write-Host "    explicitly would look like a choice, and nothing was chosen."

$env:MIRAGE_STEP_FEATURE_ARGS = "--input-jsonl `"$LocalInput`" --out-dir `"$OutDir`" --point-counts $PointCounts --seeds $Seeds"

$expected = $picked.Count * ($PointCounts.Split(",").Count) * ($Seeds.Split(",").Count)
$cliExit = 0
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    $logPath = Join-Path $OutDir "sampling_log.jsonl"
    $before = 0
    if (Test-Path -LiteralPath $logPath) {
        $before = (Get-Content -LiteralPath $logPath | Where-Object { $_ -match '"status": ?"ok"' }).Count
    }

    # NO 2>&1 HERE. In Windows PowerShell 5.1 redirecting a native executable's stderr wraps
    # every line in an ErrorRecord, and with ErrorActionPreference Stop the first line terminates
    # the script -- which is exactly what happened on the first run, reported as "FllumaCLI.exe :"
    # with an empty message. FllumaCLI writes OCCT transfer chatter to stderr constantly, so this
    # was certain to fire. Preference is scoped to Continue for the call as a second guard.
    $savedEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $FllumaCli $LocalScript | Tee-Object -FilePath $LocalLog
    $cliExit = $LASTEXITCODE
    $ErrorActionPreference = $savedEAP

    $after = 0
    if (Test-Path -LiteralPath $logPath) {
        $after = (Get-Content -LiteralPath $logPath | Where-Object { $_ -match '"status": ?"ok"' }).Count
    }

    # Completion is judged by the CLOUD COUNT, not the exit code. FllumaCLI can return non-zero
    # after a fully successful run -- it reports a SystemExit as an exception - and this project
    # has already been bitten once by trusting a status over a count, when a truncated output file
    # passed a non-empty test. The count is the ground truth; the exit code is reported alongside.
    if ($after -ge $expected) {
        if ($cliExit -ne 0) {
            Write-Host "  note: exit $cliExit but all $expected clouds are present; trusting the count."
        }
        break
    }
    Write-Host ""
    Write-Host "attempt $attempt/$MaxAttempts : exit $cliExit, $before -> $after of $expected clouds."
    # The sampler is resumable by (sample_id, n, seed), so a kernel crash costs one cloud rather
    # than the run. No forward progress means retrying will not help.
    if ($after -le $before) {
        Write-Host "  ** no forward progress, so this is not one bad shape. Stopping. **"
        break
    }
}

Write-Host ""
Write-Host "=== $after of $expected clouds written to $OutDir ==="
Write-Host ""
Write-Host "=== NOW ANALYSE, in the external_eval environment (no CAD kernel needed) ==="
Write-Host "  conda run -n external_eval python /mnt/c/Workspace/Project/Paper/MIRAGE-V2/src/scratch/occt_floor_analyze.py ``"
Write-Host "    --sample-dir /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/occt_floor ``"
Write-Host "    --out /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/occt_floor/analysis.json"
