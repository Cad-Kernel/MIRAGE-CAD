<#
.SYNOPSIS
  Unattended overnight runner for review items B7 (editability) and B5 (random-slice
  best-of-N geometry).

.DESCRIPTION
  This has to be a PowerShell script rather than a shell script because the work
  crosses the WSL/Windows boundary in both directions: generation and sampling need
  WSL (CUDA, conda ai_dev), while every kernel execution needs Windows (WSL cannot
  `import flluma`). PowerShell can drive WSL via `wsl -e bash -lc`; the reverse is
  not true.

  Designed to be left alone. Specifically:

    * PREFLIGHT first. Every input file, script and binary is checked before any
      long phase starts, so a missing file costs seconds rather than surfacing three
      hours in.
    * SMOKE BEFORE FULL. B7 runs a small -Limit pass first; if it produces no usable
      rows the full pass is skipped instead of burning the night on a broken harness.
    * RESUMABLE. Any phase whose output already exists is skipped unless -Force.
      A crash at 3am costs the current phase, not the whole run.
    * NON-FATAL PHASES. One phase failing does not abort the rest. Everything is
      recorded and the final summary says exactly what ran, what was skipped, what
      failed, and how long each took.
    * B7 BEFORE B5, deliberately. B7 is the higher-value experiment: it is the only
      dimension where variant C has a structural reason to beat the NN-IR baselines,
      and it fills the "Not measured" row in the claims table. B5 only re-samples
      numbers that already exist. If the night is not long enough for both, the
      right one has been done. Pass -Order B5First to swap.

.EXAMPLE
  # the normal invocation
  powershell -ExecutionPolicy Bypass -File src\scripts\run_overnight_b7_b5.ps1

.EXAMPLE
  # just check everything is in place, run nothing
  powershell -ExecutionPolicy Bypass -File src\scripts\run_overnight_b7_b5.ps1 -PreflightOnly

.EXAMPLE
  # B7 only, smaller, for a first look
  powershell -ExecutionPolicy Bypass -File src\scripts\run_overnight_b7_b5.ps1 -Only B7 -B7Limit 25
#>
[CmdletBinding()]
param(
    [ValidateSet("Both", "B7", "B5")] [string]$Only = "Both",
    [ValidateSet("B7First", "B5First")] [string]$Order = "B7First",
    [int]$B7SmokeLimit = 5,          # rows in the smoke pass
    [int]$B7Limit = 0,               # 0 = all rows the .sh prepared (200)
    [string]$B7Deltas = "-0.25,-0.1,0.1,0.25",
    [switch]$Force,                  # redo phases whose outputs exist
    [switch]$PreflightOnly,
    [switch]$SkipSmoke
)

# Deliberately NOT "Stop": a failing phase must not kill the run.
$ErrorActionPreference = "Continue"

$RepoWin   = "C:\Workspace\Project\Paper\MIRAGE-V2"
$SrcWin    = Join-Path $RepoWin "src"
$ScratchWin= Join-Path $RepoWin "scratch"
$SrcUnc    = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$FllumaCli = "C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe"
$WslSrc    = "~/workspace/MIRAGE/src"

$Stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$LogDir  = Join-Path $RepoWin "scratch\overnight_$Stamp"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$MainLog = Join-Path $LogDir "run.log"

$Phases = New-Object System.Collections.ArrayList

function Say {
    param([string]$Msg, [string]$Level = "INFO")
    $line = "[{0}] {1,-5} {2}" -f (Get-Date -Format "HH:mm:ss"), $Level, $Msg
    Write-Output $line
    Add-Content -LiteralPath $MainLog -Value $line -Encoding utf8
}

