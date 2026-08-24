# A5: execution rates with the deterministic repair rules DISABLED.
#
# Section 5.9 reports how often the operation-name rule fires (4.6-11.3% of
# samples) but not what the build rate would be without it, so the coverage
# figures bound the rule's contribution without measuring it. This closes that.
#
# No generation and no GPU: the un-repaired outputs already exist alongside the
# repaired ones. gen_test_{m}_stage3b.jsonl is the raw code generator output;
# gen_test_{m}_stage3b_repaired_p0.jsonl is what every reported number uses. Same
# programs, same checkpoint, same test set -- the only difference is the two
# rewrite categories of Section 5.9. So this is a clean paired comparison against
# scratch/exec_eval_25k_stage3b_{m}/, and the delta is exactly the repair rules'
# contribution to Build.
#
# Windows PowerShell only (WSL cannot import flluma). Roughly 3 minutes per
# modality at 2,500 rows, based on the B5 timings.
$ErrorActionPreference = "Stop"
$ProjectRoot = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$EvalScript = Join-Path $PSScriptRoot "..\scripts\evaluate_execution.ps1"

if (-not (Test-Path -LiteralPath $EvalScript)) { throw "not found: $EvalScript" }

$modalities = @("step", "point", "text", "image")
foreach ($m in $modalities) {
    $InputJsonl = Join-Path $ProjectRoot "outputs\qwen25_coder_1_5b_program_25k_stage4b\gen_test_${m}_stage3b.jsonl"
    if (-not (Test-Path -LiteralPath $InputJsonl)) {
        Write-Host "SKIP $m -- no un-repaired file at $InputJsonl"
        continue
    }
    Write-Host "=== execution eval, NO REPAIR: $m ==="
    $OutputDir = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_norepair_25k_stage3b_${m}"
    & $EvalScript -InputJsonl $InputJsonl -OutputDir $OutputDir
}

Write-Host ""
Write-Host "=== Compare against the repaired runs ==="
Write-Host "  repaired : scratch\exec_eval_25k_stage3b_{m}\execution_summary.json"
Write-Host "  no repair: scratch\exec_norepair_25k_stage3b_{m}\execution_summary.json"
Write-Host "The Build difference is the contribution of the Section 5.9 rewrite rules."
