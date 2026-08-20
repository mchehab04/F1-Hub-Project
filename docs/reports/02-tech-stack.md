# Stage 02 — Tech stack selection

**Date**: 2026-08-20
**Status**: Complete

## What was done

Walked through stack choices with the user via targeted questions, informed by the v1 scope from Stage 01 (ML-heavy backend, standard web frontend, solo dev, local-only for now).

## Decisions

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | Async, and its auto-generated OpenAPI spec becomes a free, always-accurate contract once implemented — useful given two different AI coding agents (Codex, Gemini) will build backend/frontend semi-independently. |
| Frontend | Next.js | React with routing/SSR built in, fits a season calendar + per-circuit + predictor page structure. |
| Data storage | SQLite | Single-file DB, zero setup, plenty for a few hundred races. |
| ML | scikit-learn | Interpretable, fast to iterate, matches the intentionally narrow v1 model from Stage 01. |
| Deployment | Local only for now | No need to design around hosting constraints (e.g. long-running ETL jobs) yet. |

## Files touched

None yet — this stage was a decision, not an artifact. The choices are baked into Stage 03's API contract and Stage 05's scaffold.

## Next stage

API contract draft (see `03-api-contract.md`).