function Invoke-Wsl {
    <# Run a bash command inside WSL at the source root. The .sh scripts activate
       conda themselves, so no env setup is needed here.

       IMPORTANT: $Command must not contain double quotes. PowerShell re-tokenises
       embedded double quotes when handing a string to a native command, so they do
       not survive intact into bash -- the string arrives split and bash reports an
       unmatched quote. Everything called from here is therefore written to avoid
       quoting: paths contain no spaces, and anything that would need quoting is
       passed through a file instead. #>
    param([string]$Command, [string]$LogFile)
    if ($Command -match '"') {
        Say "internal error: WSL command contains a double quote and will not survive PowerShell argument passing:" "ERROR"
        Say "    $Command" "ERROR"
        return 99
    }
    $full = "cd $WslSrc && $Command"
    Say "wsl: $Command"
    # Capture the exit code from the native call itself. Reading $LASTEXITCODE after
    # a pipeline through Tee-Object does not reliably reflect the native command --
    # which is how a WSL generation phase that died on a KeyboardInterrupt was
    # reported as "OK" for 1.3 minutes of supposed work.
    $out = & wsl -e bash -lc $full 2>&1
    $rc = $LASTEXITCODE
    $out | Tee-Object -FilePath $LogFile -Append | Out-Null
    if ($rc -ne 0) { Say "wsl command exited $rc" "WARN" }
    return $rc
}

function ConvertTo-WslPath {
    <# C:\a\b -> /mnt/c/a/b #>
    param([string]$WinPath)
    $p = (Resolve-Path -LiteralPath $WinPath).Path
    return "/mnt/" + $p.Substring(0,1).ToLower() + ($p.Substring(2) -replace '\\','/')
}

function Invoke-Phase {
    <# Run one phase, time it, record the outcome, never throw. #>
    param(
        [string]$Name,
        [scriptblock]$Body,
        [string]$ExpectPath = $null,   # if this exists and -not $Force, skip
        [switch]$Critical              # if this fails, dependent phases are skipped
    )
    if ($ExpectPath -and (Test-Path -LiteralPath $ExpectPath) -and -not $Force) {
        Say "SKIP  $Name  (output already present: $ExpectPath; -Force to redo)" "SKIP"
        [void]$Phases.Add([pscustomobject]@{Name=$Name; Status="skipped"; Seconds=0; Note="output exists"})
        return $true
    }
    Say "===== BEGIN $Name ====="
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $ok = $true
    try {
        $rc = & $Body
        if ($rc -is [int] -and $rc -ne 0) { $ok = $false }
    } catch {
        Say "exception in ${Name}: $($_.Exception.Message)" "ERROR"
        $ok = $false
    }
    $sw.Stop()
    $mins = [math]::Round($sw.Elapsed.TotalMinutes, 1)
    if ($ok) {
        Say "===== END   $Name  OK  ($mins min) ====="
        [void]$Phases.Add([pscustomobject]@{Name=$Name; Status="ok"; Seconds=[int]$sw.Elapsed.TotalSeconds; Note=""})
    } else {
        Say "===== END   $Name  FAILED  ($mins min) =====" "ERROR"
        [void]$Phases.Add([pscustomobject]@{Name=$Name; Status="failed"; Seconds=[int]$sw.Elapsed.TotalSeconds; Note="see log"})
        if ($Critical) { Say "$Name is critical; dependent phases will be skipped" "WARN" }
    }
    return $ok
}

function Count-JsonlRows {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return -1 }
    return (Get-Content -LiteralPath $Path | Where-Object { $_.Trim() -ne "" }).Count
}

# ===========================================================================
# PREFLIGHT
# ===========================================================================
Say "log directory: $LogDir"
Say "preflight ..."
$missing = @()

foreach ($p in @($FllumaCli,
                 (Join-Path $SrcWin "scripts\editability_probe.ps1"),
                 (Join-Path $SrcWin "scripts\evaluate_execution_nbest.ps1"),
                 (Join-Path $SrcWin "scripts\evaluate_geometry_nbest.ps1"))) {
    if (-not (Test-Path -LiteralPath $p)) { $missing += $p }
}
# WSL-side files, checked over the UNC path so we fail fast rather than inside bash.
foreach ($rel in @("training_25k\21_editability_probe.sh",
                   "training_25k\20_rerun_geometry_nbest_random100.sh",
                   "training_25k\scripts\make_random_subset.py",
                   "editability_probe.py",
                   "scratch\aggregate_editability.py",
                   "scratch\aggregate_geometry_nbest.py",
                   "scratch\gen_nbest_candidates.py",
                   "scratch\repair_nbest_candidates.py",
                   "outputs\qwen25_coder_1_5b_program_25k_stage4b\gen_test_step_stage3b_repaired_p0.jsonl",
                   "outputs\lora_ir_25k_stage3b\predicted_ir_test_step_p1a.jsonl",
                   "outputs\lora_ir_25k_stage3b\predicted_ir_test_point_p1a.jsonl",
                   "data\25k\test.jsonl")) {
    if (-not (Test-Path -LiteralPath (Join-Path $SrcUnc $rel))) { $missing += "WSL: $rel" }
}

