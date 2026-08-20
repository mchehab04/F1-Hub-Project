# Stage 07 — SQLite schema design

**Date**: 2026-08-21
**Status**: Complete

## What was done

Designed and implemented the SQLite schema (`backend/app/db/tables.py`, previously an empty stub), documented in `docs/schema-design.md`. Wired `Base.metadata.create_all()` into `app/main.py` startup so the schema is created automatically (no migrations tool for v1 — solo, local-only, revisit with Alembic if the schema needs to evolve after real data exists).

## Key decisions

- **9 tables**: `constructors`, `drivers`, `circuits`, `races`, `race_entries`, `session_weather`, `replay_laps`, `model_versions`, `predictions`.
- **Relational vs. JSON split**: `race_entries` and `replay_laps` are real tables (queried granularly, aggregated for standings/accuracy). A prediction's `inputs`/`predictions` payload and a model's feature-importance lists are JSON columns — always read/written whole, no relational access pattern, so normalizing them into child tables would be pure overhead.
- **No `seasons` or `standings` tables** — seasons are `SELECT DISTINCT season FROM races`; standings are aggregated from `race_entries` at query time. Avoids a materialized-view sync problem for data that doesn't need it at this scale.
- **`race_entries.constructor_id`** is the team driven *at that race*, not a single season-level value — mid-season constructor transfers fall out naturally rather than needing special-case handling.
- **Career stats** (`career_wins/podiums/poles/championships` on drivers/constructors) are ETL-populated, not computed on the fly — avoids expensive multi-season aggregation on every profile lookup.
- **`circuits.lap_record`** is decomposed into three nullable columns (`lap_record_time/driver_id/year`) rather than a nested structure — the API layer reassembles them into the contract's nested object or `null`.

## Verification

Beyond running the existing pytest suite (still passing, confirms the app boots with the schema wired in), ran a standalone round-trip smoke test: inserted real rows through the ORM for every table type, confirmed JSON columns (`trivia`, `inputs`, `predictions`) serialize/deserialize correctly, and confirmed both a `UNIQUE(race_id, driver_id)` violation and an invalid `status` CHECK-constraint violation are correctly rejected by SQLite. All passed.

## Files created/touched

- `docs/schema-design.md` (new)
- `backend/app/db/tables.py` (implemented, was an empty stub)
- `backend/app/main.py` (wired `create_all()` into startup)

## Next stage

Not yet decided — the Codex/Gemini orchestration plan is still open, and ETL implementation (populating this schema from Jolpica-F1 + FastF1) is the next natural dependency for the model/prediction work.
