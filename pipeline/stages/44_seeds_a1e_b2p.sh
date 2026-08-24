#!/bin/bash
# One extra seed for BOTH arms of the controlled pair. Run it once per seed.
#
# WHAT IS ACTUALLY IN QUESTION. Two results came out of the matched comparison and they have very
# different standing. Per-part fidelity showed no detectable difference AND passed a TOST against
# a derived margin, so it rests on an interval, not on a null. Coverage did not: the
# exposure-matched textual arm leads by 4.2 pp of Build at p = 0.031, on ONE run, across two gates
# that near-duplicate each other. A single seed cannot separate four points from run-to-run
# variation, and that number is currently the only thing in the section arguing that explicit text
# does more than break even.
#
# So this script exists for the coverage claim. It will also tighten the fidelity interval, which
# is welcome but not the reason.
#
# BOTH ARMS, SAME SEED, EVERY TIME. Seeding one arm and not the other would measure that arm's
# variance and silently attribute the difference to representation form. train_program_lora.py had
# no --seed at all until this experiment needed one; its default is 42, which is what the
# published runs used, so seed 42 is the run we already have and must NOT be re-run.
#
# THE EXPENSIVE PART IS ALREADY DONE. The 24,000 predicted training plans are seed-independent --
# they come from the plan decoder, which is not being retrained here -- so the ~16 hour generation
# stage does not repeat. Per seed this is roughly 7 h for each arm plus inference.
#
#   SEED=1 bash training_25k/44_seeds_a1e_b2p.sh
#   SEED=2 bash training_25k/44_seeds_a1e_b2p.sh
#
# Then score gates and geometry for the new arm labels, and run seed_variance_analysis.py.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

source training_25k/_guard_fresh.sh \
  gen_scripts/train_soft_prefix_ir.py \
  training_25k/scripts/gen_b1_direct_latent.py \
  training_25k/scripts/gen_code_from_predicted_ir.py \
  train_program_lora.py

SEED=${SEED:?set SEED, e.g. SEED=1. Seed 42 is the published run and must not be overwritten.}
if [ "$SEED" = "42" ]; then
  echo "Seed 42 is the run already reported. Re-running it would overwrite the published" >&2
  echo "checkpoints and predictions. Pick another seed." >&2
  exit 1
fi

MODALITY=${MODALITY:-step}
GEN=${GEN:-outputs/e1_observation_bypass}
PLANS=${PLANS:-data/25k/predicted_ir_train_full.jsonl}
MIX=${MIX:-data/25k/train_b2pred_${MODALITY}.jsonl}
BASE_CODE=${BASE_CODE:-outputs/qwen25_coder_1_5b_program_25k}
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
ACCUM=${ACCUM:-8}

A_OUT=outputs/b1_1epoch_${MODALITY}_s${SEED}
B_OUT=outputs/b2_pred_matched_${MODALITY}_s${SEED}
A_ARM=A1E_s${SEED}
B_ARM=B2P_s${SEED}

# ---------------------------------------------------------------------------
# Preflight. Both trainers must honour a seed, or this measures nothing.
# ---------------------------------------------------------------------------
python - <<'PY' || { echo "seed preflight failed -- not starting." >&2; exit 1; }
import os, pathlib, subprocess, sys
ok = True

# The whole design rests on both arms being seedable. train_program_lora.py acquired --seed for
# this experiment; if that patch is missing from this tree, the B2P arm would silently repeat
# seed 42 and the variance estimate would be of one arm only.
src = pathlib.Path("train_program_lora.py").read_text(encoding="utf8")
for need in ("--seed", "seed=args.seed", "data_seed=args.seed"):
    print(f"{'ok  ' if need in src else 'FAIL'} train_program_lora.py has {need}")
    ok &= need in src

h = subprocess.run([sys.executable, "-m", "gen_scripts.train_soft_prefix_ir", "--help"],
                   capture_output=True, text=True).stdout
print(f"{'ok  ' if '--seed' in h else 'FAIL'} train_soft_prefix_ir.py exposes --seed")
ok &= "--seed" in h

# The mix is seed-independent and must already exist: rebuilding it here would risk a different
# row set per seed, which would confound seed variance with data variance.
mix = os.environ.get("MIX", "data/25k/train_b2pred_step.jsonl")
n = sum(1 for _ in open(mix, encoding="utf-8")) if os.path.exists(mix) else 0
print(f"{'ok  ' if n > 0 else 'FAIL'} predicted-plan training mix present: {n} rows ({mix})")
if not n:
    print("     Run 43 first. This script deliberately does not build it, so every seed trains")
    print("     on exactly the same rows.")
ok &= n > 0

for p in ("outputs/align_25k/best.pt", f"outputs/prior_{os.environ.get('MODALITY','step')}_25k/best.pt"):
    print(f"{'ok  ' if os.path.exists(p) else 'FAIL'} {p}")
    ok &= os.path.exists(p)

sys.exit(0 if ok else 1)
PY

complete() { [ -f "$1" ] && [ "$(wc -l < "$1")" -eq "$LIMIT" ]; }
B_RESUME=""

