# Corneal Topography MVP

## Project goal and current scope

A web application that visualises corneal topography data (clinical measurement of the eye's surface curvature, used for diagnosing conditions such as keratoconus and planning refractive surgery).

- Goal: an MVP that feels like a product, not a script — clean UI, deployable, extendable.
- Current scope: load real data files from `/dataset/` (initial source: public datasets, e.g. Kaggle) and visualise them. Detailed feature scope is defined per cycle by the Analyst in `/input_data/` after the Product Owner confirms it.
- Out of scope until the Product Owner says otherwise: authentication, patient management, clinical decision support, regulatory certification.

## Tech stack

- Backend: FastAPI (Python)
- Frontend: React / Next.js
- Concrete library choices (plotting, testing, packaging) are recorded in the Changelog when decided.

## Workflow

Each feature cycle runs sequentially: **Analyst → Developer → Tester**. Each agent reads its own context file in `/agents/` before starting work. When anything is unclear (requirement, scope, data format), the agent stops and asks the Product Owner.

## Agent roster

Add new agents by appending an entry and creating the file in `/agents/`. Do not rewrite existing entries. After adding, confirm with the Product Owner before using the agent in a cycle.

| # | Agent | Role summary | File |
|---|-------|--------------|------|
| 1 | Analyst | Interprets domain requirements, defines data structures, reviews datasets, writes functional specs into `/input_data/` | `agents/analyst.md` |
| 2 | Full-Stack Developer | Implements features from the Analyst's specs in FastAPI and React/Next.js | `agents/developer.md` |
| 3 | Tester | Writes and runs tests, checks edge cases, validates against specs | `agents/tester.md` |

### Adding a new agent
1. Create `agents/<name>.md`.
2. Add a row to the roster above with role, responsibilities, and position in the sequence.
3. Inform the Product Owner and wait for confirmation before using it.

## Roles

- **Product Owner (human):** defines requirements, provides data, makes decisions, commits all changes.
- **Agents:** see roster. Agents never commit.

## Directory conventions

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Single source of truth for decisions, conventions, architecture, agents |
| `agents/` | One context file per agent |
| `input_data/` | Product Owner inputs and Analyst functional specs |
| `dataset/` | Raw datasets provided by the Product Owner (read-only for agents) |
| `backend/` | FastAPI application and its tests |
| `frontend/` | React/Next.js application and its tests |

## Hard rules

1. If unsure about a requirement, scope, or data format — stop and ask the Product Owner before proceeding.
2. No editorial artifacts (no "TODO: fill this later", no placeholder comments, no stub functions left in place across iterations). Every iteration leaves the codebase clean.
3. All project decisions, conventions, architecture notes, and agent definitions live in `CLAUDE.md`. Keep it up to date after every iteration.
4. Do not commit anything. The Product Owner commits. Agents never run `git add`, `git commit` or `git push`. At the end of each iteration, the orchestrator gives the Product Owner the exact git commands plus the proposed commit message, each with a short explanation (in Polish) of what the command does. Commit messages never contain `Co-Authored-By` or any other attribution to Claude; the Product Owner is the sole author.
5. Read the relevant agent `.md` file before performing work in that agent's role.
6. When a new agent is added, update `CLAUDE.md` immediately and confirm with the Product Owner before using that agent in a cycle.

## Language conventions

- Messages shown to the Product Owner (status updates, questions, reports in chat) are in Polish.
- Everything else is in English: code, comments, commit-ready text, documentation, specs, agent files, `CLAUDE.md`, tests.

## Architecture notes

Dataset (see `input_data/dataset_review.md`): Kaggle "Keratoconus detection", 573 eyes (Normal / Keratoconus / Suspect), 7 Pentacam map screenshots per eye (224×224 JPEG, no numeric data, no patient ids, laterality only inside the pixels). An exam is identified by (split, class, case number). The dataset lives in `dataset/archive/` and is not tracked by git.

Application architecture (first feature, `exam-browser-with-extracted-values`):

- `backend/ingest/` — offline, macOS-only ingestion (`python -m ingest`): `discovery` finds exams, `ocr` runs macOS Vision through a Swift helper (`vision_ocr.swift`, compiled to `backend/.cache/`) in four passes (scale 3 and 4, grayscale, binarised) in parallel, `consensus` merges the passes by position and voting, `rules` applies the acceptance rules (perimeter labels, formats, ranges), `indicators` derives the six indicators and laterality, `duplicates` flags duplicate exams, `builder`/`cli` write `backend/data/exams.json` atomically.
- `backend/app/` — FastAPI API under `/api` (`health`, `exams`, exam detail, map images, `stats`). `IndexStore` loads `exams.json` and reloads it when the file changes; a missing or invalid index gives HTTP 503. Images are served only from paths listed in the index and only inside `DATASET_DIR`. Configuration from environment variables (`app/config.py`).
- `frontend/` — Next.js App Router, client-side data fetching through `useApi` (`src/hooks`) against `NEXT_PUBLIC_API_URL`; pages `/` (exam list, filters in the URL), `/exams/<split>/<label>/<case>` and `/stats` (Recharts).
- Index data flow: dataset images → ingestion (OCR) → `exams.json` → API → UI. Neither the dataset nor the index is tracked by git.
- Conventions: Python 3.12+, `ruff` (line length 100) and strict `mypy`; TypeScript strict, `prettier` (print width 100), `eslint`; tests with `pytest` and `vitest` + Testing Library.

## Changelog

Record architectural and scope decisions per iteration, newest first. Format: `YYYY-MM-DD — decision — reason`.

- 2026-10-20 — Product Owner decision: AC8 target lowered from 90% to 70% (measured 74.6%, 44 of 59; laterality 10/10 and thickness 9/10 still required); the first feature iteration now passes. Better OCR (digit recognition by template) or a dataset with numeric data (e.g. CornOrb) remain options for a later iteration.
- 2026-10-20 — Tester cycle done (`input_data/reports/exam-browser-test-report.md`): iteration did not pass at first because AC8 was not met (75% vs 90% on the gold sample); all other criteria passed. Defect found and fixed: deep links to `/exams/...` hung in the production build (`ExamRouteView` now reads the URL segments on the client). Real-data acceptance tests live in `backend/tests_acceptance/` (run separately because they need the dataset and the index); end-to-end checks were done in the built-in browser instead of Playwright.
- 2026-10-20 — First feature implemented (Developer cycle done, awaiting Tester): backend (`app`, `ingest`) and frontend (list, detail, statistics). Libraries: Recharts for charts, Vitest + Testing Library for frontend tests, httpx2 for the FastAPI test client (httpx is deprecated for it). Developer self-check against the gold sample: laterality 10/10, `min_thickness_um` 9/10, all scored fields 44/59 = 75%, so **AC8 (90%) is not met**; 11 of the 12 reference duplicate pairs are detected (AC27 met). Cause: OCR on 224×224 screenshots misses or misreads single values, and max/min indicators are sensitive to any missed extreme.
- 2026-10-20 — OCR runs in four passes (scale 3 and 4, grayscale, binarised) combined by voting (`ingest/consensus.py`); `confidence` is the share of passes that read a value, because Vision's own confidence is almost always 1.0. This raised the gold score from 68% (single pass) to 75%. Padding characters around thickness and curvature values are stripped before the format check (spec 4.5 updated).
- 2026-10-20 — Spec approved by the Product Owner. Gold sample created (`input_data/gold/gold_sample.json`, 10 exams); AC8 revised to measure indicator accuracy against it instead of per-value accuracy. Laterality is read from several maps, not only `sag_a`.
- 2026-10-20 — Dataset finding: at least 12 pairs of duplicate exams (5 with conflicting classes, 1 across train/test), see `dataset_review.md` section 6; decision by the Product Owner: flag them and exclude them from the statistics (spec 4.8; conflicting-label groups are excluded entirely).
- 2026-10-20 — First feature spec drafted: `input_data/specs/exam-browser-with-extracted-values.md` (exam browser, OCR-extracted values, class statistics); awaiting Product Owner approval before the Developer starts.
- 2026-10-20 — OCR decision: numbers are read from the map images offline on macOS (Vision) into a local JSON index served by FastAPI; values are approximate and flagged by status — Vision was clearly more accurate than the portable RapidOCR on the tested sample (see `dataset_review.md` section 7).
- 2026-10-20 — Product Owner chose numeric analysis (values from maps, derived indicators, class comparison) for the first MVP, accepting OCR errors.
- 2026-10-20 — Dataset is not committed (`dataset/archive/` in `.gitignore`) — license is not stated on the Kaggle page, so redistribution rights are unknown.
- 2026-10-20 — Analyst reviewed the dataset (`input_data/dataset_review.md`); `EC_A`/`EC_P` interpreted as elevation maps with a different reference surface (confirmed by the Product Owner).
- 2026-10-20 — No Claude attribution in commits (no `Co-Authored-By` trailer) — Product Owner does not want Claude listed as a contributor on GitHub; the initial commit was rewritten to remove it.
- 2026-10-20 — Git policy: the Product Owner runs every git command; the orchestrator only supplies commands, commit message and a short explanation of each command — Product Owner wants full control over the repository history.
- 2026-10-20 — Language convention: chat messages to the Product Owner in Polish, all project artifacts in English — Product Owner wants to follow progress in Polish while keeping the codebase in English.
- 2026-10-20 — Project scaffolded (agents, directory structure, CLAUDE.md) — starting point; awaiting dataset in `/dataset/`.
