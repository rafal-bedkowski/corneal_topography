# Dataset review: Keratoconus detection (Kaggle)

Reviewed by: Analyst agent. Source description: `input_data/dataset_description_kaggle_keratoconus.md`. Files: `dataset/archive/`.

## 1. Structure

```
dataset/archive/
├── Train_Validation sets/Train_Validation sets/{Normal,Keratoconus,Suspect}/case<N>/<7 jpg>
└── Independent Test Set/Independent Test Set/{Normal,Keratoconus,Suspect}/case<N>/<7 jpg>
```

Note the duplicated folder name at each level (`X/X/`). `.DS_Store` files are present and must be ignored.

| Split | Normal | Keratoconus | Suspect | Eyes | Files |
|-------|--------|-------------|---------|------|-------|
| Train_Validation | 150 | 150 | 123 | 423 | 2961 |
| Independent Test | 50 | 50 | 50 | 150 | 1050 |
| Total | 200 | 200 | 173 | 573 | 4011 |

The counts match the Kaggle description for the Train_Validation and Independent Test splits (the larger totals quoted in the description, 204/215/123, refer to the study cohort and are not what the files contain).

## 2. Exam unit

One folder `case<N>` is one eye exam. Every case contains exactly 7 files (verified for all 573 cases), named `<PREFIX>_<N>_<MAP>.jpg`:

- Prefix by class: `NOR`, `KCN`, `SUSP`.
- `<N>` equals the case number in the folder name.
- Case numbers restart in each split and class (e.g. `case1` exists in Train_Validation and in Independent Test). The **unique exam identifier is therefore (split, class, case number)**, not the case number alone.

## 3. The seven maps

All files are 224×224 px, RGB JPEG. They are screenshots of Pentacam map displays (Oculus Optikgeräte GmbH), not raw numeric grids.

| Suffix | Map (Pentacam) | Content |
|--------|----------------|---------|
| `Sag_A` | Axial/sagittal curvature, anterior | Curvature in D, with steep/flat meridian markers and ring values |
| `Sag_P` | Axial/sagittal curvature, posterior | Curvature in D |
| `Elv_A` | Elevation, anterior | Elevation in µm vs. best-fit reference |
| `Elv_P` | Elevation, posterior | Elevation in µm vs. best-fit reference |
| `EC_A` | Elevation (enhanced/corrected reference), anterior | Elevation in µm, different reference body |
| `EC_P` | Elevation (enhanced/corrected reference), posterior | Elevation in µm |
| `CT_A` | Corneal thickness (pachymetry) | Thickness in µm; thinnest point and isopachs marked |

The interpretation of `EC_A`/`EC_P` and of the suffix `_A`/`_P` (anterior/posterior) is inferred from file names and visual inspection of sample cases; the dataset documentation does not define the suffixes. It must be confirmed by the Product Owner or a clinician.

## 4. Visual content

- Each image has a laterality label (`OD` right eye / `OS` left eye) burned into the pixels, a "9 mm" zoom icon, and orientation letters (T/N temporal/nasal, 90°/270° axes). Laterality is **not** present in file names or folders; it can only be read from the image.
- Numeric values are burned into the images (e.g. elevation values, K readings, thickness) and are not available as data.
- Colour scales differ in step size between sub-cohorts (stated in the description: training data came from different Pentacam instruments/settings). Colours cannot be mapped to absolute values without the scale bar, which is not part of the images.
- Resolution (224×224) is too low for OCR of the burned-in numbers to be reliable.

## 5. Labels

Three classes: Normal (NOR), Keratoconus (KCN), Suspect (SUSP). Labels were assigned by three corneal specialists with a two-out-of-three majority vote (per the description). Suspect criteria: atypical localized steepening, asymmetric bowtie, K > 47.00 D, oblique cylinder > 1.50 D, central thickness < 500 µm, or abnormal front elevation / PTI / BAD-D. The application must show labels as provided and make no diagnostic claims.

## 6. Constraints and risks

