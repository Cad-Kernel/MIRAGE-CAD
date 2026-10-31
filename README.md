# MIRAGE-CAD: anonymous review artifact download

This transport contains the complete sealed anonymous source-and-evidence
archive. It is a delivery format, not a new experiment or a reduced evidence
selection. All source versions, split/audit files, raw-result records and
qualitative assets in the sealed v4 archive are retained.

## Download and verify

1. Download this repository as a ZIP using the anonymous review page.
2. Extract it into a new directory and open a terminal in the directory
   containing this README, the four bundle ZIPs, and the verification script.
3. With Python 3.9 or later, run:

```bash
python3 verify_and_unpack.py
python3 MIRAGE-CAD/tools/verify_revision_artifact.py
```

On Windows, `python` may be used instead of `python3`. No additional Python
packages are required for these checks.

The first command verifies every transport part, reconstructs the sealed
archive, checks its SHA256, and extracts it. The second command is the
artifact's own CPU-only verifier: it checks 9,980 distributed files and 16
raw-result row-count records. Neither command loads a model or executes CAD.
The reconstructor refuses to overwrite an existing MIRAGE-CAD directory.

The four bundle ZIPs each contain one binary slice of the sealed archive;
do not extract or concatenate their payloads manually. Their order and hashes
are declared in `transport_manifest.json`. The reconstructed archive SHA256 is:

```
14aa7db14cc33943a25539d7f75e15bf13d9c6a9555d697e055e7c1e668036e4
```

## Scope

Start with `MIRAGE-CAD/README.md`, `evidence/README.md`, and `training/README.md`
after extraction. Full model payloads, the complete training corpus and the
native CAD runtime are not bundled; resource and licensing omissions are
documented in the extracted project. Integrity checks are not end-to-end
reproduction, semantic anonymity certification, or evidence of human editing
benefit. Original and anonymized-copy hashes remain distinct.

The archived experiments retain their recorded confounds and unfavorable
results. This download format does not change source code, training examples,
predictions, metrics, or scientific conclusions.
