> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 05 -- MIRAGE B2P Construction-Disjoint STEP Result

## Status

```yaml
Arm: B2P_CD
Protocol: construction_disjoint_step_v1
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Summary JSON: COMPLETE
Review record: COMPLETE
Record status: CLOSED
```

This record covers the MIRAGE textual-plan pathway on the frozen construction-signature-disjoint STEP stress test. The split and sample IDs were frozen before this training run. The train-only descriptor NN baseline was completed first and was not used to tune this split.

## Scope

This is a strict in-corpus construction-signature-disjoint STEP diagnostic. It addresses Reviewer 1's concern that the original family-held-out split may still share construction patterns with training data.

Important caveat: the frozen test split contains only four held-out signatures, all with `operation_count = 1`. This result should be described as a construction-signature / held-out-operation stress test, not as a balanced benchmark of broad compositional or external CAD generalization.

## Code and Output Paths

Training / inference wrapper:

```text
Windows checkout:
__DEV_ROOT__\src\training_25k\cag_run_construction_disjoint_step_b2p_training.sh
sha256: 7387a403b18204ed07cf688b56ad487b0741fa058dc4f7b2c85c47577c0962eb

WSL checkout:
~/workspace/MIRAGE/src/training_25k/cag_run_construction_disjoint_step_b2p_training.sh
sha256: 7387a403b18204ed07cf688b56ad487b0741fa058dc4f7b2c85c47577c0962eb
```

Data:

```text
WSL:
~/workspace/MIRAGE/src/data/construction_disjoint_step_v1

Review evidence:
__EVIDENCE_SOURCE_ROOT__\02\split
```

Training outputs:

```text
alignment:
~/workspace/MIRAGE/src/outputs/align_25k_cd_step
best.pt sha256: 1573ebfd1a6b7547ef40a047aae61839ff0468162a8fe5570d46f45a7ceb7f48

latent prior:
~/workspace/MIRAGE/src/outputs/prior_step_25k_cd_step
best.pt sha256: 956cd140627bcc6f37c4bc0bc047c37f9bec6f952425461e59706f5d792cca4e

STEP-to-IR soft-prefix LoRA:
~/workspace/MIRAGE/src/outputs/lora_ir_25k_cd_step
adapter_model.safetensors sha256: d2c858a3b5cb25075dc48fd05fbc53fc7cecc15e626ee1e5e1cda2d6b8d63446
soft_prefix.pt sha256: 979ee5bc1d41ad8d651d12cdb4ab6ad3be8c5fe7b537ec856b7a78b4d18fae99

ground-truth IR code decoder:
~/workspace/MIRAGE/src/outputs/qwen25_coder_1_5b_program_25k_cd_step
adapter_model.safetensors sha256: 22af8bf78c0689c01e370a8de0f9c4f5278a2fdef867129db63a5a32f7b3f368

Stage 4b mixed predicted/GT IR code decoder:
~/workspace/MIRAGE/src/outputs/qwen25_coder_1_5b_program_25k_cd_step_stage4b
adapter_model.safetensors sha256: 3b8057998790a34e55e48b14bdf8e4a06414ce3bc041d1127725c61cb4f98f91
```

Prediction / geometry input:

```text
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/gen_code_step_B2P_CD.jsonl
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/geom_input_step_B2P_CD.jsonl
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/geom_input_step_B2P_CD_manifest.json
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/B2P_CD_metadata.json
```

Windows evaluator outputs:

```text
__DEV_ROOT__\scratch\exec_cd_step_B2P_CD
__DEV_ROOT__\scratch\geom_cd_step_B2P_CD
```

Frozen review copy:

```text
__EVIDENCE_SOURCE_ROOT__\02\mirage_b2p_cd
```

Evaluation scripts:

```text
__DEV_ROOT__\src\scripts\evaluate_execution.ps1
__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1
```

## Training / Inference Metadata

```yaml
arm: B2P_CD
data: data/construction_disjoint_step_v1
alignment: outputs/align_25k_cd_step
prior: outputs/prior_step_25k_cd_step
lora_ir: outputs/lora_ir_25k_cd_step
code_gt: outputs/qwen25_coder_1_5b_program_25k_cd_step
code_stage4b: outputs/qwen25_coder_1_5b_program_25k_cd_step_stage4b
repair: false
test_limit: 500
baseline_first_guard: 0
```

Training reports:

```yaml
STEP-to-IR soft-prefix:
  model: Qwen/Qwen2.5-Coder-1.5B
  train_rows: 25000
  val_rows: 2500
  prefix_len: 4
  max_length: 1536
  normal_loss: 1.1795750574588775
  zero_loss: 1.1916718115091325
  shuffled_loss: 1.1795750574588775
  shuffled_loss_note: VACUOUS because eval batch size was 1

GT-IR code decoder:
  model: Qwen/Qwen2.5-Coder-1.5B
  seed: 42
  train_rows: 25000
  val_rows: 2500
  max_length: 1536

Stage4b code decoder:
  model: Qwen/Qwen2.5-Coder-1.5B
  seed: 42
  train_rows: 3003
  val_rows: 2500
  max_length: 1536
```