- **No numeric data.** There is no CSV, no K1/K2/Kmax, no thickness values and no grid. Features such as interactive colour scales, cross-sections, value probing, index computation or 3D surfaces cannot be derived from these files without image-based reconstruction.
- **No patient or eye IDs.** Left and right eyes of the same patient cannot be linked; there is no patient id, age or sex per case.
- **Duplicate exams, some with conflicting labels.** OCR of the thickness map (`CT_A`) on all 573 exams found 12 pairs of exams with identical thickness values (at least 4 identical printed values, so the real number is probably higher because OCR found 4 or more values on only about 490 of 573 maps). Five pairs span different classes, e.g. `independent_test/keratoconus/3` and `independent_test/suspect/7` also have identical curvature and elevation values and differ only in colour scale and label. One pair crosses the train/test boundary (`independent_test/suspect/4` and `train_validation/suspect/109`). These are most likely the same eye exported twice with different Pentacam colour settings. Consequences: class statistics are biased, and the independent test set is not fully independent. Pairs found:
  `it/keratoconus/3 = it/suspect/7`, `it/keratoconus/47 = it/suspect/41`, `it/normal/25 = it/suspect/39`, `it/normal/26 = it/suspect/40`, `tv/normal/125 = tv/suspect/75`, `it/suspect/4 = tv/suspect/109`, `tv/keratoconus/78 = tv/keratoconus/84`, `tv/keratoconus/79 = tv/keratoconus/85`, `tv/normal/127 = tv/normal/42`, `tv/normal/142 = tv/normal/94`, `tv/normal/2 = tv/normal/53`, `tv/suspect/115 = tv/suspect/116`
  (`it` = independent_test, `tv` = train_validation).
- **Mixed colour scales** between acquisitions (see section 4).
- **License is not stated** on the Kaggle page ("Other (specified in description)", with no license in the description). Redistribution rights are unknown; the dataset should not be committed to a public repository without the Product Owner's decision.
- **Class balance:** Suspect is the smallest class (173).
- **Duplicated folder names and `.DS_Store` files** require explicit handling in the loader.

## 7. Feasibility test: reading numbers from the images

Test: macOS Vision OCR (accurate mode, no language correction) on 4× upscaled images of one keratoconus case (`KCN_14`: `CT_A`, `Sag_A`, `Elv_A`), compared against the images by eye.

- `CT_A` (thickness): values `460 / 481 / 532 / 601` and laterality `OS` read correctly. The lowest value (thinnest point) is identifiable.
- `Sag_A` (curvature): most values read (e.g. `38.6`, `47.0`, `51.8`), but with errors: `43.11` instead of `43.1`, `48.€`, `148.6` instead of `48.6`.
- `Elv_A` (elevation): numbers read, but several signs and positions are unreliable (`•15`, `+12..-`, `SO`), and the position of each value on the map is not returned in a usable form without extra processing.

Conclusions:
- Only a sparse set of values is printed per map (about 10–25), at map-specific positions. Full grids cannot be reconstructed.
- Standard clinical indices (K1, K2, Kmax, mean K, BAD-D, KISA%) are not printed in these screenshots. Only point values are available; any index would be an approximation derived from them and must not be presented as a clinical measurement.
- OCR error rate on curvature and elevation maps is visible even on a single case. Using it requires validation rules (plausible ranges per map) and a flag for low-confidence values.
- Vision OCR is macOS-only. A deployable (Linux) backend needs a portable OCR engine (e.g. Tesseract or EasyOCR), which is expected to be less accurate on 224×224 images and has not been tested.
- Portable engine test: RapidOCR (ONNX, pip-installable, runs on Linux) on the same three images was clearly worse than macOS Vision: it merged or split values (`4381`, `4311`, `486 486`, `+12--+89`), dropped several values and returned confidence of 0.5–0.77. Tesseract and EasyOCR were not tested.
- Perimeter labels leak into the OCR output as numbers: for example `350.·S` (a damaged angle label) was read as a thickness-like value on one `CT_A` map, and tokens such as `330`, `300` and `240` appear without a degree sign. The position rule in the spec (4.5) is therefore essential, not optional.
- Vision OCR found at least 4 thickness values on 488 of the 573 `CT_A` maps and a laterality label on 503 of 573 thickness maps (70 maps without one). Laterality must be read from several maps, not only one.
- Reliable and cheap to extract: eye laterality (OD/OS) and the minimum pachymetry value from `CT_A`.

## 8. Implications for the MVP

The dataset supports an **image-based exam browser**: list exams by split and class, open an exam and show its 7 maps with labels. It does not support numeric topography analysis. Any feature beyond browsing and side-by-side comparison of the existing map images needs additional data or an explicit decision to derive values from images.
