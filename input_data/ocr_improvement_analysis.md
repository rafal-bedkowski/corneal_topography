# OCR accuracy: analysis of the current errors

Analyst agent. Basis: gold sample (`input_data/gold/gold_sample.json`, 10 exams) and the cached tokens of the four OCR passes. Current result: 44 of 59 scored fields correct (74.6%); laterality 10/10, thickness 9/10.

## Why indicators are wrong

Of the 15 wrong indicator values on the gold sample:

| Cause | Count | Examples |
|-------|-------|----------|
| The correct text was **never read** by any pass | 9 | bold `52.5` printed without a box, `45.2` as white text on a dark purple area, values hidden under the centre marker, `+2` / `+4` elevation values drawn over dashed circles |
| The correct text **was read by some pass but not used** | 6 | `375` (thinnest point, read by one pass only and therefore flagged `low_confidence`), `38.2`, `38.6` minima, a misread `160` winning over `+16` / `+27` |

So two different fixes are needed:

1. **Selection and consensus** (the 6 "read but not used"): cheap, no new recogniser. Examples: for the thinnest point accept a single-pass reading when it is the lowest value on the thickness scale and the neighbouring values are consistent; use the physical structure of the thickness map (values increase from the centre outwards along the line) and of curvature maps (values lie on rings) to reject outliers such as `160`.
2. **A better recogniser** (the 9 "never read"): the fonts are fixed (Pentacam renders the numbers in one bitmap font, in black on a coloured background, in white on dark areas, and in bold for the maximum). A recogniser specialised for this font, e.g. a small classifier of single digits trained on crops from these images, can read white-on-dark and bold text that general OCR misses, and it has no dependency on macOS.

## What a specialised recogniser needs

- **Training labels.** None exist. They can be bootstrapped from the values on which all four current passes agree (tens of thousands of values) and checked against the gold sample. Risk: the bootstrap contains only what the current OCR reads well, so the hardest cases (white on dark, bold) are under-represented; a small set of hand-labelled hard crops is needed.
- **Segmentation.** Locating the number boxes and splitting them into digits at 224×224 after JPEG compression; digits are about 5 px wide, so this is the main technical risk.
- **Evaluation.** The current gold sample (10 exams, 59 fields) is too small to compare approaches or to detect overfitting. A larger gold sample, ideally with exams held out from any tuning, is needed.
- **Dependencies.** A small classifier needs `numpy` and `scikit-learn` or `torch`/`onnxruntime`; `opencv` or Pillow for segmentation. `torch` is heavy; `scikit-learn` (or a hand-written nearest-neighbour on templates) is enough for single digits.

## Open decisions for the Product Owner

1. Staged approach (first consensus/selection fixes, then the specialised recogniser) or only one of them.
2. Size of the new gold sample and who labels it.
3. Target accuracy.
4. Whether the new recogniser must run without macOS (Linux deployment), with macOS Vision kept as an optional pass.