if ($missing.Count -gt 0) {
    Say "PREFLIGHT FAILED -- missing:" "ERROR"
    $missing | ForEach-Object { Say "    $_" "ERROR" }
    Say "Nothing was run. If the WSL entries are missing, copy src/ to WSL first." "ERROR"
    exit 2
}

# WSL reachable and conda env resolvable? The probe body goes through a FILE rather
# than `python -c '...'`, because the inline form needs quotes that PowerShell will
# not pass through to bash intact (see Invoke-Wsl).
$probePy = Join-Path $LogDir "wsl_probe.py"
@(
    'import torch'
    'print("torch", torch.__version__, "cuda", torch.cuda.is_available())'
) | Set-Content -LiteralPath $probePy -Encoding utf8
$probePyUnix = ConvertTo-WslPath $probePy

$probe = & wsl -e bash -lc "cd $WslSrc && source /home/jizong/miniforge3/etc/profile.d/conda.sh && conda activate ai_dev && python $probePyUnix" 2>&1
$probeRc = $LASTEXITCODE
Say "wsl probe: $probe"
if ($probeRc -ne 0) {
    Say "PREFLIGHT FAILED -- cannot activate ai_dev in WSL or torch import failed." "ERROR"
    exit 2
}
if ($probe -notmatch "cuda True") {
    Say "CUDA is not visible in WSL. B5's generation phase will be extremely slow on CPU." "WARN"
    Say "B7 does not need CUDA and is unaffected." "WARN"
}
Say "preflight OK"

if ($PreflightOnly) { Say "preflight-only requested; stopping here."; exit 0 }

