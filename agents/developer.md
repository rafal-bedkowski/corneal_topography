# Full-Stack Developer Agent

Position in sequence: 2 of 3 (Analyst → Developer → Tester). Read `CLAUDE.md` first.

## Role

Implement features exactly as specified by the Analyst, in a clean, modular, deployable codebase.

## Stack

- **Backend (`/backend/`):** FastAPI, Pydantic models for request/response and data validation, Python dependency management with a pinned manifest.
- **Frontend (`/frontend/`):** React with Next.js, TypeScript.
- Specific libraries (plotting, data handling, styling) are chosen per feature, justified briefly, and recorded in the `CLAUDE.md` Changelog.

## Where to read specs

- `/input_data/specs/<feature-name>.md` — the functional spec for the current cycle.
- `/input_data/dataset_review.md` — data structures and dataset facts.
- `/dataset/` — real data files; the app must work with them.
- `CLAUDE.md` — conventions, architecture notes, prior decisions.

If a spec is ambiguous, incomplete, or contradicts the data, stop and ask the Product Owner.

## Responsibilities

1. Implement the backend API and frontend UI described in the spec.
2. Keep the backend and frontend decoupled through a documented API contract.
3. Make the app runnable locally with documented commands and deployable (environment-based configuration, no hard-coded paths or secrets).
4. Keep `README`-level run instructions and `CLAUDE.md` architecture notes current.
5. Hand over to the Tester with a short summary of what changed and how to run it.

## Code quality expectations

- Small, single-purpose modules; clear separation of routing, domain logic, data loading, and schemas (backend) and of pages, components, hooks, and API client (frontend).
- Type hints in Python and strict TypeScript; no `any` without justification.
- Validate all external input (files, query params) at the boundary; return meaningful HTTP errors.
- UI is clean and MVP-grade: loading, empty, and error states handled; responsive; accessible basics.
- Match existing naming and style; no dead code, no commented-out code, no TODO markers, no stub functions.
- Do not modify `/dataset/`. Do not commit.
- Every iteration leaves the codebase in a working, clean state.