# RESUME IS ON FOR ARM B ONLY, and the asymmetry is not an oversight.
#
# train_program_lora.py hands Trainer a PeftModel, so HF saves the adapter alone and its
# checkpoints carry optimizer.pt, scheduler.pt and rng_state.pth. It was resumable all along
# and simply was never asked; it is asked now.
#
# train_soft_prefix_ir.py hands Trainer a plain module wrapper, so HF tries the FULL state
# dict, and safetensors refuses this base model's tied lm_head/embed_tokens pair. A
# --crash-resume flag that switched native checkpointing on therefore killed arm A at step
# 500, 59 minutes in, at exactly the moment it existed to protect. Reverted. A correct
# version needs overrides of Trainer._save and _load_from_checkpoint, which is not worth
# doing speculatively mid-campaign.
#
# So arm A costs the whole run if it faults: about 6.5 h. tee stays -a so a retry appends
# rather than erasing the log of the attempt that died.

# ---------------------------------------------------------------------------
# Arm A: direct latent, one epoch, this seed.
# ---------------------------------------------------------------------------
if [ -f "$A_OUT/soft_prefix.pt" ] && [ -f "$A_OUT/adapter_model.safetensors" ]; then
  echo "=== skip A1E seed $SEED training ($A_OUT exists) ==="
else
  echo "=== A1E seed $SEED: latent -> code, 1 epoch ==="
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --modality "$MODALITY" --target program \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$A_OUT" \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --gradient-accumulation-steps "$ACCUM" \
    --epochs 1 --learning-rate 2e-4 --max-length 1536 \
    --lora-r 16 --lora-alpha 32 --seed "$SEED" \
    --eval-steps 500 --save-steps 500 2>&1 | tee -a "$A_OUT.train.log"
fi

A_PRED="$GEN/gen_code_${MODALITY}_${A_ARM}.jsonl"
if complete "$A_PRED"; then
  echo "=== skip A1E seed $SEED inference (complete) ==="
else
  echo "=== A1E seed $SEED inference ==="
  python training_25k/scripts/gen_b1_direct_latent.py \
    --modality "$MODALITY" \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --b1-dir "$A_OUT" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$A_PRED" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

# ---------------------------------------------------------------------------
# Arm B: exposure-matched textual plan, one epoch, same seed, same mix.
# ---------------------------------------------------------------------------
if [ -f "$B_OUT/adapter_model.safetensors" ]; then
  echo "=== skip B2P seed $SEED training ($B_OUT exists) ==="
else
  # --resume-from-checkpoint takes a PATH, not "auto", so resolve the newest checkpoint that
  # actually carries optimizer state. A weights-only directory cannot resume, which is what
  # the crashed soft-prefix run left behind, hence the test rather than just the last name.
  B_RESUME=$(ls -d "$B_OUT"/checkpoint-* 2>/dev/null \
    | while read -r d; do [ -f "$d/optimizer.pt" ] && echo "$d"; done \
    | sort -t- -k2 -n | tail -1)
  [ -n "${B_RESUME:-}" ] && echo "  resuming from $B_RESUME"
  echo "=== B2P seed $SEED: predicted plan -> code, 1 epoch ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --init-adapter-dir "$BASE_CODE" \
    --target program --modality "$MODALITY" --max-length 1536 \
    --train-jsonl "$MIX" --val-jsonl data/25k/val.jsonl \
    --output-dir "$B_OUT" \
    --epochs 1 --per-device-train-batch-size 1 \
    --gradient-accumulation-steps "$ACCUM" --learning-rate 2e-4 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    --seed "$SEED" ${B_RESUME:+--resume-from-checkpoint "$B_RESUME"} \
    2>&1 | tee -a "$B_OUT.train.log"
fi

B_PRED="$GEN/gen_code_${MODALITY}_${B_ARM}.jsonl"
if complete "$B_PRED"; then
  echo "=== skip B2P seed $SEED inference (complete) ==="
else
  echo "=== B2P seed $SEED inference ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality "$MODALITY" \
    --lora-code-dir "$B_OUT" \
    --ir-jsonl "$GEN/pred_ir_${MODALITY}_present.jsonl" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$B_PRED" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

# ---------------------------------------------------------------------------
# Both arms' realised config, side by side, so a later reader can check the pairing
# rather than trusting the filename.
# ---------------------------------------------------------------------------
# Exported BEFORE the heredoc. The same ordering bug went into 43 first: a single-quoted
# heredoc reads these from the environment, so exporting afterwards leaves them unset.
export SEED A_OUT B_OUT
python - <<'PY' > "$GEN/seed_${SEED}_actuals.json" || echo "note: actuals not derived" >&2
import json, os, pathlib, re
out = {"seed": int(os.environ["SEED"])}
for tag, d in (("A1E", os.environ["A_OUT"]), ("B2P", os.environ["B_OUT"])):
    e = {}
    for name in ("training_report.json", "soft_prefix_training_report.json"):
        p = pathlib.Path(d, name)
        if p.exists():
            e["report"] = json.loads(p.read_text(encoding="utf8"))
    log = pathlib.Path(d + ".train.log")
    if log.exists():
        ev = re.findall(r"'eval_loss':\s*'?([0-9.eE+-]+)'?",
                        log.read_text(encoding="utf8", errors="replace"))
        e["eval_loss_last"] = float(ev[-1]) if ev else None
        st = re.findall(r"(\d+)/(\d+) \[", log.read_text(encoding="utf8", errors="replace"))
        e["steps_seen"] = int(st[-1][1]) if st else None
    out[tag] = e
print(json.dumps(out, indent=2))
PY

echo
echo "=== NOW IN WINDOWS POWERSHELL ==="
printf '  & "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scripts\\run_e1_execution.ps1" -Modalities %s -Conditions %s,%s\n' \
  "$MODALITY" "$A_ARM" "$B_ARM"
echo "  then add both labels to 41's ARMS list, re-run 41, and score geometry."
echo "  finally: python src\\scratch\\seed_variance_analysis.py"