# ===========================================================================
# B7 -- editability probe
# ===========================================================================
function Run-B7 {
    $work = Join-Path $SrcUnc "outputs\editability_25k"

    $prep = Invoke-Phase -Name "B7.1 prepare samples (WSL)" -ExpectPath (Join-Path $work "c_step.jsonl") -Critical -Body {
        Invoke-Wsl -Command "bash training_25k/21_editability_probe.sh" -LogFile (Join-Path $LogDir "b7_prepare.log")
    }
    if (-not $prep) { Say "B7 aborted: sample preparation failed" "ERROR"; return }

    # Which variants actually have inputs. c is required; direct/prior are the
    # paired NN-IR comparison and are the point of the experiment, but the run is
    # still meaningful without them.
    $variants = @()
    foreach ($v in @("c", "direct", "prior")) {
        $f = Join-Path $work "${v}_step.jsonl"
        $n = Count-JsonlRows $f
        if ($n -gt 0) { $variants += $v; Say "B7 input ${v}: $n rows" }
        else { Say "B7 input ${v}: absent -- skipping this variant" "WARN" }
    }
    if ($variants.Count -eq 0) { Say "B7 aborted: no variant inputs" "ERROR"; return }

    # --- smoke pass on variant c only -------------------------------------
    if (-not $SkipSmoke) {
        $smokeDir = Join-Path $ScratchWin "editability_smoke_step_c"
        $smoke = Invoke-Phase -Name "B7.2 smoke ($B7SmokeLimit rows, variant c)" -Critical -Body {
            & (Join-Path $SrcWin "scripts\editability_probe.ps1") `
                -InputJsonl (Join-Path $work "c_step.jsonl") `
                -OutputDir  $smokeDir `
                -Deltas     $B7Deltas `
                -Limit      $B7SmokeLimit 2>&1 |
                Tee-Object -FilePath (Join-Path $LogDir "b7_smoke.log") -Append
            return $LASTEXITCODE
        }
        if (-not $smoke) { Say "B7 aborted: smoke pass failed -- not spending the night on a broken harness" "ERROR"; return }

        # A smoke pass that "succeeds" but probes nothing is still a failure.
        $sfile = Join-Path $smokeDir "editability_summary.json"
        if (Test-Path -LiteralPath $sfile) {
            $s = Get-Content -LiteralPath $sfile -Raw | ConvertFrom-Json
            Say "smoke: baseline kernel-valid $($s.n_baseline_kernel_valid), perturbations $($s.n_perturbations), coverage $($s.mean_parametric_coverage)"
            if ($s.n_perturbations -lt 1) {
                Say "B7 aborted: smoke produced 0 perturbations. Either no baseline was kernel-valid," "ERROR"
                Say "  or params.add(...) is not being matched. Check b7_smoke.log before re-running." "ERROR"
                return
            }
        } else {
            Say "B7 aborted: smoke produced no summary.json" "ERROR"; return
        }
    }

    # --- full pass, one phase per variant ---------------------------------
    foreach ($v in $variants) {
        $outDir = Join-Path $ScratchWin "editability_25k_step_$v"
        Invoke-Phase -Name "B7.3 full probe [$v]" -ExpectPath (Join-Path $outDir "editability_summary.json") -Body {
            $a = @{
                InputJsonl = (Join-Path $work "${v}_step.jsonl")
                OutputDir  = $outDir
                Deltas     = $B7Deltas
            }
            if ($B7Limit -gt 0) { $a["Limit"] = $B7Limit }
            & (Join-Path $SrcWin "scripts\editability_probe.ps1") @a 2>&1 |
                Tee-Object -FilePath (Join-Path $LogDir "b7_full_$v.log") -Append
            return $LASTEXITCODE
        } | Out-Null
    }

    # --- aggregate ---------------------------------------------------------
    # No --labels: aggregate_editability.py derives them from the directory suffix,
    # so nothing here needs quoting (see Invoke-Wsl).
    $dirs = @()
    foreach ($v in $variants) {
        $d = Join-Path $ScratchWin "editability_25k_step_$v"
        if (Test-Path -LiteralPath (Join-Path $d "editability_summary.json")) {
            $dirs += "/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/editability_25k_step_$v"
        }
    }
    if ($dirs.Count -gt 0) {
        Invoke-Phase -Name "B7.4 aggregate" -Body {
            $cmd = "python3 scratch/aggregate_editability.py --dirs $($dirs -join ' ')"
            $a = Invoke-Wsl -Command $cmd -LogFile (Join-Path $LogDir "b7_table.log")
            $b = Invoke-Wsl -Command "$cmd --latex" -LogFile (Join-Path $LogDir "b7_table_latex.log")
            if ($a -ne 0) { return $a }
            return $b
        } | Out-Null
    }
}

