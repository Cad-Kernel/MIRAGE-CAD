# Third-party material, data and checkpoints

The existing root 0BSD license covers project-authored code. It does not grant additional rights over
datasets, model weights, upstream papers/code or third-party-derived assets.

The full FllumaOne training corpus and complete corpus manifests are not copied into this Git tree.
Fixed IDs, construction manifests, hashes, generated results and case evidence are retained separately.
Model/checkpoint payloads are catalogued by hash rather than embedded in Git; obtain the stated base
model and required adapters under their own terms. Flluma native runtime redistribution/build access
remains a separate reproduction requirement and is not solved by a source snapshot.

Fusion-derived inputs/reference assets retain the source dataset's terms. CAD-Recode is obtained from
its official source/model repository under its stated terms (currently CC BY-NC 4.0); neither project
0BSD nor this document re-licenses it. Raw upstream implementation files/full papers are reference-only
where identified; their URLs/versions/hashes remain in the source metadata.

GenCAD-3D code and dataset cards have separate licensing from its weight repository, whose captured
card did not declare a license. Text2CAD declares CC BY-NC-SA 4.0 and an access gate. Pointer-CAD source
availability does not establish availability/license of a checkpoint. CADBench retains constituent
dataset licenses. See `evidence/cpu_audits/external_baselines_v1` for the scoped source audit.

This local integration is not a declaration that every derived asset is cleared for unrestricted
redistribution. Review data/runtime terms and final anonymous access before publishing or pushing.
