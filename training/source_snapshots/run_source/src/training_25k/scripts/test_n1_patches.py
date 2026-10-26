"""Self-test for the N1 / N1b patches to gen_predicted_ir.py.

No GPU, no data, no model download -- pure logic checks on the parts that would
otherwise fail SILENTLY and produce plausible-looking wrong results:

  * the default (--prefix-source prior, --num-plans 1) must still be greedy with no
    extra output fields, i.e. bit-identical behaviour to before the patch;
  * zero_prefix must bypass Psi, and zero_latent must NOT (Psi(0) is a learned
    constant, because Psi starts with a LayerNorm);
  * the global shuffle must be a derangement -- no row may keep its own latent, which
    a within-batch permutation would not guarantee;
  * generate() groups sequences by input row, so plan extraction must index as
    row_i*K + plan_i; zip(batch_rows, gen) misaligns as soon as K > 1.

Run from the source root:

    python training_25k/scripts/test_n1_patches.py

Exit code 0 = all pass.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "gen_predicted_ir.py"
fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def main() -> int:
    if not SRC.is_file():
        print(f"cannot find {SRC}")
        return 2
    text = SRC.read_text(encoding="utf-8")
    print(f"checking {SRC}\n")

    # --- 1. the five modes exist and default to prior ---------------------
    check("--prefix-source declared", "--prefix-source" in text)
    for mode in ("prior", "oracle_ir", "zero_prefix", "zero_latent", "shuffled"):
        check(f"mode {mode} handled in the generation loop",
              re.search(rf'prefix_source\s*==\s*["\']{mode}["\']', text) is not None
              or mode == "prior")
    m = re.search(r'--prefix-source[\s\S]{0,400}?default="(\w+)"', text)
    check("--prefix-source defaults to prior", bool(m) and m.group(1) == "prior",
          f"got {m.group(1) if m else 'no default found'}")
    m = re.search(r'"--num-plans",\s*type=int,\s*default=(\d+)', text)
    check("--num-plans defaults to 1", bool(m) and m.group(1) == "1",
          f"got {m.group(1) if m else 'not found'}")

    # --- 2. zero_prefix bypasses Psi, zero_latent does not ---------------
    zp = re.search(r'prefix_source\s*==\s*["\']zero_prefix["\'][\s\S]{0,600}?(?=\n\s{16}el|\n\s{16}else)', text)
    zp_body = zp.group(0) if zp else ""
    check("zero_prefix builds zeros directly (bypasses Psi)",
          "torch.zeros(" in zp_body and "prefix_adapter(" not in zp_body,
          "zero_prefix must NOT call prefix_adapter")
    zl = re.search(r'prefix_source\s*==\s*["\']zero_latent["\'][\s\S]{0,600}?(?=\n\s{16}el)', text)
    zl_body = zl.group(0) if zl else ""
    check("zero_latent DOES call Psi on a zero latent",
          "prefix_adapter(" in zl_body and "zeros_like" in zl_body,
          "zero_latent must be Psi(0), not zeros")

    # --- 3. shuffle is global and deranged --------------------------------
    check("shuffle pre-encodes all rows before the loop",
          "pre-encoding" in text and "randperm" in text)
    check("shuffle asserts no fixed point",
          "fixed point" in text or "fixed" in text and "perm ==" in text)

    # --- 4. plan indexing is explicit, not zip ---------------------------
    check("plans indexed as row_i*K + plan_i",
          re.search(r"gen\[\s*row_i\s*\*\s*K\s*\+\s*plan_i\s*\]", text) is not None)
    # Strip comments first: the file deliberately *mentions* the old buggy form in a
    # comment explaining why it was replaced, and a naive substring test flags that.
    code_only = "\n".join(l.split("#", 1)[0] for l in text.splitlines())
    check("no zip(batch_rows, gen) left in executable code",
          "zip(batch_rows, gen)" not in code_only,
          "zip misaligns when num_return_sequences > 1")
    check("sequence count asserted", "gen.shape[0] == len(batch_rows) * K" in text)

    # --- 5. ablation outputs are tagged ----------------------------------
    check("non-prior runs tag ablation_only", '"ablation_only"' in text)
    check("non-prior runs warn on stdout", "[ABLATION]" in text)
    check("oracle_ir warns that it reads ground truth",
          "READS THE GROUND-TRUTH" in text or "READS GROUND TRUTH" in text)

    # --- 6. --point-evidence: default must reproduce published runs -------
    m = re.search(r'"--point-evidence"[\s\S]{0,300}?default="(\w+)"', text)
    check("--point-evidence defaults to off (published runs stay reproducible)",
          bool(m) and m.group(1) == "off",
          f"got {m.group(1) if m else 'not found'}")
    check("point_xyz is gated on --point-evidence, not hardcoded None",
          "point_xyz=None) for row in batch_rows" not in code_only
          and "point_evidence" in text,
          "the prompt builder must receive points when the flag is on")
    # encode_query now returns (z, point_xyz). Every caller must unpack, or the
    # shuffled pre-encode pass silently feeds a tuple to prior() and dies mid-run.
    bad = [l.strip() for l in code_only.splitlines()
           if "encode_query(" in l and "def encode_query" not in l
           and "[0]" not in l and "encoded = " not in l]
    check("every encode_query() caller unpacks the (z, point_xyz) tuple",
          not bad, f"unpatched call site: {bad[0] if bad else ''}")

    # --- 7. behavioural simulation of the derangement --------------------
    try:
        import torch
    except ImportError:
        print("\n  (torch unavailable -- skipping the numeric derangement check)")
    else:
        for n in (2, 3, 8, 100):
            g = torch.Generator().manual_seed(1234)
            perm = torch.randperm(n, generator=g)
            fixed = (perm == torch.arange(n)).nonzero(as_tuple=True)[0]
            for i in fixed.tolist():
                j = (i + 1) % n
                perm[i], perm[j] = perm[j].clone(), perm[i].clone()
            ok = not bool((perm == torch.arange(n)).any())
            check(f"derangement holds for n={n}", ok)

    print()
    if fails:
        print(f"{len(fails)} FAILED: " + ", ".join(fails))
        print("Do not start the ablation runs until these pass.")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
