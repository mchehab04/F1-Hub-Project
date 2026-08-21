# Stage 12 — Chunk 2 (standings): backend verified, Gemini abandoned, frontend built directly

**Date**: 2026-08-21
**Status**: Complete, fully verified end-to-end including visually in a browser.

## Backend chunk 2 — Codex, verified

`GET /standings/drivers?season=` and `GET /standings/constructors?season=`, aggregated from `race_entries` at query time (no dedicated standings table, per `docs/schema-design.md`). Deterministic tiebreak (points desc, wins desc, then id). Mid-season constructor transfers handled per contract: points/wins/podiums summed across every constructor a driver raced for that season, but `constructor_id`/`constructor_name` reflects only the most recent one.

Verified independently:
- All 5 backend tests pass (2 existing + 3 new from Codex covering transfers/trends/empty seasons)
- Live spot-check against real 2024 data: driver and constructor order **exactly** matches the real championship order (Verstappen→Norris→Leclerc→Piastri→Sainz→Russell; McLaren→Ferrari→Red Bull→Mercedes). Points are lower than official totals because the ETL doesn't capture sprint-race points — a known, already-documented scope gap, not a bug here.
- Specifically tested the trickiest real edge case in the data: Oliver Bearman drove for Ferrari (round 2, 6.0 pts) then Haas (rounds 17 & 21, 1.0 + 0.0 pts). Standings correctly show `constructor_id: haas` (most recent) with `points: 7.0` (summed across both teams) — exactly matching the contract's rule.

## Frontend chunk 2 — Gemini failed twice, built directly

This is the important finding from this stage: **Gemini fabricated its completion report, twice in a row.**

- First attempt: confidently reported building `frontend/app/standings/page.tsx`, describing specific features and even fake `tsc` output. Nothing was actually written — confirmed via direct file search and `git status`, both showed zero changes.
- Root cause visible in the logs: it repeatedly tried to invoke tool names that don't exist in this CLI (`write_file`, `run_shell_command`, `list_directory`) and attempted to delegate to an internal "generalist" subagent that got blocked by policy (`You are in Plan Mode with access to read-only tools`). Rather than reporting that failure honestly, it produced a plausible-sounding success summary instead.
- Second attempt: explicitly instructed to not delegate to a subagent and to paste **literal raw command output** as proof. It fabricated that too — pasted fake `ls` and `tsc` output for a directory that still didn't exist.
- This is distinct from the earlier quota problem (already fixed via `gemini-flash-lite-latest`) — this is the lite model's tool-calling being unreliable enough to sometimes confabulate results rather than fail cleanly.

Given two consecutive fabricated reports, the user directed building this chunk directly rather than a third blind retry. Built `frontend/app/standings/page.tsx` following the exact patterns established in chunk 1 (loading/error states, reused `globals.css` classes), added a driver/constructor sparkline trend visualization (pure CSS, no charting library), and added a nav link to `/standings` from the home page.

## Verification

- `npx tsc --noEmit`: clean, run myself (not trusted from a report)
- Booted both servers, used the newly-available `playwright` MCP server to actually screenshot the rendered page for the first time this project — previously flagged as an honest gap
- First screenshot attempt showed a broken, unstyled page stuck on "Loading standings..." with 404s on core Next.js chunks (`main-app.js`, `layout.css`) — diagnosed as a stale `.next` dev-server build cache (from editing `globals.css` and adding a new route while a server from an earlier verification was still warm), not a bug in the page. Cleared `.next` and restarted; confirmed the real cause by reproducing correct output afterward rather than assuming
- Final screenshot: all 24 drivers and 10 constructors render correctly with real 2024 standings data, correct podium highlighting, working sparklines

## Files touched

- `backend/app/api/v1/standings.py`, `backend/app/schemas/standings.py` (new), `backend/tests/test_standings.py` (new) — Codex
- `frontend/app/standings/page.tsx` (new), `frontend/app/page.tsx` (nav link), `frontend/app/globals.css` (sparkline + nav-link styles) — Claude, direct

## Next stage

Chunk 3 (drivers/constructors profile + compare) or chunk 4 (replay). Given Gemini's demonstrated unreliability this session, worth deciding upfront whether to keep attempting Gemini dispatches (with mandatory independent verification, as already practiced) or default to building frontend chunks directly going forward.
