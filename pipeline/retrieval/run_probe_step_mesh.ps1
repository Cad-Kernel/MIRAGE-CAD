# Ask Flluma what it can actually do with a STEP: mesh it, and boolean it. One file, no GPU.
#
# This decides an architecture question rather than producing a result. If Flluma can tessellate a
# loaded STEP with a settable tolerance, the canonical mesh stays inside the frozen operator. If it
# can compute B-Rep booleans and volumes, IoU needs no mesh at all. If either can only be guessed
# at, the rule is to stop and build an explicit STEP-to-mesh pipeline in the CAD-Recode environment
# instead -- an auditable second mesher beats an unauditable "probably the same OCCT underneath".
#
#   & .\src\scripts\run_probe_step_mesh.ps1
#   & .\src\scripts\run_probe_step_mesh.ps1 -Step "C:\path\to\some.step"
[CmdletBinding()]
param(
    [string]$Step = "",
    [string]$OutJson = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\occt_floor\step_mesh_probe.json"
)

$ErrorActionPreference = "Stop"
$FllumaCli  = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$ProjectSrc = "C:\Workspace\Project\Paper\MIRAGE-V2\src"
$Queries    = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360\queries.jsonl"

if (-not (Test-Path -LiteralPath $FllumaCli)) { throw "FllumaCLI not found: $FllumaCli" }

# Default to the median-sized Fusion360 part rather than the first row: the smallest and largest
# are 1.59 mm and 5,264 mm, and a probe should run on something representative.
if (-not $Step) {
    if (-not (Test-Path -LiteralPath $Queries)) { throw "queries.jsonl not found and no -Step given" }
    $rows = Get-Content -LiteralPath $Queries | Where-Object { $_.Trim() } | ForEach-Object {
        $o = $_ | ConvertFrom-Json
        [pscustomobject]@{ step_path = $o.step_path; bbox_diag = [double]$o.bbox_diag }
    } | Where-Object { $_.step_path -and (Test-Path -LiteralPath $_.step_path) } | Sort-Object bbox_diag
    if ($rows.Count -eq 0) { throw "no readable STEP files among the queries rows" }
    $mid = [int][Math]::Floor($rows.Count / 2)
    $Step = $rows[$mid].step_path
    Write-Host ("=== probing the median-sized part, bbox diagonal {0:N2} mm ===" -f $rows[$mid].bbox_diag)
}
Write-Host "    $Step"

$LocalDir = "C:\tmp\MIRAGE\probe_step_mesh"
New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutJson) | Out-Null
$LocalScript = Join-Path $LocalDir "probe_step_mesh.py"
$LocalLog    = Join-Path $LocalDir "cli.log"
Copy-Item -LiteralPath (Join-Path $ProjectSrc "probe_step_mesh.py") -Destination $LocalScript -Force

$env:MIRAGE_STEP_FEATURE_ARGS = "`"$Step`""
$env:MIRAGE_PROBE_OUT = $OutJson

# No 2>&1 on the native call: in PowerShell 5.1 that wraps each stderr line in an ErrorRecord and,
# with ErrorActionPreference Stop, the first line kills the script. FllumaCLI writes OCCT chatter
# to stderr constantly. Preference is scoped to Continue as a second guard.
$savedEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $FllumaCli $LocalScript | Tee-Object -FilePath $LocalLog
$cliExit = $LASTEXITCODE
$ErrorActionPreference = $savedEAP

Write-Host ""
if (Test-Path -LiteralPath $OutJson) {
    # The report file is the ground truth, not the exit code: FllumaCLI returns non-zero after a
    # clean run when the script raises SystemExit, and this project has already been bitten once
    # by trusting a status over an artefact.
    Write-Host "=== probe report written: $OutJson  (FllumaCLI exit $cliExit) ==="
} else {
    Write-Host "=== no probe report written; FllumaCLI exit $cliExit. See $LocalLog ==="
}
