# Stage 03 — API contract (draft, review, fixes)

**Date**: 2026-08-20
**Status**: Complete

## What was done

1. Drafted a full REST API contract (`docs/api-contract.md`) covering the entire v1 scope from Stage 01 — circuits, season calendar, race detail, prediction, explainability, accuracy tracking, standings, drivers/constructors, and replay.
2. User feedback caught a real gap: the accuracy tracker's `mean_absolute_position_error` alone could make a "close but not exact" model look bad — added `rank_correlation` (Spearman's ρ) and `podium_hit_rate` as complementary metrics.
3. Ran the `subagent-verification` skill (independent reviewer agent, fresh context, no access to the drafting reasoning) against the contract, checking correctness, internal consistency, edge cases, and forward-compatibility with the deferred what-if mode.
4. Reviewer verdict: **CRITICAL** — 2 critical + 7 major + 5 minor + 1 nit issue. A resolver agent fixed all 15 (0 declined), and the corrected contract was applied.

## Key decisions / fixes

- **Critical**: added a missing `GET /constructors/{id}` resolver (drivers and circuits already had one; constructors didn't — every standings/results screen needed this).
- **Critical**: the what-if forward-compatibility claim was self-contradicting — it promised overriding `constructor_recent_form` later, but that field didn't exist in the `inputs` schema. Fixed by adding a `derived_features` block enumerating every model feature, making the schema genuinely override-ready.
- **Major**: moved `/prediction/explain` to a model-level resource (`/models/{version}/explain`) since feature importances are a global model property, not per-race.
- **Major**: extended race `status` to include `postponed`/`cancelled`; added the missing constructor head-to-head endpoint; documented DNF/nullability edge cases (lap records, replay lap arrays, mid-season transfers, pre-2018 FastF1 coverage).

## Files created/touched

- `docs/api-contract.md` (drafted, then revised)
- `.claude/skills/subagent-verification/active/verification/verification_report.md`

## Next stage

Git/GitHub setup (see `04-git-github-setup.md`).
