# Test report: exam browser with extracted values

Tester agent. Spec: `input_data/specs/exam-browser-with-extracted-values.md`. Data: real dataset (573 exams) and the index built by `python -m ingest` with four OCR passes.

## Verdict

**The iteration passes** after the Product Owner lowered the AC8 target (set to 70%, measured 74.6%). Before that decision AC8 failed (75% measured against a 90% target); everything else passed.

## Suites run

| Suite | Result |
|-------|--------|
| Backend unit tests (`pytest`) | 136 passed |
| Backend acceptance tests on real data (`pytest tests_acceptance`) | 36 passed |
| Frontend tests (`npm test`) | 60 passed |
| `ruff`, `mypy` (strict), `eslint`, `tsc`, `prettier --check` | clean |
| `npm audit --omit=dev` | 0 vulnerabilities |
| TODO / placeholder scan | none |
| End-to-end in the built-in browser against production builds (`next build` + `next start`, real API) | see below |

No tests are skipped. Playwright was not installed (browser download); end-to-end checks were done by driving the running app in the built-in browser.

## Acceptance criteria

| AC | Result | Evidence |
|----|--------|----------|
| 1, 2, 3 | pass | `tests_acceptance/test_ingestion_real_data.py`: 573 exams (200/200/173; 423/150), 7 existing files each, no stray entries |
| 4, 5 | pass | `tests/test_ingestion.py`: atomic write leaves no partial file; non-macOS exits 1 and writes nothing |
| 6 | pass | no accepted value has a degree sign, a letter, or a position outside 0.42 of the image width |
| 7 | pass | `tests/test_rules.py` incl. `43.11`, `148.6`, `•15`, `+12..-` |
| 8 | pass (target lowered) | gold sample: 44 of 59 scored fields correct = 74.6% (target now 70%, was 90%); laterality 10/10; `min_thickness_um` 9/10 |
| 9-17 | pass | `tests_acceptance/test_api_real_data.py` and `tests/test_api.py`, `tests/test_stats.py` |
| 18 | pass | e2e: 24 cards, "Page 1 of 24", filters update URL and list, filter change resets to page 1 |
| 19 | pass | e2e: API returning 503 shows the ingestion hint and a Retry button on list, statistics and detail pages; unit tests for loading, empty, error |
| 20 | pass | e2e: 7 maps, 7 value tables, 6 indicators, notice, enlarged map closes with Escape |
| 21 | pass | e2e: class counts, excluded-duplicate line and thickness statistics equal the API; histogram has a legend with three series |
| 22 | pass | page text contains no diagnostic wording; label shown as "Dataset label: …" |
| 23 | pass | no horizontal scroll at 768 px on list, detail and statistics |
| 24 | pass | `git check-ignore` confirms `dataset/archive` and `backend/data/exams.json`; nothing tracked |
| 25 | pass | suites, linters and type checks green; README has run instructions |
| 26 | pass | no TODO, placeholder or stub |
| 27 | pass | 11 of 12 reference pairs flagged (needs 10); every flagged pair shares at least 4 thickness values |
| 28 | pass | all groups follow the exclusion rules on the real index |
| 29 | pass | excluded exams stay in list and detail with flags; badge and notice covered by frontend tests |

## Defects

1. **D1, found and fixed during testing.** In the production build, opening an exam by its URL (reload or deep link) stayed on "Loading…" forever and never called the API, because the route read `params` on the server inside a Suspense boundary and React did not hydrate it. Clicking a card worked. Fix: the page now reads the URL segments on the client (`ExamRouteView`, `useParams`). Verified in the production build, plus a unit test.
2. **D2, closed by decision: AC8.** OCR of the 224×224 screenshots misses or misreads single printed values; max/min indicators change with every missed extreme. Errors on the gold sample: maximum or minimum curvature wrong in 10 cases, elevation maximum in 7, thickness in 1.

## Other findings

- A thirteenth duplicate pair beyond the Analyst's list, `train_validation/normal/1 = train_validation/normal/52`, was flagged. Verified by eye: identical thickness and curvature maps. Not a false positive.
- `confidence` is now the share of the four OCR passes that read a value (spec updated). 18,536 values are `low_confidence` (read by a single pass) and are not used for indicators.
- A full ingestion takes about 10 minutes and has no resume.
- Cosmetic: the legend of the thickness histogram lists the classes alphabetically (Keratoconus, Normal, Suspect), unlike the rest of the UI.
- Spec housekeeping: AC27-29 are numbered after AC17.
