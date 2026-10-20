# Corneal Topography

A web application for visualising corneal topography data — clinical measurements of the eye's surface curvature used in diagnosing conditions such as keratoconus and planning refractive surgery.

The goal is an MVP that feels like a product: clean UI, deployable, extendable. It works with real data files from public sources (e.g. Kaggle).

## Tech stack

- Backend: FastAPI (Python)
- Frontend: React / Next.js

## Project structure

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Project decisions, conventions, architecture notes, agent roster and changelog |
| `agents/` | Context files for the Analyst, Full-Stack Developer and Tester agents |
| `input_data/` | Requirements and functional specifications |
| `dataset/` | Raw datasets |
| `backend/` | FastAPI application |
| `frontend/` | React/Next.js application |

## Development workflow

Features are built in sequential cycles: **Analyst → Developer → Tester**. The Product Owner defines requirements, provides data, and commits all changes. See `CLAUDE.md` for details.

## Status

Project scaffold only. Run instructions will be added together with the first implemented feature.
