# Spec: OCR accuracy improvement and portable ingestion

Status: draft for Product Owner approval. Author: Analyst agent. Extends `exam-browser-with-extracted-values.md` (iteration 1). Basis: `input_data/ocr_improvement_analysis.md`.

## 1. Purpose

Raise the accuracy of the values and indicators extracted from the map images, and remove the macOS-only restriction of the ingestion, without changing the API or the UI.

Measured on the 30-exam gold sample with the iteration-1 pipeline: 75.7% of scored fields correct overall (tuning set 79.1%, holdout set 69.5%); laterality 30/30; `min_thickness_um` 28/30; `max_curvature_a_d` 9/20; `min_curvature_a_d` 21/29; `max_elevation_a_um` 18/30; `max_elevation_p_um` 22/30.

## 2. Decisions already taken by the Product Owner

- Staged approach: stage 1 improves the selection and consensus of values read by the existing OCR; stage 2 adds a recogniser specialised for the Pentacam font.
- New gold sample of 30 exams: 20 `tuning`, 10 `holdout` (`input_data/gold/gold_sample.json`).
- Target: 85% of scored fields correct.
- The new recogniser must run without macOS. macOS Vision stays an optional extra engine where available. (Revised: the portable engine is RapidOCR instead of a custom digit recogniser, see section 6.)

## 3. Scope

In scope: ingestion code under `backend/ingest/`, a second portable OCR engine, test updates, documentation.

Out of scope: API and frontend changes, new indicators, changes to the duplicate rules, changes to the gold sample after approval (except corrections of proven reading errors, recorded in the Changelog).

## 4. Evaluation protocol

- **Metric.** Same as AC8 of iteration 1: for every gold exam, laterality and the five indicators `min_thickness_um`, `max_curvature_a_d`, `min_curvature_a_d`, `max_elevation_a_um`, `max_elevation_p_um` computed by ingestion are compared with the gold lists; an indicator is correct if it equals a listed value; `null` gold entries are not scored.
- **Tuning set.** The Developer may inspect and tune on the 20 `tuning` exams only. Any script or test used during development filters on `set == "tuning"`.
- **Holdout set.** The 10 `holdout` exams are not used for tuning, thresholds, or choices between variants. They are evaluated by the Tester after the Developer hands over, and once by the Developer at the very end for the report, after which no further tuning happens.
- **Reporting.** Every stage reports tuning and holdout scores, broken down by field, in the Changelog entry or the handover note.

## 5. Stage 1: selection and consensus

Operates on the tokens the existing recognition passes already produce. Behaviour to implement and test:

1. **Thickness sequence.** On `ct_a` the printed values form a column of boxes below the centre, increasing from the thinnest point downwards. After clustering, take the accepted values whose positions lie in one column (horizontal positions within ±0.06 of each other) and sort by `y`. A topmost value that is read by fewer passes than required (status `low_confidence`) is promoted to `accepted` when it is smaller than the next value in the column by 5 to 150 µm and lies above it (smaller `y`). No promotion otherwise.
2. **Isolated outliers.** A value on a curvature map (`sag_a`, `sag_p`) that differs by more than 12 D from the median of all other accepted values within 0.15 (fraction of image size) of it, or a value on an elevation map (`elv_a`, `elv_p`, `ec_a`, `ec_p`) that differs by more than 100 µm from that median, gets status `out_of_range`. Maps where fewer than 3 other values are nearby are not checked.
3. **Single-pass readings.** Experiment: lower the agreement needed for `accepted` from 2 of 4 passes to 1 of 4, with the outlier rule (2) as the safeguard. Adopt it only if the tuning-set score improves by at least 2 percentage points; otherwise keep the current threshold. The decision and the numbers are recorded.
4. **Voting detail.** When several readings in one cluster have equal votes, prefer the reading that satisfies the outlier rule relative to the neighbours, then the one with the higher Vision confidence.

Stage 1 is complete when the tuning score and the holdout score are reported. There is no separate pass/fail threshold for stage 1.

## 6. Stage 2: portable OCR engine (revised)

Revision of 2026-10-20, decided by the Product Owner. The first draft of this stage asked for a recogniser specialised for the Pentacam font. A prototype showed that segmenting the 5×9 px characters (merged or broken by JPEG compression, white boxes, bold maxima) is a large research task with an uncertain result, whereas combining many recognition passes by voting already works well. Stage 2 therefore adds a second, portable OCR engine to the same multi-pass voting.

