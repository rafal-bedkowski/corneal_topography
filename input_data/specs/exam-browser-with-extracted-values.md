# Spec: Exam browser with values extracted from map images

Status: draft for Product Owner approval. Author: Analyst agent. Depends on: `input_data/dataset_review.md`.

## 1. Purpose

Let a user browse the 573 exams of the Kaggle keratoconus dataset, see the seven Pentacam map images of each exam, see the numeric values printed on those maps (extracted automatically with OCR), see a small set of indicators derived from those values, and compare the three classes (Normal, Keratoconus, Suspect) statistically.

The dataset contains images only. All numeric values are therefore OCR output of burned-in text and are approximate. The application must never present them as clinical measurements.

## 2. Scope

In scope:
1. Ingestion: an offline, macOS-only command that builds a local JSON index of all exams and their extracted values.
2. Backend API (FastAPI) serving exams, map images and statistics from the index.
3. Frontend (Next.js) with three views: exam list, exam detail, statistics.

Out of scope: authentication, uploading new exams, editing or correcting values, computing true clinical indices (K1, K2, Kmax, BAD-D, KISA%), diagnosis or classification of exams, exam-to-exam comparison view, 3D surfaces, deployment of the OCR step to Linux.

## 3. Decisions already taken by the Product Owner

- Scope includes numeric analysis: values from maps, derived indicators, class comparison.
- OCR runs offline on the Product Owner's Mac with macOS Vision; the backend only serves the resulting JSON. Errors are accepted but must be flagged.
- The dataset and the JSON index are not committed to git (unknown dataset license).
- `EC_A` / `EC_P` are elevation maps with a different reference surface.
- Suspected duplicate exams (same eye exported twice, see `dataset_review.md` section 6) are flagged and excluded from the statistics.

## 4. Data model

### 4.1 Exam identifier

`exam_id` = `<split>/<label>/<case>` where:
- `split` ∈ `train_validation`, `independent_test`
- `label` ∈ `normal`, `keratoconus`, `suspect`
- `case` = integer from the folder name `case<N>`

Example: `train_validation/keratoconus/14`.

### 4.2 Map types

| `map_type` | File suffix | Title shown in UI | Unit |
|------------|-------------|-------------------|------|
| `sag_a` | `Sag_A` | Axial curvature, anterior | D |
| `sag_p` | `Sag_P` | Axial curvature, posterior | D |
| `elv_a` | `Elv_A` | Elevation, anterior | µm |
| `elv_p` | `Elv_P` | Elevation, posterior | µm |
| `ec_a` | `EC_A` | Elevation (alt. reference), anterior | µm |
| `ec_p` | `EC_P` | Elevation (alt. reference), posterior | µm |
| `ct_a` | `CT_A` | Corneal thickness | µm |

### 4.3 Extracted value

```
{
  "text": "43.1",            raw OCR string
  "value": 43.1,            parsed number, null when not parseable
  "confidence": 0.75,       share of recognition passes that read this value, 0..1 (see 4.5)
  "x": 0.62, "y": 0.41,     centre of the text box, fraction of image width/height, origin top-left
  "status": "accepted"      accepted | low_confidence | out_of_range | rejected
}
```

### 4.4 Exam record (index entry)

```
{
  "exam_id": "...", "split": "...", "label": "...", "case": 14,
  "laterality": "OD" | "OS" | "unknown",
  "maps": { "<map_type>": { "file": "<relative path under dataset dir>", "values": [ExtractedValue, ...] } },
  "indicators": { ...see 4.6 },
  "possible_duplicate_of": ["<exam_id>", ...],      empty list when none (see 4.8)
  "stats_excluded": false,                         true when excluded from statistics
  "stats_exclusion_reason": null | "duplicate" | "duplicate_conflicting_labels"
}
```

### 4.5 Value acceptance rules (applied at ingestion)

Perimeter labels (angle labels such as `90°`, `330°`, axis letters `T`, `N`, `OD`, `OS`, and the `9mm` caption) are not map values and get status `rejected`. They are identified by (a) a degree sign or a letter-only / `9mm` text, and (b) position: text centred outside the central map circle, i.e. farther from the image centre than 0.42 of the image width. Both rules apply.

