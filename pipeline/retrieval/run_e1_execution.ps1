<#
E1, part 2: put every generated program through the five kernel gates.

Generation happens in WSL (39_e1_observation_bypass.sh); execution happens here, because
the kernel does. This wrapper is a loop over evaluate_execution.ps1, one call per
condition per modality, reading the generation output straight from the WSL tree.

WHAT IT DOES NOT DO. No repair, no geometry, no selection. Repair is off so that the four
conditions are compared on what the decoder produced rather than on what the rewrite rules
could rescue; the main tables report post-repair rates and these are not comparable to
them. Geometry is a separate pass and only worth running once the gate rates say the
comparison is interesting.

RESUMABLE. evaluate_execution.ps1 keeps its own per-arm staging directory and appends, so
re-running skips finished arms. Kill it and start it again freely.
#>
param(
    [string[]]$Modalities = @("step", "point", "text", "image"),
    [string[]]$Conditions = @("C3", "C2", "C1", "C0"),
    [string]$Work = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\e1_observation_bypass",
    [string]$OutRoot = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch",
    [int]$Limit = 0
)
$ErrorActionPreference = "Stop"

$Evaluator = "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1"
if (-not (Test-Path $Evaluator)) { throw "missing evaluator: $Evaluator" }
if (-not (Test-Path $Work))      { throw "missing generation output: $Work  (run the WSL script first)" }

$missing = @()
foreach ($m in $Modalities) {
    foreach ($c in $Conditions) {
        $f = Join-Path $Work "gen_code_${m}_${c}.jsonl"
        if (-not (Test-Path $f)) { $missing += "gen_code_${m}_${c}.jsonl" }
    }
}
if ($missing.Count -gt 0) {
    Write-Host "Not generated yet, so these will be skipped:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
}

foreach ($m in $Modalities) {
    foreach ($c in $Conditions) {
        $in  = Join-Path $Work "gen_code_${m}_${c}.jsonl"
        $out = Join-Path $OutRoot "exec_e1_${m}_${c}"
        if (-not (Test-Path $in)) { continue }
        if (Test-Path (Join-Path $out "execution_summary.json")) {
            Write-Host "=== skip $m / $c (already scored) ===" -ForegroundColor DarkGray
            continue
        }
        Write-Host "=== gates: $m / $c ===" -ForegroundColor Cyan
        & $Evaluator -InputJsonl $in -OutputDir $out -Limit $Limit
    }
}

Write-Host ""
Write-Host "=== E1 gate summary ===" -ForegroundColor Cyan
$rows = @()
foreach ($m in $Modalities) {
    foreach ($c in $Conditions) {
        $s = Join-Path $OutRoot "exec_e1_${m}_${c}\execution_rows.jsonl"
        if (-not (Test-Path $s)) { continue }
        $n = 0; $syntax = 0; $build = 0; $export = 0
        Get-Content $s | ForEach-Object {
            $r = $_ | ConvertFrom-Json
            $n++
            if ($r.syntax_ok)      { $syntax++ }
            if ($r.build_ok)       { $build++ }
            if ($r.step_export_ok) { $export++ }
        }
        if ($n -eq 0) { continue }
        $rows += [pscustomobject]@{
            modality = $m
            cond     = $c
            n        = $n
            syntax   = [math]::Round(100 * $syntax / $n, 1)
            build    = [math]::Round(100 * $build  / $n, 1)
            export   = [math]::Round(100 * $export / $n, 1)
        }
    }
}
$rows | Format-Table -AutoSize

Write-Host "Read C2 against C3 first: that is the plan-only condition and the one the"
Write-Host "framing depends on. C2 is a LOWER bound -- the code decoder was trained with"
Write-Host "the evidence block present, so suppressing it at inference is a distribution"
Write-Host "shift. C1 and C0 carry the same caveat in the other direction and must not be"
Write-Host "compared against the trained no-plan baseline as if they were equivalent."
Write-Host ""
Write-Host "Repair was NOT applied, so these do not line up with the main tables."
Write-Host ""
Write-Host "Paired significance, once the arms exist:"
Write-Host "  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\e1_analysis.py"