### 6.1 Engines

- **macOS Vision** (existing): passes as in iteration 1, plus extra passes on the four maps that feed the indicators (`ct_a`, `sag_a`, `elv_a`, `elv_p`): `gray6`, `rgb2`, `invert4`, `gray3`, `sharpen4`. The set was chosen by greedy selection on the tuning set.
- **RapidOCR** (`rapidocr-onnxruntime`, installed with pip, runs on macOS, Linux and Windows without system packages): an additional engine producing passes from the same image variants. Its pass set is chosen by greedy selection on the tuning set within the time budget below.
- Passes of all available engines enter `consensus.merge_passes` together; the vote count rule, the plausibility rules of stage 1 and the indicators are unchanged. `confidence` keeps its meaning (share of the passes that ran for the map that read the value).

### 6.2 Portable ingestion

- Ingestion no longer requires macOS. Engine availability: Vision on macOS when the helper compiles; RapidOCR when its package is importable. The environment variable `INGEST_ENGINES` (comma separated, e.g. `vision,rapid`) restricts the engines; `INGEST_DISABLE_VISION=1` is a shortcut for `rapid`.
- Passes run in parallel processes; the wall-clock budget for a full ingestion with the default configuration on the Product Owner's Mac is 20 minutes (R12).
- If no engine is available, ingestion stops with a message that names the requirements and writes nothing.
- No model file and no training step exist; nothing new is shipped with deployments except the Python dependency.

## 7. Acceptance criteria

1. **R1.** `gold_sample.json` has 30 exams, 20 with `set: "tuning"` and 10 with `set: "holdout"`; every exam has laterality and the five indicators (a list or `null`); a test checks the schema.
2. **R2.** Stage 1 rule 1 (thickness sequence) is implemented; unit tests with synthetic tokens cover: promotion of a single-pass topmost value, no promotion when the gap is outside 5-150 µm, no promotion when the value is not above the next one, a column of fewer than 2 values.
3. **R3.** Stage 1 rule 2 (isolated outliers) is implemented; unit tests cover `160` among elevation values below 30, `69.2` among curvature values near 50, a value exactly at the threshold, and a map with fewer than 3 neighbours.
4. **R4.** The single-pass experiment (rule 3) is run, and its tuning score before and after and the decision are recorded in the Changelog.
5. **R5.** The OCR engines are separate modules behind one interface; unit tests cover the RapidOCR token conversion (box to centre fractions, confidence) with a faked engine, the engine selection from `INGEST_ENGINES` / `INGEST_DISABLE_VISION`, and the per-map pass lists (extra passes on the four key maps only).
6. **R6.** The extra Vision passes and the RapidOCR passes are implemented as specified in 6.1; the chosen pass sets and the tuning scores of the candidates are recorded in the Changelog.
7. **R7.** With `INGEST_DISABLE_VISION=1` ingestion builds a complete index (573 exams, none skipped) on the Product Owner's Mac using RapidOCR alone; with no engine available it exits non-zero with a clear message and writes nothing (unit test with faked availability).
8. **R8.** Accuracy with the default configuration, measured by the Tester on the real index: at least 85% of scored fields correct on the tuning set **and** at least 85% on the holdout set; laterality correct for all 30 exams; `min_thickness_um` correct for at least 28 of 30 exams.
9. **R9.** Accuracy with RapidOCR alone (`INGEST_DISABLE_VISION=1`): reported on both sets; the holdout score is at least 75%.
10. **R10.** The duplicate criteria of iteration 1 (AC27, AC28) still pass on the new index.
11. **R11.** All suites of iteration 1 still pass; the real-data acceptance tests use the 30-exam gold sample and the rules of this spec instead of the 10-exam AC8.
12. **R12.** A full ingestion with the default configuration takes at most 20 minutes on the Product Owner's Mac; the time is reported.
13. **R13.** README (running, training, portable ingestion, environment variables) and `CLAUDE.md` (architecture, Changelog) are up to date; no TODO markers, placeholder comments or stubs remain.

If R8 is not reached, the iteration is reported to the Product Owner with the scores by field, not silently adjusted.

## 8. Open questions for the Product Owner

None blocking. Items to confirm when approving:
- The target applies to the default configuration; the RapidOCR-only floor in R9 is a proposal (75% on the holdout set).