Remaining numeric strings are validated per map type:

| Map types | Accepted format | Accepted range |
|-----------|-----------------|----------------|
| `sag_a`, `sag_p` | decimal with exactly one fractional digit, optional leading minus | anterior 30.0–75.0 D; posterior −15.0 to −3.0 D |
| `elv_a`, `elv_p`, `ec_a`, `ec_p` | integer with explicit sign (`+` or `−`) or `0` | −300 to +300 µm |
| `ct_a` | integer of 3 digits | 300–900 µm |

- Format or range violation → `out_of_range`.
- Confidence below 0.5 → `low_confidence` (checked first). Vision's own confidence is almost always 1.0 and says little, so the application runs several recognition passes over each image (different scale and contrast treatment) and combines them: tokens at the same position form one cluster, the value most passes agree on wins, and `confidence` is the share of passes that read it. A value read by fewer than half of the passes is `low_confidence`.
- Padding characters (`.`, `-`, `*`, `•`, `:`) that the OCR reads around thickness and curvature values (box borders) are stripped before the format check; posterior curvature keeps a leading minus. Elevation values keep the strict format.
- All others → `accepted`.

Confidence alone is not sufficient: the test run produced wrong values at confidence 1.0, so format and range rules are mandatory.

### 4.6 Derived indicators (per exam)

These are computed only from `accepted` values and are named so as not to claim clinical equivalence. Each is `null` when no accepted value exists.

| Indicator | Definition |
|-----------|------------|
| `min_thickness_um` | minimum accepted value on `ct_a` |
| `max_curvature_a_d` | maximum accepted value on `sag_a` |
| `min_curvature_a_d` | minimum accepted value on `sag_a` |
| `curvature_spread_a_d` | `max_curvature_a_d − min_curvature_a_d` |
| `max_elevation_a_um` | maximum accepted value on `elv_a` |
| `max_elevation_p_um` | maximum accepted value on `elv_p` |

The UI labels them "visible max curvature", "visible min thickness", etc., with a tooltip that they derive from values printed on the image, not from the measurement data.

### 4.7 Laterality

Read from the `OD` / `OS` text found on the exam's maps. Several maps are inspected (not only `sag_a`, because some maps carry no label); the exam gets the value found on the majority of its maps. If no map yields a label, or maps disagree with no majority, the value is `unknown`.

### 4.8 Duplicate detection

Run at ingestion, after value acceptance (4.5), on `ct_a` accepted values only.

1. Two exams are possible duplicates when both have at least 4 accepted `ct_a` values, they share at least 4 identical accepted values, and the shared values make up at least 60% of the union of their accepted values. Laterality must not contradict (equal, or at least one `unknown`).
2. Duplicate relations are transitive: exams linked directly or through others form a group. Each member lists the other members in `possible_duplicate_of`.
3. Statistics exclusion, per group:
   - All members have the same label: exactly one member stays in the statistics, the one in `train_validation` before `independent_test`, then with the lowest case number. The others get `stats_excluded: true`, reason `duplicate`.
   - Members have different labels: the label is ambiguous, so **all** members get `stats_excluded: true`, reason `duplicate_conflicting_labels`.
4. Excluded exams stay in listings and detail views; only the statistics ignore them.
5. The ingestion summary prints the number of groups, of excluded exams per reason, and the list of groups.

Reference result on the provided dataset: the Analyst's OCR run found these 12 pairs (`it` = `independent_test`, `tv` = `train_validation`): `it/keratoconus/3 = it/suspect/7`, `it/keratoconus/47 = it/suspect/41`, `it/normal/25 = it/suspect/39`, `it/normal/26 = it/suspect/40`, `tv/normal/125 = tv/suspect/75`, `it/suspect/4 = tv/suspect/109`, `tv/keratoconus/78 = tv/keratoconus/84`, `tv/keratoconus/79 = tv/keratoconus/85`, `tv/normal/127 = tv/normal/42`, `tv/normal/142 = tv/normal/94`, `tv/normal/2 = tv/normal/53`, `tv/suspect/115 = tv/suspect/116`. More groups may exist.

## 5. Ingestion (offline command)