P1a repair:

```yaml
ADD: 0
CUT: 0
gated_out: 4
conflict_skip: 0
ambiguous_skip: 0
distinct_samples_with_remap: 0
predicted_ir_test_step_sha256: 79bcdb87a2b5dfda375cce18b8d6bffe23ae2c97cb6605851549e05dbf1c2107
predicted_ir_test_step_p1a_sha256: 79bcdb87a2b5dfda375cce18b8d6bffe23ae2c97cb6605851549e05dbf1c2107
```

The identical hashes show that the P1a repair did not modify the predicted-IR file.

## Gate Evaluation

```yaml
rows: 500
runtime_seconds: 17.851
syntax_ok: 500 / 500 = 100.0%
exec_ok: 410 / 500 = 82.0%
build_ok: 410 / 500 = 82.0%
solid_valid: 410 / 500 = 82.0%
step_export_ok: 410 / 500 = 82.0%
kernel_crash_count: 0
```

The model produced syntactically valid Python for every test item. The main loss is executable/build coverage: 90 / 500 predictions failed during execution/build/export.

## Geometry Scoring

Geometry rows:

```yaml
rows: 500
has_target: 500
gate_ok_candidates: 410
scoreable: 410
unscoreable: 90
```

Chamfer distance on scoreable outputs:

```yaml
n: 410
min: 0.10143143646451966
q25: 2.350638250604856
median: 4.409928410527609
mean: 5.769056340747087
q75: 7.968130811241014
max: 68.09219575577654
sd_population: 5.331509389646838
```

F@1% on scoreable outputs:

```yaml
n: 410
min: 0.0
q25: 0.009380139802631578
median: 0.027308872767857144
mean: 0.03122076613473148
q75: 0.04714174041223689
max: 0.13902138157894736
sd_population: 0.02474710725252913
```

BBox error on scoreable outputs:

```yaml
n: 410
min: 4.0363564342745427e-11
q25: 0.0792463020917203
median: 0.3232082152694501
mean: 1.6405549264523733
q75: 3.3800388019281566
max: 11.466667811333332
sd_population: 2.02106278631356
```

Unconditional F@1% with unscoreable outputs counted as zero:

```yaml
mean: 0.025601028230479814
median: 0.01805320945945946
```

## Comparison to Train-Only Descriptor NN Baseline

Baseline: `NN_DESC_TRAIN`, train-only z-score L2 STEP descriptor nearest neighbour. That baseline copies valid train-set reference programs, so its gate coverage is expected to be 100%; geometry is the meaningful comparison.

Aggregate comparison:

```yaml
NN build_ok: 500 / 500 = 100.0%
B2P build_ok: 410 / 500 = 82.0%

NN scoreable: 500 / 500
B2P scoreable: 410 / 500

NN median CD: 6.492554284974444
B2P median CD: 4.409928410527609
Delta median CD, B2P - NN: -2.082625874446835

NN median F@1%: 0.011637369791666666
B2P median F@1%: 0.027308872767857144
Delta median F@1%, B2P - NN: 0.01567150297619048

NN unconditional mean F@1%: 0.01838105238740643
B2P unconditional mean F@1%: 0.025601028230479814
Delta unconditional mean F@1%, B2P - NN: 0.007219975843073385
```

Paired comparison on the 410 samples where B2P was scoreable and NN was also scoreable:

```yaml
paired_rows: 410

CD delta, B2P - NN:
  median: -0.8857744492659907
  mean: -2.6877994699136334
  q25: -4.50170487102476
  q75: 1.7651177030355574
  B2P lower-CD wins: 242
  B2P higher-CD losses: 168
  ties: 0
  sign_test_two_sided_p: 0.0003013854053005725

F@1% delta, B2P - NN:
  median: 0.007307493995405179
  mean: 0.01394540308457751
  q25: -0.0038851351351351345
  q75: 0.030599380671337904
  B2P higher-F wins: 270
  B2P lower-F losses: 137
  ties: 3
  sign_test_two_sided_p: 4.07685690721975e-11
```

Interpretation: MIRAGE B2P has lower executable coverage than train-set retrieval, but among its executable/scoreable predictions it is geometrically closer to the target than the descriptor NN baseline. Even when failed B2P outputs are counted as zero for F@1%, B2P still has a higher unconditional mean F@1% than NN retrieval.

## Failure Summary

The 90 execution/build failures are concentrated in API/schema mismatches rather than syntax failures.

