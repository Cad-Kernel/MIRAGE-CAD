# Phase 6 execution eval: real Flluma/OpenCASCADE build/validate/export for
# all four modalities' repaired generated code. Must run in Windows
# PowerShell (WSL cannot `import flluma`). Reuses the existing, already-
# generic src/scripts/evaluate_execution.ps1 -- no new .ps1 logic needed here,
# just the four correct invocations.
$ErrorActionPreference = "Stop"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$EvalScript = Join-Path $PSScriptRoot "..\scripts\evaluate_execution.ps1"

$modalities = @("step", "point", "text", "image")
foreach ($m in $modalities) {
    Write-Host "=== execution eval: $m ==="
    $InputJsonl = Join-Path $ProjectRoot "outputs\qwen25_coder_1_5b_program_25k_stage4b\gen_test_${m}_repaired_p0.jsonl"
    $OutputDir = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_eval_25k_${m}"
    & $EvalScript -InputJsonl $InputJsonl -OutputDir $OutputDir
}

Write-Host "=== Wrote scratch/exec_eval_25k_{step,point,text,image}/{execution_rows.jsonl,execution_summary.json} ==="
