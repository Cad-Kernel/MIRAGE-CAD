# C-EXT1 — cross-dataset evaluation and external comparison: protocol

**Status: protocol, not a runnable script.** Unlike `20_` and `21_`, this one cannot
be written blind, and a script that pretended otherwise would be worse than none.
Three things must be decided by you first (§1), and one of them changes the whole
shape of the run. What follows is the design, the traps, and the pieces that already
exist — so that when the inputs are in place this is assembly rather than invention.

**Why it matters more than anything else left.** It is the only open item that
addresses the review's second blocker, and after the competing-interest declaration
that blocker got *stronger*: the kernel is ours, the corpus is ours, the IR grammar
is ours, and the dataset paper is unpublished. Every number in the paper is
internally produced. One external comparison changes that qualitatively; no amount
of additional internal ablation does.

---

## 1. Three decisions to make before writing code

### 1.1 Which target corpus

| Option | For | Against |
|---|---|---|
| **DeepCAD** | Large, standard, sketch-extrude command sequences, widely used for exactly this comparison | Sketch-extrude only, so most of our 44-operation vocabulary is unusable — see §3.1 |
| **Fusion 360 Gallery** (reconstruction subset) | Richer operation set, real designs, per-step B-Rep | Smaller; licence terms need checking before redistribution of anything derived |

Recommendation: **DeepCAD**, because it is what CAD-Recode reports on, which makes
the external number directly citable rather than re-derived by us.

### 1.2 Which comparison axis — this is the decision that matters

Our system emits Flluma Python; CAD-Recode emits CadQuery; DeepCAD emits its own
command sequence. **The programs are not comparable to each other.** The only common
ground is the executed geometry:

```
point cloud  ->  [system]  ->  program  ->  its own kernel  ->  solid
                                                              -> sample points
                                                              -> CD / F@1% vs reference
```

That comparison is legitimate and is what the reconstruction literature already
uses. Two consequences to accept up front: it evaluates geometry, not construction
quality, so our central claim about *plans* is not what gets compared; and each
system runs on its own kernel, so a small part of any difference is kernel
behaviour rather than model quality. Both belong in the write-up.

### 1.3 Zero-shot or fine-tuned

- **Zero-shot** (train on FllumaOne, test on DeepCAD) is the honest generalisation
  test and the one the review asks for. Expect it to be poor, and expect that to be
  informative — this is also the setting where the NN-IR baselines should finally
  fail, because the index contains nothing from the target distribution. **That
  prediction is the most valuable single thing this run can test**, since NN-IR
  beating us on both internal splits is currently the paper's main negative result.
- **Fine-tuned** (adapt Stage 3/4 on DeepCAD training data) measures whether the
  architecture transfers at all. Stronger numbers, weaker claim.

Recommendation: **report both**, zero-shot first. If only one is affordable, zero-shot.

---

## 2. Pipeline, and what already exists

| Step | Status |
|---|---|
| 1. Obtain DeepCAD; extract per-part point clouds + reference solids | **new** |
| 2. Convert to our manifest schema (`sample_id`, `point_path`, `step_path`, `text`) | **new**, small — see §2.1 |
| 3. Run variant C: prior → prefix → LoRA-IR → LoRA-Code | **exists**: `scripts/gen_predicted_ir.py`, `scripts/gen_code_from_predicted_ir.py` |
| 4. Run NN-IR baselines A/B against the **FllumaOne** train index | **exists**: `13_gen_nnir_baseline.sh` pattern |
| 5. Execute + score geometry | **exists**: `evaluate_geometry_nbest.py` via `evaluate_geometry_nbest.ps1` |
| 6. Run CAD-Recode on the same point clouds | **new**, external repo + its own env |
| 7. Score CAD-Recode's CadQuery output with the *same* metric | **new**, small — see §2.2 |
| 8. Aggregate into one table | **new**, trivial |

Steps 3–5 need no new code: they take explicit paths. The work is 1, 2, 6, 7.

### 2.1 Manifest adapter

Only these fields are actually required by `gen_predicted_ir.py` /
`build_program_prompt` for point-cloud queries: `sample_id`, `point_path`, and
optionally `text`. `step_feature_path` is needed only for STEP queries — **omit STEP
as a query modality for this run** rather than reimplementing our extractor against
another corpus, and say so.

