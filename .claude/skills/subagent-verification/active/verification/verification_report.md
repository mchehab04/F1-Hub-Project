# Subagent Verification Report

**Artifact**: `docs/api-contract.md` — F1Hub v1 API contract (pre-implementation design doc)
**Date**: 2026-08-20
**Rounds**: 1 (reviewer → resolver)

## Review Verdict: CRITICAL → FIXED

## Issues Found
| # | Severity | Location | Problem | Status |
|---|----------|----------|---------|--------|
| 1 | critical | Global (`constructor_id` usage) | No `/constructors/{id}` endpoint to resolve a display name — forces frontend to hardcode a name map | Fixed |
| 2 | critical | Forward compatibility / `inputs` / `/explain` | Forward-compat claim references `constructor_recent_form` as overridable, but `inputs` never actually contained it — self-contradicting schema | Fixed |
| 3 | major | `/races/{id}/prediction/explain` | Feature importances are a global model property, wrongly nested under a per-race path | Fixed — moved to `/models/{model_version}/explain` |
| 4 | major | Race `status` enum | Only `upcoming`/`completed` — no way to represent postponed/cancelled races | Fixed — added `postponed`/`cancelled` |
| 5 | major | Accuracy tracker `per_driver[]` | `actual_status` inconsistently shown (present for DNF example, absent for finished example) | Fixed — always present |
| 6 | major | Head-to-head coverage | Only driver compare existed; "team head-to-head" (explicit v1 scope) had no endpoint | Fixed — added `/constructors/compare` |
| 7 | major | Circuit `lap_record` | Not documented as nullable for a circuit's first-ever GP | Fixed |
| 8 | major | Standings `trend` | "Last N races" — N never specified, agents would diverge | Fixed — pinned to "every completed race so far this season" |
| 9 | major | Replay `laps[]` | No spec for DNF'd drivers' lap arrays or `gap_to_leader_s` once lapped | Fixed — truncation + gap semantics documented |
| 10 | minor | `/explain`, `/accuracy` error parity | Didn't state whether they mirror `/prediction`'s 409 | Fixed (moot for `/explain` after the move; explicit for `/accuracy`) |
| 11 | minor | Season/Calendar | No `GET /seasons` to list browsable years | Fixed |
| 12 | minor | Pre-FastF1-coverage races | No documented behavior for replay/prediction before ~2018 | Fixed — explicit 404 vs. 409 distinction |
| 13 | minor | Driver-compare edge case | No behavior for a driver absent from the requested season | Fixed — explicit 404 |
| 14 | minor | Standings mid-season transfer | Ambiguous whether `constructor_id` is current team, and how points are attributed | Fixed — clarified per real F1 convention |
| 15 | nit | Timestamp conventions | Race `date` is date-only but conventions section implied full ISO 8601 everywhere | Fixed — one-line clarification, no new field added |

**0 issues declined** — every finding was directly actionable without reintroducing v1.1+ scope or contradicting another fix.

## Simplifications Applied
- Kept all four accuracy metrics (MAE, DNF Brier score, rank correlation, podium hit rate) — reviewer agreed all are justified by the explicit "visible backtested accuracy" requirement.
- Added a precise mathematical definition of `podium_hit_rate` in prose instead of leaving it inferable only from example numbers.

## Changes Made
- Added two new resources: `GET /constructors/{id}` and `GET /constructors/compare`.
- Added `GET /seasons` (list of browsable years).
- Moved `/races/{id}/prediction/explain` → `/models/{model_version}/explain` (model-level, not race-level).
- Expanded the prediction `inputs` schema with a `derived_features` block enumerating every model feature, making the what-if forward-compatibility claim actually true.
- Extended race `status` enum with `postponed`/`cancelled`, with defined effects on `results`, prediction, and accuracy endpoints.
- Documented nullability, array-length, and edge-case behavior in half a dozen previously-ambiguous spots (lap_record, replay DNF truncation, standings trend window, mid-season transfers, pre-2018 coverage, season-absent driver/constructor lookups).
- Inlined `constructor_name` alongside `constructor_id` in race results and standings rows, matching the existing `circuit_name` pattern.

## Reviewer's Summary
"The document is well organized, uses a consistent ID/naming scheme, correctly omits the live-dashboard/what-if/bulletin/game endpoints that were cut from v1, and generally keeps the schema appropriately minimal for a solo learning project. However, it has real gaps that would cause exactly the implementation drift it's meant to prevent... None of these require a redesign — they're additive fixes — but they should be resolved before either agent starts building."

## Resolver's Notes
No items declined. All critical/major/minor findings were fixed as directly recommended; the one nit (timestamp field naming) was addressed with a one-line clarification rather than adding a new `start_time` field, per instructions to avoid scope creep.
