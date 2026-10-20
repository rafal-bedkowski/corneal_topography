# Corneal Topography

A web application for visualising corneal topography data — clinical measurements of the eye's surface curvature used in diagnosing conditions such as keratoconus and planning refractive surgery.

The goal is an MVP that feels like a product: clean UI, deployable, extendable. It works with real data files from public sources (e.g. Kaggle).

The application is for research and demonstration only. Values shown are extracted automatically from images and may contain errors; it is not a clinical tool.

## What it does

The dataset ([Kaggle "Keratoconus detection"](https://www.kaggle.com/datasets/elmehdi12/keratoconus-detection/data)) contains 573 exams, each as seven Pentacam map screenshots. The app:

- lists the exams with filters (split, dataset label, eye) and sorting,
- shows the seven maps of an exam together with the numbers printed on them (read with OCR),
- derives a few indicators from those numbers ("visible min thickness", "visible max curvature", ...),
- compares the three dataset classes statistically, excluding suspected duplicate exams.

Details: `input_data/specs/exam-browser-with-extracted-values.md` and `input_data/dataset_review.md`.

## Tech stack

- Backend: FastAPI (Python 3.12+), Pydantic
- Frontend: Next.js (React, TypeScript), Recharts
- OCR (offline ingestion step): macOS Vision (Swift helper, macOS only) and RapidOCR (pip package, runs anywhere), several image passes per map combined by voting

## Project structure

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Project decisions, conventions, architecture notes, agent roster and changelog |
| `agents/` | Context files for the Analyst, Full-Stack Developer and Tester agents |
| `input_data/` | Requirements, functional specifications, dataset notes, hand-read gold sample |
| `dataset/` | Raw datasets (not tracked by git, license unknown) |
| `backend/app/` | FastAPI application (serves the exam index and images) |
| `backend/ingest/` | Offline ingestion: discovers exams, runs OCR, builds the exam index |
| `frontend/` | Next.js application |

## Running locally

### 1. Dataset

Download the Kaggle dataset and unpack it so that the folders `Train_Validation sets` and `Independent Test Set` are in `dataset/archive/`.

### 2. Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Build the exam index (takes about 15–20 minutes; recognises 573 exams × 7 maps in several passes):

```bash
.venv/bin/python -m ingest
```

The ingestion uses every OCR engine that is available: macOS Vision (needs macOS and the Xcode command line tools for `swiftc`) and RapidOCR (installed by `requirements.txt`, works on macOS, Linux and Windows). On Linux it therefore runs with RapidOCR alone. Restrict the engines with `INGEST_ENGINES=rapid` (or `vision`, `vision,rapid`); `INGEST_DISABLE_VISION=1` is a shortcut for RapidOCR alone.

To try rule changes without recognising the images again, keep the recognised tokens: `.venv/bin/python -m ingest --tokens-cache .cache/tokens.json --output .cache/exams.json` (the first run writes the cache, later runs reuse it). Score an index against the hand-read gold sample with `.venv/bin/python -m ingest.evaluate --index <file> --set tuning` (`holdout` is for final evaluation only).

Start the API on http://localhost:8000:

```bash
.venv/bin/uvicorn app.main:app --reload
```

Backend checks:

```bash
.venv/bin/pytest
.venv/bin/pytest tests_acceptance   # real dataset and index; needs the ingestion to have run
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Frontend checks: `npm test`, `npm run lint`, `npm run typecheck`, `npm run format:check`.

## Configuration

| Variable | Used by | Default |
|----------|---------|---------|
| `DATASET_DIR` | ingestion, backend (serves images) | `dataset/archive` |
| `EXAMS_INDEX_PATH` | ingestion, backend | `backend/data/exams.json` |
| `INGEST_ENGINES` | ingestion (comma separated: `vision`, `rapid`) | all available |
| `INGEST_DISABLE_VISION` | ingestion (`1` = RapidOCR alone) | unset |
| `CORS_ORIGINS` | backend (comma separated) | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | frontend (set at build time) | `http://localhost:8000` |

Relative paths are resolved against the repository root.

## Deployment notes

The ingestion can run on any platform with RapidOCR, but the highest accuracy comes from running it on macOS with both engines. Deploy the backend with a prebuilt `exams.json` and the dataset directory, and the frontend with `NEXT_PUBLIC_API_URL` pointing at the backend. The dataset has no stated license, so check its redistribution terms before putting it on a public server.

## Development workflow

Features are built in sequential cycles: **Analyst → Developer → Tester**. The Product Owner defines requirements, provides data, and commits all changes. See `CLAUDE.md` for details.