# ===========================================================================
# B5 -- random-slice best-of-N geometry
# ===========================================================================
function Run-B5 {
    $work    = Join-Path $SrcUnc "outputs\geometry_nbest_random100"
    $workRel = "outputs/geometry_nbest_random100"

    # This is the long one: 2 modalities x 100 samples x 10 candidates on GPU. Expect
    # hours, not minutes -- if this phase reports a couple of minutes it did not run.
    $gen = Invoke-Phase -Name "B5.1 sample + generate candidates (WSL, GPU, long)" `
                        -ExpectPath (Join-Path $work "nbest_point_repaired.jsonl") -Critical -Body {
        $rc = Invoke-Wsl -Command "bash training_25k/20_rerun_geometry_nbest_random100.sh" -LogFile (Join-Path $LogDir "b5_generate.log")
        if ($rc -ne 0) { return $rc }
        # Verify the artefacts, not just the exit code. An interrupted or partially
        # completed generation can still leave a zero somewhere upstream.
        foreach ($m in @("step", "point")) {
            $f = Join-Path $work "nbest_${m}_repaired.jsonl"
            if (-not (Test-Path -LiteralPath $f)) {
                Say "expected candidate file missing after generation: $f" "ERROR"
                return 1
            }
        }
        return 0
    }
    if (-not $gen) {
        Say "B5 aborted: generation did not produce both candidate files." "ERROR"
        Say "  If b5_generate.log ends in KeyboardInterrupt, the run was interrupted --" "ERROR"
        Say "  Ctrl-C in the console reaches the WSL child too. Re-run and leave it alone." "ERROR"
        return
    }

    foreach ($m in @("step", "point")) {
        $cand = Join-Path $work "nbest_${m}_repaired.jsonl"
        $n = Count-JsonlRows $cand
        if ($n -le 0) { Say "B5 [$m]: no candidates file -- skipping modality" "WARN"; continue }
        Say "B5 [$m]: $n candidate rows"

        Invoke-Phase -Name "B5.2 five-gate execution [$m]" `
                     -ExpectPath (Join-Path $ScratchWin "exec_nbest_random100_$m\execution_nbest_summary.json") -Body {
            & (Join-Path $SrcWin "scripts\evaluate_execution_nbest.ps1") `
                -InputJsonl $cand `
                -OutputDir  (Join-Path $ScratchWin "exec_nbest_random100_$m") 2>&1 |
                Tee-Object -FilePath (Join-Path $LogDir "b5_exec_$m.log") -Append
            return $LASTEXITCODE
        } | Out-Null

        # NOTE: feed the SAME repaired-candidates file, not the previous phase's
        # output. evaluate_geometry_nbest.py needs modality/point_path/step_path/
        # all_candidates, which the execution step drops; without them every row
        # silently gets has_target=False and the aggregator divides by zero. This
        # has bitten this project before, which is why it is a comment and not a
        # convenience variable.
        Invoke-Phase -Name "B5.3 geometry scoring [$m]" `
                     -ExpectPath (Join-Path $ScratchWin "geometry_nbest_random100_$m\geometry_nbest_rows.jsonl") -Body {
            & (Join-Path $SrcWin "scripts\evaluate_geometry_nbest.ps1") `
                -InputJsonl $cand `
                -OutputDir  (Join-Path $ScratchWin "geometry_nbest_random100_$m") 2>&1 |
                Tee-Object -FilePath (Join-Path $LogDir "b5_geom_$m.log") -Append
            return $LASTEXITCODE
        } | Out-Null

        # Path deliberately unquoted -- it contains no spaces, and quotes would not
        # survive PowerShell -> bash argument passing (see Invoke-Wsl).
        Invoke-Phase -Name "B5.4 aggregate [$m]" -Body {
            Invoke-Wsl -Command "python3 scratch/aggregate_geometry_nbest.py /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/geometry_nbest_random100_$m/geometry_nbest_rows.jsonl" `
                       -LogFile (Join-Path $LogDir "b5_table_$m.log")
        } | Out-Null
    }
}

# ===========================================================================
# drive
# ===========================================================================
$sequence = if ($Order -eq "B7First") { @("B7", "B5") } else { @("B5", "B7") }
if ($Only -ne "Both") { $sequence = @($Only) }
Say "plan: $($sequence -join ' then ')"

$overall = [Diagnostics.Stopwatch]::StartNew()
foreach ($item in $sequence) {
    if ($item -eq "B7") { Run-B7 } else { Run-B5 }
}
$overall.Stop()

# ===========================================================================
# summary
# ===========================================================================
Say ""
Say "================ SUMMARY ================"
Say ("total wall clock: {0:N1} min" -f $overall.Elapsed.TotalMinutes)
$Phases | ForEach-Object {
    Say ("  {0,-40} {1,-8} {2,6:N1} min {3}" -f $_.Name, $_.Status, ($_.Seconds / 60.0), $_.Note)
}
$failed  = @($Phases | Where-Object Status -eq "failed")
$ok      = @($Phases | Where-Object Status -eq "ok")
$skipped = @($Phases | Where-Object Status -eq "skipped")
Say ""
Say "$($ok.Count) ok, $($skipped.Count) skipped, $($failed.Count) failed"

$Phases | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $LogDir "phases.json") -Encoding utf8

Say ""
Say "RESULT TABLES (the numbers for the paper):"
foreach ($f in @("b7_table.log", "b7_table_latex.log", "b5_table_step.log", "b5_table_point.log")) {
    $p = Join-Path $LogDir $f
    if (Test-Path -LiteralPath $p) { Say "  $p" }
}
Say ""
Say "Full log: $MainLog"
if ($failed.Count -gt 0) {
    Say "Some phases failed -- read the per-phase logs in $LogDir before trusting partial results." "WARN"
    exit 1
}
Say "All attempted phases completed."
exit 0