Behaviour:
1. Read the dataset directory (environment variable `DATASET_DIR`, default `dataset/archive`).
2. Discover exams under `Train_Validation sets/Train_Validation sets/<Class>/case<N>` and `Independent Test Set/Independent Test Set/<Class>/case<N>`. Ignore `.DS_Store` and any other non-matching entry.
3. Per exam, require exactly the 7 expected files; an exam with missing or unexpected files is skipped and reported.
4. Upscale each image 4× (Lanczos) and run macOS Vision text recognition (accurate mode, no language correction).
5. Apply the rules in 4.5 and compute 4.6 and 4.7.
6. Write the index to `EXAMS_INDEX_PATH` (default `backend/data/exams.json`) atomically (write to a temporary file, then rename).
7. Print a summary: exams found, exams skipped with reasons, number of values per status, exams without laterality.

Requirements: runs only on macOS; on any other platform it exits with a clear message. Re-running replaces the index. The command is idempotent.

## 6. Backend API

Base path `/api`. All responses JSON except images. Errors use `{"detail": "<message>"}` with the matching HTTP status.

| Method and path | Description |
|-----------------|-------------|
| `GET /api/health` | `{"status": "ok", "exams": <count>}`. Returns 503 with a message when the index is missing or unreadable. |
| `GET /api/exams` | Paginated list. Query: `split`, `label`, `laterality` (each optional, one value), `page` (≥1, default 1), `page_size` (1–100, default 24), `sort` ∈ `case`, `min_thickness` (default `case`), `order` ∈ `asc`, `desc`. Response: `{"total": n, "page": p, "page_size": s, "items": [ExamSummary]}`. |
| `GET /api/exams/{split}/{label}/{case}` | Full exam record per 4.4, with map image URLs instead of file paths. 404 if unknown. |
| `GET /api/exams/{split}/{label}/{case}/maps/{map_type}/image` | The JPEG file. 404 if unknown. Path components are validated against the index; no file path is built from raw user input. |
| `GET /api/stats` | Class comparison per 6.1. Optional query `split`. |

`ExamSummary`: `exam_id, split, label, case, laterality, min_thickness_um, max_curvature_a_d, possible_duplicate_of, stats_excluded, thumbnail_url` (thumbnail = `sag_a` image).

Invalid query values (unknown `split`, `label`, `map_type`, out-of-range `page_size`) return 422 or 404 as FastAPI/Pydantic standard behaviour.

### 6.1 Statistics response

```
{
  "classes": [
    {
      "label": "normal",
      "exams": 195,
      "excluded_duplicates": 5,
      "laterality": {"OD": n, "OS": n, "unknown": n},
      "indicators": {
        "min_thickness_um": {"n": 190, "mean": ..., "median": ..., "std": ..., "min": ..., "max": ...},
        "max_curvature_a_d": {...}, "min_curvature_a_d": {...}, "curvature_spread_a_d": {...},
        "max_elevation_a_um": {...}, "max_elevation_p_um": {...}
      },
      "histograms": { "min_thickness_um": {"bin_width": 20, "bins": [{"from": 400, "count": n}, ...]} },
      "extraction": {"accepted": n, "low_confidence": n, "out_of_range": n, "rejected": n}
    }
  ]
}
```

All statistics ignore exams with `stats_excluded: true`; `exams` counts the remaining exams of the class and `excluded_duplicates` the excluded ones, so `exams + excluded_duplicates` equals the number of exams of that class in the selected split. (The numbers above are illustrative.) `n` is the number of exams with a non-null value for that indicator. `std` is the sample standard deviation and is `null` when `n < 2`. The class order is `normal`, `keratoconus`, `suspect`.

## 7. Frontend

Language of the UI: English. Responsive layout (desktop and tablet minimum).

### 7.1 Exam list (`/`)

- Filters: split, label, laterality. Sorting per the API. Pagination.
- Grid of cards: thumbnail, label badge, `exam_id` short form, laterality, visible min thickness, visible max curvature (shown as `—` when null), and a "Possible duplicate" badge when `possible_duplicate_of` is not empty.
- States: loading skeleton, empty result ("No exams match the filters"), error with retry (including the 503 "index missing" message, which tells the user to run the ingestion command).

