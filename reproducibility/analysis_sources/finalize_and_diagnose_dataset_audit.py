"""Finalize complete real-dataset row evidence and test a missing-feature-path hypothesis.

The first run finished all 50,000 real __getitem__ calls/packing assertions, then
stopped on disagreement with Claude v2. Do not erase that stop or rerun it away.
This separate script aggregates its durable rows, pins the STEP feature inputs,
and tests an explicitly COUNTERFACTUAL unresolved-feature-path condition.
"""
from __future__ import annotations
import os
os.environ.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1")
import collections
import hashlib
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

REVIEW = Path("__EVIDENCE_SOURCE_ROOT__")
SOURCE = Path("__RUN_SOURCE_ROOT__")
AUDIT = REVIEW / "09_cpu_preparation/review01_dataset_v1"
OUT = REVIEW / "09_cpu_preparation/review01_diagnosis_v2"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise ValueError("Do not overwrite diagnosis")
    os.chdir(SOURCE)  # Historical JSONL STEP-feature paths are relative to src.
    sys.path.insert(0, str(SOURCE))
    from transformers import AutoTokenizer
    from miragecad import gen_prompts
    import torch
    import transformers
    tok = AutoTokenizer.from_pretrained(AUDIT / "tokenizer_snapshot", local_files_only=True)
    assert tok(tok.eos_token, add_special_tokens=False)["input_ids"] == [tok.eos_token_id]
    rows = [json.loads(line) for line in (AUDIT / "per_sample_tokens_labels.jsonl").open()]
    assert len(rows) == 50000
    paired = {arm: [r for r in rows if r["arm"] == arm] for arm in ("A1E", "B2P")}
    train = [json.loads(x) for x in (AUDIT / "b2p_train_source.jsonl").open()]
    assert len(train) == 25000
    for arm, records in paired.items():
        assert len(records) == len({r["sample_id"] for r in records}) == 25000
        assert [r["sample_id"] for r in records] == [r["sample_id"] for r in train]
        assert [r["index"] for r in records] == list(range(25000))
    actual = {}
    for arm, records in paired.items():
        c = collections.Counter(r["bucket"] for r in records)
        loss = sorted(r["body_tokens_lost"] for r in records if r["body_tokens_lost"])
        body_total = sum(r["body_tokens"] for r in records)
        lost = sum(r["body_tokens_lost"] for r in records)
        actual[arm] = {"rows": 25000, "complete_rows": c["complete"], "eos_only_rows": c["eos_only"],
                       "partial_body_rows": c["partial_body"], "no_target_rows": c["no_target"],
                       "body_cut_rows_including_no_target": c["partial_body"] + c["no_target"],
                       "incomplete_target_rows": 25000 - c["complete"],
                       "median_prompt_tokens": statistics.median(r["prompt_tokens"] for r in records),
                       "body_tokens_total_excluding_eos": body_total, "body_tokens_lost": lost,
                       "body_tokens_lost_pct_of_body_tokens": 100 * lost / body_total,
                       "body_loss_median": statistics.median(loss) if loss else 0,
                       "body_loss_p90_nearest_rank": loss[(9 * len(loss) + 9) // 10 - 1] if loss else 0,
                       "body_loss_max": max(loss, default=0)}
    OUT.mkdir()
    counterfactual = {arm: collections.Counter() for arm in paired}
    cf_prompt_lengths = {arm: [] for arm in paired}
    samples = []
    missing_actual_features = []
    with (OUT / "step_feature_source_archive.jsonl").open("x", encoding="utf-8") as archive:
        for i, original in enumerate(train):
            feature = Path(original["step_feature_path"])
            assert feature.is_file(), f"Actual WSL STEP feature missing: {feature}"
            raw = feature.read_bytes()
            archive.write(json.dumps({"sample_id": original["sample_id"], "path": str(feature), "sha256": hashlib.sha256(raw).hexdigest(),
                                      "utf8_text": raw.decode("utf-8")}, ensure_ascii=False) + "\n")
            fake = dict(original, step_feature_path="/__review_cpu_audit_deliberately_missing_step_features__.json")
            assert not Path(fake["step_feature_path"]).exists()
            for arm, include in (("A1E", False), ("B2P", True)):
                prompt = gen_prompts.build_program_prompt(fake, "step", original["ir_text_for_program"] if include else "", include_plan=include)
                plen = len(tok(prompt, add_special_tokens=True)["input_ids"])
                cf_prompt_lengths[arm].append(plen)
                tlen = paired[arm][i]["target_tokens_including_eos"]
                kept = max(0, min(tlen, 1536 - plen))
                lost_body = tlen - 1 - min(kept, tlen - 1)
                bucket = "no_target" if kept == 0 else "partial_body" if lost_body else "eos_only" if kept < tlen else "complete"
                counterfactual[arm].update({bucket: 1, "body_lost": lost_body})
            if i < 3:
                samples.append({"sample_id": original["sample_id"], "actual_step_feature_path": str(feature),
                                "actual_evidence": gen_prompts.get_query_evidence(original, "step"),
                                "unresolved_path_evidence": gen_prompts.get_query_evidence(fake, "step"),
                                "actual_prompt_tokens": {a: paired[a][i]["prompt_tokens"] for a in paired},
                                "unresolved_path_prompt_tokens": {a: cf_prompt_lengths[a][-1] for a in paired}})
            if (i + 1) % 5000 == 0:
                print(f"missing-feature-path diagnosis {i+1}/25000; CPU only", flush=True)
    claude = json.loads((REVIEW / "08_claude/support/trunc_audit_v2_results.json").read_text())
    comparison = {}
    for arm, c in counterfactual.items():
        counts = {"eos_only_rows": c["eos_only"], "body_cut_rows": c["partial_body"] + c["no_target"],
                  "no_target_rows": c["no_target"], "body_tokens_lost": c["body_lost"],
                  "median_prompt_tokens": statistics.median(cf_prompt_lengths[arm])}
        comparison[arm] = {"counterfactual_counts": counts, "matches_claude_v2_all_these_fields": all(counts[k] == claude["arms"][arm][k] for k in counts)}
    report = {"status": "REAL_DATASET_AUDIT_COMPLETE_WITH_SEPARATE_REFERENCE_DISAGREEMENT_DIAGNOSIS", "created_utc": datetime.now(timezone.utc).isoformat(),
              "real_dataset_rows": 50000, "actual_wsl_inputs": actual, "missing_path_counterfactual": comparison,
              "examples": samples, "cuda_initialized_in_diagnosis": torch.cuda.is_initialized(),
              "runtime": {"torch": torch.__version__, "transformers": transformers.__version__, "python": sys.version},
              "source_snapshots": {p.name: sha(p) for p in (AUDIT / "source_snapshots").iterdir()},
              "tokenizer_snapshot": {p.name: sha(p) for p in (AUDIT / "tokenizer_snapshot").iterdir()},
              "real_dataset_row_file_sha256": sha(AUDIT / "per_sample_tokens_labels.jsonl"),
              "first_run_stop": "All 25000 paired real dataset calls and packing/labels assertions finished; comparison to Claude v2 then failed. Kept unchanged.",
              "limitations": ["Original training runtime input-byte binding not retrospectively proved", "No historical LM or latent checkpoint loaded", "A1E token path uses explicitly unused dummy latent", "Counterfactual reproduces unresolved feature path, not a new trained condition", "All counts conditional on pinned current data helper/prompt/tokenizer and recorded-hash-matching trainers"],
              "audit_script_sha256": sha(Path(__file__))}
    assert not torch.cuda.is_initialized()
    (OUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifact_files = [p for d in (AUDIT, OUT) for p in d.rglob("*") if p.is_file()]
    (OUT / "artifact_manifest.json").write_text(json.dumps([{"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)} for p in artifact_files], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"actual": actual, "counterfactual_comparison": comparison}, indent=2), flush=True)


if __name__ == "__main__":
    main()
