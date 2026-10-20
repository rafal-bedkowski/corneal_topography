# Spec: OCR accuracy improvement and portable ingestion

Status: draft for Product Owner approval. Author: Analyst agent. Extends `exam-browser-with-extracted-values.md` (iteration 1). Basis: `input_data/ocr_improvement_analysis.md`.

## 1. Purpose

Raise the accuracy of the values and indicators extracted from the map images, and remove the macOS-only restriction of the ingestion, without changing the API or the UI.

Measured on the 30-exam gold sample with the iteration-1 pipeline: 75.7% of scored fields correct overall (tuning set 79.1%, holdout set 69.5%); laterality 30/30; `min_thickness_um` 28/30; `max_curvature_a_d` 9/20; `min_curvature_a_d` 21/29; `max_elevation_a_um` 18/30; `max_elevation_p_um` 22/30.

## 2. Decisions already taken by the Product Owner

- Staged approach: stage 1 improves the selection and consensus of values read by the existing OCR; stage 2 adds a recogniser specialised for the Pentacam font.
- New gold sample of 30 exams: 20 `tuning`, 10 `holdout` (`input_data/gold/gold_sample.json`).
- Target: 85% of scored fields correct.
- The new recogniser must run without macOS. macOS Vision stays an optional extra pass where available.

## 3. Scope

In scope: ingestion code under `backend/ingest/`, a training command for the digit recogniser, test updates, documentation.

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

## 6. Stage 2: specialised digit recogniser

### 6.1 Interface

A module `ingest/glyphs/` exposes `recognise_glyph_tokens(image) -> list[RawToken]`, with the same token structure as the Vision output (`text`, `confidence`, `x`, `y`). Its tokens enter `consensus.merge_passes` as additional passes, so the consensus, rules, indicators and duplicate detection stay unchanged. Its output must be deterministic for a given image and model.

### 6.2 Recognition

- Locate the printed numbers and split them into characters using classical image processing (thresholding for dark text, for white text on dark areas, and for the bold text), without a general-purpose OCR engine.
- Classify the characters `0-9`, `.`, `+`, `-`. Characters outside this set are ignored.
- Rebuild numbers by grouping characters by line and spacing, and report one token per number with its centre.
- The recogniser must read the three renderings of the font: black on a coloured background (normal), white on dark areas, and bold (the maximum curvature printed without a box).

### 6.3 Training

- Command `python -m ingest.train`. It builds training crops from values on which at least 3 of the 4 Vision passes agree and which pass the rules in iteration-1 spec 4.5, trains the classifier, and writes the model to `EXAMS_MODEL_PATH` (default `backend/models/glyphs.npz`, gitignored).
- Training is deterministic (fixed seeds) and takes no more than 10 minutes. It needs macOS only because it reads the Vision output; it uses the exams in the index, never the holdout exams of the gold sample.
- A held-out split of the crops (20%) is used to report character accuracy; the number is printed at the end of training.
- Dependencies are limited to `numpy`, `Pillow` and, if needed, `scikit-learn`. Heavy frameworks (e.g. `torch`) need Product Owner approval.

### 6.4 Portable ingestion

- Ingestion no longer requires macOS. Recognition passes: the glyph recogniser always; macOS Vision passes only when the platform is macOS and the helper compiles. The environment variable `INGEST_DISABLE_VISION=1` forces the glyph recogniser alone.
- If the model file is missing, ingestion stops with a message that names the training command. On a machine without macOS the model must have been trained elsewhere and copied; the README documents this.
- The index format is unchanged. `confidence` keeps the iteration-1 meaning (share of passes that read the value); the number of passes is the number of passes that ran.

## 7. Acceptance criteria

1. **R1.** `gold_sample.json` has 30 exams, 20 with `set: "tuning"` and 10 with `set: "holdout"`; every exam has laterality and the five indicators (a list or `null`); a test checks the schema.
2. **R2.** Stage 1 rule 1 (thickness sequence) is implemented; unit tests with synthetic tokens cover: promotion of a single-pass topmost value, no promotion when the gap is outside 5-150 µm, no promotion when the value is not above the next one, a column of fewer than 2 values.
3. **R3.** Stage 1 rule 2 (isolated outliers) is implemented; unit tests cover `160` among elevation values below 30, `69.2` among curvature values near 50, a value exactly at the threshold, and a map with fewer than 3 neighbours.
4. **R4.** The single-pass experiment (rule 3) is run, and its tuning score before and after and the decision are recorded in the Changelog.
5. **R5.** `ingest/glyphs/` implements 6.1 and 6.2; unit tests render synthetic digit strings in several sizes (black on colour, white on dark, bold) and check that the tokens and positions are recovered.
6. **R6.** `python -m ingest.train` is deterministic: two runs on the same index give identical model files; it prints the character accuracy on the held-out crops, which is at least 98%.
7. **R7.** With `INGEST_DISABLE_VISION=1` and the model present, ingestion builds a complete index on the Product Owner's Mac (573 exams, no skipped). A unit test covers the platform logic with a faked platform; with the model missing, ingestion exits non-zero naming the training command and writes nothing.
8. **R8.** Accuracy with the default configuration (glyph recogniser plus Vision on macOS), measured by the Tester on the real index: at least 85% of scored fields correct on the tuning set **and** at least 85% on the holdout set; laterality correct for all 30 exams; `min_thickness_um` correct for at least 28 of 30 exams.
9. **R9.** Accuracy with the glyph recogniser alone (`INGEST_DISABLE_VISION=1`): reported on both sets; the holdout score is at least 75%.
10. **R10.** The duplicate criteria of iteration 1 (AC27, AC28) still pass on the new index.
11. **R11.** All suites of iteration 1 still pass; the real-data acceptance tests use the 30-exam gold sample and the rules of this spec instead of the 10-exam AC8.
12. **R12.** A full ingestion with the default configuration takes at most 20 minutes on the Product Owner's Mac; the time is reported.
13. **R13.** README (running, training, portable ingestion, environment variables) and `CLAUDE.md` (architecture, Changelog) are up to date; no TODO markers, placeholder comments or stubs remain.

If R8 is not reached, the iteration is reported to the Product Owner with the scores by field, not silently adjusted.

## 8. Open questions for the Product Owner

None blocking. Items to confirm when approving:
- The trained model file is not committed (it is produced from the dataset, whose license is unknown); it is gitignored and shipped with deployments like the index.
- A model file is needed on a Linux server; training stays a macOS step because it uses Vision output as labels.
- The target applies to the default configuration; the glyph-only floor in R9 is a proposal (75% on the holdout set).
