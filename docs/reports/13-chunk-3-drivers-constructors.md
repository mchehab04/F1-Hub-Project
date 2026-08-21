# Stage 13 — Chunk 3 (drivers/constructors profile + compare): backend verified, frontend built directly

**Date**: 2026-08-21
**Status**: Complete, fully verified end-to-end including in a browser. First chunk executed entirely under the new Codex-backend + Claude-frontend-direct model (Gemini dropped, see `docs/reports/12-standings-chunk-2.md` and `docs/orchestration.md`).

## Backend chunk 3 — Codex, verified

Dispatched via the `multi-agent-mcp-orchestration` skill per established practice. Implemented against `docs/api-contract.md` lines 312-381:

- `GET /api/v1/drivers/{driver_id}` — direct read from the `drivers` table.
- `GET /api/v1/drivers/compare?driver_a=&driver_b=&season=` — head-to-head computed from `race_entries` joined to `races`, scoped by season or career. `qualifying_wins` compares `grid_position` per shared race (the only qualifying-adjacent field in the schema — no dedicated qualifying table); `race_finish_wins` compares `finish_position`; `points` sums per driver. Only races where both drivers have an entry count.
- `GET /api/v1/constructors/{constructor_id}` — direct read, `current_drivers` derived from `drivers.current_constructor_id`.
- `GET /api/v1/constructors/compare?constructor_a=&constructor_b=&season=` — independent per-constructor tallies (race wins, points, podiums) from `race_entries`, not pairwise like the driver endpoint, since each race has two entries per constructor.
- 404s on unknown IDs and on "did not race/compete in season `<year>`" per contract.

Codex could not run pytest itself (same known sandbox limitation as prior chunks — no fastapi in its shell's Python) and said so explicitly instead of fabricating output.

Verified independently:
- Found the project actually has a `backend/.venv` (previously unused in this session — earlier commands were hitting the wrong `python` on PATH). All 10 new tests pass, full suite (15 tests) passes.
- Live spot-check against real 2024 data on a fresh server: driver IDs use Jolpica's `max_verstappen` (not `verstappen`) — confirmed by querying the DB directly, not a bug in this chunk's code. `max_verstappen` vs `perez` 2024 compare returns 399 vs 138 points, 21-3 qualifying wins, 23-1 race wins — matches the real lopsided 2024 teammate battle. `red_bull` vs `mclaren` compare points (537 vs 609) match the standings endpoint's already-verified season totals exactly.
- Found and could not resolve a pre-existing orphaned TCP listener on port 8000 (PID doesn't map to any live process in either `netstat`/PowerShell `Get-Process` — a genuinely dead listener, not something `taskkill`/`Stop-Process` could touch). Worked around it by verifying on port 8001 instead of chasing it further; not a chunk 3 regression, flagged here in case it recurs.

## Frontend chunk 3 — built directly (per rule 4, Gemini dropped)

New pages, following the exact patterns from `frontend/app/standings/page.tsx` and `races/[raceId]/page.tsx` (loading/error states, shared `globals.css` classes):

- `frontend/app/drivers/[driverId]/page.tsx`, `frontend/app/constructors/[constructorId]/page.tsx` — profile pages with career stat grids (reusing the existing `.circuit-stats-grid`/`.stat-item` classes from the circuit card), cross-links between driver ↔ constructor.
- `frontend/app/drivers/compare/page.tsx`, `frontend/app/constructors/compare/page.tsx` — compare pages. Scoping decision: the contract has no "list all drivers/constructors" endpoint, so rather than free-text ID inputs (error-prone given IDs like `max_verstappen`), the compare pages populate dropdowns from `getDriverStandings`/`getConstructorStandings` for a selected season, then let the user toggle Season vs. Career scope independently of which season's roster is shown. Both pages needed a `Suspense` boundary around their `useSearchParams()` usage — `next build` failed without it (`missing-suspense-with-csr-bailout`), fixed by splitting each into an outer default export + inner `*Content` component.
- `frontend/app/standings/page.tsx` — driver_id and constructor_name/id cells in both tables now link to the new profile pages; added "Compare Drivers"/"Compare Constructors" nav links.
- `frontend/app/globals.css` — added `.compare-form`/`.compare-field` and a `.results-table td a` rule so the new in-table links don't pick up default blue/underline styling.

`frontend/lib/api.ts` already had the `Driver`/`Constructor` types and `getDriver`/`compareDrivers`/`getConstructor`/`compareConstructors` client functions scaffolded from earlier work — no changes needed there.

## Verification

- `npx tsc --noEmit`: clean.
- `npm run build`: failed once on the missing Suspense boundary (caught and fixed as above), clean on retry.
- Booted backend (port 8001, working around the orphaned 8000 listener) and frontend dev server, used the `playwright` MCP server for real interaction: standings → click driver → profile page → "Compare Drivers" (query param correctly prefilled Driver A) → selected Driver B → verified the head-to-head table renders and its point totals match the standings page exactly → toggled Season/Career scope, confirmed the season selector hides in career mode and the response's `season: null` renders as "— Career". Also checked a constructor profile (current_drivers rendered as links) and a 404 driver ID (renders the exact backend error message, not a generic failure).
- Playwright's `filename`-targeted screenshot/snapshot calls silently wrote to the repo root instead of `frontend/.playwright-mcp/` (auto-named calls behaved correctly) — cleaned up the two stray files (`standings.png`, `standings2.yml`) before committing; noting this in case it happens again in a future chunk.

## Files touched

- `backend/app/api/v1/drivers.py`, `backend/app/api/v1/constructors.py`, `backend/app/schemas/drivers.py` (new), `backend/app/schemas/constructors.py` (new), `backend/tests/test_drivers.py` (new), `backend/tests/test_constructors.py` (new) — Codex
- `frontend/app/drivers/[driverId]/page.tsx` (new), `frontend/app/drivers/compare/page.tsx` (new), `frontend/app/constructors/[constructorId]/page.tsx` (new), `frontend/app/constructors/compare/page.tsx` (new), `frontend/app/standings/page.tsx` (links), `frontend/app/globals.css` (compare form + table-link styles) — Claude, direct

## Next stage

Chunk 4 (replay endpoint + visualization), or one of the ML chunks (5-8: feature engineering, training, prediction+explainability, accuracy tracker) — worth confirming with the user which to prioritize next.
