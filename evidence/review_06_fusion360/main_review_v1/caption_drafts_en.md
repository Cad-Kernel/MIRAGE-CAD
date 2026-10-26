> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Fusion 360 Main-Case Caption Drafts

Author confirmation pending. No new metrics.

## M01 f360_82203_8b9714ce_0000

MIRAGE produces a notched bossed block instead of the thin open-frame reference. Its IoU is higher than CAD-Recode's in this selected case, but both IoUs are low and its CD is worse. This is a relative IoU advantage, not an accurate-reconstruction success.

## M02 f360_43562_004c6cea_0003

Near the paired median MIRAGE IoU, the reference's open triangular frame is not reproduced: MIRAGE returns block-like geometry. CAD-Recode retains more plate and circular-end structure but also differs in the visible openings and silhouette.

## M03 f360_34917_61633e20_0004

In this lower-tail case, MIRAGE generates a capsule rather than the thin planar reference, consistent with its predicted OP_CAPSULE plan and capsule API call. CAD-Recode retains the plate-like envelope; the small reference corner aperture is not visible in its fixed isometric view.

## M04 f360_54501_96041527_0000

MIRAGE fails before producing evaluated geometry: the recorded runtime rejects the length keyword passed to Part.wedge(). The failure is shown explicitly, while the reference and CAD-Recode outputs retain the slab-like geometry. No replacement geometry is rendered.

## M05 f360_121262_f4a03dbc_0000

CAD-Recode retains the circular envelope of the reference but differs in its visible openings. MIRAGE instead generates a bossed block with a different outline and aperture layout; its recorded IoU is zero. This is a global reconstruction mismatch, not an isolated missing-hole diagnosis.

## M06 f360_55031_57f7bdba_0000

The reference's stepped shaft-and-flange profile is closely retained by CAD-Recode. MIRAGE and NN instead produce ellipsoidal bodies without the visible stepped profile. MIRAGE improves both recorded geometry metrics over NN in this case, but this relative gain does not recover the target construction.

## Shared Legend

Columns: reference, CAD-Recode, MIRAGE generated-plan, NN retrieval. Each panel contains fixed isometric and front orthographic views. The shape-normalized series independently centers and scales each shape as in the existing external metrics, removing global scale and translation. A separate reference-world diagnostic uses the declared CAD-Recode DSL conversion and shared union framing. CD is the historical dimensionless squared CD x1000. Unavailable metrics are not zero. Placeholders denote recorded failures, not generated replacement solids.