### 7.2 Exam detail (`/exams/<split>/<label>/<case>`)

- Header: label badge, laterality, split, case, link back to the list with filters preserved.
- Seven maps in a responsive grid, titled per 4.2. Clicking a map opens it enlarged (modal, closable with Esc).
- Per map, a table of extracted values: text, value, unit, confidence, status. Rows with status other than `accepted` are visually distinguished and listed after the accepted rows.
- Indicator panel with the six derived indicators and the tooltip from 4.6.
- When `possible_duplicate_of` is not empty: a notice "This exam looks like a duplicate of …" with links to the other exams (showing their labels), and the statement whether this exam is excluded from the statistics and why (`duplicate`, or `duplicate_conflicting_labels` with the text "labels of the duplicates disagree").
- Permanent notice: "Values are extracted automatically from images and may contain errors. For research and demonstration only; not a clinical tool."
- Label wording is neutral: "Dataset label: Keratoconus". No diagnostic claim.
- States: loading, 404 ("Exam not found"), error with retry.

### 7.3 Statistics (`/stats`)

- Filter: split (all / train_validation / independent_test).
- Class count chart (3 bars) of the exams included in the statistics, and a line "N exams excluded as possible duplicates" (with the per-class split), linking to the exam list.
- Table of indicator statistics per class (n, mean, median, std, min, max).
- Histogram of `min_thickness_um` with one series per class.
- Extraction quality table per class (accepted, low confidence, out of range, rejected).
- Same notice as 7.2.
- States: loading, error with retry.

### 7.4 Navigation

Top bar with links "Exams" and "Statistics".

## 8. Configuration

