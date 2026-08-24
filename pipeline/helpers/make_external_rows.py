"""Turn the external manifest into rows the generation scripts already understand.

`gen_predicted_ir.py` and `gen_nn_ir_baseline.py` read a fixed handful of keys off each
row -- `sample_id`, and `step_feature_path` or `point_path` depending on modality -- and
reach for `ir_path`, `program_path` and `text` through `.get`, so their absence is tolerated
rather than fatal. That absence is the whole shape of this experiment: external models come
with no reference construction plan and no reference program, so **no IR-level metric exists
here**. Op-Set F1, LCS and Prog-Op-F1 are all agreement-with-a-reference-plan measures and
simply cannot be computed. What survives is Build, STEP export, and geometry against the
reference cloud -- which is the right set anyway, since the internal work already showed the
IR metrics measure plan agreement rather than part fidelity.

Paths are emitted WSL-side because that is where generation runs. `bbox_diag` and
`external_id` ride along so the analysis can stratify without re-reading the clouds: only
64.5% of these parts fall inside the corpus's 9-134 mm scale band, and since the STEP
descriptor carries bbox, area and volume under log1p as absolute quantities while the point
path normalises, the STEP arms are extrapolating on the rest. The A-vs-B discriminator is
readable on the within-band stratum only.

    python training_25k/scripts/make_external_rows.py \\
        --index data/external/fusion360/step_index.jsonl \\
        --output data/external/fusion360/rows.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WSL_ROOT = "/home/jizong/workspace/MIRAGE/src/data/external/fusion360"
CORPUS_ROOT = "/mnt/c/Workspace/Project/FllumaOne/FllumaOne-100K"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--wsl-root", default=WSL_ROOT)
    ap.add_argument("--corpus-root", default=CORPUS_ROOT,
                    help="Where the retrieval index's relpaths resolve. Needed by the NN-IR "
                         "arm, which reads the retrieved neighbour's files from here.")
    args = ap.parse_args()

    rows, dropped = [], 0
    for line in args.index.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if not r.get("success", True):
            dropped += 1
            continue
        sid = r["sample_id"]
        # Derive rather than trust. The manifest's own point_path_wsl was written by a
        # to_wsl that only understood drive letters, so a build whose --output-dir was the
        # UNC share recorded //wsl.localhost/... for all 400 -- a path that resolves nowhere
        # inside WSL. The recorded value is used only if it actually exists.
        derived = f"{args.wsl_root}/clouds/{r['external_id']}.npz"
        recorded = r.get("point_path_wsl") or ""
        rows.append({
            "sample_id": sid,
            "external_id": r.get("external_id", sid),
            # Not about this row at all: build_retrieved_examples resolves the RETRIEVED
            # neighbour's training_ir.txt and program.py under the QUERY row's
            # dataset_root, defaulting to ".". Omitting it made read_text return "" for
            # every neighbour, so the NN-IR arm generated 400 programs from a prompt with
            # neither a plan nor a retrieved example, and reported 0% build as if that
            # were a finding about the index.
            "dataset_root": args.corpus_root,
            "step_feature_path": f"{args.wsl_root}/step_features/{sid}.json",
            "point_path": recorded if (recorded and Path(recorded).is_file()) else derived,
            "bbox_diag": r.get("bbox_diag"),
            "source_dataset": r.get("source_dataset", "fusion360_gallery_r1.0.1"),
            "split": r.get("split", "test"),
        })

    missing = [r for r in rows if not Path(r["step_feature_path"]).is_file()]
    missing_pc = [r for r in rows if not Path(r["point_path"]).is_file()]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                           encoding="utf-8")
    print(f"wrote {len(rows)} rows -> {args.output}"
          + (f"   ({dropped} dropped for failed extraction)" if dropped else ""))
    if missing or missing_pc:
        print(f"  ** {len(missing)} step feature files and {len(missing_pc)} clouds are not")
        print("     readable from here. If this is Windows that is expected -- the paths are")
        print("     WSL-side by design -- but re-check from WSL before generating. **")
        for r in (missing or missing_pc)[:3]:
            print(f"       {r['step_feature_path'] if missing else r['point_path']}")
    else:
        print("  all step features and clouds resolve")

    inside = sum(1 for r in rows if (r["bbox_diag"] or 0) <= 134.30)
    print(f"  within corpus scale band: {inside}/{len(rows)} ({100*inside/max(len(rows),1):.1f}%)")
    print("  no ir_path or program_path: IR-level metrics are not computable on external data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
