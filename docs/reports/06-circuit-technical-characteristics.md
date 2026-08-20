# Stage 06 — Circuit technical characteristics (downforce vs. top speed)

**Date**: 2026-08-20
**Status**: Complete

## What was done

User proposed a new feature idea: tips on car setup per circuit (e.g. Monaco/Hungaroring reward high downforce, Baku/Las Vegas reward low drag/high top speed). Assessed whether to add to v1, defer, or scrap.

## Decision

**Added to v1**, but scoped narrower than "tips" — as descriptive circuit metadata, not a new feature/endpoint/model:

- Added a `technical_characteristic` object (`downforce_level`: low/medium/high, plus a `key_trait` sentence) to the existing `GET /circuits/{circuit_id}` response in `docs/api-contract.md`.
- Framed as static, editorial content (like `trivia`), not telemetry-derived.
- Deliberately **not** built: prescriptive setup-optimization advice (tire degradation, aero balance modeling) — reframed from "tips for winning" (not actionable by F1Hub's users, who don't control car setup) to descriptive context, and scoped away from actual physics modeling, which would be a much larger, more speculative effort out of step with the narrow, honest-model approach from Stage 01.

## Why this fits cleanly

`circuit_overtaking_difficulty` is already a model feature (see the `derived_features` block in the prediction endpoint, and the explainability panel in `docs/api-contract.md`). Currently that's just a bare importance number with no explanation. `technical_characteristic` gives the explainability panel actual human-readable content to explain *why* that feature matters at a given circuit — strengthening a feature already committed to, rather than adding a new one.

## Files touched

- `docs/api-contract.md` — added `technical_characteristic` to the Circuit resource

## Next stage

Not yet decided — SQLite schema design or the Codex/Gemini orchestration plan are still open.
