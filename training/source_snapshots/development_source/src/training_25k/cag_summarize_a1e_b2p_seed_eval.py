from __future__ import annotations

import argparse
import hashlib
import json
import statistics as st
from datetime import datetime, timezone
from math import comb
from pathlib import Path


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pct(num: int | float, den: int | float) -> float:
    return 100.0 * num / den if den else 0.0


def two_sided_sign(k: int, n: int) -> float:
    if n <= 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def execution_stats(path: Path) -> dict:
    rows = read_jsonl(path)
    total = len(rows)
    out = {"path": str(path), "sha256": sha256_file(path), "n": total}
    for key in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"):
        count = sum(1 for r in rows if r.get(key))
        out[key] = count
        out[f"{key}_pct"] = pct(count, total)
    return out


def geometry_stats(path: Path, expected_rows: int) -> tuple[dict, dict[str, dict]]:
    rows = read_jsonl(path)
    scored = {}
    counts = {
        "path": str(path),
        "sha256": sha256_file(path),
        "n": len(rows),
        "syntax_ok": 0,
        "exec_ok": 0,
        "build_ok": 0,
        "solid_valid": 0,
        "step_export_ok": 0,
        "pointcloud_scored": 0,
    }

    cds = []
    f1s = []
    unconditional_f1s = []

    for r in rows:
        cands = r.get("candidate_results") or []
        c = cands[0] if cands else {}

        for key in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"):
            if c.get(key):
                counts[key] += 1

        cd = c.get("cd")
        f1 = c.get("f_score_1pct")
        unconditional_f1s.append(float(f1) if f1 is not None else 0.0)

        if c.get("step_export_ok") and cd is not None:
            counts["pointcloud_scored"] += 1
            cds.append(float(cd))
            if f1 is not None:
                f1s.append(float(f1))
            scored[r["sample_id"]] = {
                "cd": float(cd),
                "f1": float(f1) if f1 is not None else None,
            }

    for key in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok", "pointcloud_scored"):
        counts[f"{key}_pct"] = pct(counts[key], expected_rows)

    counts["median_cd"] = st.median(cds) if cds else None
    counts["median_f1"] = st.median(f1s) if f1s else None
    counts["unconditional_f1_mean"] = st.mean(unconditional_f1s) if unconditional_f1s else None
    counts["unconditional_f1_median"] = st.median(unconditional_f1s) if unconditional_f1s else None
    return counts, scored


def paired_stats(a: dict[str, dict], b: dict[str, dict]) -> dict:
    both = sorted(set(a) & set(b))
    if not both:
        return {"jointly_scoreable_n": 0}

    a_cd = [a[sid]["cd"] for sid in both]
    b_cd = [b[sid]["cd"] for sid in both]
    a_f1 = [a[sid]["f1"] for sid in both if a[sid]["f1"] is not None]
    b_f1 = [b[sid]["f1"] for sid in both if b[sid]["f1"] is not None]

    wins = sum(1 for sid in both if a[sid]["cd"] < b[sid]["cd"])
    ties = sum(1 for sid in both if a[sid]["cd"] == b[sid]["cd"])

    return {
        "jointly_scoreable_n": len(both),
        "A1E_paired_median_cd": st.median(a_cd),
        "B2P_paired_median_cd": st.median(b_cd),
        "A1E_paired_median_f1": st.median(a_f1) if a_f1 else None,
        "B2P_paired_median_f1": st.median(b_f1) if b_f1 else None,
        "A1E_cd_wins": wins,
        "non_tied_pairs": len(both) - ties,
        "sign_test_p": two_sided_sign(wins, len(both) - ties),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--scratch-root", type=Path, default=Path(r"__DEV_ROOT__\scratch"))
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--expected-rows", type=int, default=500)
    args = ap.parse_args()

    summary = {
        "purpose": "CAG frozen A1E/B2P seed evaluation summary",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "expected_rows": args.expected_rows,
        "arms": {},
    }
    scored = {}

    for arm in ("A1E", "B2P"):
        label = f"step_{arm}_s{args.seed}"
        exec_rows = args.scratch_root / f"exec_e1_{label}" / "execution_rows.jsonl"
        geom_rows = args.scratch_root / f"geom_e1_{label}" / "geometry_nbest_rows.jsonl"

        if not exec_rows.exists():
            raise FileNotFoundError(f"missing execution rows: {exec_rows}")
        if not geom_rows.exists():
            raise FileNotFoundError(f"missing geometry rows: {geom_rows}")

        geom, scored_arm = geometry_stats(geom_rows, args.expected_rows)
        summary["arms"][arm] = {
            "execution": execution_stats(exec_rows),
            "geometry": geom,
        }
        scored[arm] = scored_arm

    summary["paired"] = paired_stats(scored["A1E"], scored["B2P"])

    print(f"\nCAG frozen A1E/B2P seed {args.seed}")
    print("arm   n   build    STEP     scored   med CD     med F@1   uncond mean F@1")
    for arm in ("A1E", "B2P"):
        g = summary["arms"][arm]["geometry"]
        med_cd = g["median_cd"] if g["median_cd"] is not None else float("nan")
        med_f1 = 100 * g["median_f1"] if g["median_f1"] is not None else float("nan")
        uncond_f1 = 100 * g["unconditional_f1_mean"] if g["unconditional_f1_mean"] is not None else float("nan")
        print(
            f"{arm:<4} {g['n']:>3} "
            f"{g['build_ok_pct']:>6.1f}% "
            f"{g['step_export_ok_pct']:>6.1f}% "
            f"{g['pointcloud_scored']:>6}/{args.expected_rows:<3} "
            f"{med_cd:>8.3f} "
            f"{med_f1:>9.2f}% "
            f"{uncond_f1:>13.2f}%"
        )

    p = summary["paired"]
    print("\npaired on jointly scoreable subset")
    print(f"  n = {p['jointly_scoreable_n']}")
    if p["jointly_scoreable_n"]:
        print(f"  paired median CD: A1E {p['A1E_paired_median_cd']:.3f} vs B2P {p['B2P_paired_median_cd']:.3f}")
        print(f"  paired median F@1: A1E {100 * p['A1E_paired_median_f1']:.2f}% vs B2P {100 * p['B2P_paired_median_f1']:.2f}%")
        print(f"  A1E closer on {p['A1E_cd_wins']}/{p['non_tied_pairs']} non-tied pairs; sign-test p={p['sign_test_p']:.4g}")

    out_json = args.out_json or (args.scratch_root / f"cag_seed_{args.seed}_a1e_b2p_eval_summary.json")
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())