# Stage 14 — Chunk 4 (race replay): backend verified, frontend built directly

**Date**: 2026-08-21
**Status**: Complete, fully verified end-to-end including in a browser.

## Backend chunk 4 — Codex, verified

Dispatched via the `multi-agent-mcp-orchestration` skill. Implemented `GET /api/v1/races/{race_id}/replay` against `docs/api-contract.md`'s "Replay" section, reading directly from the existing `replay_laps` table (already populated by `backend/etl/fetch_fastf1.py` from earlier chunks — no new ETL work).

Error handling mirrors the 404-vs-409 convention already established for `/prediction` and `/accuracy`:
- 404 `race not found` for unknown race_id.
- 404 (not 409) for races before 2018 — FastF1 coverage will never exist for them, per the contract's explicit distinction.
- 409 for a race that exists but isn't `"completed"` yet (upcoming/postponed/cancelled) — the "not yet, but could be later" case.
- 404 for a completed, post-2018 race with zero `replay_laps` rows — a judgment call for a case the contract doesn't explicitly spell out (a genuine ETL data gap rather than an expected state); Codex flagged this itself as a judgment call rather than silently deciding, which is exactly the right call.

Codex again could not run pytest itself (its sandboxed shell has no fastapi/pytest installed, and it couldn't invoke the project's `backend/.venv` python either — same known Windows Store python-alias sandbox limitation as prior chunks) and said so explicitly instead of fabricating results.

Verified independently:
- All 5 new tests pass; full suite now at 20/20.
- Live spot-check against real 2024 Bahrain data: `total_laps: 57` matches `races.total_laps`; drivers who DNF'd (`albon`, `bottas`, confirmed via direct DB query of `race_entries.status`) have 56-lap arrays instead of 57 — correctly truncated at the ETL layer, not padded by this endpoint.
- 409/pre-2018 paths have no real-data example to test live since only season 2024 is ingested (no upcoming or pre-2018 races exist in the dataset) — covered instead by Codex's synthetic-fixture unit tests, which is the correct fallback here.
- Hit the same pre-existing orphaned port-8000 TCP listener from chunk 3 again (still unresolvable via `taskkill`/`Stop-Process` — the PID doesn't map to a live process either time). Verified on port 8001 again; flagging a third time in case this is worth a machine-level fix outside this project.

## Frontend chunk 4 — built directly

New page `frontend/app/races/[raceId]/replay/page.tsx`: a lap-by-lap replay viewer rather than a multi-line position chart, to stay consistent with the project's established "no charting library" approach (pure CSS, same as the standings sparklines). Controls: Play/Pause (auto-advances one lap per 500ms via `setInterval`, cleaned up on unmount/pause), Prev/Next lap buttons, and a range slider. For the currently selected lap, shows a leaderboard table (reusing `.results-table`/`.podium-1/2/3` styling) built by finding each driver's entry at that lap number and sorting by position; drivers who don't yet have an entry at the selected lap (retired before it, per the DNF-truncated arrays) are listed separately under "Already retired by lap N" rather than silently disappearing. Both the leaderboard and the retired list link to the driver profile pages built in chunk 3.

Added a "Watch Replay" link on the race detail page (`frontend/app/races/[raceId]/page.tsx`), shown only when `status === 'completed' && season >= 2018` — matching the backend's error conditions so users don't get routed into a 404/409 from the UI itself.

New CSS: `.replay-controls`, `.replay-slider`, `.replay-lap-label` in `globals.css`.

`frontend/lib/api.ts` already had `ReplayResponse`/`getReplay` scaffolded from earlier work — no changes needed there.

## Verification

- `npx tsc --noEmit`: clean.
- `npm run build`: clean, no Suspense/prerender issues this time (this page doesn't use `useSearchParams`).
- Real browser check via the `playwright` MCP server: navigated race detail → clicked "Watch Replay" → confirmed lap 1 leaderboard (20 drivers, positions/gaps match the live API response) → scrubbed to lap 56 (`sargeant` correctly shown as the one driver retired by then, `albon`/`bottas` still present since their last recorded lap is exactly 56) → advanced to the final lap 57 (exactly the 10 real finishers in the exact real finishing order, exactly the 10 real DNF drivers listed as retired — both matching the race-results table byte-for-byte) → confirmed Play/Next both correctly disable at the final lap.
- Hit a real environment issue during verification, not a code bug: the dev server's default port 3000 was held by an orphaned `node.exe` process from an earlier session (unlike the port-8000 listener, this one *did* resolve to a real process and `Stop-Process` cleared it). Backend CORS (`backend/app/core/config.py`) only allows `http://localhost:3000`, so the first attempt on the fallback port 3002 failed with a CORS error before this was diagnosed and fixed — noting this since it's a recurring class of stale-process issue this session, distinct each time (killable vs. not).

## Files touched

- `backend/app/api/v1/races.py` (added `get_replay` implementation), `backend/app/schemas/replay.py` (new), `backend/tests/test_replay.py` (new) — Codex
- `frontend/app/races/[raceId]/replay/page.tsx` (new), `frontend/app/races/[raceId]/page.tsx` (Watch Replay link), `frontend/app/globals.css` (replay control styles) — Claude, direct

## Next stage

ML chunks (5-8: feature engineering, training, prediction+explainability endpoints, accuracy tracker) are the remaining backlog — worth confirming with the user which to prioritize next, and whether scikit-learn training should happen as its own dispatch or be broken down further.