| Variable | Used by | Default |
|----------|---------|---------|
| `DATASET_DIR` | ingestion, backend (serving images) | `dataset/archive` |
| `EXAMS_INDEX_PATH` | ingestion, backend | `backend/data/exams.json` |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:8000` |

`backend/data/` must be added to `.gitignore` together with the first code that writes there.

## 9. Edge cases

1. Index file missing, empty, or invalid JSON → `/api/health` and all data endpoints return 503 with an actionable message.
2. An exam whose `sag_a` image has no recognisable laterality → `unknown`; it is included in listings and filterable as `unknown`.
3. A map with zero accepted values → indicator `null`; UI shows `—`, never `0`.
4. Duplicate case numbers across splits and classes are valid (see dataset review 2); the three-part id disambiguates them.
5. Query parameters outside the allowed set → 422; unknown `exam_id` or `map_type` → 404.
6. Path traversal attempts in path parameters (`..`, encoded slashes) → 404; no file outside `DATASET_DIR` is ever served.
7. A class or split filter with no exams → empty list and valid (zero-count) statistics, not an error.
8. Image file listed in the index but missing on disk → 404 for that image; the UI shows a placeholder.
9. OCR returns text with a decimal comma or a Unicode minus (`−`, `–`) → normalised to `.` and `-` before parsing.

## 10. Acceptance criteria

Ingestion
1. AC1: Running ingestion on the provided dataset yields 573 exams: 200 normal, 200 keratoconus, 173 suspect; 423 in `train_validation`, 150 in `independent_test`.
2. AC2: Every exam in the index has exactly 7 maps with a `file` that exists under `DATASET_DIR`.
3. AC3: `.DS_Store` files and the duplicated folder level do not produce errors or exams.
4. AC4: Re-running ingestion produces an equivalent index and never leaves a partial file at `EXAMS_INDEX_PATH`.
5. AC5: On a non-macOS platform the command exits non-zero with a message and writes nothing.
6. AC6: Perimeter labels and `9mm` never appear with status `accepted`.
7. AC7: Values violating the format or range rules in 4.5 are never `accepted`, verified by unit tests with synthetic OCR output including `43.11`, `148.6` on `sag_a`, `•15` and `+12..-` on `elv_a`.
8. AC8: Accuracy on the gold sample `input_data/gold/gold_sample.json` (10 exams, hand-read by the Analyst): laterality and the five indicators `min_thickness_um`, `max_curvature_a_d`, `min_curvature_a_d`, `max_elevation_a_um`, `max_elevation_p_um` computed by ingestion are compared with the gold lists of acceptable values (an indicator is correct if it equals any listed value; `null` gold entries are not scored). At least 70% of the scored (exam, field) pairs are correct (lowered from the first draft's 90% by the Product Owner after the first implementation measured 74.6%, i.e. 44 of 59; 70% leaves room for run-to-run variation of the OCR: OCR of the 224×224 screenshots misses or misreads single values), laterality is correct for all 10 exams, and `min_thickness_um` is correct for at least 9 of 10 exams. If the targets are missed, the iteration is reported to the Product Owner, not silently adjusted. (Revised from the first draft, which measured the share of correct accepted values: hand-labelling all values on 70 images was not practical, and the indicators are what the application reports.)

API
9. AC9: `GET /api/health` returns 200 with `exams: 573` for the provided index and 503 when the index file is absent.
10. AC10: `GET /api/exams` with no parameters returns `total: 573`, `page: 1`, `page_size: 24`, 24 items.
11. AC11: Filters `split`, `label`, `laterality` combine with AND; `label=suspect` returns `total: 173`.
12. AC12: `sort=min_thickness` places exams with `null` thickness last in both orders.
13. AC13: `page_size=101`, `page=0`, `label=foo` return 422.
14. AC14: `GET /api/exams/train_validation/keratoconus/14` returns 7 maps with image URLs; an unknown id returns 404.
15. AC15: The image endpoint returns `image/jpeg` bytes for a valid map and 404 for an unknown map, unknown exam, or traversal attempt (`..%2f`).
16. AC16: `GET /api/stats` returns the classes in the order `normal`, `keratoconus`, `suspect`, `exams + excluded_duplicates` per class equal to the class size in AC1 (or in the filtered split), `std` null when `n < 2`, and indicator statistics that equal values recomputed from the index over the non-excluded exams only.
17. AC17: `GET /api/stats?split=independent_test` has `exams + excluded_duplicates` = 50 per class.
27. AC27: Duplicate detection (4.8) flags at least 10 of the 12 reference pairs; every flagged group has identical thickness values in the shared set, verified by unit tests with synthetic data (same label, different labels, three-member group, unknown laterality, fewer than 4 values).
28. AC28: In a group with different labels all members have `stats_excluded: true` with reason `duplicate_conflicting_labels`; in a same-label group exactly one member has `stats_excluded: false`, chosen by the rule in 4.8.
29. AC29: Excluded exams still appear in `GET /api/exams` and the detail endpoint, with `stats_excluded` and `possible_duplicate_of` set; the list and detail UI show the duplicate badge/notice.

Frontend
18. AC18: The list shows 24 cards on the first page, filters update the list and the URL query, and pagination reaches page 24 (573 / 24, rounded up).
19. AC19: Empty, loading and error states from 7.1–7.3 are reachable and covered by tests (including the 503 message).
20. AC20: The detail page shows 7 maps, per-map value tables with non-accepted rows distinguished, six indicators, and the permanent notice; Esc closes the enlarged map.
21. AC21: The statistics page shows the class chart, the indicator table, the thickness histogram with three series, and the extraction quality table; values match the API.
22. AC22: No UI text claims a diagnosis; labels read "Dataset label: …".
23. AC23: Layout has no horizontal scroll at 768 px width.

General
24. AC24: The dataset directory and the index are not tracked by git (`git check-ignore` confirms both).
25. AC25: Backend and frontend test suites, linters and type checks pass; README run instructions are updated with the ingestion, backend and frontend commands.
26. AC26: No TODO markers, placeholder comments or stub functions remain.

## 11. Open questions for the Product Owner

None blocking. Items to confirm when approving this spec:
- Accuracy targets in AC8 (90% of accepted values, 9 of 10 thickness values) are proposals.
- The six derived indicators and their "visible max / visible min" naming (4.6).
- Exam-to-exam comparison is out of scope for this iteration.
- Duplicates with different labels exclude all members from the statistics (4.8), because the true label is unknown; the Product Owner asked only for "exclude duplicates from statistics" and this rule is the Analyst's proposal.