Point clouds must be normalised the way `point_sampling.normalize_xyz` does it
(centre at centroid, divide by max radius) or the encoder sees a different
distribution than it was trained on. This is easy to get wrong because the
*geometry metric* uses unnormalised millimetres while the *encoder* uses the unit
sphere — see §3.2.

### 2.2 Scoring another system's output fairly

`evaluate_geometry_nbest.py` computes CD in mm² on unnormalised geometry against a
reference cloud. To score CAD-Recode the same way, execute its CadQuery program in
its own environment, export STEP, sample the same number of points (1,024, matching
`--point-count`), and feed the resulting cloud through the same
`symmetric_chamfer`. **Do not compare our CD against a CD reported in CAD-Recode's
paper** — different sampling density, different normalisation, and possibly a
different CD convention (ours carries the ½ factors; many papers' do not). Re-score
both under one harness or the comparison is meaningless.

---

## 3. Traps, in the order they will bite

### 3.1 Vocabulary mismatch is a confound, not a bug — but must be separated

Our IR vocabulary is 44 FllumaOne operations (Appendix `app:ir_grammar`), and about
half are template-specific composites (`OP_STANDOFF_ARRAY_PLATE`,
`OP_SENSOR_MOUNT_PLATE`, …). DeepCAD parts are sketch-extrude. So a weak zero-shot
result could mean the model does not generalise, **or** that the target geometry is
inexpressible in the vocabulary it learned. These are different findings.

Separate them by reporting an **expressibility ceiling**: for a sample of DeepCAD
parts, have the *reference* geometry rebuilt using only our operation vocabulary
(by hand for ~20 parts is enough) and report what fraction is reachable at all. A
zero-shot Build of 30% against a ceiling of 45% is a very different paper from 30%
against a ceiling of 95%.

### 3.2 Two normalisations, one of which is invisible

Encoder input is unit-sphere normalised; geometry scoring is unnormalised mm. Both
are correct in our pipeline and were verified. On a new corpus with different part
scales, forgetting the first silently degrades the encoder, and forgetting the
second silently changes CD by orders of magnitude. Assert both explicitly in the
adapter.

### 3.3 The NN-IR index must not be rebuilt on the target corpus

The point of A/B here is that the index holds **FllumaOne** plans while queries come
from DeepCAD. Rebuilding the index on DeepCAD would destroy the experiment. Keep
`outputs/align_25k/train_ir_index.npz`.

### 3.4 Batched decoding

`comp_11`/`comp_13` used `--batch-size 16`; every other table used 1, and they are
not bit-identical (§6.4). Pick one for this run, use it for every variant, and state
it.

### 3.5 Licence

Check redistribution terms before committing any derived DeepCAD artefact to this
repository. Paths and scripts are fine; extracted geometry may not be.

---

## 4. The table this produces

```
Corpus     Method                     Input   Build %   Median CD   F@1%
FllumaOne  C: Generated IR            point    55.4       60.25      3.7     <- have
FllumaOne  A/B: NN-IR substitution    point    95-96        --         --     <- have
DeepCAD    C: Generated IR (0-shot)   point      ?          ?          ?
DeepCAD    A/B: NN-IR (FllumaOne idx) point      ?          ?          ?      <- the key row
DeepCAD    CAD-Recode (published wts) point      ?          ?          ?
DeepCAD    C: fine-tuned on DeepCAD   point      ?          ?          ?      <- optional
```

**Write it up whichever way it comes out.** We do not need to win. What the paper
needs is one row produced by someone else's system on someone else's data under our
harness, plus the NN-IR row that tests whether retrieval finally breaks when the
index is off-distribution. If NN-IR collapses there while variant C degrades
gracefully, that is the compositional-generalisation claim the paper currently has
to withdraw (§7.7), recovered on a benchmark that is not ours to shape. If NN-IR
holds up even across corpora, that is a strong and publishable negative result about
retrieval baselines in this field, and it is worth more than another internal
ablation.

---

## 5. Effort

2–4 weeks. Roughly: 3–5 days for steps 1–2 and the normalisation asserts, 2–3 days
to stand up CAD-Recode and its scoring, 2 days of runs, 2 days for the
expressibility ceiling, the rest for the fine-tuned arm and writing. The zero-shot
arm alone, without fine-tuning, is about half that and already discharges the
blocker.
