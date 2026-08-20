# Stage 05 — Backend/frontend repo scaffolding

**Date**: 2026-08-20
**Status**: Complete

## What was done

Scaffolded the actual project structure against the finalized `docs/api-contract.md`, so both a future backend agent (Codex) and frontend agent (Gemini) have a consistent skeleton to build logic into rather than inventing their own conventions.

**Backend** (`backend/`): FastAPI app with one router file per contract resource (`circuits.py`, `seasons.py`, `races.py`, `explainability.py`, `standings.py`, `drivers.py`, `constructors.py`), every contract endpoint registered and returning `501` as a placeholder. Also scaffolded `db/` (SQLAlchemy session + empty table module — schema not designed yet), `etl/` (Jolpica-F1 + FastF1 ingestion stubs), `ml/` (feature engineering, training, prediction, accuracy-metric stubs), and a `tests/` suite.

**Frontend** (`frontend/`): Next.js App Router skeleton plus `lib/api.ts` — a fully typed fetch client with one function and response type per contract endpoint, so frontend code imports from a single source of truth instead of hand-writing fetch calls that could drift from the contract.

## Verification

Rather than just writing files, created a venv and ran the backend test suite (`pytest`) to confirm the scaffold actually boots — both tests passed (`/health` check, and a contract-route registration check). This caught a real issue: `app/core/config.py` used Pydantic's deprecated class-based `Config` style, which was fixed and re-verified before committing.

## Files created

40 files across `backend/` and `frontend/`, plus root `README.md` tying the stack/structure/scope together. Full list in the two commits below.

## Commits

- `496a34d` — Scaffold backend (FastAPI) and frontend (Next.js) repo structure
- `95c77ab` — Fix deprecated Pydantic Config style in backend settings

Both pushed to `origin/main`.

## Next stage

Not yet decided — candidates raised: SQLite schema design, or the Codex/Gemini orchestration plan.
