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
4. Do not commit anything. The Product Owner commits. Agents never run `git add`, `git commit` or `git push`. At the end of each iteration, the orchestrator gives the Product Owner the exact git commands plus the proposed commit message, each with a short explanation (in Polish) of what the command does.
5. Read the relevant agent `.md` file before performing work in that agent's role.
6. When a new agent is added, update `CLAUDE.md` immediately and confirm with the Product Owner before using that agent in a cycle.

## Language conventions

- Messages shown to the Product Owner (status updates, questions, reports in chat) are in Polish.
- Everything else is in English: code, comments, commit-ready text, documentation, specs, agent files, `CLAUDE.md`, tests.

## Architecture notes

None yet. Recorded after the first Analyst and Developer cycles.

## Changelog

Record architectural and scope decisions per iteration, newest first. Format: `YYYY-MM-DD — decision — reason`.

- 2026-10-20 — Git policy: the Product Owner runs every git command; the orchestrator only supplies commands, commit message and a short explanation of each command — Product Owner wants full control over the repository history.
- 2026-10-20 — Language convention: chat messages to the Product Owner in Polish, all project artifacts in English — Product Owner wants to follow progress in Polish while keeping the codebase in English.
- 2026-10-20 — Project scaffolded (agents, directory structure, CLAUDE.md) — starting point; awaiting dataset in `/dataset/`.