```yaml
Part.wedge unexpected keyword width: 50
Part.bossed_plate missing hole args: 22
missing Part helper/method: 5
Part.linear_pattern unexpected keyword: 2
boss_center shape error: 2
ParameterRef type misuse: 2
Part.clamp_pad_plate unexpected chamfer_distance: 1
missing height key: 1
mirrored_lug_plate missing hole_radius: 1
Sketch name/API misuse: 1
feature-handle target error: 1
unsupported sketch_on_face profile: 1
sketch_on_face unexpected keyword: 1
```

Two dominant API/schema errors account for 72 / 90 failures: `Part.wedge` unexpected `width` arguments and `Part.bossed_plate` missing hole arguments. This suggests that many failures are not random syntax collapses. The model often reaches plausible held-out operation families, but the decoder does not reliably reproduce the exact API argument schema for those operations.

## Paper / Response Position

Recommended reviewer-facing wording:

> We added a construction-signature-disjoint STEP stress test using frozen train/validation/test sample IDs and zero overlap in the frozen operation-graph signature and exact operation sequence. On this held-out-construction diagnostic, MIRAGE's textual-plan pathway achieved 82.0% Build and STEP-export success. A train-only global STEP-descriptor nearest-neighbour baseline achieved 100% executable coverage because it returned valid training programs, but it showed weaker target geometry. On scoreable outputs, MIRAGE reduced median CD from 6.49 to 4.41 and increased median F@1% from 1.16% to 2.73%; on the paired scoreable subset, MIRAGE had lower CD in 242/410 cases and higher F@1% in 270/407 non-tied cases.

Keep the scope limitation attached:

> Because the split contains only four held-out operation-count-1 signatures, we treat this as a strict in-corpus construction-overlap diagnostic rather than a balanced benchmark of external or broad compositional generalization.

Recommended concise conclusion:

```text
On this construction-signature-disjoint stress test, MIRAGE B2P achieved 82.0% Build and STEP-export coverage. The held-out test set is not solved by train-only descriptor retrieval: the NN baseline is executable but geometrically weak, while MIRAGE produces better target geometry on successful outputs and a higher unconditional mean F@1% despite 90 failures. This supports the narrower claim that MIRAGE learns signal beyond nearest-neighbour construction copying; it does not show accurate reconstruction of held-out constructions or broad external generalization.
```

## Evidence Files

All paths below are stored under `__EVIDENCE_SOURCE_ROOT__\02\mirage_b2p_cd`.

```yaml
B2P_CD_metadata.json:
  sha256: 3018fd0bcbbe8c40e2629d640cf5f41aace53c160f010e48a4442b9aa09721e1
execution_rows_B2P_CD.jsonl:
  sha256: 47bcf952fb7dfbeb0349a1213772c8f214c20c8b7a8c92ea4d5f1e893e2a080f
execution_summary_B2P_CD.json:
  sha256: 5affc469a7ebe8489a5e8d2140048c78205e4aa2d22ea2b285a8976a4f3dbbfb
gen_code_step_B2P_CD.jsonl:
  sha256: 6d35403bafa2e194afbcdf09fec3d7e95fc5db58b17193de150fa1a301e4201a
geom_input_step_B2P_CD.jsonl:
  sha256: 5f1e363939d63e9b389cecd53cc505579dc5c1eadaeb245b13552860ec0c6063
geom_input_step_B2P_CD_manifest.json:
  sha256: 89ecb217f5887e347ef224a63fad9207e07dd09b6cc8d24801eefe4b9d9a20c3
geometry_nbest_rows_B2P_CD.jsonl:
  sha256: 0eaa053cc6a4a663c87a5bbf88272ab63b0d8f4c52e24a99c467132b2a271e71
mirage_b2p_cd_summary.json:
  sha256: 7ab6aab2cb8a7263bce92b376552f91bf16e9bb67e175fb5980ef072a2094db2
predicted_ir_test_step.jsonl:
  sha256: 79bcdb87a2b5dfda375cce18b8d6bffe23ae2c97cb6605851549e05dbf1c2107
predicted_ir_test_step_p1a.jsonl:
  sha256: 79bcdb87a2b5dfda375cce18b8d6bffe23ae2c97cb6605851549e05dbf1c2107
repair_face_extrude_alias_log_step_cd.json:
  sha256: 5f7802910c945e216049ee193fa48c83ad0a00e4d3df695d31324697507667e1
soft_prefix_training_report.json:
  sha256: 737b7fab3357ef337e16381c0d98dd0b3a200ea87b35e99cc7380b6f8cf64e36
training_report_code_gt.json:
  sha256: 6bca1a4ee7310a04c0f7bbb055952611b4515a523c4b1d5f848e9fd86e893fb1
training_report_code_stage4b.json:
  sha256: 5d48e6d3a6702df814bb687688975d378b31ab44d14a455680d0271b59520ab7
```
